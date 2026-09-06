import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List

from schema import get_s3_fields
import boto3

from artifacts import ParquetArtifact
from stages.base import Stage


class S3ImageUploadStage(Stage):
    artifact_cls = ParquetArtifact
    postfix = "uploaded"
    name = "S3_UPLOAD"
    logger = logging.getLogger(name)

    def _upload_file(self, s3_client, local_path: str, s3_key: str, bucket_name: str) -> bool:
        """Атомарная функция загрузки одного файла."""
        try:
            s3_client.upload_file(
                Filename=local_path,
                Bucket=bucket_name,
                Key=s3_key
            )
            return True
        except Exception as e:
            self.logger.error(f"Ошибка загрузки файла {local_path} -> S3: {e}")
            return False

    def run(self, artifacts: Dict[str, ParquetArtifact]) -> None:
        s3_fields_mapping = get_s3_fields()
        print(s3_fields_mapping)

        for oc_table_name in artifacts:
            if oc_table_name not in s3_fields_mapping:
                continue

            print(oc_table_name)
            artifact = artifacts[oc_table_name]
            for column in s3_fields_mapping[oc_table_name]:
                relative_paths = artifact.get_unique_image_paths(column)
                print(relative_paths)

        return



        # Шаг 1: Извлекаем относительные пути через добавленный в артефакт метод Polars
        self.logger.info("Извлечение путей к изображениям из Parquet с помощью Polars...")


        if not relative_paths:
            self.logger.info("Валидные пути к изображениям в артефакте не найдены.")
            return

        # Получаем настройки путей и S3 из глобального контекста рантайма
        image_base_dir = self.global_context.get_opencart_image_dir()
        s3_bucket = self.global_context.get_s3_bucket_name()
        s3_config = self.global_context.get_s3_config()
        max_workers = getattr(self.global_context, "s3_max_workers", 16)

        # Шаг 2: Фильтруем и готовим абсолютные локальные пути
        upload_tasks = []
        for rel_path in relative_paths:
            local_full_path = os.path.join(image_base_dir, rel_path)
            if os.path.exists(local_full_path):
                upload_tasks.append({"local_path": local_full_path, "s3_key": rel_path})
            else:
                self.logger.warning(f"Файл не найден на диске: {local_full_path}")

        self.logger.info(f"Найдено локально файлов для отправки: {len(upload_tasks)}")

        if not upload_tasks:
            return

        # Шаг 3: Многопоточная загрузка (Load)
        # boto3 client является потокобезопасным (thread-safe)
        s3_client = boto3.client("s3", **s3_config)
        success_count = 0

        self.logger.info(f"Запуск пула потоков для S3. Воркеров: {max_workers}")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    self._upload_file,
                    s3_client=s3_client,
                    local_path=task["local_path"],
                    s3_key=task["s3_key"],
                    bucket_name=s3_bucket
                ): task for task in upload_tasks
            }

            for i, future in enumerate(as_completed(futures), 1):
                if future.result():
                    success_count += 1

                if i % 500 == 0 or i == len(upload_tasks):
                    self.logger.info(f"Прогресс отправки: {i}/{len(upload_tasks)} файлов...")

        self.logger.info(
            f"🎉 Стадия S3_IMAGE_UPLOAD успешно завершена. "
            f"Загружено картинок: {success_count}/{len(upload_tasks)}"
        )


if __name__ == '__main__':
    from pipeline import RunTimeContext
    from pathlib import Path

    context = RunTimeContext(
        work_dir="/tmp",
        chunk_size=5000,
        pg_user="django_user",
        pg_password="django_password",
        pg_host="postgres",
        pg_port=5432,
        pg_database="django_project_db",
    )
    extract_stage = S3ImageUploadStage(context)
    extract_stage.run(
        {
            # 'oc_product': ParquetArtifact(Path("/tmp/oc_product.oc_product_description.joined.parquet")),

            # Стандартные нормализованные таблицы и справочники
            # 'oc_review': ParquetArtifact(Path("/tmp/cartageddon/oc_review.checked.parquet")),
            'oc_product': ParquetArtifact(Path("/tmp/cartageddon/oc_product.normalized.parquet")),
            # 'oc_manufacturer': ParquetArtifact(Path("/tmp/oc_manufacturer.normalized.parquet")),
            # 'oc_stock_status': ParquetArtifact(Path("/tmp/oc_stock_status.normalized.parquet")),
            # 'oc_tax_class': ParquetArtifact(Path("/tmp/oc_tax_class.normalized.parquet")),
            # 'oc_length_class': ParquetArtifact(Path("/tmp/oc_length_class.normalized.parquet")),
            # 'oc_weight_class': ParquetArtifact(Path("/tmp/oc_weight_class.normalized.parquet")),
        }
    )
