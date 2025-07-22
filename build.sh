#!/usr/bin/env bash
# exit on error
set -o errexit

echo "📦 Installing requirements"
pip install -r requirements.txt

echo "🚀 Running migrations"
cd whatsapp_project
python manage.py migrate

echo "✅ Build complete"