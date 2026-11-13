import pyarrow as pa

from related_schemas.utils import create_meta, pk_field


CART_SCHEMA = pa.schema([
    pk_field("cart_id"),
    pa.field("api_id", pa.int32(), metadata={"default": "0"}),
    pa.field("customer_id", pa.int32(), metadata={"default": "0"}),
    pa.field("session_id", pa.string(), metadata={"max_length": "32"}),
    pa.field("product_id", pa.int32(), metadata={
        "foreign_key": "oc_product", "on_delete": "CASCADE"
    }),
    pa.field("quantity", pa.int32(), metadata={"default": "1"}),
    pa.field("date_added", pa.timestamp('ms'), metadata={
        "auto_now_add": "True", "callback": "normalize_date"
    }),
], metadata={"pg_name": "orders_cart"})


# Только поля целевой модели Order: язык и валюта в Django не хранятся.
# Поля расширения Simple присоединяются из ORDER_SIMPLE_FIELDS_SCHEMA.
ORDER_SCHEMA = pa.schema([
    pk_field("order_id"),
    pa.field("invoice_no", pa.int32(), metadata={"default": "0"}),
    pa.field("invoice_prefix", pa.string(), metadata={"max_length": "26"}),
    pa.field("store_id", pa.int32(), metadata={"default": "0"}),
    pa.field("store_name", pa.string(), metadata={"max_length": "64"}),
    pa.field("store_url", pa.string(), metadata={"max_length": "255"}),
    pa.field("customer_id", pa.int32(), metadata={"default": "0"}),
    pa.field("customer_group_id", pa.int32(), metadata={"default": "0"}),

    pa.field("firstname", pa.string(), metadata={"max_length": "32"}),
    pa.field("lastname", pa.string(), metadata={"max_length": "32"}),
    pa.field("email", pa.string(), metadata={"max_length": "96"}),
    pa.field("telephone", pa.string(), metadata={"max_length": "32"}),
    pa.field("fax", pa.string(), metadata={"max_length": "32"}),
    pa.field("custom_field", pa.string()),

    pa.field("payment_firstname", pa.string(), metadata={"max_length": "32"}),
    pa.field("payment_lastname", pa.string(), metadata={"max_length": "32"}),
    pa.field("payment_company", pa.string(), metadata={"max_length": "60"}),
    pa.field("payment_address_1", pa.string(), metadata={"max_length": "128"}),
    pa.field("payment_address_2", pa.string(), metadata={"max_length": "128"}),
    pa.field("payment_city", pa.string(), metadata={"max_length": "128"}),
    pa.field("payment_postcode", pa.string(), metadata={"max_length": "10"}),
    pa.field("payment_country", pa.string(), metadata={"max_length": "128"}),
    pa.field("payment_country_id", pa.int32()),
    pa.field("payment_zone", pa.string(), metadata={"max_length": "128"}),
    pa.field("payment_zone_id", pa.int32()),
    pa.field("payment_address_format", pa.string()),
    pa.field("payment_custom_field", pa.string()),
    pa.field("payment_method", pa.string(), metadata={"max_length": "128"}),
    pa.field("payment_code", pa.string(), metadata={"max_length": "128"}),

    pa.field("shipping_firstname", pa.string(), metadata={"max_length": "32"}),
    pa.field("shipping_lastname", pa.string(), metadata={"max_length": "32"}),
    pa.field("shipping_company", pa.string(), metadata={"max_length": "40"}),
    pa.field("shipping_address_1", pa.string(), metadata={"max_length": "128"}),
    pa.field("shipping_address_2", pa.string(), metadata={"max_length": "128"}),
    pa.field("shipping_city", pa.string(), metadata={"max_length": "128"}),
    pa.field("shipping_postcode", pa.string(), metadata={"max_length": "10"}),
    pa.field("shipping_country", pa.string(), metadata={"max_length": "128"}),
    pa.field("shipping_country_id", pa.int32()),
    pa.field("shipping_zone", pa.string(), metadata={"max_length": "128"}),
    pa.field("shipping_zone_id", pa.int32()),
    pa.field("shipping_address_format", pa.string()),
    pa.field("shipping_custom_field", pa.string()),
    pa.field("shipping_method", pa.string(), metadata={"max_length": "128"}),
    pa.field("shipping_code", pa.string(), metadata={"max_length": "128"}),
], metadata={"pg_name": "orders_order"})


ORDER_SIMPLE_FIELDS_SCHEMA = pa.schema([
    pk_field("order_id"),
    # JSON передается в PostgreSQL текстом; пустая строка означает SQL NULL.
    pa.field("metadata", pa.string(), metadata=create_meta("value_to_none", gauge="")),
    pa.field("patronymic", pa.string(), metadata={"max_length": "128"}),
    # FileField хранит путь; загрузка самого файла требует отдельного переноса.
    pa.field("upload", pa.string(), metadata={"max_length": "100"}),
    pa.field("example", pa.string()),
    pa.field("deliverytime", pa.string(), metadata={"max_length": "64"}),
    pa.field("deliverydate", pa.date32(), metadata={"callback": "parse_delivery_date"}),
    pa.field("bic", pa.string(), metadata={"max_length": "11"}),
    pa.field("settlement_account", pa.string(), metadata={"max_length": "20"}),
], metadata={"pg_name": "orders_order", "join_to": "oc_order"})


ORDER_HISTORY_SCHEMA = pa.schema([
    pk_field("order_history_id"),
    pa.field("order_id", pa.int32(), metadata={
        "foreign_key": "oc_order", "on_delete": "CASCADE"
    }),
    # В модели это IntegerField, а не ForeignKey.
    pa.field("order_status_id", pa.int32()),
    pa.field("notify", pa.bool_(), metadata={
        "default": "False", "callback": "int_to_bool"
    }),
    pa.field("comment", pa.string()),
    pa.field("date_added", pa.timestamp('ms'), metadata={"callback": "normalize_date"}),
], metadata={"pg_name": "orders_orderhistory"})


ORDER_PRODUCT_SCHEMA = pa.schema([
    pk_field("order_product_id"),
    pa.field("order_id", pa.int32(), metadata={
        "foreign_key": "oc_order", "on_delete": "CASCADE"
    }),
    pa.field("product_id", pa.int32(), metadata={
        "foreign_key": "oc_product", "on_delete": "CASCADE"
    }),
    pa.field("name", pa.string(), metadata={"max_length": "255"}),
    pa.field("model", pa.string(), metadata={"max_length": "64"}),
    pa.field("quantity", pa.int32()),
    pa.field("price", pa.decimal128(15, 4), metadata={"default": "0.0000"}),
    pa.field("total", pa.decimal128(15, 4), metadata={"default": "0.0000"}),
    pa.field("tax", pa.decimal128(15, 4), metadata={"default": "0.0000"}),
    pa.field("reward", pa.int32()),
], metadata={"pg_name": "orders_orderproduct"})


ORDER_OPTION_SCHEMA = pa.schema([
    pk_field("order_option_id"),
    pa.field("order_id", pa.int32(), metadata={
        "foreign_key": "oc_order", "on_delete": "CASCADE"
    }),
    pa.field("order_product_id", pa.int32(), metadata={
        "foreign_key": "oc_order_product", "on_delete": "CASCADE"
    }),
    pa.field("product_option_id", pa.int32()),
    pa.field("product_option_value_id", pa.int32(), metadata={"default": "0"}),
    pa.field("name", pa.string(), metadata={"max_length": "255"}),
    pa.field("value", pa.string()),
    pa.field("type", pa.string(), metadata={"max_length": "32"}),
], metadata={"pg_name": "orders_orderoption"})


ORDER_STATUS_SCHEMA = pa.schema([
    pk_field("order_status_id"),
    pa.field("language_id", pa.int32()),
    pa.field("name", pa.string(), metadata={"max_length": "64"}),
], metadata={"pg_name": "orders_orderstatus"})


ORDER_TOTAL_SCHEMA = pa.schema([
    pk_field("order_total_id"),
    pa.field("order_id", pa.int32(), metadata={
        "foreign_key": "oc_order", "on_delete": "CASCADE"
    }),
    pa.field("code", pa.string(), metadata={"max_length": "32"}),
    pa.field("title", pa.string(), metadata={"max_length": "255"}),
    pa.field("value", pa.decimal128(15, 4), metadata={"default": "0.0000"}),
    pa.field("sort_order", pa.int32()),
], metadata={"pg_name": "orders_ordertotal"})
