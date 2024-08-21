import sys
from pathlib import Path
from config.settings.base import *

# configure test-specific database settings
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": ":memory:",
#     }
# }

DATABASES = {
    "default": env.db(
        "SUPERPOOL_TEST_PROD_DB_URL",
    )
}

print("Test database configuration:")
print(DATABASES)
