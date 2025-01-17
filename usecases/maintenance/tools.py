import os
from typing import Optional

import requests

from .util import tool

BASE_URL = os.getenv(
    "TOOLS_API_URL", "https://mock-api-realtime-938786674786.us-central1.run.app"
)


@tool
def book_appointment(
    customer_id: str, vehicle_id: str, date: str, time: str, service: str
):
    """
    Book an appointment for a vehicle service, get all the details from the user to book the appointment.
    These details should be gathered from the user before invoking this tool.
    Customer ID, Vehicle ID, Date, Time, and Service.
    """
    url = f"{BASE_URL}/book-appointment"
    headers = {"Content-Type": "application/json"}
    payload = {
        "customer_id": customer_id,
        "vehicle_id": vehicle_id,
        "date": date,
        "time": time,
        "service": service,
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.text


@tool
def get_vehicle_details(vehicle_id: str):
    """
    Retrieve details of a vehicle by its ID. This should be invoked when vehicle details requested by user.
    """
    url = f"{BASE_URL}/vehicle/{vehicle_id}"
    response = requests.get(url)
    return response.text


@tool
def get_vector_info(query: str):
    """
    Query the knowledge base for general information, such as customer details, maintenance details and any other information.
    """
    url = f"{BASE_URL}/vector-info"
    headers = {"Content-Type": "application/json"}
    payload = {
        "query": query,
        "filter": {"topic": "maintenance"},
        "native": True,
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.text


@tool
def get_vector_info_inventory(query: str):
    """
    Query the knowledge base for vehicle inventory information. VIN, StockNumber, Type, Make, Model, Year, etc will be returned.
    """
    url = f"{BASE_URL}/vector-info"
    headers = {"Content-Type": "application/json"}
    payload = {
        "query": query,
        "filter": {"topic": "inventory"},
        "native": True,
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.text


@tool
def get_inventory_search(
    vin: Optional[str] = None,
    make: Optional[str] = None,
    model: Optional[str] = None,
    year: Optional[int] = None,
):
    """
    Search the database for vehicle inventory information. VIN, StockNumber, Type, Make, Model, Year, etc will be returned.
    """
    url = f"{BASE_URL}/search?vin={vin}&make={make}&model={model}&year={year}"
    print("URL: ", url)
    response = requests.get(url)
    return response.text


# TOOLS = [get_vehicle_details, get_vector_info, book_appointment]
TOOLS = [get_vector_info_inventory]
TOOLS_SCHEMA = [tool.get_schema() for tool in TOOLS]
