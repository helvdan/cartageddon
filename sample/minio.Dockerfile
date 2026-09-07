FROM minio/minio:latest

# Кастомный скрипт запуска сервера и его автоматической настройки
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Переопределяем стандартную точку входа
ENTRYPOINT ["/entrypoint.sh"]