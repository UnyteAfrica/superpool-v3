AUTHOR = "Unyte Africa LTD."

API_VERSION = "1.4.0"

# TODO: Dynamically insert the correct fields
SPECTACULAR_SETTINGS = {
    "TITLE": "Superpool API",
    "DESCRIPTION": "API for Superpool",
    "VERSION": API_VERSION,
    "AUTHOR": AUTHOR,
    "CONTACT": {
        "name": AUTHOR,
        "url": "https://ng.unyte.africa",
        "email": "tech@unyte.com",
    },
    "AUTHENTICATION": [
        {
            "name": "APIKey",
            "type": "apiKey",
            "in": "header",
            "x": {
                "name": "Authorization",
                "description": "API Key should be provided in the format `SUPERPOOL <key>`",
            },
        },
        {"name": "Bearer", "type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
    ],
    "SECURITY": [
        {"APIKey": []},
        {"Bearer": []},
    ],
}
