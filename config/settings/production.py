from .base import *  # noqa: F403

DEBUG = False

SECURE_SSL_REDIRECT = env.bool(  # noqa: F405
    "SECURE_SSL_REDIRECT",
    default=True,
)

SESSION_COOKIE_SECURE = env.bool(  # noqa: F405
    "SESSION_COOKIE_SECURE",
    default=True,
)

CSRF_COOKIE_SECURE = env.bool(  # noqa: F405
    "CSRF_COOKIE_SECURE",
    default=True,
)

SECURE_HSTS_SECONDS = env.int(  # noqa: F405
    "SECURE_HSTS_SECONDS",
    default=31536000,
)

SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(  # noqa: F405
    "SECURE_HSTS_INCLUDE_SUBDOMAINS",
    default=True,
)

SECURE_HSTS_PRELOAD = env.bool(  # noqa: F405
    "SECURE_HSTS_PRELOAD",
    default=True,
)

SECURE_CONTENT_TYPE_NOSNIFF = True

X_FRAME_OPTIONS = "DENY"
