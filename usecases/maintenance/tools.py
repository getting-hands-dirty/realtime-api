import requests
import os
from .util import tool

BASE_URL = os.getenv(
    "TOOLS_API_URL", "https://mock-api-realtime-938786674786.us-central1.run.app"
)


@tool
def book_appointment(
    customer_id: str, vehicle_id: str, date: str, time: str, service: str
):
    """
    Book an appointment for a vehicle service.

    Args:
        customer_id (str): The ID of the customer.
        vehicle_id (str): The ID of the vehicle.
        date (str): The date of the appointment (YYYY-MM-DD).
        time (str): The time of the appointment (HH:MM).
        service (str): The type of service to be performed.

    Returns:
        dict: Response from the API.
    """
    url = f"{BASE_URL}/book-appointment"
    payload = {
        "customer_id": customer_id,
        "vehicle_id": vehicle_id,
        "date": date,
        "time": time,
        "service": service,
    }
    response = requests.post(url, json=payload)
    return response.json()


@tool
def get_vehicle_details(vehicle_id: str):
    """
    Retrieve details of a vehicle by its ID.

    Args:
        vehicle_id (str): The ID of the vehicle.

    Returns:
        dict: Response from the API.
    """
    url = f"{BASE_URL}/vehicle/{vehicle_id}"
    response = requests.get(url)
    return response.json()


@tool
def get_vector_info(query: str):
    """
    Query the vector information from the vector database.

    Args:
        query (str): The query text.

    Returns:
        dict: Response from the API.
    """
    url = f"{BASE_URL}/vector-info"
    params = {"query": query, filter: {"customer_id": "C126"}}
    response = requests.post(url, params=params)
    return response.json()


@tool
def load_vector_info():
    """
    Load the vector information from the vector database.

    Returns:
        dict: Response from the API.
    """
    url = f"{BASE_URL}/vector-store/load"
    response = requests.get(url)
    return response.json()


TOOLS = [get_vehicle_details, get_vector_info]
TOOLS_SCHEMA = [tool.get_schema() for tool in TOOLS]
