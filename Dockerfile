FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt requirements-production.txt ./
RUN pip install --no-cache-dir -r requirements-production.txt

COPY ProjetoFamaPet/ ./

RUN groupadd --system app \
    && useradd --system --gid app --home-dir /app app \
    && mkdir -p /app/media /app/staticfiles \
    && chown -R app:app /app/media /app/staticfiles

RUN python -c "import os; from django.core.management.utils import get_random_secret_key; os.environ['DJANGO_SECRET_KEY'] = get_random_secret_key(); os.environ['DEBUG'] = 'False'; os.environ['DJANGO_SETTINGS_MODULE'] = 'FamaPet.settings'; import django; django.setup(); from django.core.management import call_command; call_command('collectstatic', interactive=False)"

USER app

EXPOSE 8000

CMD ["gunicorn", "FamaPet.wsgi:application", "--bind=0.0.0.0:8000", "--workers=3", "--access-logfile=-", "--error-logfile=-"]
