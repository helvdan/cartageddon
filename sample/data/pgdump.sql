-- 1. Справочники и независимые таблицы

CREATE TABLE IF NOT EXISTS public.catalog_stockstatus (
    id bigserial PRIMARY KEY,
    name varchar(32) NOT NULL
);

CREATE TABLE IF NOT EXISTS public.catalog_taxclass (
    id bigserial PRIMARY KEY,
    title varchar(32) NOT NULL,
    description varchar(255) NOT NULL,
    date_added timestamp with time zone NOT NULL,
    date_modified timestamp with time zone NOT NULL
);

CREATE TABLE IF NOT EXISTS public.catalog_manufacturer (
    id bigserial PRIMARY KEY,
    name varchar(64) NOT NULL,
    image varchar(255) NULL,
    sort_order integer NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS public.catalog_weightclass (
    id bigserial PRIMARY KEY,
    value numeric(15, 8) NOT NULL
);

CREATE TABLE IF NOT EXISTS public.catalog_lengthclass (
    id bigserial PRIMARY KEY,
    value numeric(15, 8) NOT NULL
);

-- 2. Таблица товаров (со всеми внешними ключами)

CREATE TABLE IF NOT EXISTS public.catalog_product (
    id bigserial PRIMARY KEY,
    model varchar(64) NOT NULL,
    sku varchar(64) NOT NULL DEFAULT '',
    upc varchar(12) NOT NULL DEFAULT '',
    ean varchar(14) NOT NULL DEFAULT '',
    jan varchar(13) NOT NULL DEFAULT '',
    isbn varchar(64) NULL,
    mpn varchar(64) NOT NULL DEFAULT '',
    location varchar(128) NOT NULL DEFAULT '',
    quantity integer NOT NULL DEFAULT 0,
    name varchar(255) NOT NULL,
    description text NOT NULL,
    tag text NOT NULL,
    meta_title varchar(255) NOT NULL,
    meta_description varchar(255) NOT NULL,
    meta_keyword varchar(255) NOT NULL,
    image varchar(255) NULL,
    shipping boolean NOT NULL DEFAULT TRUE,
    price numeric(15, 4) NOT NULL DEFAULT 0.0000,
    points integer NOT NULL DEFAULT 0,
    date_available date NULL,
    weight numeric(15, 8) NOT NULL DEFAULT 0.00000000,
    length numeric(15, 8) NOT NULL DEFAULT 0.00000000,
    width numeric(15, 8) NOT NULL DEFAULT 0.00000000,
    height numeric(15, 8) NOT NULL DEFAULT 0.00000000,
    subtract boolean NOT NULL DEFAULT TRUE,
    minimum integer NOT NULL DEFAULT 1,
    sort_order integer NOT NULL DEFAULT 0,
    status boolean NOT NULL DEFAULT TRUE,
    viewed integer NOT NULL DEFAULT 0,
    date_added timestamp with time zone NOT NULL,
    date_modified timestamp with time zone NOT NULL,
    yandexmerchants boolean NOT NULL DEFAULT FALSE,
    stock_status_id bigint NOT NULL REFERENCES public.catalog_stockstatus(id) ON DELETE NO ACTION,
    manufacturer_id bigint NULL REFERENCES public.catalog_manufacturer(id) ON DELETE SET NULL,
    tax_class_id bigint NULL REFERENCES public.catalog_taxclass(id) ON DELETE SET NULL,
    weight_class_id bigint NULL REFERENCES public.catalog_weightclass(id) ON DELETE NO ACTION,
    length_class_id bigint NULL REFERENCES public.catalog_lengthclass(id) ON DELETE NO ACTION
);

-- 3. Зависимые таблицы и связи Many-to-Many

CREATE TABLE IF NOT EXISTS public.catalog_producttocategory (
    id bigserial PRIMARY KEY,
    category_id integer NOT NULL,
    main_category boolean NOT NULL DEFAULT FALSE,
    product_id bigint NOT NULL REFERENCES public.catalog_product(id) ON DELETE CASCADE,
    CONSTRAINT catalog_producttocategory_product_id_category_id_uniq UNIQUE (product_id, category_id)
);

CREATE TABLE IF NOT EXISTS public.catalog_review (
    id bigserial PRIMARY KEY,
    author varchar(64) NOT NULL,
    text text NOT NULL,
    rating integer NOT NULL,
    status boolean NOT NULL DEFAULT FALSE,
    date_added timestamp with time zone NOT NULL,
    date_modified timestamp with time zone NULL,
    product_id bigint NOT NULL REFERENCES public.catalog_product(id) ON DELETE CASCADE
);

-- 4. Индексы производительности (автоматически создаваемые Django для Foreign Keys)

CREATE INDEX IF NOT EXISTS catalog_product_stock_status_id ON public.catalog_product(stock_status_id);
CREATE INDEX IF NOT EXISTS catalog_product_manufacturer_id ON public.catalog_product(manufacturer_id);
CREATE INDEX IF NOT EXISTS catalog_product_tax_class_id ON public.catalog_product(tax_class_id);
CREATE INDEX IF NOT EXISTS catalog_product_weight_class_id ON public.catalog_product(weight_class_id);
CREATE INDEX IF NOT EXISTS catalog_product_length_class_id ON public.catalog_product(length_class_id);
CREATE INDEX IF NOT EXISTS catalog_review_product_id ON public.catalog_review(product_id);
