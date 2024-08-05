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
            "vehicle_make": "Toyota",
            "vehicle_model": "Camry",
            "vehicle_year": 2022,
            "vehicle_value": 30000,
            "vehicle_age": 1,
        },
    },
    request_only=True,
    response_only=False,
)
