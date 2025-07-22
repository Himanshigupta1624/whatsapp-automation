#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

cd whatsapp_project
python manage.py collectstatic --no-input
python manage.py migrate
