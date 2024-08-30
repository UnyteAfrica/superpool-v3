from django.conf import settings

from ..environment import env

# Set the default storage to Google Cloud Storage
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
    }
}

# There are multiple way to authenticate Google Cloud environment/infrastucture
# We can authenticate my storing  `your-project-XXXXX.json` or inject these
# values into the application at runtime
if "GOOGLE_CLOUD_STORAGE_BUCKET_NAME" in env:
    STORAGES["default"]["BUCKET_NAME"] = env("GOOGLE_CLOUD_STORAGE_BUCKET_NAME") or ""
    STORAGES["default"]["PROJECT_ID"] = env("GOOGLE_CLOUD_STORAGE_PROJECT_ID") or ""
    STORAGES["default"]["CREDENTIALS"] = env("GOOGLE_CLOUD_STORAGE_CREDENTIALS") or ""

if "GOOGLE_CLOUD_STORAGE_OPTIONS" in env:
    STORAGES["default"]["OPTIONS"] = env.dict("GOOGLE_CLOUD_STORAGE_OPTIONS")


# Compile staticfiles to Google Cloud Storage in Production or staging environments only
if settings.DEBUG == "False":
    STORAGES["staticfiles"] = {
        "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
    }
else:
    STORAGES["staticfiles"] = {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    }
