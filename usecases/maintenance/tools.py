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
    stock_number: Optional[str] = None,
    vehicle_type: Optional[str] = None,
    year: Optional[int] = None,
    make: Optional[str] = None,
    model: Optional[str] = None,
    trim: Optional[str] = None,
    style: Optional[str] = None,
    exterior_color: Optional[str] = None,
    interior_color: Optional[str] = None,
    certified: Optional[bool] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    fuel_type: Optional[str] = None,
    transmission: Optional[str] = None,
    drive_type: Optional[str] = None,
    doors: Optional[int] = None,
):
    """
    Search the database for vehicle inventory information.

    Parameters:
        vin (str): Vehicle Identification Number.
        stock_number (str): Stock number of the vehicle.
        vehicle_type (str): Type of the vehicle (e.g., SUV, Sedan).
        year (int): Manufacturing year of the vehicle.
        make (str): Vehicle manufacturer (e.g., Toyota).
        model (str): Vehicle model (e.g., Corolla).
        trim (str): Vehicle trim level.
        style (str): Vehicle body style.
        exterior_color (str): Exterior color of the vehicle.
        interior_color (str): Interior color of the vehicle.
        certified (bool): Whether the vehicle is certified pre-owned.
        min_price (float): Minimum price range for the vehicle.
        max_price (float): Maximum price range for the vehicle.
        fuel_type (str): Type of fuel used by the vehicle.
        transmission (str): Transmission type (e.g., Automatic, Manual).
        drive_type (str): Drive type (e.g., AWD, FWD, RWD).
        doors (int): Number of doors.

    Returns:
        str: Response from the inventory search API.
    """
    query_params = {
        "vin": vin,
        "stock_number": stock_number,
        "vehicle_type": vehicle_type,
        "year": year,
        "make": make,
        "model": model,
        "trim": trim,
        "style": style,
        "exterior_color": exterior_color,
        "interior_color": interior_color,
        "certified": certified,
        "min_price": min_price,
        "max_price": max_price,
        "fuel_type": fuel_type,
        "transmission": transmission,
        "drive_type": drive_type,
        "doors": doors,
    }

    # Filter out None values from query parameters
    filtered_params = {k: v for k, v in query_params.items() if v is not None}

    # Construct the URL with query parameters
    url = f"{BASE_URL}/search"
    response = requests.get(url, params=filtered_params)
    return response.text


# TOOLS = [get_vehicle_details, get_vector_info, book_appointment]
TOOLS = [get_vector_info_inventory]
TOOLS_SCHEMA = [tool.get_schema() for tool in TOOLS]
