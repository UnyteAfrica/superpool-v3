from django.conf import settings

from ..environment import env

STORAGES = {
    "default": {
        "ENGINE": "storages.backends.gcloud.GoogleCloudStorage",
    }
}

# There are multiple way to authenticate Google Cloud environment/infrastucture
# We can authenticate my storing  `your-project-XXXXX.json` or inject these
# values into the application at runtime

if "GS_BUCKET_NAME" or "GOOGLE_CLOUD_STORAGE_BUCKET_NAME" in env:
    STORAGES["default"]["BUCKET_NAME"] = (
        env.str("GOOGLE_CLOUD_STORAGE_BUCKET_NAME")
        if env("GOOGLE_CLOUD_STORAGE_BUCKET_NAME")
        else env.str("GS_BUCKET_NAME")
    )
    STORAGES["default"]["PROJECT_ID"] = (
        env.str("GOOGLE_CLOUD_STORAGE_PROJECT_ID")
        if env("GOOGLE_CLOUD_STORAGE_PROJECT_ID")
        else env("GS_PROJECT_ID", default="superpool")
    )
    STORAGES["default"]["CREDENTIALS"] = (
        env.str("GOOGLE_CLOUD_STORAGE_CREDENTIALS")
        if env("GS_CREDENTIALS")
        else env("GOOGLE_CLOUD_STORAGE_CREDENTIALS")
    )

if "GS_OPTIONS" or "GOOGLE_CLOUD_STORAGE_OPTIONS" in env:
    STORAGES["default"]["OPTIONS"] = env.dict("GOOGLE_CLOUD_STORAGE_OPTIONS")


# Compile staticfiles to Google Cloud Storage in Production or staging environments only
if not settings.DEBUG:
    STORAGES["staticfiles"] = STORAGES["default"]["ENGINE"]
