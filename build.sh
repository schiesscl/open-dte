#!/usr/bin/env bash
set -o errexit

python -m pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput

if [[ "${RENDER_SEED_DEMO:-False}" == "True" ]]; then
    python manage.py seed_demo
fi
