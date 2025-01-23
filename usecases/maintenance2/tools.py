import os
from typing import Optional

import requests
from langchain_core.tools import StructuredTool, tool
from pydantic import BaseModel, Field

from usecases.util import convert_to_function

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


class InventoryVectorSearchModel(BaseModel):
    query: str = Field(
        None,
        description="User's Query to search the knowledge base. Must be a question",
    )


@tool
def get_vector_info_inventory(query: str):
    """
    Query the knowledge base for vehicle inventory information. VIN, StockNumber, Type, Make, Model, Year, etc will be returned.
    """
    url = f"{BASE_URL}/vector-info"
    headers = {"Content-Type": "application/json"}
    payload = {
        "query": query,
        "filter": {},
        "doRerank": False,
        "doHybridSearch": False,
        "hybridSearchOptions": {"searchWeight": 0.5, "useEntities": True},
        "native": False,
        "k": 10,
    }

    response = requests.post(url, json=payload, headers=headers)
    json_response = response.json()

    return str(json_response["context"])


schema = StructuredTool.from_function(
    func=get_vector_info_inventory,
    name="get_vector_info_inventory",
    description="Query the knowledge base for vehicle inventory information. VIN, StockNumber, Type, Make, Model, Year, etc will be returned.",
    args_schema=InventoryVectorSearchModel,
    return_direct=True,
)

TOOLS = [get_vector_info_inventory]
TOOLS_SCHEMA = [convert_to_function(schema)]
