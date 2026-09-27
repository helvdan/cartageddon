import pyarrow as pa

from related_schemas.utils import pk_field


CATEGORY_SCHEMA = pa.schema([
    pk_field('category_id'),
    pa.field(
        'image',
        pa.string(),
        nullable=True,
        metadata={
            "upload_to_s3": "True"
        }
    ),
    pa.field('sbmenu_icon', pa.string(), nullable=True),  # varchar(255)
    pa.field('sbmenu_image', pa.string(), nullable=True), # varchar(255)
    pa.field('parent_id', pa.int32(), nullable=True, metadata={"callback": "zero_to_none"}),    # int (default 0)
    pa.field('top', pa.int8(), nullable=False),           # tinyint(1) -> в Arrow как int8/bool
    pa.field('column', pa.int32(), nullable=False),       # int
    pa.field('sort_order', pa.int32(), nullable=False),   # int (default 0)
    pa.field('status', pa.int8(), nullable=False),        # tinyint(1) -> в Arrow как int8/bool
    pa.field('date_added', pa.timestamp('us'), nullable=False),    # datetime
    pa.field('date_modified', pa.timestamp('us'), nullable=False), # datetime
    pa.field('code', pa.string(), nullable=True),         # varchar(64)
    pa.field('sbmenu_content', pa.string(), nullable=True) # text
], metadata={"pg_name": "catalog_category"})

CATEGORY_DESCRIPTION_SCHEMA = pa.schema([
    pa.field('category_id', pa.int32(), metadata={"primary_key": "True"}),   # int (PRIMARY KEY)
    pa.field('language_id', pa.int32(), nullable=False),   # int (PRIMARY KEY)
    pa.field('name', pa.string(), nullable=False),         # varchar(255)
    pa.field('description', pa.string(), nullable=True),   # text
    pa.field('meta_title', pa.string(), nullable=False),   # varchar(255)
    pa.field('meta_description', pa.string(), nullable=True), # text (по вашему скриншоту)
    pa.field('meta_keyword', pa.string(), nullable=True)   # varchar(255)
], metadata={"pg_name": "catalog_categorydescription"})

CATEGORY_PATH_SCHEMA = pa.schema([
    pa.field('category_id', pa.int32(), nullable=False),   # int (PRIMARY KEY)
    pa.field('path_id', pa.int32(), nullable=False),       # int (PRIMARY KEY)
    pa.field('level', pa.int32(), nullable=False)          # int
], metadata={"pg_name": "catalog_categorypath"})


PRODUCT_TO_CATEGORY = pa.schema([
    # Первичные ключи / Внешние ключи типа INT
    pa.field('product_id', pa.int32(), nullable=False),
    pa.field('category_id', pa.int32(), nullable=False),
    pa.field('main_category', pa.bool_(), metadata={
        "callback": "int_to_bool"
    })
], metadata={"pg_name": "catalog_producttocategory"})
