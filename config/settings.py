from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = "django-insecure-change-this-secret-key"


DEBUG = True


ALLOWED_HOSTS = []


INSTALLED_APPS = [
    "accounts",
    "customers",
    "service_orders",
    "crispy_forms",
    "crispy_bootstrap5",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "config.urls"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


WSGI_APPLICATION = "config.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# AUTH_PASSWORD_VALIDATORS = [
#     {
#         "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
#         "OPTIONS": {
#             "user_attributes": (
#                 "email",
#                 "first_name",
#                 "last_name",
#             ),
#         },
#     },
#     {
#         "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
#         "OPTIONS": {
#             "min_length": 8,
#         },
#     },
#     {
#         "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
#     },
#     {
#         "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
#     },
# ]


LANGUAGE_CODE = "pt-br"


TIME_ZONE = "America/Sao_Paulo"


USE_I18N = True


USE_TZ = True


DATE_FORMAT = "d/m/Y"


DATETIME_FORMAT = "d/m/Y H:i"


SHORT_DATE_FORMAT = "d/m/Y"


SHORT_DATETIME_FORMAT = "d/m/Y H:i"


DECIMAL_SEPARATOR = ","


THOUSAND_SEPARATOR = "."


USE_THOUSAND_SEPARATOR = True


LOCALE_PATHS = [
    BASE_DIR / "locale",
]


STATIC_URL = "static/"


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


AUTH_USER_MODEL = "accounts.CustomUser"


LOGIN_URL = "accounts:login"


LOGIN_REDIRECT_URL = "accounts:dashboard"


LOGOUT_REDIRECT_URL = "accounts:login"


CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"


CRISPY_TEMPLATE_PACK = "bootstrap5"


MESSAGE_TAGS = {
    10: "secondary",
    20: "info",
    25: "success",
    30: "warning",
    40: "danger",
}
