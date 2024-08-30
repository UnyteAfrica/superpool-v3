from drf_spectacular.utils import OpenApiExample

claim_request_payload_example = OpenApiExample(
    "Basic valid payload with required fields",
    value={
        "claimant_metadata": {
            "first_name": "John",
            "last_name": "Doe",
            "birth_date": "1985-05-15",
            "email": "johndoe@example.com",
            "relationship": "Self",
        },
        "claim_details": {
            "claim_type": "accident",
            "incident_description": "Car accident on highway",
            "incident_date": "2024-07-10",
            "claim_amount": "1500.00",
        },
        "policy_id": "123e4567-e89b-12d3-a456-426614174000",
        "witness_details": [],
        "authority_report": {
            "report_number": "ABC123456",
            "report_date": "2024-07-11",
            "filing_station": "Miami Police Station",
        },
    },
)

minimal_request_payload_example = OpenApiExample(
    "Minimal valid payload with only required field - omitting optional fields",
    value={
        "claimant_metadata": {
            "first_name": "Alice",
            "last_name": "Johnson",
            "birth_date": "1980-01-01",
            "email": "alicejohnson@example.com",
            "relationship": "Parent",
        },
        "claim_details": {
            "claim_type": "theft",
            "incident_description": "Bicycle stolen from garage",
            "incident_date": "2024-07-20",
        },
    },
)

full_claim_request_payload_example = OpenApiExample(
    "Full valid payload with all fields",
    value={
        "claimant_metadata": {
            "first_name": "Jane",
            "last_name": "Smith",
            "birth_date": "1990-12-01",
            "email": "janesmith@example.com",
            "phone_number": "+1234567890",
            "relationship": "Spouse",
        },
        "claim_details": {
            "claim_type": "illness",
            "incident_description": "Hospitalized due to severe illness",
            "incident_date": "2024-06-15",
            "claim_amount": "5000.00",
            "supporting_documents": [
                {
                    "document_name": "Medical Report",
                    "evidence_type": "PDF",
                    "blob": "base64encodedstring",
                    "uploaded_at": "2024-06-16T08:00:00Z",
                }
            ],
        },
        "policy_id": "123e4567-e89b-12d3-a456-426614174001",
        "policy_number": "POL12345678",
        "witness_details": [
            {
                "witness_name": "Michael Doe",
                "witness_contact_phone": "+1987654321",
                "witness_contact_email": "michael.doe@example.com",
                "witness_statement": "I saw the entire incident happen.",
            }
        ],
        "authority_report": {
            "report_number": "XYZ987654",
            "report_date": "2024-06-17",
            "filing_station": "IsaleEko Police Station",
        },
    },
)

single_claim_response_example = OpenApiExample(
    "Claim informaton",
    value={
        "claim_id": "d2d0c0b4-bf72-4a61-a02e-3ab896dd8bf7",
        "claim_reference_number": "CLAIM-20240813-5678",
        "claim_status": "approved",
        "claim_date": "2024-08-13",
        "customer": {
            "first_name": "Michael",
            "last_name": "Smith",
            "dob": "1975-04-22",
            "email": "michaelsmith@example.com",
            "phone_number": "+9876543210",
        },
        "claim_amount": "3200.00",
        "insurer": "Leadway Assurance",
        "product": {"name": "Auto Insurance", "product_type": "Automobile"},
        "policy": "dc4bf271-6491-3812-8f39-58d4ccf39b70",
        "claim_status_timeline": [
            {"time_stamp": "2024-08-13 08:45:00", "name": "submitted"},
            {"time_stamp": "2024-08-13 10:00:00", "name": "under review"},
            {"time_stamp": "2024-08-13 12:15:00", "name": "pending approval"},
            {"time_stamp": "2024-08-13 14:30:00", "name": "approved"},
        ],
    },
)
