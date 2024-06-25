try:
    from core.settings.base import *  # noqa: F403
except ImportError:
    pass

DEBUG = True

TESTS = True

DATABASES = {}

STORAGES = {}

CACHES = {}
