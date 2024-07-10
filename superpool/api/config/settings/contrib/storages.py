import os

from django.conf import settings
from google.oauth2 import service_account

from ..environment import env

BASE_DIR = settings.BASE_DIR

# There are multiple way to authenticate Google Cloud environment/infrastucture
# We can authenticate my storing  `your-project-XXXXX.json` or inject these
# Compile staticfiles to Google Cloud Storage in Production or staging environments only
GOOGLE_APPLICATION_CREDENTIALS = BASE_DIR.joinpath("gcp.json")
GS_BUCKET_NAME = env("GS_BUCKET_NAME") or env("GOOGLE_CLOUD_STORAGE_BUCKET_NAME")
GS_PROJECT_ID = env("GS_PROJECT_ID") or env("GOOGLE_CLOUD_STORAGE_PROJECT_ID")


# Set the default storage to Google Cloud Storage
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
    }
}

if settings.DEBUG == "False":
    STORAGES["staticfiles"] = {
        "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
    }
else:
    STORAGES["staticfiles"] = {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    }

# Add unique file names to the files uploaded to the storage
GS_FILE_OVERWRITE = False

GS_CREDENTIALS = service_account.Credentials.from_service_account_file(
    GOOGLE_APPLICATION_CREDENTIALS
)
