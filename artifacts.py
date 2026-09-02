import io
import pickle
from functools import cached_property
from pathlib import Path
from typing import Any, Optional, Iterable, Set, Generator

import polars as pl
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq


class Artifact:
    """
    Изолированная логика работы с таблицами Parquet (на движке PyArrow).
    Полностью скрывает бинарные структуры данных от бизнес-логики.
    """

    def __init__(self, path: Path):
        self.path = path
        self._table = None
        self._data = None

    def delete(self):
        self._data = None

        import gc
        gc.collect()

        self.path.unlink()

    @property
    def exists(self) -> bool:
        return self.path.exists()

    @property
    def _data_table(self) -> pa.Table:
        """Внутреннее ленивое чтение таблицы Parquet."""
        if self._table is None:
            self._table = pq.read_table(self.path)
        return self._table

    @cached_property
    def oc_table_name(self) -> str:
        return self.path.name.split(".", maxsplit=1)[0]

    def get_rows_iterable(self) -> Iterable[tuple[Any, list]]:
        """
        Возвращает ленивый итератор по строкам в формате (pk, row_data).
        """
        table = self._data_table
        pydict = table.to_pydict()
        col_names = table.schema.names
        pk_name = col_names[0]
        num_rows = table.num_rows

        for i in range(num_rows):
            row = [pydict[col][i] for col in col_names]
            pk = pydict[pk_name][i]
            yield pk, row

    def get_column_values(self, column_index: int) -> Set[Any]:
        """
        Высокоэффективное извлечение множества уникальных значений колонки.
        """
        table = self._data_table
        col_name = table.schema.names[column_index]
        return set(table[col_name].to_pylist())

    def __contains__(self, key: Any) -> bool:
        """
        Проверка наличия Primary Key в первой колонке таблицы.
        """
        table = self._data_table
        pk_name = table.schema.names[0]
        scalar_key = pa.scalar(key, type=table.schema.field(pk_name).type)
        return pc.any(pc.equal(table[pk_name], scalar_key)).as_py()

    def save(self, columns_data: list, schema: pa.Schema = None) -> None:
        raise NotImplementedError()

    def save_deleted_rows(self, source_artifact: 'Artifact', ids_to_delete: Set[Any]) -> None:
        """
        Бэкап удаляемых строк (сохраняет только совпадения по ids_to_delete).
        """
        table = source_artifact._data_table
        pk_name = table.schema.names[0]
        id_array = pa.array(list(ids_to_delete), type=table.schema.field(pk_name).type)
        mask = pc.is_in(table[pk_name], value_set=id_array)
        deleted_table = table.filter(mask)
        pq.write_table(deleted_table, self.path)

    def __str__(self):
        return f"<Artifact {self.path}>"

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.path.name}>"

    @property
    def data(self):
        return self._data


class PickleArtifact(Artifact):
    extension = "pkl"

    @property
    def data(self) -> Generator[tuple, None, None]:
        """
        Лениво читает данные с диска по одному чанку.
        Не держит всю таблицу в оперативной памяти.
        """
        # Открываем файл и поочередно вычитываем все записанные pickle-блоки
        with self.path.open("rb") as f:
            while True:
                try:
                    for row in pickle.load(f):
                        yield row
                except EOFError:
                    break

    def save(self, data: Generator[list, None, None], column_names: list[str]) -> None:
        """
        Принимает генератор чанков данных и последовательно пишет их на диск.
        """
        with self.path.open("wb") as f:
            for chunk in data:
                if chunk:  # Проверяем, что чанк не пустой
                    pickle.dump(chunk, f, protocol=pickle.HIGHEST_PROTOCOL)


class ParquetArtifact(Artifact):
    extension = "parquet"

    @cached_property
    def data(self) -> pl.LazyFrame:
        return pl.scan_parquet(self.path)

    def get_data_chunks(self, chunk_size: int) -> Generator[io.BytesIO, None, None]:
        df_collected = self.data.collect(streaming=True)

        for slice_df in df_collected.iter_slices(n_rows=chunk_size):
            if slice_df.is_empty():
                continue

            buffer = io.BytesIO()
            # Важно: отключаем заголовки, задаем явный маркер NULL
            slice_df.write_csv(buffer, include_header=False, null_value="")
            buffer.seek(0)
            yield buffer

    @cached_property
    def pk_name(self) -> str:
        return self.data.collect_schema().names()[0]

    def save(self, data: Any, schema: Optional[pa.Schema] = None) -> None:
        # Сценарий 1: На вход прилетел LazyFrame Polars (Стадия Transform)
        if isinstance(data, pl.LazyFrame):
            try:
                data.sink_parquet(self.path)
            except pl.exceptions.InvalidOperationError:
                # Присутствует блокирующая операция в плане запроса
                data.collect().write_parquet(self.path)

        # Сценарий 2: На вход прилетел DataFrame Polars (Стадия Transform для бэкапа broken_rows)
        elif isinstance(data, pl.DataFrame):
            data.write_parquet(self.path)

        # Сценарий 3: На вход прилетел список колонок list (Стадия Normalize)
        elif isinstance(data, list):
            if schema is None:
                raise ValueError("schema is required when saving raw list data to ParquetArtifact")

            table_to_save = pa.Table.from_arrays(data, schema=schema)
            pq.write_table(table_to_save, self.path)

        else:
            raise ValueError(f"ParquetArtifact.save received unsupported data type: {type(data)}")

    def get_broken_fks(self, fk_column: str, target_artifact: 'ParquetArtifact') -> pl.DataFrame:
        """
        Выполняет встроенный многопоточный Rust anti-join для поиска битых связей.
        Возвращает DataFrame со строками, которые нарушают целостность.
        """
        current_lazy = self.data
        target_lazy = target_artifact.data

        # Фильтруем дефолтные пустые значения OpenCart и ищем сирот
        broken_rows = current_lazy.filter(
            pl.col(fk_column).is_not_null() &
            (pl.col(fk_column) != 0)
        ).join(
            target_lazy.select([target_artifact.pk_name]),  # Берем только PK целевой таблицы
            left_on=fk_column,
            right_on=target_artifact.pk_name,
            how="anti"
        ).collect()  # Вычисляем силами Rust на всех ядрах

        return broken_rows

    def apply_cascading_cleanup(self, fk_column: str, broken_rows: pl.DataFrame, action: str) -> pl.LazyFrame:
        """
        Возвращает новый очищенный LazyFrame на основе правила (CASCADE или SET_NULL).
        """
        current_lazy = self.data

        if action == "CASCADE" and not broken_rows.is_empty():
            # Оставляем только те строки, чьих PK нет в списке битых
            return current_lazy.filter(~pl.col(self.pk_name).is_in(broken_rows[self.pk_name]))

        elif action == "SET_NULL" and not broken_rows.is_empty():
            # Зануляем битые внешние ключи
            return current_lazy.with_columns(
                pl.when(pl.col(fk_column).is_in(broken_rows[fk_column]))
                .then(None)
                .otherwise(pl.col(fk_column))
                .alias(fk_column)
            )

        return current_lazy

    def join(self, artifact: 'ParquetArtifact') -> 'ParquetArtifact':
        """
        Выполняет ленивый LEFT JOIN и сохраняет метаданные исходных таблиц.
        """
        joined_lazy = self.data.join(
            artifact.data,
            on=self.pk_name,
            how="left",
            coalesce=True
        )

        new_artifact = self.__class__(self.path)
        object.__setattr__(new_artifact, "data", joined_lazy)

        return new_artifact

    def deduplicate(self, subset: list[str], keep: str = "first") -> 'ParquetArtifact':
        """
        Возвращает новый экземпляр ParquetArtifact с обновленным графом вычислений.
        """

        deduped_lazy = self.data.unique(
            subset=subset,
            keep=keep,
            maintain_order=True
        )

        new_artifact = self.__class__(self.path)
        object.__setattr__(new_artifact, "data", deduped_lazy)

        return new_artifact
