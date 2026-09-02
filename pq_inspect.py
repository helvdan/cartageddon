from pathlib import Path
import pyarrow.parquet as pq

# Укажите путь к папке, куда ваша стадия Normalize сохранила .parquet файлы
DATA_DIR = Path("/home/lmakeev/tmp")  # измените на ваш реальный путь


def inspect_parquet_files(directory: Path):
    # Находим все файлы с расширением .parquet
    parquet_files = list(directory.glob("*.parquet"))

    if not parquet_files:
        print(f"❌ В директории {directory} не найдено файлов .parquet")
        return

    for file_path in parquet_files:
        print("=" * 60)
        print(f"📄 Файл: {file_path.name}")
        print("=" * 60)

        # 1. Читаем только метаданные файла, чтобы узнать общее количество строк
        file_metadata = pq.read_metadata(file_path)
        print(f"📊 Всего строк в файле: {file_metadata.num_rows}")
        print(f"🗂 Количество колонок: {file_metadata.num_columns}")

        if file_metadata.num_rows == 0:
            print("⚠️ Файл пустой, читать нечего.\n")
            continue

        table_sample = pq.read_table(file_path).slice(0, 1)

        # Переводим эту одну строку в обычный питоновский словарь
        row_dict = table_sample.to_pydict()

        # Красиво выводим имя колонки, её тип и значение первой строки
        print(f"\n🔍 Структура и первая строка:")
        print(f"{'Название колонки':<25} | {'Тип данных':<15} | {'Значение'}")
        print("-" * 60)

        for field in table_sample.schema:
            col_name = field.name
            col_type = str(field.type)
            # Достаем первый элемент из списка значений этой колонки
            col_value = row_dict[col_name][0]

            print(f"{col_name:<25} | {col_type:<15} | {col_value}")
        print("\n")


if __name__ == "__main__":
    inspect_parquet_files(DATA_DIR)
