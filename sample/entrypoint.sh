#!/bin/sh

# 1. Запускаем сервер MinIO в фоновом режиме
minio server /data --console-address ":9001" &
MINIO_PID=$!

# 2. Дожидаемся доступности API (замена вашего цикла until)
echo "Ожидание запуска MinIO..."
until (/usr/bin/mc alias set myminio http://localhost:9000 minio_admin minio_strong_password) > /dev/null 2>&1; do
    sleep 1
done

echo "MinIO запущен. Начинаю настройку бакета 'dev'..."

# 3. Создаем бакет, если его нет
/usr/bin/mc mb --ignore-existing myminio/dev

# 4. Открываем бакет на чтение (для статики и картинок Django)
/usr/bin/mc anonymous set download myminio/dev

# 5. ОТКЛЮЧАЕМ ВЕРСИОНИРОВАНИЕ (приостанавливаем корзину)
/usr/bin/mc version suspend myminio/dev

echo "Настройка завершена успешно! Бакет 'dev' готов (версионирование отключено)."

# 6. Переводим фоновый процесс MinIO в активный режим, чтобы контейнер не умирал
wait $MINIO_PID
