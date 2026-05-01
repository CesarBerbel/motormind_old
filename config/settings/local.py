from .base import *  # noqa: F403

DEBUG = True

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
]

CSRF_TRUSTED_ORIGINS = []

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
