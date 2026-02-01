#!/bin/bash
# Reset database for development
set -e

cd "$(dirname "$0")/.."

echo "==> Removing old database..."
rm -f db.sqlite3

echo "==> Removing old migrations..."
rm -f predictions/migrations/0*.py

echo "==> Creating new migrations..."
python manage.py makemigrations predictions

echo "==> Applying migrations..."
python manage.py migrate

echo "==> Seeding 2026 data..."
python manage.py seed_2026

echo "==> Done! Database reset complete."
