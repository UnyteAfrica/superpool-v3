from drf_spectacular.utils import OpenApiExample
from django.conf import settings

BASE_URL = settings.BASE_URL

insurance_provider_search_example = OpenApiExample(
    "Paginated Response Example",
    value={
        "count": 100,
        "next": f"http://{BASE_URL}/providers/?name=example&limit=25&offset=25",
        "previous": "null",
        "results": [
            {
                "id": "e1a5d88c-4b23-4b90-8e7a-b3fef95e3a80",
                "name": "Acme Insurance Co.",
                "address": "123 Elm Street, Springfield, IL",
                "phone_number": "+1-800-555-1234",
            },
            {
                "id": "d8e9d79a-d1c1-4f07-b6d8-7399be13b47e",
                "name": "Globex Corporation",
                "address": "456 Oak Avenue, Metropolis, NY",
                "phone_number": "+1-800-555-5678",
            },
            {
                "id": "ff7b7b3c-2df9-4b93-9f2e-9bde4b7a40da",
                "name": "Initech Insurance",
                "address": "789 Pine Road, Silicon Valley, CA",
                "phone_number": "+1-800-555-9876",
            },
        ],
    },
)

insurance_provider_list_example = OpenApiExample(
    "List of Insurance Providers",
    value={
        "count": 3,
        "next": f"http://{BASE_URL}/insurers/?limit=25&offset=25",
        "previous": "null",
        "results": [
            {
                "id": "e1a5d88c-4b23-4b90-8e7a-b3fef95e3a80",
                "name": "Acme Insurance Co.",
                "address": "123 Elm Street, Springfield, IL",
                "phone_number": "+1-800-555-1234",
            },
            {
                "id": "d8e9d79a-d1c1-4f07-b6d8-7399be13b47e",
                "name": "Globex Corporation",
                "address": "456 Oak Avenue, Metropolis, NY",
                "phone_number": "+1-800-555-5678",
            },
            {
                "id": "ff7b7b3c-2df9-4b93-9f2e-9bde4b7a40da",
                "name": "Initech Insurance",
                "address": "789 Pine Road, Silicon Valley, CA",
                "phone_number": "+1-800-555-9876",
            },
        ],
    },
)
