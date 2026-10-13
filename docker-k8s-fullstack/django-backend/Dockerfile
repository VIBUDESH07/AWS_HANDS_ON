# ---- Base image: slim = chinna size, debian based (psycopg binary wheel work aagum)
FROM python:3.12-slim

# .pyc files ezhudhadha, logs buffer pannama udane stdout-ku anuppu
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Layer caching trick: requirements mattum mudhalla copy. Code maarinaalum
# requirements maaralana indha pip install layer cache-la irundhu varum.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Root-a run panna koodadhu — fixed UID kudutha K8s runAsUser-oda match pannalaam
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin appuser
USER 10001

EXPOSE 8000

# CMD = default command. Compose/K8s-la migrate job-ku idha override pannuvom.
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-"]
