AUTHOR = "Unyte Africa LTD."

API_VERSION = "1.4.0"

# TODO: Dynamically insert the correct fields
SPECTACULAR_SETTINGS = {
    "TITLE": "Superpool API",
    "DESCRIPTION": "Insurance infrastructure for Financial Institutions, Insurers, and Insurtechs",
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
    "SERVE_URLS": [
        {"url": "https://ng.unyte.africa/api/v1/", "name": "Production"},
        {
            "url": "https://superpool-v3-dev-ynoamqpukq-uc.a.run.app/api/docs/swagger/",
            "name": "Staging",
        },
        {"url": "http://localhost:8000/api/docs/swagger/", "name": "Development"},
    ],
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "docExpansion": "list",
        "filter": True,
        "showExtensions": True,
        "tagsSorter": "alpha",
        "operationsSorter": "alpha",
        "showCommonExtensions": True,
        "supportedSubmitMethods": ["get", "post", "put", "delete", "patch"],
    },
    "SERVERS": [
        {
            "url": "https://ng.unyte.africa/api/v1/",
            "description": "Production",
        },
        {
            "url": "https://superpool-v3-dev-ynoamqpukq-uc.a.run.app/api/docs/swagger/",
            "description": "Staging",
        },
        {
            "url": "http://localhost:8000/api/docs/swagger/",
            "description": "Development",
        },
    ],
}
