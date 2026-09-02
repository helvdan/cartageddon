-- Тестовый дамп MySQL для OpenCart 3.x
SET FOREIGN_KEY_CHECKS = 0;

-- --------------------------------------------------------
-- Структура таблицы `oc_length_class`
-- --------------------------------------------------------
DROP TABLE IF EXISTS `oc_length_class`;
CREATE TABLE `oc_length_class` (
  `length_class_id` int(11) NOT NULL AUTO_INCREMENT,
  `value` decimal(15,8) NOT NULL,
  PRIMARY KEY (`length_class_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

INSERT INTO `oc_length_class` (`length_class_id`, `value`) VALUES
(1, 1.00000000),
(2, 0.10000000),
(3, 0.39370000);

-- --------------------------------------------------------
-- Структура таблицы `oc_weight_class`
-- --------------------------------------------------------
DROP TABLE IF EXISTS `oc_weight_class`;
CREATE TABLE `oc_weight_class` (
  `weight_class_id` int(11) NOT NULL AUTO_INCREMENT,
  `value` decimal(15,8) NOT NULL,
  PRIMARY KEY (`weight_class_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

INSERT INTO `oc_weight_class` (`weight_class_id`, `value`) VALUES
(1, 1.00000000),
(2, 1000.00000000),
(3, 0.45359237);

-- --------------------------------------------------------
-- Структура таблицы `oc_tax_class`
-- --------------------------------------------------------
DROP TABLE IF EXISTS `oc_tax_class`;
CREATE TABLE `oc_tax_class` (
  `tax_class_id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(32) NOT NULL,
  `description` varchar(255) NOT NULL,
  `date_added` datetime NOT NULL,
  `date_modified` datetime NOT NULL,
  PRIMARY KEY (`tax_class_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

INSERT INTO `oc_tax_class` (`tax_class_id`, `title`, `description`, `date_added`, `date_modified`) VALUES
(1, 'Standard Tax', 'Standard VAT rate', '2026-01-01 00:00:00', '2026-01-01 00:00:00'),
(2, 'Eco Tax', 'Ecological tax rate', '2026-01-01 00:00:00', '2026-01-01 00:00:00');

-- --------------------------------------------------------
-- Структура таблицы `oc_stock_status`
-- --------------------------------------------------------
DROP TABLE IF EXISTS `oc_stock_status`;
CREATE TABLE `oc_stock_status` (
  `stock_status_id` int(11) NOT NULL AUTO_INCREMENT,
  `language_id` int(11) NOT NULL,
  `name` varchar(32) NOT NULL,
  PRIMARY KEY (`stock_status_id`,`language_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

INSERT INTO `oc_stock_status` (`stock_status_id`, `language_id`, `name`) VALUES
(1, 1, 'In Stock'),
(2, 1, 'Out Of Stock'),
(3, 1, 'Pre-Order');

-- --------------------------------------------------------
-- Структура таблицы `oc_manufacturer`
-- --------------------------------------------------------
DROP TABLE IF EXISTS `oc_manufacturer`;
CREATE TABLE `oc_manufacturer` (
  `manufacturer_id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(64) NOT NULL,
  `image` varchar(255) DEFAULT NULL,
  `sort_order` int(3) NOT NULL,
  PRIMARY KEY (`manufacturer_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

INSERT INTO `oc_manufacturer` (`manufacturer_id`, `name`, `image`, `sort_order`) VALUES
(1, 'Apple', 'catalog/demo/apple_logo.png', 0),
(2, 'HTC', 'catalog/demo/htc_logo.png', 1),
(3, 'Sony', 'catalog/demo/sony_logo.png', 2);

-- --------------------------------------------------------
-- Структура таблицы `oc_product`
-- --------------------------------------------------------
DROP TABLE IF EXISTS `oc_product`;
CREATE TABLE `oc_product` (
  `product_id` int(11) NOT NULL AUTO_INCREMENT,
  `model` varchar(64) NOT NULL,
  `sku` varchar(64) NOT NULL,
  `upc` varchar(12) NOT NULL,
  `ean` varchar(14) NOT NULL,
  `jan` varchar(13) NOT NULL,
  `isbn` varchar(13) NOT NULL,
  `mpn` varchar(64) NOT NULL,
  `location` varchar(128) NOT NULL,
  `quantity` int(4) NOT NULL DEFAULT '0',
  `stock_status_id` int(11) NOT NULL,
  `image` varchar(255) DEFAULT NULL,
  `manufacturer_id` int(11) NOT NULL,
  `shipping` tinyint(1) NOT NULL DEFAULT '1',
  `price` decimal(15,4) NOT NULL DEFAULT '0.0000',
  `points` int(8) NOT NULL DEFAULT '0',
  `tax_class_id` int(11) NOT NULL,
  `date_available` date NOT NULL,
  `weight` decimal(15,8) NOT NULL DEFAULT '0.00000000',
  `weight_class_id` int(11) NOT NULL DEFAULT '0',
  `length` decimal(15,8) NOT NULL DEFAULT '0.00000000',
  `width` decimal(15,8) NOT NULL DEFAULT '0.00000000',
  `height` decimal(15,8) NOT NULL DEFAULT '0.00000000',
  `length_class_id` int(11) NOT NULL DEFAULT '0',
  `subtract` tinyint(1) NOT NULL DEFAULT '1',
  `minimum` int(11) NOT NULL DEFAULT '1',
  `sort_order` int(11) NOT NULL DEFAULT '0',
  `status` tinyint(1) NOT NULL DEFAULT '0',
  `viewed` int(5) NOT NULL DEFAULT '0',
  `date_added` datetime NOT NULL,
  `date_modified` datetime NOT NULL,
  `yandexmerchants` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`product_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

INSERT INTO `oc_product` (`product_id`, `model`, `sku`, `upc`, `ean`, `jan`, `isbn`, `mpn`, `location`, `quantity`, `stock_status_id`, `image`, `manufacturer_id`, `shipping`, `price`, `points`, `tax_class_id`, `date_available`, `weight`, `weight_class_id`, `length`, `width`, `height`, `length_class_id`, `subtract`, `minimum`, `sort_order`, `status`, `viewed`, `date_added`, `date_modified`, `yandexmerchants`) VALUES
(1, 'Product 1', 'SKU-001', '', '', '', '', '', 'Warehouse A', 10, 1, 'catalog/demo/iphone_1.png', 1, 1, 100.0000, 0, 1, '2026-01-01', 0.50000000, 1, 15.00000000, 7.00000000, 0.80000000, 1, 1, 1, 1, 1, 42, '2026-01-01 10:00:00', '2026-01-01 10:00:00', 1),
(2, 'Product 2', 'SKU-002', '', '', '', '', '', 'Warehouse B', 0, 2, 'catalog/demo/htc_touch_hd_1.png', 2, 1, 250.0000, 0, 1, '2026-01-02', 0.60000000, 1, 12.00000000, 6.00000000, 1.20000000, 1, 1, 1, 2, 1, 15, '2026-01-02 11:00:00', '2026-01-02 11:00:00', 1);

-- --------------------------------------------------------
-- Структура таблицы `oc_product_description`
-- --------------------------------------------------------
DROP TABLE IF EXISTS `oc_product_description`;
CREATE TABLE `oc_product_description` (
  `product_id` int(11) NOT NULL,
  `language_id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `description` text NOT NULL,
  `tag` text NOT NULL,
  `meta_title` varchar(255) NOT NULL,
  `meta_description` varchar(255) NOT NULL,
  `meta_keyword` varchar(255) NOT NULL,
  PRIMARY KEY (`product_id`,`language_id`),
  KEY `name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

INSERT INTO `oc_product_description` (`product_id`, `language_id`, `name`, `description`, `tag`, `meta_title`, `meta_description`, `meta_keyword`) VALUES
(1, 1, 'iPhone 15', '<p>The latest Apple smartphone with amazing features.</p>', 'apple, iphone, smartphone', 'iPhone 15 - Buy Online', 'Buy iPhone 15 at the best price.', 'iphone, apple'),
(2, 1, 'HTC Touch HD', '<p>Classic HTC smartphone with a large touchscreen.</p>', 'htc, smartphone', 'HTC Touch HD', 'HTC Touch HD review and specifications.', 'htc, mobile');

-- --------------------------------------------------------
-- Структура таблицы `oc_review`
-- --------------------------------------------------------
DROP TABLE IF EXISTS `oc_review`;
CREATE TABLE `oc_review` (
  `review_id` int(11) NOT NULL AUTO_INCREMENT,
  `product_id` int(11) NOT NULL,
  `customer_id` int(11) NOT NULL,
  `author` varchar(64) NOT NULL,
  `text` text NOT NULL,
  `rating` int(1) NOT NULL,
  `status` tinyint(1) NOT NULL DEFAULT '0',
  `date_added` datetime NOT NULL,
  `date_modified` datetime NOT NULL,
  PRIMARY KEY (`review_id`),
  KEY `product_id` (`product_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

INSERT INTO `oc_review` (`review_id`, `product_id`, `customer_id`, `author`, `text`, `rating`, `status`, `date_added`, `date_modified`) VALUES
(1, 1, 0, 'John Doe', 'Great smartphone! Battery life is excellent.', 5, 1, '2026-01-05 14:30:00', '2026-01-05 14:30:00'),
(2, 1, 0, 'Иван Иванов', 'Отличный телефон, пользуюсь каждый день.', 5, 1, '2026-01-06 09:15:00', '2026-01-06 09:15:00'),
(3, 2, 0, 'Jane Smith', 'Good phone but the battery could be better.', 4, 1, '2026-01-07 18:20:00', '2026-01-07 18:20:00');

SET FOREIGN_KEY_CHECKS = 1;
