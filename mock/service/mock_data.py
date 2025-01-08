from langchain_core.documents import Document

docs = [
    Document(
        page_content="Customer prefers evening appointments and has a busy morning schedule.",
        metadata={
            "id": 1,
            "customer_id": "C123",
            "preference": "evening",
            "topic": "appointment",
        },
    ),
    Document(
        page_content="Customer reported frequent brake issues in the last visit.",
        metadata={
            "id": 2,
            "customer_id": "C124",
            "vehicle_id": "V5678",
            "topic": "vehicle_issues",
        },
    ),
    Document(
        page_content="Vehicle Toyota Camry requires an oil change and tire rotation service.",
        metadata={
            "id": 3,
            "vehicle_id": "1234-ABC",
            "service_due": "oil change",
            "topic": "maintenance",
        },
    ),
    Document(
        page_content="Customer requested a quote for replacing car windshield wipers.",
        metadata={
            "id": 4,
            "customer_id": "C125",
            "vehicle_id": "9101-GHI",
            "topic": "quote_request",
        },
    ),
    Document(
        page_content="The community center offers yoga classes every Saturday morning.",
        metadata={"id": 5, "location": "community center", "topic": "events"},
    ),
    Document(
        page_content="Customer has a scheduled service appointment on January 15th at 10:00 AM.",
        metadata={
            "id": 6,
            "customer_id": "C126",
            "appointment_date": "2025-01-15",
            "topic": "appointment",
        },
    ),
    Document(
        page_content="A special discount on brake pad replacement is available this month.",
        metadata={
            "id": 7,
            "offer_id": "D789",
            "valid_until": "2025-01-31",
            "topic": "offers",
        },
    ),
    Document(
        page_content="The library is hosting a workshop on effective car maintenance tips.",
        metadata={"id": 8, "location": "library", "topic": "events"},
    ),
    Document(
        page_content="Tesla Model 3 is due for its annual maintenance check-up.",
        metadata={
            "id": 9,
            "vehicle_id": "9101-GHI",
            "service_due": "annual maintenance",
            "topic": "maintenance",
        },
    ),
    Document(
        page_content="Customer prefers communication via email for service updates.",
        metadata={
            "id": 10,
            "customer_id": "C127",
            "contact_preference": "email",
            "topic": "customer_preference",
        },
    ),
]


# Mock data for demonstration purposes
vehicles = {
    "1234-ABC": {"make": "Toyota", "model": "Camry", "year": 2020},
    "5678-DEF": {"make": "Honda", "model": "Civic", "year": 2022},
    "9101-GHI": {"make": "Tesla", "model": "Model 3", "year": 2023},
}
