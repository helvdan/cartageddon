import argparse
import logging
import os

from common import PipelineContext
from pipeline import Pipeline
from schema import SCHEMAS
from stages import (
    ExtractTableStage,
    NormalizeValuesStage,
    CheckIntegrityStage,
    JoinTablesStage
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ETL Transform Pipeline с использованием классов Stage.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--work-dir",
        dest="work_dir",
        default="/tmp",
        help="Папка для хранения артифактов (pickle файлов)"
    )
    parser.add_argument(
        "--clean-run",
        action="store_true",
        dest="clean_run",
        default=True,
        help="Убрать за собой артефакты",
    )
    parser.add_argument(
        "--chunk-size",
        dest="chunk_size",
        default=5000,
        help="Папка для хранения артифактов (pickle файлов)"
    )
    parser.add_argument(
        '--tables',
        dest='tables',
        nargs='+',
        required=False,
        help='Список таблиц из БД Open Cart'
    )
    parser.add_argument(
        '--oc-user',
        dest='oc_user',
        default=os.environ.get('MYSQL_USER'),
        help='Пользователь БД Open Cart'
    )
    parser.add_argument(
        '--oc-password',
        dest='oc_password',
        default=os.environ.get('MYSQL_PASSWORD'),
        help='Пароль от БД Open Cart'
    )
    parser.add_argument(
        '--oc-host',
        dest='oc_host',
        default=os.environ.get('MYSQL_HOST', 'localhost'),
        help='Хост БД Open Cart'
    )
    parser.add_argument(
        '--oc-port',
        dest='oc_port',
        default=os.environ.get('MYSQL_PORT', 3306),
        help='Порт БД Open Cart'
    )
    parser.add_argument(
        '--oc-database',
        dest='oc_database',
        default=os.environ.get('MYSQL_DATABASE'),
        help='Имя БД Open Cart'
    )

    parser.add_argument(
        '--pg-user',
        dest='pg_user',
        default=os.environ.get('POSTGRES_USER'),
        help='Пользователь Postgres'
    )
    parser.add_argument(
        '--pg-password',
        dest='pg_password',
        default=os.environ.get('POSTGRES_PASSWORD'),
        help='Пароль Postgres'
    )
    parser.add_argument(
        '--pg-host',
        dest='pg_host',
        default=os.environ.get('POSTGRES_HOST'),
        help='Хост Postgres'
    )
    parser.add_argument(
        '--pg-port',
        dest='pg_port',
        default=os.environ.get('MYSQL_PORT', 5432),
        help='Порт Postgres'
    )
    parser.add_argument(
        '--pg-database',
        dest='pg_database',
        default=os.environ.get('POSTGRES_DB'),
        help='Имя БД Postgres'
    )

    parser.add_argument(
        '--single-language',
        dest='single_language',
        action='store_true',
        help='Убрать мультиязычность'
    )
    parser.add_argument(
        "--extract-tables",
        action="store_true",
        dest="extract_tables",
        help="Выгрузить таблицы из Open Cart",
    )
    parser.add_argument(
        "--normalize-values",
        action="store_true",
        dest="normalize_values",
        help="Запустить стадию normalize_values",
    )
    parser.add_argument(
        "--check-integrity",
        action="store_true",
        dest="check_integrity",
        help="Запустить стадию check_integrity",
    )
    parser.add_argument(
        "--join-tables",
        action="store_true",
        dest="join_tables",
        help="Запустить стадию join_tables",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        dest="debug",
        help="Влючить дебаг-логи",
    )

    return parser.parse_args()


def transform():
    args = parse_arguments()

    loglevel = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=loglevel, format="%(asctime)s [%(name)s] [%(levelname)s] %(message)s"
    )

    active_stages = set()
    if args.extract_tables:
        active_stages.add(ExtractTableStage.name)
    if args.normalize_values:
        active_stages.add(NormalizeValuesStage.name)
    if args.check_integrity:
        active_stages.add(CheckIntegrityStage.name)
    if args.join_tables:
        active_stages.add(JoinTablesStage.name)

    # Запуск пайплайна
    context = PipelineContext(
        work_dir=args.work_dir,
        single_language=args.single_language,
        chunk_size=int(args.chunk_size),

        # mysql
        oc_user=args.oc_user,
        oc_password=args.oc_password,
        oc_host=args.oc_host,
        oc_port=int(args.oc_port),
        oc_database=args.oc_database,

        # postgres
        pg_user=args.pg_user,
        pg_password=args.pg_password,
        pg_host=args.pg_host,
        pg_port=int(args.pg_port),
        pg_database=args.pg_database,
    )
    pipeline = Pipeline(context)

    tables = args.tables if args.tables else set(SCHEMAS.keys())

    pipeline.execute(tables, active_stages, clean_run=args.clean_run)


if __name__ == "__main__":
    transform()
