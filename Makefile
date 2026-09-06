# Переменные для удобства настройки
COMPOSE_DIR = sample
CLI_CONTAINER = etl_cli
SCRIPT_NAME = run.py
VENV = .env
PYTHON_BIN ?= python3
PIP = $(VENV)/bin/pip

.PHONY: up down restart build logs shell migrate mysql-check

# 1. Управление инфраструктурой
up:
	cd $(COMPOSE_DIR) && docker-compose up -d

down:
	cd $(COMPOSE_DIR) && docker-compose down

down-clean:
	cd $(COMPOSE_DIR) && docker-compose down -v

restart:
	cd $(COMPOSE_DIR) && docker-compose down && docker-compose up -d

build:
	cd $(COMPOSE_DIR) && docker-compose up -d --build

# 2. Логи и мониторинг
logs:
	cd $(COMPOSE_DIR) && docker-compose logs -f

# 3. Запуск миграции и скриптов
migrate:
	docker exec -it $(CLI_CONTAINER) python /app/run.py --debug --single-language

# 4. Интерактивный доступ и отладка
shell:
	docker exec -it $(CLI_CONTAINER) /bin/bash

mysql-check:
	docker exec -it $(CLI_CONTAINER) python -c "import pymysql, os; conn = pymysql.connect(host='mysql_sample', user=os.environ.get('MYSQL_USER'), password=os.environ.get('MYSQL_PASSWORD'), database=os.environ.get('MYSQL_DATABASE')); cur=conn.cursor(); cur.execute('SHOW TABLES;'); print('Таблицы в MySQL:', cur.fetchall()); conn.close()"

pg-clean:
	docker exec -it django_postgres bash -c 'psql -U $$POSTGRES_USER -d $$POSTGRES_DB -c \
	"TRUNCATE TABLE public.catalog_producttocategory, \
	public.catalog_review, \
	public.catalog_product, \
	public.catalog_stockstatus, \
	public.catalog_taxclass, \
	public.catalog_manufacturer, \
	public.catalog_weightclass, \
	public.catalog_lengthclass \
	RESTART IDENTITY CASCADE;"'

create-env:
	@echo "Creating virtual environment..."
	$(PYTHON_BIN) -m venv $(VENV)
	@echo "Upgrading pip and installing requirements..."
	$(PIP) install --upgrade pip
	$(PIP) install -r $(COMPOSE_DIR)/requirements.txt
