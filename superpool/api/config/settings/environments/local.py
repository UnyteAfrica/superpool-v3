try:
    from config.settings.base import *  # noqa: F403
except ImportError:
    from config.settings.base import INSTALLED_APPS, MIDDLEWARE, env
else:
    pass

# DEBUG = True

TESTS = True

# DATABASES = {}

# STORAGES = {}

# CACHES = {}

ENABLE_PROFILING = env.bool("ENABLE_PROFILING", default=False)

if ENABLE_PROFILING:
    INSTALLED_APPS += [
        "debug_toolbar",
        "silk",
    ]
    MIDDLEWARE += [
        "debug_toolbar.middleware.DebugToolbarMiddleware",
        "silk.middleware.SilkyMiddleware",
    ]

    # DJANGO DEBUG TOOLBAR CONFIGURATION
    #
    # Just some custom configuration to improve the efficency of our application
    #
    # See: https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html
    # for more information.
    DEBUG_TOOLBAR_CONFIG = {
        "IS_RUNNING_TESTS": False,
        # allow only admins access to debug and profiling panels
        #
        # this same thing is, configured below for `Silk` as boolen  flags
        "SHOW_TOOLBAR_CALLBACK": lambda request: request.user.is_superuser,
    }

    # By default, silk allows dashboard access to anyone
    #
    # We want to limit that to only, authorized superusers
    # Seee: https://pypi.org/project/django-silk/#Configuration
    SILK_AUTHENTICATION = True
    SILK_AUTHORIZATION = True
