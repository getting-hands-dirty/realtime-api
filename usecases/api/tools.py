import os

import requests
from langchain_core.tools import StructuredTool, tool
from pydantic import BaseModel, Field

from usecases.util import convert_to_function

BASE_URL = os.getenv(
    "TOOLS_API_URL", "https://mock-api-realtime-938786674786.us-central1.run.app"
)

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


# ---------------------------
# Inventory Search Tool
# ---------------------------


class InventorySearchModel(BaseModel):
    vin: str = Field(None, description="Vehicle Identification Number.")
    stock_number: str = Field(None, description="Stock number of the vehicle.")
    vehicle_type: str = Field(enum=["New", "Used"], description="Type of the vehicle.")
    year: int = Field(None, description="Manufacturing year of the vehicle.")
    make: str = Field(
        enum=[
            "BMW",
            "Nissan",
            "Ford",
            "Cadillac",
            "Acura",
            "Tesla",
            "Volvo",
            "Honda",
            "Toyota",
            "Hyundai",
            "Volkswagen",
            "Mercedes-Benz",
            "Jeep",
            "Chevrolet",
            "Porsche",
            "Lexus",
            "INFINITI",
            "Audi",
            "Subaru",
            "MINI",
        ],
        description="Vehicle manufacturer (e.g., Toyota).",
    )
    model: str = Field(
        enum=[
            "5 Series",
            "2 Series",
            "4 Series",
            "3 Series",
            "M4",
            "M8",
            "X1",
            "X2",
            "iX",
            "X3",
            "X5",
            "X7",
            "i4",
            "Rogue",
            "Bronco",
            "Escalade",
            "MDX",
            "7 Series",
            "Model S",
            "S90",
            "Civic Sedan",
            "CTS Coupe",
            "RAV4",
            "Corolla",
            "Mustang",
            "Explorer",
            "Palisade",
            "M5",
            "Tiguan",
            "GLE",
            "8 Series",
            "Pathfinder",
            "Wrangler",
            "Escape",
            "Tahoe",
            "Cayenne",
            "CR-V",
            "Altima",
            "RX",
            "Macan",
            "X6",
            "Model Y",
            "TLX",
            "QX60",
            "UX",
            "GLC",
            "Q3",
            "X4",
            "WRX",
            "RC",
            "QX50",
            "Fit",
            "M3",
            "CLA",
            "Grand Cherokee",
            "Convertible",
            "Wrangler Unlimited",
            "Sienna",
            "i7",
            "i5",
            "X5 M",
            "Z4",
        ],
        description="Vehicle model (e.g., X5, X1).",
    )
    trim: str = Field(
        enum=[
            "530i xDrive",
            "540i xDrive",
            "M240i xDrive",
            "M440i xDrive",
            "M340i xDrive",
            "Competition xDrive",
            "Competition",
            "M35i",
            "xDrive28i",
            "330i xDrive",
            "xDrive50",
            "M60",
            "228 xDrive",
            "M235 xDrive",
            "430i xDrive",
            "30 xDrive",
            "xDrive40i",
            "M60i",
            "eDrive40",
            "M50",
            "xDrive40",
            "xDrive50e",
            "sDrive30i",
            "228i xDrive",
            "SL",
            "Outer Banks",
            "4WD Premium Luxury Platinum",
            "w/Technology Pkg",
            "760i xDrive",
            "75D",
            "Plus",
            "M235i xDrive",
            "EX",
            "Premium",
            "Limited",
            "LE",
            "330i",
            "Shelby GT350",
            "sDrive28i",
            "Platinum",
            "Sedan",
            "SE R-Line Black",
            "GLE 350",
            "M50i",
            "M850i xDrive",
            "S",
            "Unlimited Rubicon",
            "SV",
            "Titanium",
            "Premier",
            "AWD",
            "EX-L",
            "2.5 SR",
            "RX 350",
            "T",
            "M440i",
            "Touring",
            "Long Range",
            "Type S",
            "FWD 4dr",
            "UX 250h",
            "w/Tech",
            "GLC 300",
            "2.0T Prestige",
            "xDrive30i",
            "M40i",
            "RC 350 F SPORT",
            "AWD 4dr",
            "CLA 250",
            "Laredo",
            "RX 450h",
            "w/Technology Package",
            "Cooper S",
            "530i",
            "435i xDrive",
            "AMG GLE 53",
            "Rubicon",
            "Manual",
            "xDrive45e",
            "XSE",
            "840i",
            "eDrive50",
            "230i xDrive",
            "eDrive35",
            "xDrive60",
            "M70",
            "740i xDrive",
            "228i",
            "M50 xDrive",
            "M850i",
            "M340i",
        ],
        description="Vehicle trim level. Sometimes Refers to the version of the vehicle (e.g., xDrive).",
    )
    style: str = Field(
        enum=[
            "530i xDrive Sedan",
            "540i xDrive Sedan",
            "M240i xDrive Coupe",
            "M440i xDrive Convertible",
            "M340i xDrive Sedan",
            "Competition xDrive Convertible",
            "Competition Convertible",
            "M35i Sports Activity Vehicle",
            "xDrive28i Sports Activity Coupe",
            "330i xDrive Sedan",
            "xDrive28i Sports Activity Vehicle",
            "xDrive50 Sports Activity Vehicle",
            "M60 Sports Activity Vehicle",
            "228 xDrive Gran Coupe",
            "M235 xDrive Gran Coupe",
            "430i xDrive Convertible",
            "30 xDrive Sports Activity Vehicle",
            "xDrive40i Sports Activity Vehicle",
            "M60i Sports Activity Vehicle",
            "430i xDrive Coupe",
            "eDrive40 Gran Coupe",
            "M50 Gran Coupe",
            "xDrive40 Gran Coupe",
            "xDrive50e Plug-In Hybrid",
            "sDrive30i Sports Activity Vehicle",
            "228i xDrive Gran Coupe",
            "AWD SL",
            "Outer Banks 4 Door 4x4",
            "4WD 4dr Premium Luxury Platinum",
            "SH-AWD w/Technology Pkg",
            "760i xDrive Sedan",
            "75D AWD",
            "B6 AWD Plus",
            "M235i xDrive Gran Coupe",
            "EX CVT",
            "2dr Cpe Premium AWD",
            "Limited AWD",
            "LE CVT",
            "330i Sedan",
            "Shelby GT350 Fastback",
            "sDrive28i Sports Activity Coupe",
            "Platinum 4WD",
            "Sedan",
            "2.0T SE R-Line Black 4MOTION",
            "GLE 350 4MATIC SUV",
            "M50i Sports Activity Vehicle",
            "M850i xDrive Coupe",
            "4x4 S",
            "Unlimited Rubicon 4x4",
            "AWD SV",
            "FWD 4dr Titanium",
            "4WD 4dr Premier",
            "AWD",
            "EX-L AWD",
            "2.5 SR Sedan",
            "RX 350 AWD",
            "T AWD",
            "M440i Coupe",
            "xDrive40i Sports Activity Coupe",
            "Touring AWD",
            "Long Range AWD",
            "Type S SH-AWD",
            "FWD 4dr",
            "UX 250h AWD",
            "SH-AWD 4dr w/Tech",
            "GLC 300 4MATIC SUV",
            "quattro 4dr 2.0T Prestige",
            "xDrive30i Sports Activity Coupe",
            "M40i Sports Activity Vehicle",
            "Limited CVT",
            "330i Sedan North America",
            "RC 350 F SPORT AWD",
            "AWD 4dr",
            "5dr HB CVT EX",
            "330i xDrive Sedan North America",
            "M440i xDrive Gran Coupe",
            "CLA 250 4MATIC Coupe",
            "430i xDrive Gran Coupe",
            "4WD 4dr Laredo",
            "RX 450h AWD",
            "SH-AWD w/Technology Package",
            "M440i xDrive Coupe",
            "Cooper S FWD",
            "530i Sedan",
            "4dr Sdn 435i xDrive AWD Gran Coupe",
            "AMG GLE 53 4MATIC SUV",
            "Limited FWD",
            "Rubicon 4x4",
            "Manual",
            "xDrive30i Sports Activity Vehicle",
            "xDrive45e Plug-In Hybrid",
            "XSE AWD 7-Passenger",
            "SH-AWD 7-Passenger w/Technology Pkg",
            "840i xDrive Gran Coupe",
            "eDrive50 Sedan",
            "230i xDrive Coupe",
            "eDrive40 Sedan",
            "eDrive35 Gran Coupe",
            "M60 Sedan",
            "xDrive30i Sports Activity Vehicle South Africa",
            "xDrive40 Sedan",
            "xDrive60 Sedan",
            "M70 Sedan",
            "740i xDrive Sedan",
            "228i Gran Coupe",
            "M50 xDrive Sports Activity Vehicle",
            "M850i xDrive Gran Coupe",
            "Competition Gran Coupe",
            "Competition AWD",
            "Competition xDrive Sedan",
            "M40i Roadster",
            "840i xDrive Convertible",
            "sDrive30i Roadster",
            "M340i Sedan",
        ],
        description="Vehicle body style.",
    )
    exterior_color: str = Field(
        enum=[
            "Mineral White Metallic",
            "Oxide Grey Metallic",
            "Alpine White",
            "Arctic Race Blue Metallic",
            "Black Sapphire Metallic",
            "Skyscraper Grey Metallic",
            "Space Silver Metallic",
            "Vegas Red Metallic",
            "Dravit Grey Metallic",
            "Brooklyn Grey Metallic",
            "Dark Graphite Metallic",
            "Storm Bay Metallic",
            "Aventurin Red Metallic",
            "Thundernight Metallic",
            "Phytonic Blue Metallic",
            "Dune Grey Metallic",
            "San Remo Green Metallic",
            "Cape York Green Metallic",
            "Carbon Black Metallic",
            "Portimao Blue Metallic",
            "Jet Black",
            "Marina Bay Blue Metallic",
            "Gray",
            "Pearl White Tricoat",
            "Dark Moon Blue Metallic",
            "White",
            "Blue",
            "Black",
            "Melbourne Red Metallic",
            "Silver Coast Metallic",
            "Bluestone Metallic",
            "Silver",
            "Arctic Grey Metallic",
            "Sunset Orange Metallic",
            "Becketts Black",
            "Donington Grey Metallic",
            "Barcelona Blue Metallic",
            "Magnetic Black Pearl",
            "Granite Crystal Metallic Clearcoat",
            "Iridescent Pearl Tricoat",
            "Super Black",
            "Black Obsidian",
            "Ceramic White",
            "Tanzanite Blue II Metallic",
            "Atomic Silver",
            "Bright White Clearcoat",
            "Firecracker Red Clearcoat",
            "Dark Gray Metallic",
            "Brands Hatch Grey Metallic",
            "Snapper Rocks Blue Metallic",
            "Ametrin Metallic",
            "Utah Orange Metallic",
            "Brooklyn Gray Metallic",
            "(Ind) Frozen Brilliant White metallic",
            "Isle of Man Green Metallic",
            "Manhattan Green Metallic",
            "Special Order Color",
        ],
        description="Exterior color of the vehicle.",
    )
    interior_color: str = Field(
        enum=[
            "Black",
            "Mocha",
            "Tacora Red",
            "Silverstone/Black",
            "Silverstone",
            "Black w/Stitching",
            "Oyster",
            "Cognac",
            "Canberra Beige",
            "Red/Black Bicolor",
            "Black w/Red Highlight",
            "Espresso Brown",
            "Calm Beige",
            "Coffee",
            "Tartufo",
            "Black w/Contrast",
            "Light Gray",
            "Oyster/Black",
            "Whisper Beige with Gideon accents",
            "Beige",
            "Gray",
            "Cashmere/Ebony",
            "BLACK",
            "Aragon Brown",
            "Brown",
            "Black w/M Piping",
            "Charcoal",
            "Almond",
            "Jet Black",
            "Sport Interior",
            "Red",
            "Graphite",
            "Fiona Red/Black",
            "Smoke White",
            "Carbon Black",
            "Black w/Blue Stitching",
            "Oyster w/Contrast Stitch",
            "Ivory White/Night Blue",
            "Oyster w/Stitching",
            "Black w/Atlas Grey M",
            "Burgundy Red",
            "Kyalami Orange/Black",
            "Black/Atlas Grey",
            "Sakhir Orange/Black",
            "Silverstone II Atlas Grey",
            "Copper Brown/Atlas Grey",
            "Magma Red w/Black Stitch",
            "Red/Black",
        ],
        description="Interior color of the vehicle.",
    )
    certified: bool = Field(
        None, description="Whether the vehicle is certified pre-owned."
    )
    min_price: int = Field(None, description="Minimum price range for the vehicle.")
    max_price: int = Field(None, description="Maximum price range for the vehicle.")
    fuel_type: str = Field(None, description="Type of fuel used by the vehicle.")
    transmission: str = Field(
        enum=["Automatic", "Manual", "CVT", "Other"],
        description="Transmission type.",
    )
    drive_type: str = Field(
        enum=["AWD", "RWD", "4WD", "FWD"], description="Drive type."
    )
    doors: int = Field(None, description="Number of doors.")
    engine_type: str = Field(
        enum=[
            "0",
            "4",
            "4 Cylinder",
            "5",
            "8",
            "S",
            "Turbocharged",
            "6",
            "3",
            "Electric Motor",
            "V6",
            "V8",
            "V6 24V VVT",
            "EcoTec3 V8 engine",
            "V8 engine",
            "I4",
        ],
        description="Type of engine (Turbocharged, Hybrid, Electric).",
    )
    features: str = Field(
        enum=[
            "Auxiliary Audio Input",
            "Blind Spot Monitor",
            "Hands-Free Liftgate",
            "Heated Steering Wheel",
            "Lane Departure Warning",
            "LED Headlights",
            "Navigation System",
            "Rain Sensing Wipers",
            "Heated Seats",
            "Rear Heated Seats",
            "Wifi Hotspot",
            "Leather Seats",
            "Speed Sensitive Wipers",
            "Power Seats",
            "Telescoping Steering Wheel",
            "Rear Air Conditioning",
            "Rear Sunshade",
            "3rd Row Seat",
            "Automatic Climate Control",
            "Steering Wheel Controls",
            "Apple CarPlay",
            "Premium Audio",
            "Traffic Sign Recognition",
            "Android Auto",
            "Running Boards",
            "Fog Lights",
            "Forward Collision Warning",
            "Xenon Headlights",
        ],
        description="Specific vehicle feature to search for (e.g., Heated Seats).",
    )
    packages: str = Field(
        None,
        description="Specific vehicle package to search for (e.g., Premium Package, M Sport Package).",
    )
    fields: str = Field(
        None,
        description="The fields required to search the inventory (e.g., make, model, description, options, packages, features and all other fields) The fields must be picked based on the context of the user query and the information required to fulfill the user request.",
    )
    options: str = Field(
        None,
        description="Contains vehicle options and additional details about packages and features of the vehicle",
    )
    description: str = Field(
        None,
        description="Contains details related to the test drive, and general sales and service information.",
    )


@tool
def get_inventory_search(
    vin: str = None,
    stock_number: str = None,
    vehicle_type: str = None,
    year: int = None,
    make: str = None,
    model: str = None,
    trim: str = None,
    style: str = None,
    exterior_color: str = None,
    interior_color: str = None,
    certified: bool = None,
    min_price: int = None,
    max_price: int = None,
    fuel_type: str = None,
    transmission: str = None,
    drive_type: str = None,
    doors: int = None,
    engine_type: str = None,
    features: str = None,
    packages: str = None,
    description: str = None,
    fields: str = None,
    options: str = None,
    enable_fields: bool = False,
    context_limit: int = None,
):
    """
    Search the database for vehicle inventory information. VIN, StockNumber, Type, Make, Model, Year, etc., will be returned.
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
        "engine_type": engine_type,
        "features": features,
        "packages": packages,
        "description": description,
        "fields": fields if enable_fields else None,  # Include fields only if enabled
        "options": options,
        "context_limit": context_limit,
    }

    # Filter out None values
    filtered_params = {k: v for k, v in query_params.items() if v is not None}

    # Debugging print statements
    print(f"enable_fields: {enable_fields} | fields: {fields}")
    print(f"Filtered parameters: {filtered_params}")

    # Construct the URL with query parameters
    url = f"{BASE_URL}/search"
    full_url = requests.Request("GET", url, params=filtered_params).prepare().url
    print(f"Invoked URL: {full_url}")

    # Make the GET request
    response = requests.get(url, params=filtered_params)
    json_response = response.json()
    return str(json_response["data"])


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

TOOLS = [get_inventory_search, book_appointment, get_appointment_details]
TOOLS_SCHEMA = [
    convert_to_function(book_appointment_schema),
    convert_to_function(get_inventory_search_schema),
    convert_to_function(get_appointment_details_schema),
]
