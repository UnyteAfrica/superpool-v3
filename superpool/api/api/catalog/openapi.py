from drf_spectacular.utils import OpenApiExample

travel_insurance_example = OpenApiExample(
    name="Travel Insurance",
    value={
        "product_type": "travel",
        "insurance_name": "World Travel Protection",
        "quote_code": "TRAVEL123",
        "insurance_details": {
            "destination": "France",
            "departure_date": "2023-09-01",
            "return_date": "2023-09-15",
            "number_of_travellers": 2,
            "trip_duration": 14,
            "trip_type": "round_trip",
            "trip_type_details": "leisure",
        },
        # Customer Information is optional
        "customer_metadata": {
            "first_name": "Pluto",
            "last_name": "Presido",
            "customer_email": "plutopresido@management.com",
            "customer_address": "Planet Pluto",
        },
    },
    request_only=True,  # indicates this is a request example
    response_only=False,
)

health_insurance_example = OpenApiExample(
    name="Health Insurance",
    value={
        "product_type": "health",
        "insurance_name": "Smart Health Insurance",
        "quote_code": "HEALTH123",
        "insurance_details": {
            "health_condition": "good",
            "age": 30,
            "coverage_type": "standard",
            "coverage_type_details": "individual",
        },
        # Customer Information is optional
        "customer_metadata": {
            "first_name": "Pluto",
            "last_name": "Presido",
            "customer_email": "plutopresido@management.com",
            "customer_address": "Planet Pluto",
        },
    },
    request_only=True,
    response_only=False,
)

home_insurance_example = OpenApiExample(
    name="Home Insurance",
    value={
        "product_type": "home",
        "insurance_name": "Home Protection",
        "quote_code": "HOME123",
        "insurance_details": {
            "home_type": "apartment",
            "home_location": "New York",
            "home_value": 500000,
            "home_age": 10,
        },
        # Customer Information is optional
        "customer_metadata": {
            "first_name": "Pluto",
            "last_name": "Presido",
            "customer_email": "plutopresido@management.com",
            "customer_address": "Planet Pluto",
        },
    },
    request_only=True,
    response_only=False,
)

gadget_insurance_example = OpenApiExample(
    name="Gadget Insurance",
    value={
        "product_type": "gadget",
        "insurance_name": "Gadget Protection",
        "quote_code": "GADGET123",
        "insurance_details": {
            "gadget_type": "smartphone",
            "gadget_brand": "Apple",
            "gadget_model": "iPhone 13",
            "gadget_value": 1000,
            "gadget_age": 1,
        },
        # Customer Information is optional
        "customer_metadata": {
            "first_name": "Pluto",
            "last_name": "Presido",
            "customer_email": "plutopresido@management.com",
            "customer_address": "Planet Pluto",
        },
    },
    request_only=True,
    response_only=False,
)

auto_insurance_example = OpenApiExample(
    name="Auto Insurance",
    value={
        "product_type": "auto",
        "insurance_name": "Comprehensive Auto Protection",
        "quote_code": "AUTO123",
        "insurance_details": {
            "vehicle_type": "car",
            "vehicle_make": "Tesla",
            "vehicle_model": "GLE",
            "vehicle_year": 2022,
            "vehicle_value": 30000,
            "vehicle_age": 1,
        },
        "customer_metadata": {
            "first_name": "Pluto",
            "last_name": "Presido",
            "customer_email": "plutopresido@management.com",
            "customer_address": "Planet Pluto",
        },
    },
    request_only=True,
    response_only=False,
)


##############################################################################
# PRODUCTS
##############################################################################
products_response_example = OpenApiExample(
    "List of Insurance Products Example",
    value=[
        {
            "id": "d0378ac1-f7e2-45ca-9312-6473d8d3d567",
            "created_at": "2024-08-06T10:56:00.900428Z",
            "updated_at": "2024-08-06T10:56:00.900485Z",
            "is_trashed": False,
            "trashed_at": None,
            "restored_at": None,
            "name": "Travel Insurance",
            "description": "Travel",
            "product_type": "Travel",
            "coverage_details": None,
            "is_live": True,
            "provider": "c8ab1b72-5fee-4ca0-9d3e-591f9e782171",
        },
        {
            "id": "584926a8-c2ed-4feb-a37f-98d071656427",
            "created_at": "2024-07-29T16:58:40.262604Z",
            "updated_at": "2024-07-29T16:58:40.262664Z",
            "is_trashed": False,
            "trashed_at": None,
            "restored_at": None,
            "name": "Plus Economic Life Insurance",
            "description": "City treat national price.",
            "product_type": "Auto",
            "coverage_details": None,
            "is_live": True,
            "provider": "a53dccce-cced-4fea-a794-028986f43927",
        },
        {
            "id": "5fc4f5d2-c1de-4007-b8f7-fe44836473ed",
            "created_at": "2024-08-06T10:55:54.453115Z",
            "updated_at": "2024-08-06T10:55:54.453162Z",
            "is_trashed": False,
            "trashed_at": None,
            "restored_at": None,
            "name": "Health Insurance",
            "description": "Health",
            "product_type": "Health",
            "coverage_details": None,
            "is_live": True,
            "provider": "c8ab1b72-5fee-4ca0-9d3e-591f9e782171",
        },
        {
            "id": "05268117-a576-4318-8e3c-e0df7c399fa5",
            "created_at": "2024-08-06T10:55:58.175434Z",
            "updated_at": "2024-08-06T10:55:58.175497Z",
            "is_trashed": False,
            "trashed_at": None,
            "restored_at": None,
            "name": "Auto Insurance",
            "description": "Auto",
            "product_type": "Auto",
            "coverage_details": None,
            "is_live": True,
            "provider": "c8ab1b72-5fee-4ca0-9d3e-591f9e782171",
        },
        {
            "id": "72512701-906f-4aa7-9d19-2c2315f7df37",
            "created_at": "2024-08-06T10:56:43.935129Z",
            "updated_at": "2024-08-06T10:56:43.935207Z",
            "is_trashed": False,
            "trashed_at": None,
            "restored_at": None,
            "name": "Gadget Insurance",
            "description": "Gadget",
            "product_type": "Gadget",
            "coverage_details": None,
            "is_live": True,
            "provider": "c8ab1b72-5fee-4ca0-9d3e-591f9e782171",
        },
    ],
)
