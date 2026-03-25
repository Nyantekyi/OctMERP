#!/bin/sh
set -e

echo "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."
until python -c "import os; import psycopg; psycopg.connect(host=os.environ['DB_HOST'], port=os.environ['DB_PORT'], dbname=os.environ['DB_NAME'], user=os.environ['DB_USER'], password=os.environ['DB_PASSWORD']).close()"; do
  sleep 2
done

python manage.py migrate_schemas --shared --noinput
python manage.py bootstrap_tenant
python manage.py runserver 0.0.0.0:8000