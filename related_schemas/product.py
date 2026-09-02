import pyarrow as pa

from related_schemas.utils import pk_field, create_meta

PRODUCT_SCHEMA = pa.schema([
    pk_field("product_id"),

    # Базовые текстовые поля
    pa.field("model", pa.string(), metadata={"max_length": "64"}),
    pa.field("sku", pa.string(), metadata={"max_length": "64", "default": ""}),
    pa.field("upc", pa.string(), metadata={"max_length": "12", "default": ""}),
    pa.field("ean", pa.string(), metadata={"max_length": "14", "default": ""}),
    pa.field("jan", pa.string(), metadata={"max_length": "13", "default": ""}),
    pa.field(
        "isbn", pa.string(), metadata=create_meta(
            "value_to_none", {"max_length": "64", "nullable": "True"}, gauge="Не маркируется"
        )
    ),
    pa.field("mpn", pa.string(), metadata={"max_length": "64", "default": ""}),
    pa.field("location", pa.string(), metadata={"max_length": "128", "default": ""}),
    pa.field("quantity", pa.int32(), metadata={"default": "0"}),

    # Внешние ключи (В OpenCart это обычно INT)
    pa.field("stock_status_id", pa.int32(), metadata={
        "foreign_key": "oc_stock_status",
        "on_delete": "DO_NOTHING"
    }),
    pa.field("image", pa.string(), metadata={"max_length": "255", "nullable": "True"}),
    pa.field("manufacturer_id", pa.int32(), metadata={
        "foreign_key": "oc_manufacturer",
        "on_delete": "SET_NULL",
        "nullable": "True",
        "callback": "zero_to_none",
    }),

    # Булевы флаги и числа
    pa.field("shipping", pa.bool_(), metadata={
        "default": "True",
        "db_type": "TINYINT",
        "callback": "int_to_bool",
    }),
    pa.field("price", pa.decimal128(15, 4), metadata={"default": "0.0000"}),
    pa.field("points", pa.int32(), metadata={"default": "0"}),

    pa.field("tax_class_id", pa.int32(), metadata={
        "foreign_key": "oc_tax_class",
        "on_delete": "SET_NULL",
        "nullable": "True"
    }),

    # Даты
    pa.field(
        "date_available", pa.date32(), metadata=create_meta("value_to_none", gauge="0000-00-00")
    ),

    # Физические параметры (Высокая точность decimal128)
    pa.field("weight", pa.decimal128(15, 8), metadata={"default": "0.00000000"}),
    pa.field("weight_class_id", pa.int32(), metadata={
        "foreign_key": "oc_weight_class",
        "on_delete": "DO_NOTHING",
        "nullable": "True",
        "callback": "zero_to_none",
    }),
    pa.field("length", pa.decimal128(15, 8), metadata={"default": "0.00000000"}),
    pa.field("width", pa.decimal128(15, 8), metadata={"default": "0.00000000"}),
    pa.field("height", pa.decimal128(15, 8), metadata={"default": "0.00000000"}),
    pa.field("length_class_id", pa.int32(), metadata={
        "foreign_key": "oc_length_class",
        "on_delete": "DO_NOTHING",
        "nullable": "True",
        "callback": "zero_to_none",
    }),

    # Системные флаги
    pa.field("subtract", pa.bool_(), metadata={
        "default": "True",
        "callback": "int_to_bool",
    }),
    pa.field("minimum", pa.int32(), metadata={"default": "1"}),
    pa.field("sort_order", pa.int32(), metadata={"default": "0"}),
    pa.field("status", pa.bool_(), metadata={
        "default": "True", "callback": "int_to_bool"
    }),
    pa.field("viewed", pa.int32(), metadata={"default": "0"}),

    # Даты со временем (Timestamp)
    pa.field("date_added", pa.timestamp('ms'), metadata={
        "auto_now_add": "True",
        "callback": "normalize_date",
    }),
    pa.field("date_modified", pa.timestamp('ms'), metadata={
        "auto_now": "True",
        "callback": "normalize_date",
    }),

    pa.field("yandexmerchants", pa.bool_(), metadata={
        "default": "False",
        "callback": "int_to_bool",
    })
], metadata={"pg_name": "catalog_product"})


PRODUCT_DESCRIPTION_SCHEMA = pa.schema([
    pa.field("product_id", pa.int32(), metadata={"primary_key": "True"}),
    pa.field("name", pa.string(), nullable=True),
    pa.field("description", pa.string(), nullable=True, metadata={"callback": "to_html"}),
    pa.field("tag", pa.string(), nullable=True),
    pa.field("meta_title", pa.string(), nullable=True),
    pa.field("meta_description", pa.string(), nullable=True),
    pa.field("meta_keyword", pa.string(), nullable=True),
])


STOCK_STATUS_SCHEMA = pa.schema([
    pk_field("stock_status_id"),
    pa.field("name", pa.string(), metadata={"max_length": "32"}),
], metadata={"pg_name": "catalog_stockstatus"})


MANUFACTURER_SCHEMA = pa.schema([
    pk_field("manufacturer_id"),
    pa.field("name", pa.string(), metadata={"max_length": "64"}),
    pa.field("image", pa.string(), nullable=True, metadata={"max_length": "255", "nullable": "True"}),
    pa.field("sort_order", pa.int32(), metadata={"default": "0"}),
], metadata={"pg_name": "catalog_manufacturer"})


TAX_CLASS_SCHEMA = pa.schema([
    pk_field("tax_class_id"),
    pa.field("title", pa.string(), metadata={"max_length": "32"}),
    pa.field("description", pa.string(), metadata={"max_length": "255"}),

    # Даты со временем (Timestamp с миллисекундами)
    pa.field("date_added", pa.timestamp('ms'), metadata={
        "auto_now_add": "True",
        "callback": "normalize_date",
    }),
    pa.field("date_modified", pa.timestamp('ms'), metadata={
        "auto_now": "True",
        "callback": "normalize_date",
    }),
], metadata={"pg_name": "catalog_taxclass"})


LENGTH_CLASS_SCHEMA = pa.schema([
    pk_field("length_class_id"),
    pa.field("value", pa.decimal128(15, 8), metadata={"default": "0.00000000"}),
], metadata={"pg_name": "catalog_lengthclass"})


WEIGHT_CLASS_SCHEMA = pa.schema([
        pk_field("weight_class_id"),
        # Десятичное число высокой точности (15 знаков всего, 8 после запятой)
        pa.field("value", pa.decimal128(15, 8), metadata={"default": "0.00000000"}),
    ], metadata={"pg_name": "catalog_weightclass"})


REVIEW_SCHEMA = pa.schema([
    pk_field("review_id"),

    pa.field("product_id", pa.int32(), metadata={
        "foreign_key": "oc_product",
        "on_delete": "CASCADE",
        "verbose_name": "Товар"
    }),

    # Текстовые поля отзыва
    pa.field("author", pa.string(), metadata={
        "max_length": "64",
        "verbose_name": "Имя автора"
    }),
    pa.field("text", pa.string(), metadata={
        "type": "text",
        "verbose_name": "Текст отзыва"
    }),

    # Числовой рейтинг (Валидаторы оставляем на уровне Python/Django, в Parquet это int32)
    pa.field("rating", pa.int32(), metadata={
        "min_value": "1",
        "max_value": "5",
        "verbose_name": "Рейтинг"
    }),

    # Булево поле статуса модерации (TINYINT в MySQL)
    pa.field("status", pa.bool_(), metadata={
        "default": "False",
        "verbose_name": "Статус модерации",
        "callback": "int_to_bool"
    }),

    # Метки времени (Timestamp)
    pa.field("date_added", pa.timestamp('ms'), metadata={
        "auto_now_add": "True",
        "verbose_name": "Дата добавления",
        "callback": "normalize_date",
    }),
    pa.field("date_modified", pa.timestamp('ms'), metadata={
        "auto_now": "True",
        "nullable": "True",
        "verbose_name": "Дата изменения",
        "callback": "normalize_date",
    })
], metadata={"pg_name": "catalog_review"})
