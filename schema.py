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


SCHEMAS = {
    "oc_product_description": PRODUCT_DESCRIPTION_SCHEMA,
    "oc_stock_status": STOCK_STATUS_SCHEMA,
    "oc_tax_class": TAX_CLASS_SCHEMA,
    "oc_manufacturer": MANUFACTURER_SCHEMA,
    "oc_weight_class": WEIGHT_CLASS_SCHEMA,
    "oc_length_class": LENGTH_CLASS_SCHEMA,
    "oc_product": PRODUCT_SCHEMA,
    "oc_review": REVIEW_SCHEMA
}


OC_TABLES = set(SCHEMAS)


class MissingTableError(KeyError):
    def __init__(self, oc_table_name: str):
        super().__init__(oc_table_name)
        self.oc_table_name = oc_table_name

    def __str__(self) -> str:
        return f"Таблица Open Cart '{self.oc_table_name}' не найдена в SCHEMAS"


def _get_schema(oc_table_name):
    if oc_table_name not in OC_TABLES:
        raise MissingTableError(oc_table_name)
    return SCHEMAS[oc_table_name]


def get_foreign_keys(oc_table_name):
    schema = _get_schema(oc_table_name)
    fks = []
    for field in schema:
        if field.metadata and b"foreign_key" in field.metadata:
            fk_column = field.name
            target_table = field.metadata[b"foreign_key"].decode()
            on_delete = field.metadata.get(b"on_delete", b"DO_NOTHING").decode()
            fks.append((fk_column, target_table, on_delete))
    return fks


def get_pg_table_name(oc_table_name):
    schema = _get_schema(oc_table_name)
    return schema.metadata[b"pg_name"].decode("utf-8")


def get_pg_columns(oc_table_name, *joined_tables):
    pg_columns = []

    # 1. Обрабатываем главную таблицу
    main_schema = _get_schema(oc_table_name)
    for field in main_schema:
        # Проверяем, является ли поле первичным ключом
        if _field_is_pk(field):
            pg_columns.append("id")
            continue

        pg_columns.append(field.name)

    # 2. Добавляем колонки из присоединенных таблиц
    for oc_dep_table in joined_tables:
        dep_schema = _get_schema(oc_dep_table)
        for field in dep_schema:
            if _field_is_pk(field):
                continue  # Выбрасываем первичный ключ зависимой таблицы

            pg_columns.append(field.name)

    return pg_columns


def _field_is_pk(field):
    if field.metadata and b"primary_key" in field.metadata:
        return field.metadata[b"primary_key"].decode("utf-8") == "True"
    return False
