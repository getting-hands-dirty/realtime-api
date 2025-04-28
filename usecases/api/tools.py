import json
import os
from urllib.parse import urlencode

import httpx
import requests
from bs4 import BeautifulSoup
from langchain_core.tools import StructuredTool, tool
from pydantic import BaseModel, Field

from usecases.util import convert_to_function

BASE_URL = os.getenv(
    "TOOLS_API_URL", "https://mock-api-realtime-938786674786.us-central1.run.app"
)

ALGOLIA_API_KEY = "78311e75e16dd6273d6b00cd6c21db3c"
ALGOLIA_APP_ID = "2591J46P8G"

HEADERS = {
    "Content-Type": "application/json",
    "X-Algolia-API-Key": ALGOLIA_API_KEY,
    "X-Algolia-Application-Id": ALGOLIA_APP_ID,
    "X-Algolia-Agent": "Algolia for JavaScript (4.9.1); Browser (lite); JS Helper (3.22.4)",
}

URL = f"https://{ALGOLIA_APP_ID.lower()}-dsn.algolia.net/1/indexes/*/queries"

# ---------------------------
# Book Appointment Tool
# ---------------------------


class BookAppointmentModel(BaseModel):
    customer_name: str = Field(None, description="Customer Name.")
    vehicle_details: str = Field(None, description="Vehicle Details.")
    date: str = Field(None, description="Appointment date.")
    time: str = Field(None, description="Appointment time.")
    service: str = Field(None, description="Service type.")


@tool
def book_appointment(
    customer_name: str,
    vehicle_details: str,
    date: str,
    time: str,
    service: str,
    enable_fields: bool = False,  # Not used
    context_limit: int = None,  # Not used
):
    """
    Book an appointment for a vehicle service, get all the details from the user to book the appointment.
    These details should be gathered from the user before invoking this tool.
    Customer Name, Vehicle Details, Date, Time, and Service.
    """
    url = f"{BASE_URL}/book-appointment"
    headers = {"Content-Type": "application/json"}
    payload = {
        "customer_name": customer_name,
        "vehicle_details": vehicle_details,
        "date": date,
        "time": time,
        "service": service,
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.text


book_appointment_schema = StructuredTool.from_function(
    func=book_appointment,
    name="book_appointment",
    description="""
    Book an appointment for a vehicle service, get all the details from the user to book the appointment.
    These details should be gathered from the user before invoking this tool.
    Customer Name, Vehicle Details, Date, Time, and Service.
    """,
    args_schema=BookAppointmentModel,
    return_direct=True,
)

# -------------------------
# Get Booking Details Tool
# -------------------------


class AppointmentDetails(BaseModel):
    query: str = Field(
        None,
        description="User's Query about the booked appointment. Must be a question",
    )


@tool
def get_appointment_details(
    query: str,
    re_rank: bool = False,
    hybrid_search: bool = False,
    hybrid_search_weight: float = 0.5,
    native: bool = False,
    top_k: int = 10,
    db: str = "pg",
    enable_fields: bool = False,  # Not used
    context_limit: int = None,  # Not used
):
    """
    Query the knowledge base for questions about the booked appointment.
    """
    url = f"{BASE_URL}/vector-info"
    headers = {"Content-Type": "application/json"}
    payload = {
        "query": query,
        "filter": {
            "topic": "maintenance",
        },
        "doRerank": re_rank,
        "doHybridSearch": hybrid_search,
        "hybridSearchOptions": {"searchWeight": hybrid_search_weight},
        "native": native,
        "k": top_k,
        "db": db,
    }

    response = requests.post(url, json=payload, headers=headers)
    print("RAG Payload: ", payload)

    return str(response.text)


get_appointment_details_schema = StructuredTool.from_function(
    func=get_appointment_details,
    name="get_appointment_details",
    description="Query the knowledge base for questions about the booked appointment.",
    args_schema=AppointmentDetails,
    return_direct=True,
)
# ----------------------------
# Inventory Search Tool
# ----------------------------


class InventorySearchModel(BaseModel):
    vehicle_type: str = Field(
        enum=["New", "Used", "Demo", "Certified Used"],
        description="Vehicle classification (e.g., New, Used, Demo, Certified Used).",
    )
    vehicle_status: str = Field(
        enum=["In Stock", "In-Transit"],
        description="Vehicle status (e.g., In Stock, In-Transit).",
    )
    model: str = Field(
        None,
        enum=[
            "Blazer",
            "Colorado",
            "Equinox",
            "Malibu",
            "Silverado 1500",
            "Silverado 2500 HD",
            "Silverado 3500 HD",
            "Suburban",
            "Tahoe",
            "Trailblazer",
            "Traverse",
            "Trax",
        ],
        description="Vehicle model (e.g., Silverado 1500).",
    )
    trim: str = Field(
        None,
        enum=[
            "2RS",
            "3LT",
            "ACTIV",
            "Custom",
            "Custom Trail Boss",
            "High Country",
            "LS",
            "LT",
            "LT Trail Boss",
            "LTZ",
            "RS",
            "RST",
            "Trail Boss",
            "WT",
            "WT/LT",
            "Z71",
        ],
        description="Vehicle trim level (e.g., LT, LTZ).",
    )
    body_style: str = Field(
        None, enum=["Cars", "SUVs", "Trucks"], description="Body style of the vehicle."
    )
    year: int = Field(
        None,
        enum=["2025", "2026", "2025-2026"],
        description="Manufacturing year of the vehicle.",
    )
    min_price: int = Field(None, description="Minimum price range for the vehicle.")
    max_price: int = Field(None, description="Maximum price range for the vehicle.")
    min_mileage: int = Field(None, description="Minimum mileage of the vehicle.")
    max_mileage: int = Field(None, description="Maximum mileage of the vehicle.")
    features: str = Field(
        None,
        enum=[
            "3rd Row Seat",
            "AWD",
            "Adaptive Cruise Control",
            "Android Auto",
            "Apple CarPlay",
            "Automatic Climate Control",
            "Backup Camera",
            "Bluetooth",
            "Cooled Seats",
            "Fog Lights",
            "Heated Seats",
            "Keyless Entry",
            "Lane Departure Warning",
            "Lane keep assist",
            "Leather Appointed Seating Package",
            "Navigation System",
            "Parking Sensors / Assist",
            "Power Seats",
            "Remote Start",
            "Side-Impact Air Bags",
            "Sunroof / Moonroof",
            "Technology Package",
            "Tow Package",
            "Wireless Phone Charging",
        ],
        description="Specific vehicle feature to search for (e.g., Apple CarPlay).",
    )
    fuel_type: str = Field(
        None,
        enum=["Diesel Fuel", "Gasoline Fuel"],
        description="Type of fuel used by the vehicle.",
    )
    engine_type: str = Field(
        None,
        enum=[
            "1.5L Turbo 4-cylinder engine",
            "2.5L Turbo engine",
            "3.0L Duramax® Turbo Diesel engine",
            "3.6L V6 engine",
            "5.3L EcoTec3 V8 engine",
            "5.3L V8 engine",
            "6.2L EcoTec3 V8 engine",
            "6.2L V8 engine",
            "6.6L Duramax Turbo-Diesel V8 engine",
            "6.6L V8 Gas engine",
            "ECOTEC 1.2L Turbo engine",
            "ECOTEC 1.3L Turbo engine",
            "TurboMax™ engine",
        ],
        description="Type of engine (e.g., 3.6L V6 engine).",
    )
    transmission: str = Field(
        None, enum=["Automatic"], description="Transmission type."
    )
    exterior_color: str = Field(
        None,
        enum=[
            "Black",
            "Cacti Green",
            "Cypress Gray",
            "Iridescent Pearl Tricoat",
            "Lakeshore Blue Metallic",
            "Mineral Gray Metallic",
            "Mosaic Black Metallic",
            "Nitro Yellow Metallic",
            "Radiant Red Tintcoat",
            "Slate Gray Metallic",
            "Sterling Gray Metallic",
            "Summit White",
        ],
        description="Exterior color of the vehicle.",
    )
    interior_color: str = Field(
        None,
        enum=[
            "Artemis Gray, Evotex seat trim",
            "Black with Red Accents, Evotex seat trim",
            "Black, Cloth seat trim",
            "Dark Atmosphere/ Medium Ash Gray, Premium cloth seat trim",
            "Gideon/Very Dark Atmosphere, Cloth seat trim",
            "Gideon/Very Dark Atmosphere, Leather-Appointed seating surfaces",
            "Gideon/Very Dark Atmosphere, Perforated leather-appointed front outboard seating positions",
            "Jet Black with Blue accents, Cloth/Evotex seat trim",
            "Jet Black with Red Accents, Perforated Leather-Appointed seat trim",
            "Jet Black with Red accents, Evotex seat trim",
            "Jet Black with Yellow accents, Cloth/Evotex seat trim",
            "Jet Black with Yellow stitching, Evotex seat trim",
            "Jet Black, Cloth seat trim",
            "Jet Black, Evotex seat trim",
            "Jet Black, Leather-Appointed seating surfaces",
            "Jet Black, Leather-appointed front outboard seat trim",
            "Jet Black, Leather-appointed front outboard seating positions",
            "Jet Black, Perforated Leather Seating surfaces",
            "Jet Black, Perforated Leather-Appointed seat trim",
            "Jet Black, Perforated leather-appointed front outboard seating positions",
            "Jet Black, Premium Cloth seat trim",
            "Jet Black, Vinyl seat trim",
            "Jet Black/Artemis with Yellow stitching, Evotex seat trim",
            "Jet Black/Nightshift Blue, Perforated leather seating surfaces",
            "LT Jet Black, Evotex seat trim",
            "LT Jet Black, Premium cloth seat trim",
            "Maple Sugar, Sueded Microfiber seat trim",
            "RS Jet Black with Torch Red accents, Perforated Leather-appointed seat trim",
        ],
        description="Interior color of the vehicle.",
    )


@tool
def get_inventory_search(
    vehicle_type: str = None,
    vehicle_status: str = None,
    model: str = None,
    trim: str = None,
    body_style: str = None,
    year: int = None,
    min_price: int = None,
    max_price: int = None,
    min_mileage: int = None,
    max_mileage: int = None,
    features: str = None,
    fuel_type: str = None,
    engine_type: str = None,
    transmission: str = None,
    exterior_color: str = None,
    interior_color: str = None,
    enable_fields: bool = False,
    context_limit: int = None,
):
    """
    Search the database for vehicle inventory information, including VIN, StockNumber, Type, Make, Model, Year, etc.
    When using this tool, always REMEMBER to say: "Give me a few minutes to have a look at our inventory."
    When describing the search results, avoid repeating the model name multiple times.
    After initially mentioning the model, simply refer to it using natural phrases like "It offers...", "This model comes with...", or "You'll get..." to keep the conversation flowing and avoid sounding robotic.
    """

    def build_facet_filter(key: str, value: str):
        return f"{key}:{value}"

    def generate_facet_filters(params: dict):
        mapping = {
            "type": "type",
            "vehicle_status": "vehicle_status",
            "model": "model",
            "trim": "trim",
            "body_style": "body",
            "features": "features",
            "fuel_type": "fueltype",
            "engine_type": "engine_description",
            "transmission": "transmission_description",
            "exterior_color": "ext_color",
            "interior_color": "int_color",
        }

        facet_filters = []
        for key, prefix in mapping.items():
            value = params.get(key)
            if value:
                facet_filters.append([build_facet_filter(prefix, value)])
        return facet_filters

    params = locals()
    facet_filters = generate_facet_filters(params)

    request_payload = {
        "requests": [
            {
                "indexName": "capitolchevroletal_production_inventory_custom_sort",
                "params": urlencode(
                    {
                        "facetFilters": json.dumps(facet_filters),
                        "facets": json.dumps(["model", "type", "trim", "body"]),
                        "hitsPerPage": 20,
                        "maxValuesPerFacet": 250,
                    }
                ),
            }
        ]
    }

    print("RAG Payload: ", request_payload)

    try:
        response = requests.post(URL, headers=HEADERS, json=request_payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        data = extract_vehicle_chunks_text(result["results"][0]["hits"])
        print("DATA: ", data)
        return data
    except requests.RequestException as e:
        print("❌ Request failed:", e)
        return None


get_inventory_search_schema = StructuredTool.from_function(
    func=get_inventory_search,
    name="get_inventory_search",
    description="Search the database for vehicle inventory information. VIN, StockNumber, Type, Make, Model, Year, etc., will be returned.",
    args_schema=InventorySearchModel,
    return_direct=True,
)

# ---------------------------
# Exported Tools
# ---------------------------

TOOLS = [book_appointment, get_inventory_search, get_appointment_details]
TOOLS_SCHEMA = [
    convert_to_function(book_appointment_schema),
    convert_to_function(get_inventory_search_schema),
    convert_to_function(get_appointment_details_schema),
]


def extract_vehicle_chunks_text(options: list) -> str:
    chunks = []

    for vehicle in options:
        ext_options = [
            BeautifulSoup(option, "html.parser").get_text(" ", strip=True)
            for option in vehicle.get("ext_options", [])
        ]
        int_options = [
            BeautifulSoup(option, "html.parser").get_text(" ", strip=True)
            for option in vehicle.get("int_options", [])
        ]

        chunk = f"""Title: {vehicle.get("title_vrp")}
                    MSRP: {vehicle.get("msrp")}
                    Our Price: {vehicle.get("our_price")}
                    Body: {vehicle.get("body")}
                    Cylinders: {vehicle.get("cylinders")}
                    In Stock Since: {vehicle.get("date_in_stock")}
                    Doors: {vehicle.get("doors")}
                    Drivetrain: {vehicle.get("drivetrain")}
                    Engine: {vehicle.get("engine_description")}
                    Exterior Color: {vehicle.get("ext_color")} ({vehicle.get("ext_color_generic")})
                    Fuel Type: {vehicle.get("fueltype")}
                    Interior Color: {vehicle.get("int_color")}
                    Location: {vehicle.get("location")}
                    Make: {vehicle.get("make")}
                    Miles: {vehicle.get("miles")}
                    Model: {vehicle.get("model")}
                    Transmission: {vehicle.get("transmission_description")}
                    Trim: {vehicle.get("trim")}
                    Type: {vehicle.get("type")}
                    Year: {vehicle.get("year")}
                    Vehicle Status: {vehicle.get("vehicle_status")}
                    
                    """.strip()

        chunks.append(chunk)

    return "\n\n".join(chunks[:10])
