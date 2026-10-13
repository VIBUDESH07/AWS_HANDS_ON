import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# 12-factor style: ellame environment variable-la irundhu. Docker/K8s-la
# ConfigMap & Secret moolama idha inject pannuvom.
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-insecure-key")
DEBUG = os.environ.get("DEBUG", "0") == "1"

# K8s probes pod IP-a Host header-a anuppum (eg: 10.244.0.12:8000). Specific
# hosts mattum allow panna probes 400 DisallowedHost vaangum.
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "tasks",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# DB_HOST illana local-a SQLite — docker illamaye `python manage.py runserver` try pannalaam
if os.environ.get("DB_HOST"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "HOST": os.environ["DB_HOST"],
            "PORT": os.environ.get("DB_PORT", "5432"),
            "NAME": os.environ.get("DB_NAME", "tasks"),
            "USER": os.environ.get("DB_USER", "tasks"),
            "PASSWORD": os.environ.get("DB_PASSWORD", ""),
            "CONN_MAX_AGE": 60,
            "CONN_HEALTH_CHECKS": True,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

USE_TZ = True
TIME_ZONE = "UTC"

# Container logs stdout-ku poganum — `docker logs` / `kubectl logs` adha thaan padikkum
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": os.environ.get("LOG_LEVEL", "INFO")},
}
