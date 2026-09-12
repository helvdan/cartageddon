import pyarrow as pa
from collections import defaultdict

from related_schemas.category import (
    CATEGORY_SCHEMA,
    CATEGORY_DESCRIPTION_SCHEMA,
    CATEGORY_PATH_SCHEMA,
)
from related_schemas.product import (
    PRODUCT_SCHEMA,
    STOCK_STATUS_SCHEMA,
    PRODUCT_DESCRIPTION_SCHEMA,
    LENGTH_CLASS_SCHEMA,
    WEIGHT_CLASS_SCHEMA,
    TAX_CLASS_SCHEMA,
    MANUFACTURER_SCHEMA,
    REVIEW_SCHEMA
)


class MissingTableError(KeyError):
    def __init__(self, oc_table_name: str):
        super().__init__(oc_table_name)
        self.oc_table_name = oc_table_name

    def __str__(self) -> str:
        return f"Таблица Open Cart '{self.oc_table_name}' не найдена в SCHEMAS"


class MutableSchema:

    def __init__(self, schema: pa.Schema):
        self._schema = schema

    @property
    def schema(self) -> pa.Schema:
        return self._schema

    def add_metadata(self, **metadata) -> "MutableSchema":
        existing = self._schema.metadata or {}
        b_meta = {k.encode('utf-8'): v.encode('utf-8') for k, v in metadata.items()}
        updated = {**existing, **b_meta}

        self._schema = self._schema.with_metadata(updated)
        return self

    def remove_field(self, field_name: str) -> "MutableSchema":
        """Удаляет поле из схемы по его имени"""
        # Ищем индекс поля по имени
        try:
            index = self._schema.get_field_index(field_name)
            if index != -1:
                # Метод .remove() у pa.Schema удаляет по индексу и сохраняет метаданные
                self._schema = self._schema.remove(index)
        except KeyError:
            pass  # Если поля нет, просто ничего не делаем
        return self

    # Пробрасываем стандартные полезные свойства оригинальной схемы
    @property
    def metadata(self):
        return self._schema.metadata

    @property
    def names(self):
        return self._schema.names

    @property
    def types(self):
        return self._schema.types

    def __getitem__(self, item):
        return self._schema[item]

    def __repr__(self):
        return f"MutableSchema(\n{self._schema.__repr__()}\n)"


class OpenCartSchema:

    def __init__(self, single_language=False):
        self._schema = {
            "oc_product_description": MutableSchema(PRODUCT_DESCRIPTION_SCHEMA),
            "oc_stock_status": STOCK_STATUS_SCHEMA,
            "oc_tax_class": TAX_CLASS_SCHEMA,
            "oc_manufacturer": MANUFACTURER_SCHEMA,
            "oc_weight_class": WEIGHT_CLASS_SCHEMA,
            "oc_length_class": LENGTH_CLASS_SCHEMA,
            "oc_product": PRODUCT_SCHEMA,
            "oc_review": REVIEW_SCHEMA,
            "oc_category": CATEGORY_SCHEMA,
            "oc_category_path": CATEGORY_PATH_SCHEMA,
            "oc_category_description": MutableSchema(CATEGORY_DESCRIPTION_SCHEMA),
        }

        if single_language:
            self._schema.pop('oc_language', None)
            self._schema['oc_product_description'].add_metadata(join_to='oc_product').remove_field('language_id')
            self._schema['oc_category_description'].add_metadata(join_to='oc_category').remove_field('language_id')

        self.oc_tables = set(self._schema)

    def get_join_map(self):
        tables_to_join = defaultdict(list)

        for oc_table_name, schema in self._schema.items():
            metadata = schema.metadata or {}

            if b'join_to' in metadata:
                main_table = metadata[b"join_to"].decode("utf-8")
                tables_to_join[main_table].append(oc_table_name)

        return dict(tables_to_join)

    def get_foreign_keys(self, oc_table_name):
        schema = self._get_schema(oc_table_name)
        fks = []
        for field in schema:
            if field.metadata and b"foreign_key" in field.metadata:
                fk_column = field.name
                target_table = field.metadata[b"foreign_key"].decode()
                on_delete = field.metadata.get(b"on_delete", b"DO_NOTHING").decode()
                fks.append((fk_column, target_table, on_delete))
        return fks

    def get_pg_tables(self):
        tables = []
        for oc_table_name in self.oc_tables:
            oc_table = self.get_pg_table_name(oc_table_name)
            tables.append(oc_table)
        return tables

    def get_pg_table_name(self, oc_table_name):
        schema = self._get_schema(oc_table_name)
        return schema.metadata[b"pg_name"].decode("utf-8")

    def get_pg_columns(self, headers, oc_table_name, *joined_tables):
        pg_columns = []

        # 1. Обрабатываем главную таблицу
        main_schema = self._get_schema(oc_table_name)
        for field in main_schema:
            # Проверяем, является ли поле первичным ключом
            if self._field_is_pk(field):
                pg_columns.append("id")
                continue

            if field.name in headers:
                pg_columns.append(field.name)

        # 2. Добавляем колонки из присоединенных таблиц
        for oc_dep_table in joined_tables:
            dep_schema = self._get_schema(oc_dep_table)
            for field in dep_schema:
                if self._field_is_pk(field):
                    continue  # Выбрасываем первичный ключ зависимой таблицы

                if field.name in headers and field.name not in pg_columns:
                    pg_columns.append(field.name)

        return [f'"{col}"' for col in pg_columns]

    def get_s3_fields(self):
        s3_fields_mapping = {}

        for oc_table_name in self.oc_tables:
            schema = self._get_schema(oc_table_name)
            s3_fields = []
            for field in schema:
                if self._field_is_s3(field):
                    s3_fields.append(field.name)

            if s3_fields:
                s3_fields_mapping[oc_table_name] = s3_fields

        return s3_fields_mapping

    def get_pyarrow_schema(self, oc_table_name):
        schema = self._get_schema(oc_table_name)
        if isinstance(schema, MutableSchema):
            return schema.schema

        return schema

    def _get_schema(self, oc_table_name):
        if oc_table_name not in self.oc_tables:
            raise MissingTableError(oc_table_name)
        return self._schema[oc_table_name]

    @staticmethod
    def _field_is_pk(field):
        if field.metadata and b"primary_key" in field.metadata:
            return field.metadata[b"primary_key"].decode("utf-8") == "True"
        return False

    @staticmethod
    def _field_is_s3(field):
        if field.metadata and b"upload_to_s3" in field.metadata:
            return field.metadata[b"upload_to_s3"].decode("utf-8") == "True"
        return False

    def keys(self):
        return self._schema.keys()

    def items(self):
        return self._schema.items()

    def __getitem__(self, item):
        return self._schema[item]
