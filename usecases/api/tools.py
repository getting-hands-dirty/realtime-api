import json
import os
from typing import Optional, List
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup
from langchain_core.tools import StructuredTool, tool
from pydantic import BaseModel, Field

from usecases.util import convert_to_function, extract_prices, format_vehicle_price

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
# Get Customer Details Tool
# ---------------------------
class ContactDetailsModel(BaseModel):
    customer_name: str = Field(..., description="Customer's full name.")
    phone_number: str = Field(..., description="Customer's phone number.")


@tool
def capture_contact_details(
    customer_name: str,
    phone_number: str,
    enable_fields: bool = False,  # Not used
    context_limit: int = None,  # Not used
):
    """
    Capture the customer's contact details for safety in case the conversation gets interrupted.
    Always invoke this tool right after the greeting, **only after collecting and confirming** the customer's contact details.

                    Follow these steps strictly before invoking:
                    1. Politely ask the customer for their full name and best phone number.
                       → Example: “Just before we dive in, can I grab your name and the best number to reach you in case we get disconnected?”

                    2. Repeat the captured phone number and confirm:
                       → “Thanks, [Name]. I’ve noted your number as [Phone Number]. Can you please confirm that this is correct?”

                    3. Wait for the customer to explicitly confirm.

                    4. ONLY AFTER the customer confirms, invoke this tool with the captured name and phone number.

    """

    url = f"{BASE_URL}/save-contact"
    headers = {"Content-Type": "application/json"}
    payload = {
        "customer_name": customer_name,
        "phone_number": phone_number,
        "service_supplier": "Capitol Chevrolet Montgomery",
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.text


capture_contact_details_schema = StructuredTool.from_function(
    func=capture_contact_details,
    name="capture_contact_details",
    description="""Always invoke this tool right after the greeting, **only after collecting and confirming** the customer's contact details.
                    
                    Follow these steps strictly before invoking:
                    1. Politely ask the customer for their full name and best phone number.
                       → Example: “Just before we dive in, can I grab your name and the best number to reach you in case we get disconnected?”
                    
                    2. Repeat the captured phone number and confirm:
                       → “Thanks, [Name]. I’ve noted your number as [Phone Number]. Can you please confirm that this is correct?”
                    
                    3. Wait for the customer to explicitly confirm.
                    
                    4. ONLY AFTER the customer confirms, invoke this tool with the captured name and phone number.
                """,
    args_schema=ContactDetailsModel,
    return_direct=True,
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
    Book an appointment for a vehicle test drive or store visit.

    Before invoking this tool, collect the following mandatory details from the user:
    • Customer Name
    • Vehicle Details
    • Date
    • Time (must be strictly between 9:00 AM and 8:00 PM)
    • Service Type

    Important:
    - Do NOT proceed if the time is outside 9:00 AM to 8:00 PM.
    - If the user provides an invalid time, respond with:
    "Our store hours are between 9:00 AM and 8:00 PM. Please provide a time within this range."

    This validation is mandatory and must be enforced before invoking the tool.
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
    description="""Book an appointment for a vehicle test drive or store visit.

                Before invoking this tool, collect the following mandatory details from the user:
                • Customer Name
                • Vehicle Details
                • Date
                • Time (must be strictly between 9:00 AM and 8:00 PM)
                • Service Type

                Important:
                - Do NOT proceed if the time is outside 9:00 AM to 8:00 PM.
                - If the user provides an invalid time, respond with:
                "Our store hours are between 9:00 AM and 8:00 PM. Please provide a time within this range."

                This validation is mandatory and must be enforced before invoking the tool.
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
    """"Query the knowledge base strictly for questions related to appointments that were already booked over the phone.
        Do not use this for vehicle service status check related queries or new booking inquiries.
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
    description=""""Query the knowledge base strictly for questions related to appointments that were already booked over the phone.
                    Do not use this for vehicle service status check related queries or new booking inquiries.
                """,
    args_schema=AppointmentDetails,
    return_direct=True,
)


# ----------------------------
# Inventory Search Tool
# ----------------------------
class InventorySearchModel(BaseModel):
    make: str = Field(
        None,
        enum=[
            "Audi",
            "BMW",
            "Buick",
            "Chevrolet",
            "Chrysler",
            "Dodge",
            "Ford",
            "GMC",
            "Honda",
            "Hyundai",
            "INFINITI",
            "Jaguar",
            "Jeep",
            "Kia",
            "Lexus",
            "Mercedes-Benz",
            "Nissan",
            "Ram",
            "Tesla",
            "Toyota",
            "Volkswagen",
        ],
        description="Vehicle make (e.g., Chevrolet, BMW, Nissan).",
    )
    type: str = Field(
        None,
        enum=["New", "Used", "Demo", "Certified Used"],
        description="Vehicle classification. Options: New, Used, Demo, Certified Used.",
    )
    model: str = Field(
        None,
        enum=[
            "1500",
            "3 Series",
            "4 Series",
            "5 Series",
            "7 Series",
            "Altima",
            "Armada",
            "Avalanche",
            "Blazer",
            "C-Class",
            "Camry",
            "Charger",
            "Cherokee",
            "Colorado",
            "Compass",
            "Durango",
            "E-PACE",
            "Encore",
            "Equinox",
            "Expedition",
            "Explorer",
            "F-150",
            "Forte",
            "GLE",
            "GLS",
            "Grand Cherokee",
            "Highlander",
            "K5",
            "Malibu",
            "Model 3",
            "Mustang",
            "NX 200t",
            "Optima",
            "Pilot",
            "Q7",
            "QX50",
            "RAV4",
            "Rogue",
            "Santa Cruz",
            "Sentra",
            "Sienna",
            "Sierra 1500",
            "Silverado 1500",
            "Silverado 2500 HD",
            "Silverado 3500 HD",
            "Sportage",
            "Suburban",
            "Tacoma 4WD",
            "Tahoe",
            "Taos",
            "Telluride",
            "Terrain",
            "Trailblazer",
            "Traverse",
            "Trax",
            "Tundra 4WD",
            "Voyager",
            "Wagoneer L",
            "Wrangler",
            "Wrangler Unlimited",
            "X1",
            "X2",
            "X3",
            "X5",
            "X6",
            "X7",
            "Yukon XL",
            "i4",
            "i7",
        ],
        description="Vehicle model (e.g., Silverado 1500, Colorado).",
    )
    trim: str = Field(
        None,
        enum=[
            "(RED) Edition",
            "1LT",
            "2.5 S",
            "2.5 SV",
            "2RS",
            "330e",
            "330i",
            "330i xDrive",
            "3LT",
            "430i",
            "530i",
            "530i xDrive",
            "740i",
            "740i xDrive",
            "ACTIV",
            "Altitude Lux",
            "C 300",
            "Custom",
            "Denali",
            "EX",
            "EcoBoost",
            "Elevation",
            "FWD 4dr",
            "GLE 350",
            "GLS 580",
            "GT Plus",
            "GT-Line",
            "High Country",
            "L",
            "LE AAS",
            "LS",
            "LT",
            "LT Trail Boss",
            "LTZ",
            "LUXE",
            "LX",
            "Laramie",
            "Latitude",
            "Limited",
            "M40i",
            "NA",
            "Performance",
            "Platinum",
            "Preferred",
            "Premier",
            "Prestige",
            "RS",
            "RST",
            "S",
            "SE",
            "SLT",
            "SR",
            "SV",
            "SX Prestige X-Pro",
            "SXT",
            "Series II",
            "Special Edition",
            "Sport",
            "Trail Boss",
            "Trailhawk",
            "Unlimited Rubicon",
            "WT",
            "WT/LT",
            "XL",
            "XLE",
            "XLE V6",
            "XLT",
            "Z71",
            "eDrive35",
            "sDrive28i",
            "sDrive30i",
            "sDrive40i",
            "xDrive28i",
            "xDrive40i",
            "xDrive60",
        ],
        description="Vehicle trim level (e.g., LT, LTZ).",
    )
    body_style: str = Field(
        None,
        enum=["Cars", "Compact", "Convertible", "SUVs", "Trucks", "Vans"],
        description="Body style of the vehicle.",
    )
    min_year: int = Field(
        None,
        enum=[
            2007,
            2011,
            2014,
            2015,
            2016,
            2017,
            2018,
            2019,
            2020,
            2021,
            2022,
            2023,
            2024,
            2025,
            2026,
        ],
        description="Minimum manufacturing year of the vehicle. e.g., 2020, 2021",
    )
    max_year: int = Field(
        None,
        enum=[
            2007,
            2011,
            2014,
            2015,
            2016,
            2017,
            2018,
            2019,
            2020,
            2021,
            2022,
            2023,
            2024,
            2025,
            2026,
        ],
        description="Maximum manufacturing year of the vehicle. e.g., 2020, 2021",
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
            "Blind Spot Monitor",
            "Bluetooth",
            "Collision Avoidance",
            "Cooled Seats",
            "Fog Lights",
            "Forward Collision Warning",
            "Hands-Free Liftgate",
            "Heated Seats",
            "Interior Accents",
            "Keyless Entry",
            "Lane Departure Warning",
            "Lane keep assist",
            "Leather Appointed Seating Package",
            "Leather Seats",
            "M Sport",
            "Navigation System",
            "Parking Sensors / Assist",
            "Parktronic",
            "Performance Tire and Wheel",
            "Power Liftgate",
            "Power Seats",
            "Premium Audio",
            "Premium Package",
            "Push Start",
            "Rain Sensing Wipers",
            "Rear A/C",
            "Rear Entertainment System",
            "Rear Heated Seats",
            "Rear Sunshade",
            "Remote Start",
            "Satellite Radio Ready",
            "Side-Impact Air Bags",
            "Sunroof / Moonroof",
            "Technology Package",
            "Tow Package",
            "WiFi Hotspot",
            "Wireless Phone Charging",
            "Xenon Headlights",
        ],
        description="Specific vehicle feature to search for (e.g., Apple CarPlay).",
    )
    fuel_type: str = Field(
        None,
        enum=[
            "Diesel Fuel",
            "Electric Fuel System",
            "Flex Fuel Capability",
            "Gasoline Fuel",
            "Gasoline/Mild Electr",
            "Hybrid Fuel",
        ],
        description="Type of fuel used by the vehicle.",
    )
    engine_type: str = Field(
        None,
        enum=[
            "1.5 Liter 3 Cylinder",
            "1.5 Liter 4 Cylinder",
            "1.5L Turbo 4-cylinder engine",
            "1.5L Turbo Gas Engine",
            "1.6 Liter 4 Cylinder",
            "2.0 Liter 4 Cylinder",
            "2.0L Turbo 4-cylinder engine",
            "2.3 Liter 4 Cylinder",
            "2.4 Liter 4 Cylinder",
            "2.5 Liter 4 Cylinder",
            "2.5L 4-cylinder engine",
            "2.5L Turbo engine",
            "2.7 Liter V6 Cylinde",
            "3.0 Liter Straight 6",
            "3.0 Liter V6 Cylinde",
            "3.0L Duramax Turbo-Diesel I6 engine",
            "3.0L Duramax® Turbo Diesel engine",
            "3.2 Liter V6 Cylinde",
            "3.5 Liter V6 Cylinde",
            "3.6 Liter V6 Cylinde",
            "3.6L V6 engine",
            "3.8 Liter V6 Cylinde",
            "4.0 Liter 8 Cylinder",
            "5.3L EcoTec3 V8 engine",
            "5.3L V8 engine",
            "5.6 Liter 8 Cylinder",
            "5.7 Liter 8 Cylinder",
            "6.2L EcoTec3 V8 engine",
            "6.2L V8 engine",
            "6.6L Duramax Turbo-Diesel V8 engine",
            "6.6L V8 Gas engine",
            "ECOTEC 1.2L Turbo engine",
            "ECOTEC 1.3L Turbo engine",
            "ECOTEC 1.4L Turbo engine",
            "Electric",
            "FLEXIBLE FUEL, (GAS/ALC), 8 CYL, 5.3L, SFI, ALUM CYL DEACTIVATION, GM",
            "GAS, 4 CYL, 2.4L, SIDI, DOHC, E85 MAX, ALUM, GM",
            "Gas/Electric V-6 3.6 L/220",
            "Intercooled Supercharger Premium Unleaded V-6 3.0 L/183",
            "Intercooled Turbo Gas/Electric I-6 3.0 L/183",
            "Intercooled Turbo Premium Unleaded I-4 2.0 L/120",
            "Intercooled Turbo Premium Unleaded I-4 2.0 L/121",
            "Intercooled Turbo Premium Unleaded I-4 2.0 L/122",
            "Intercooled Turbo Premium Unleaded I-6 3.0 L/183",
            "Regular Unleaded I-4 2.5 L/152",
            "Regular Unleaded V-6 3.5 L/211",
            "TurboMax™ engine",
        ],
        description="Type of engine (e.g. 3.6L V6 engine, 6.6L V8 Gas engine).",
    )
    transmission: str = Field(
        None,
        enum=[
            "1-Speed Automatic",
            "1-Speed CVT w/OD",
            "6-Speed Automatic w/OD",
            "7-Speed Auto-Shift Manual w/OD",
            "8-Speed Automatic w/OD",
            "9-Speed Automatic w/OD",
            "Automatic",
        ],
        description="Transmission type.",
    )
    exterior_color: str = Field(
        None,
        enum=[
            "Alpine White",
            "Bernina Grey Amber Effect",
            "Black",
            "Black Sapphire Metallic",
            "Blk/black",
            "Blu/blue",
            "Blue",
            "Bright Blue Metallic",
            "CAJUN RED TINTCOAT",
            "Cacti Green",
            "Cherry Red Tintcoat",
            "Crimson Metallic",
            "Cypress Gray",
            "Dark Copper Metallic",
            "Dark Graphite Metallic",
            "Donington Gray Metallic",
            "Ebony Twilight Metallic",
            "Fountain Blue",
            "Glacier Silver Metallic",
            "Gld/gold",
            "Graphite Shadow",
            "Gray",
            "Graystone Metallic",
            "Green",
            "Gy/gray",
            "Hydro Blue Pearlcoat",
            "Iridescent Pearl Tricoat",
            "Lakeshore Blue Metallic",
            "Mar/maroon",
            "Midnight Black Metallic",
            "Mineral Gray Metallic",
            "Mineral White Metallic",
            "Mosaic Black Metallic",
            "Nitro Yellow Metallic",
            "Onyx Black",
            "Orange",
            "Pacific Blue Metallic",
            "Pewter Metallic",
            "Radiant Red Tintcoat",
            "Red",
            "Red Hot",
            "Red/red",
            "Satin Steel Metallic",
            "Sil/silver",
            "Silver",
            "Silver Ice Metallic",
            "Skyscraper Grey Metallic",
            "Titanium Rush Metallic",
            "Whi/white",
            "White",
            "White Frost Tricoat",
        ],
        description="Exterior color of the vehicle.",
    )
    interior_color: str = Field(
        None,
        enum=[
            "Artemis Gray, Evotex seat trim",
            "Ash",
            "BLK/Black",
            "Beige",
            "Black",
            "Black with Red Accents, Evotex seat trim",
            "Black, Cloth seat trim",
            "Brown",
            "CUSTOM LEATHER APPOINTED SEAT TRIM",
            "Canberra Beige",
            "Canberra Beige/Black",
            "Cognac",
            "Dark Atmosphere/ Medium Ash Gray, Premium cloth seat trim",
            "Dark Walnut/Slate, Perforated leather-appointed front outboard seat trim",
            "Ebony, Cloth with leatherette seat trim",
            "GRY/Gray",
            "Gideon/Very Dark Atmosphere, Cloth seat trim",
            "Gideon/Very Dark Atmosphere, Leather-Appointed seating surfaces",
            "Gideon/Very Dark Atmosphere, Perforated leather-appointed front outboard seating positions",
            "Gideon/Very Dark Atmosphere, Premium cloth seat trim",
            "Graphite",
            "Gray",
            "Ivory White/Black",
            "Jet Black with Blue accents, Cloth/Evotex seat trim",
            "Jet Black with Red Accents, Perforated Leather-Appointed seat trim",
            "Jet Black with Red Accents, Perforated Leather-Appointed seat trim",
            "Jet Black with Red accents, Evotex seat trim",
            "Jet Black with Yellow accents, Cloth/Evotex seat trim",
            "Jet Black with Yellow stitching, Evotex seat trim",
            "Jet Black, Cloth seat trim",
            "Jet Black, Evotex seat trim",
            "Jet Black, Forge perforated leather seat trim",
            "Jet Black, Leather-Appointed seating surfaces",
            "Jet Black, Perforated Leather-Appointed seat trim",
            "Jet Black, Perforated Leather-Appointed seating",
            "Jet Black, Perforated leather seating surfaces 1st and 2nd row",
            "Jet Black, Leather-appointed front outboard seat trim",
            "Jet Black, Leather-appointed front outboard seating positions",
            "Jet Black/Dark Ash, Cloth seat trim",
            "Jet Black/Medium Ash Gray, Cloth seat trim",
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
            "Medium Ash Gray, Premium Cloth seat trim",
            "NNB/BLACK",
            "RA00/Charcoal",
            "RS Jet Black with Torch Red accents, Perforated Leather-appointed seat trim",
            "TAN/Tan",
        ],
        description="Interior color of the vehicle. (e.g. Black, Gray, Jet Black, Perforated leather-appointed front outboard seating positions).",
    )


@tool
def get_inventory_search(
    make: Optional[str] = None,
    type: Optional[str] = None,
    model: Optional[str] = None,
    trim: Optional[str] = None,
    body_style: Optional[str] = None,
    min_year: Optional[int] = None,
    max_year: Optional[int] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    min_mileage: Optional[int] = None,
    max_mileage: Optional[int] = None,
    features: Optional[str] = None,
    fuel_type: Optional[str] = None,
    engine_type: Optional[str] = None,
    transmission: Optional[str] = None,
    exterior_color: Optional[str] = None,
    interior_color: Optional[str] = None,
    enable_fields: bool = False,
    context_limit: int = None,
):
    """Use this tool to search the database for available vehicle inventory.

                ➤ Response Behavior:

                1. **Before triggering the tool**, always say exactly:
                   **“Give me a second. Let me check that for you”**
                   🔒 Do not add anything else. Do not repeat the vehicle name here — trust that context is already established.

                2. If 3 or fewer vehicles are returned, provide a very brief summary of each vehicle and highlight the pricing.

                3. When more than 3 vehicles are returned:
                   - Summarize up to **three** vehicles using only:
                     - Exterior Color
                     - Model
                     - Interior Color

                   ➤ Use natural, descriptive phrasing instead of bullet points.
                   ➤ Mention the model name **only once per vehicle**. For subsequent references, use phrases like:
                     “this one,” “you’ll get,” or “it features.”

                4. Do **not** include full specifications in the initial summary. Only provide detailed information for one specific vehicle **if the customer requests it.**

                5. If vehicles are summarized, conclude with:
                   “Choose one of the options you just mentioned in the summary,” and provide full specifications for that specific vehicle.

                6. Always maintain a warm, confident, and helpful tone. Avoid robotic or overly scripted responses. Use contractions and natural expressions. Speak as if you’re having a real conversation.
    """
    def build_facet_filter(key: str, value: str | int | List[int]) -> List[str]:
        if isinstance(value, list):
            return [f"{key}:{v}" for v in value]
        return [f"{key}:{value}"]

    def generate_facet_filters(params: dict):
        mapping = {
            "make": "make",
            "type": "type",
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
            if value is not None:
                facet_filters.append(build_facet_filter(prefix, value))

        min_year = params.get("min_year")
        max_year = params.get("max_year")

        if min_year and max_year:
            year_range = list(range(min_year, max_year + 1))
            facet_filters.append(build_facet_filter("year", year_range))
        elif min_year:
            facet_filters.append(build_facet_filter("year", min_year))
        elif max_year:
            facet_filters.append(build_facet_filter("year", max_year))

        return facet_filters

    def generate_numeric_filters(params: dict) -> List[str]:
        numeric_filters = []

        min_price = params.get("min_price")
        max_price = params.get("max_price")

        if min_price is not None:
            numeric_filters.append(f"our_price>={min_price}")
        if max_price is not None:
            numeric_filters.append(f"our_price<={max_price}")

        min_mileage = params.get("min_mileage")
        max_mileage = params.get("max_mileage")

        if min_mileage is not None:
            numeric_filters.append(f"miles>={min_mileage}")
        if max_mileage is not None:
            numeric_filters.append(f"miles<={max_mileage}")

        return numeric_filters

    params = locals()
    facet_filters = generate_facet_filters(params)
    numeric_filters = generate_numeric_filters(params)
    print("Facet Filters: ", facet_filters)
    print("Numeric Filters: ", numeric_filters)

    request_payload = {
        "requests": [
            {
                "indexName": "capitolchevroletal_production_inventory_custom_sort",
                "params": urlencode(
                    {
                        "facetFilters": json.dumps(facet_filters),
                        "numericFilters": json.dumps(numeric_filters),
                        "facets": json.dumps(
                            [
                                "Location",
                                "Location_VDP",
                                "algolia_sort_order",
                                "api_id",
                                "bedtype",
                                "body",
                                "certified",
                                "city_mpg",
                                "courtesy_transportation",
                                "custom_sort",
                                "cylinders",
                                "date_in_stock",
                                "date_modified",
                                "days_in_stock",
                                "doors",
                                "drivetrain",
                                "engine_description",
                                "ext_color",
                                "ext_color_generic",
                                "ext_options",
                                "features",
                                "features",
                                "finance_details",
                                "ford_SpecialVehicle",
                                "fueltype",
                                "hash",
                                "hw_mpg",
                                "in_transit_filter",
                                "int_color",
                                "int_options",
                                "lease_details",
                                "lightning",
                                "lightning.class",
                                "lightning.finance_monthly_payment",
                                "lightning.isPolice",
                                "lightning.isSpecial",
                                "lightning.lease_monthly_payment",
                                "lightning.locations",
                                "lightning.locations.meta_location",
                                "lightning.status",
                                "link",
                                "location",
                                "make",
                                "metal_flags",
                                "miles",
                                "model",
                                "model_number",
                                "msrp",
                                "objectID",
                                "our_price",
                                "our_price_label",
                                "special_field_4",
                                "special_field_5",
                                "stock",
                                "thumbnail",
                                "title_vrp",
                                "transmission_description",
                                "trim",
                                "type",
                                "vehicle_status",
                                "vin",
                                "year",
                            ]
                        ),
                        "hitsPerPage": 20,
                        "maxValuesPerFacet": 250,
                    }
                ),
            }
        ]
    }

    try:
        response = requests.post(URL, headers=HEADERS, json=request_payload, timeout=30)
        response.raise_for_status()
        result = response.json()

        hits = result["results"][0].get("hits")
        if not hits:
            print("❌ No vehicles found.")
            return "No vehicles available for the selected criteria."

        data = extract_vehicle_chunks_text(hits)
        return data
    except requests.RequestException as e:
        print("❌ Request failed:", e)
        return "No vehicles available"


get_inventory_search_schema = StructuredTool.from_function(
    func=get_inventory_search,
    name="get_inventory_search",
    description="""Use this tool to search the database for available vehicle inventory.

                ➤ Response Behavior:
                
                1. **Before triggering the tool**, always say exactly:  
                   **“Give me a second. Let me check that for you”**  
                   🔒 Do not add anything else. Do not repeat the vehicle name here — trust that context is already established.
                
                2. If 3 or fewer vehicles are returned, provide a very brief summary of each vehicle and highlight the pricing.
                
                3. When more than 3 vehicles are returned:
                   - Summarize up to **three** vehicles using only:
                     - Exterior Color  
                     - Model  
                     - Interior Color  
                
                   ➤ Use natural, descriptive phrasing instead of bullet points.  
                   ➤ Mention the model name **only once per vehicle**. For subsequent references, use phrases like:
                     “this one,” “you’ll get,” or “it features.”
                
                4. Do **not** include full specifications in the initial summary. Only provide detailed information for one specific vehicle **if the customer requests it.**
                
                5. If vehicles are summarized, conclude with:
                   “Choose one of the options you just mentioned in the summary,” and provide full specifications for that specific vehicle.
                
                6. Always maintain a warm, confident, and helpful tone. Avoid robotic or overly scripted responses. Use contractions and natural expressions. Speak as if you’re having a real conversation.
    """,
    args_schema=InventorySearchModel,
    return_direct=True,
)


def extract_vehicle_chunks_text(options: list) -> str:
    if not options:
        return "No vehicles available"

    vehicle_count = len(options)
    if vehicle_count > 3:
        summaries = []
        for vehicle in options[:3]:
            summaries.append(
                f"{vehicle.get('ext_color')} {vehicle.get('year')} {vehicle.get('trim')} with {vehicle.get('int_color')} interior"
            )
        summary_text = "; ".join(summaries)
        return (
            f"We have {vehicle_count} vehicles available. Here is a summary: {summary_text}. "
            "Would you like to see detailed specs? If so please choose one of the ones I mentioned."
        )

    chunks = []

    for vehicle in options:
        try:
            ext_options = [
                BeautifulSoup(option, "html.parser").get_text(" ", strip=True)
                for option in vehicle.get("ext_options", [])
            ]
            int_options = [
                BeautifulSoup(option, "html.parser").get_text(" ", strip=True)
                for option in vehicle.get("int_options", [])
            ]
            price = extract_prices(vehicle.get("lightning")["advancedPricingStack"])

            chunk = f"""Model: {vehicle.get("model")}
                        Trim: {vehicle.get("trim")}
                        Year: {vehicle.get("year")}
                        Miles: {vehicle.get("miles")}
                        Exterior Color: {vehicle.get("ext_color")}
                        Interior Color: {vehicle.get("int_color")}
                        
                        """.strip()

            chunks.append(chunk)
        except Exception as e:
            print(f"Error processing vehicle: {e}")
            continue

    return f"We have {vehicle_count} vehicles available:\n\n" + "\n\n".join(chunks[:10])

# ---------------------------
# Pricing Related Functions
# ---------------------------
class InventoryPriceQueryModel(BaseModel):
    make: str = Field(None, enum=[
            "Audi",
            "BMW",
            "Buick",
            "Chevrolet",
            "Chrysler",
            "Dodge",
            "Ford",
            "GMC",
            "Honda",
            "Hyundai",
            "INFINITI",
            "Jaguar",
            "Jeep",
            "Kia",
            "Lexus",
            "Mercedes-Benz",
            "Nissan",
            "Ram",
            "Tesla",
            "Toyota",
            "Volkswagen",
        ], description="Vehicle make (e.g., Chevrolet, BMW).")
    model: str = Field(None,enum=[
            "1500",
            "3 Series",
            "4 Series",
            "5 Series",
            "7 Series",
            "Altima",
            "Armada",
            "Avalanche",
            "Blazer",
            "C-Class",
            "Camry",
            "Charger",
            "Cherokee",
            "Colorado",
            "Compass",
            "Durango",
            "E-PACE",
            "Encore",
            "Equinox",
            "Expedition",
            "Explorer",
            "F-150",
            "Forte",
            "GLE",
            "GLS",
            "Grand Cherokee",
            "Highlander",
            "K5",
            "Malibu",
            "Model 3",
            "Mustang",
            "NX 200t",
            "Optima",
            "Pilot",
            "Q7",
            "QX50",
            "RAV4",
            "Rogue",
            "Santa Cruz",
            "Sentra",
            "Sienna",
            "Sierra 1500",
            "Silverado 1500",
            "Silverado 2500 HD",
            "Silverado 3500 HD",
            "Sportage",
            "Suburban",
            "Tacoma 4WD",
            "Tahoe",
            "Taos",
            "Telluride",
            "Terrain",
            "Trailblazer",
            "Traverse",
            "Trax",
            "Tundra 4WD",
            "Voyager",
            "Wagoneer L",
            "Wrangler",
            "Wrangler Unlimited",
            "X1",
            "X2",
            "X3",
            "X5",
            "X6",
            "X7",
            "Yukon XL",
            "i4",
            "i7",
        ], description="Vehicle model (e.g., Silverado 1500).")
    trim: str = Field(None,enum=[
            "(RED) Edition",
            "1LT",
            "2.5 S",
            "2.5 SV",
            "2RS",
            "330e",
            "330i",
            "330i xDrive",
            "3LT",
            "430i",
            "530i",
            "530i xDrive",
            "740i",
            "740i xDrive",
            "ACTIV",
            "Altitude Lux",
            "C 300",
            "Custom",
            "Denali",
            "EX",
            "EcoBoost",
            "Elevation",
            "FWD 4dr",
            "GLE 350",
            "GLS 580",
            "GT Plus",
            "GT-Line",
            "High Country",
            "L",
            "LE AAS",
            "LS",
            "LT",
            "LT Trail Boss",
            "LTZ",
            "LUXE",
            "LX",
            "Laramie",
            "Latitude",
            "Limited",
            "M40i",
            "NA",
            "Performance",
            "Platinum",
            "Preferred",
            "Premier",
            "Prestige",
            "RS",
            "RST",
            "S",
            "SE",
            "SLT",
            "SR",
            "SV",
            "SX Prestige X-Pro",
            "SXT",
            "Series II",
            "Special Edition",
            "Sport",
            "Trail Boss",
            "Trailhawk",
            "Unlimited Rubicon",
            "WT",
            "WT/LT",
            "XL",
            "XLE",
            "XLE V6",
            "XLT",
            "Z71",
            "eDrive35",
            "sDrive28i",
            "sDrive30i",
            "sDrive40i",
            "xDrive28i",
            "xDrive40i",
            "xDrive60",
        ], description="Vehicle trim level (e.g., LT, LTZ).")
    min_year: int = Field(
        None,
        enum=[
            2007,
            2011,
            2014,
            2015,
            2016,
            2017,
            2018,
            2019,
            2020,
            2021,
            2022,
            2023,
            2024,
            2025,
            2026,
        ],
        description="Minimum manufacturing year of the vehicle. e.g., 2020, 2021",
    )
    max_year: int = Field(
        None,
        enum=[
            2007,
            2011,
            2014,
            2015,
            2016,
            2017,
            2018,
            2019,
            2020,
            2021,
            2022,
            2023,
            2024,
            2025,
            2026,
        ],
        description="Maximum manufacturing year of the vehicle. e.g., 2020, 2021",
    )
    exterior_color: str = Field(
        None,
        enum=[
            "Alpine White",
            "Bernina Grey Amber Effect",
            "Black",
            "Black Sapphire Metallic",
            "Blk/black",
            "Blu/blue",
            "Blue",
            "Bright Blue Metallic",
            "CAJUN RED TINTCOAT",
            "Cacti Green",
            "Cherry Red Tintcoat",
            "Crimson Metallic",
            "Cypress Gray",
            "Dark Copper Metallic",
            "Dark Graphite Metallic",
            "Donington Gray Metallic",
            "Ebony Twilight Metallic",
            "Fountain Blue",
            "Glacier Silver Metallic",
            "Gld/gold",
            "Graphite Shadow",
            "Gray",
            "Graystone Metallic",
            "Green",
            "Gy/gray",
            "Hydro Blue Pearlcoat",
            "Iridescent Pearl Tricoat",
            "Lakeshore Blue Metallic",
            "Mar/maroon",
            "Midnight Black Metallic",
            "Mineral Gray Metallic",
            "Mineral White Metallic",
            "Mosaic Black Metallic",
            "Nitro Yellow Metallic",
            "Onyx Black",
            "Orange",
            "Pacific Blue Metallic",
            "Pewter Metallic",
            "Radiant Red Tintcoat",
            "Red",
            "Red Hot",
            "Red/red",
            "Satin Steel Metallic",
            "Sil/silver",
            "Silver",
            "Silver Ice Metallic",
            "Skyscraper Grey Metallic",
            "Titanium Rush Metallic",
            "Whi/white",
            "White",
            "White Frost Tricoat",
        ],
        description="Exterior color of the vehicle.",
    )
    interior_color: str = Field(
        None,
        enum=[
            "Artemis Gray, Evotex seat trim",
            "Ash",
            "BLK/Black",
            "Beige",
            "Black",
            "Black with Red Accents, Evotex seat trim",
            "Black, Cloth seat trim",
            "Brown",
            "CUSTOM LEATHER APPOINTED SEAT TRIM",
            "Canberra Beige",
            "Canberra Beige/Black",
            "Cognac",
            "Dark Atmosphere/ Medium Ash Gray, Premium cloth seat trim",
            "Dark Walnut/Slate, Perforated leather-appointed front outboard seat trim",
            "Ebony, Cloth with leatherette seat trim",
            "GRY/Gray",
            "Gideon/Very Dark Atmosphere, Cloth seat trim",
            "Gideon/Very Dark Atmosphere, Leather-Appointed seating surfaces",
            "Gideon/Very Dark Atmosphere, Perforated leather-appointed front outboard seating positions",
            "Gideon/Very Dark Atmosphere, Premium cloth seat trim",
            "Graphite",
            "Gray",
            "Ivory White/Black",
            "Jet Black with Blue accents, Cloth/Evotex seat trim",
            "Jet Black with Red Accents, Perforated Leather-Appointed seat trim",
            "Jet Black with Red Accents, Perforated Leather-Appointed seat trim",
            "Jet Black with Red accents, Evotex seat trim",
            "Jet Black with Yellow accents, Cloth/Evotex seat trim",
            "Jet Black with Yellow stitching, Evotex seat trim",
            "Jet Black, Cloth seat trim",
            "Jet Black, Evotex seat trim",
            "Jet Black, Forge perforated leather seat trim",
            "Jet Black, Leather-Appointed seating surfaces",
            "Jet Black, Perforated Leather-Appointed seat trim",
            "Jet Black, Perforated Leather-Appointed seating",
            "Jet Black, Perforated leather seating surfaces 1st and 2nd row",
            "Jet Black, Leather-appointed front outboard seat trim",
            "Jet Black, Leather-appointed front outboard seating positions",
            "Jet Black/Dark Ash, Cloth seat trim",
            "Jet Black/Medium Ash Gray, Cloth seat trim",
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
            "Medium Ash Gray, Premium Cloth seat trim",
            "NNB/BLACK",
            "RA00/Charcoal",
            "RS Jet Black with Torch Red accents, Perforated Leather-appointed seat trim",
            "TAN/Tan",
        ],
        description="Interior color of the vehicle. (e.g. Black, Gray, Jet Black, Perforated leather-appointed front outboard seating positions).",
    )

@tool
def get_vehicle_prices(
    make: Optional[str] = None,
    model: Optional[str] = None,
    trim: Optional[str] = None,
    min_year: Optional[int] = None,
    max_year: Optional[int] = None,
    exterior_color: Optional[str] = None,
    interior_color: Optional[str] = None,
    enable_fields: bool = False,  # Not used
    context_limit: int = None,  # Not used
):
    """Use this tool when the customer **asks about the price or MSRP of a specific vehicle**.

    ➤ Response Behavior:

    1. **Before triggering the tool**, always say exactly:
       **“Give me a second...”**
       🔒 Do not add anything else. Do not mention the vehicle name again here. Keep it short and consistent.

    2. Filter based on make, model, trim, year, or color to find a close match.

    3. For each matching vehicle (up to 10):
       - Always include the **MSRP** (original price).
       - Clearly show the **final sale price** after applying all available discounts (e.g., dealer discount, customer cash).
       - Example:
         “MSRP: $47,000 → Final Price: $43,500. You're saving big on this one!”

    4. Format each result like:
       “1. Black — LT — MSRP: $47,000 → Final Price: $43,500”

    5. Use energetic, friendly, and natural phrasing to highlight value and savings:
       - Say things like:
         “You’re saving big on this one,”
         “This deal won’t last long!”
       - Avoid robotic tone and don’t repeat the vehicle name unnecessarily.

    6. If no vehicles are found:
       - Say: “No vehicles found matching your pricing request.”

    7. Wrap up with a helpful line:
       “Want me to find you similar options or check what other trims are available?”
        """

    def build_facet_filter(key: str, value: str | int) -> List[str]:
        if isinstance(value, list):
            return [f"{key}:{v}" for v in value]
        return [f"{key}:{value}"]

    params = locals()
    facet_filters = []

    mapping = {
        "make": "make",
        "model": "model",
        "trim": "trim",
        "exterior_color": "ext_color",
        "interior_color": "int_color",
    }

    for key, facet in mapping.items():
        val = params.get(key)
        if val is not None:
            facet_filters.append(build_facet_filter(facet, val))

    year_min = params.get("min_year")
    year_max = params.get("max_year")

    if year_min and year_max:
        year_range = list(range(year_min, year_max + 1))
        facet_filters.append(build_facet_filter("year", year_range))
    elif year_min:
        facet_filters.append(build_facet_filter("year", year_min))
    elif year_max:
        facet_filters.append(build_facet_filter("year", year_max))


    request_payload = {
        "requests": [
            {
                "indexName": "capitolchevroletal_production_inventory_custom_sort",
                "params": urlencode({
                    "facetFilters": json.dumps(facet_filters),
                    "hitsPerPage": 5,
                }),
            }
        ]
    }

    try:
        response = requests.post(URL, headers=HEADERS, json=request_payload, timeout=30)
        response.raise_for_status()
        hits = response.json()["results"][0].get("hits")

        if not hits:
            return "No vehicles found matching your criteria."

        vehicle = hits[0]
        price_data = extract_prices(vehicle.get("lightning", {}).get("advancedPricingStack", []))
        price_text = format_vehicle_price(price_data) if price_data else f"Price: ${vehicle.get('our_price', 'Not available')}"

        return extract_vehicle_prices_text(hits)

    except requests.RequestException as e:
        print("❌ Request failed:", e)
        return "Couldn't retrieve pricing at the moment."

get_vehicle_prices_schema = StructuredTool.from_function(
    func=get_vehicle_prices,
    name="get_vehicle_prices",
    description="""Use this tool when the customer **asks about the price or MSRP of a specific vehicle**.
                
                ➤ Response Behavior:
                
                1. **Before triggering the tool**, always say exactly:  
                   **“Give me a second...”**  
                   🔒 Do not add anything else. **Do NOT repeat the vehicle name** here. Keep it short and consistent.
                
                2. Filter based on make, model, trim, year, or color to find a close match.
                
                3. **Important Model Name Rule**:  
                   - Once this tool is used, assume the model is now established in the conversation.  
                   - **Do NOT repeat the vehicle model name** when presenting prices or in any follow-up answers.  
                   - Use natural phrasing like:  
                     – “It starts around...”  
                     – “This one has...”  
                     – “You’ll get...”  
                
                4. For each matching vehicle (up to 10):  
                   - Do NOT mention the model name again in each result.  
                   - Always include the **MSRP** (original price).  
                   - Clearly show the **final sale price** after all applicable discounts (e.g., dealer discount, customer cash).  
                   - Example:  
                     **“MSRP: $47,000 → Final Price: $43,500. You’re saving big on this one!”**
                
                5. Format each result like:  
                   **“1. Black — LT — MSRP: $47,000 → Final Price: $43,500”**
                
                6. Use energetic, conversational phrasing to emphasize value:  
                   – “You’re saving big on this one.”  
                   – “This deal won’t last long!”  
                   – “Incredible value for the features it offers.”  
                   🔕 Avoid robotic tone or repeating the vehicle name.
                
                7. If no vehicles are found:  
                   **Say:** “No vehicles found matching your pricing request.”
                """,
    args_schema=InventoryPriceQueryModel,
    return_direct=True,
)

def extract_vehicle_prices_text(vehicles: list) -> str:
    if not vehicles:
        return "No vehicles found matching your pricing request."

    limited_vehicles = vehicles[:3]
    count = len(limited_vehicles)
    multiple_vehicle_text = 'with the number of vehicles available \'Here are a few of the available options.\''
    one_vehicle_text = 'The following is the price for the vehicle you requested.'

    summaries = [f"Read exactly the following {one_vehicle_text if count == 1 else multiple_vehicle_text} It is essential to mention any available discounts, if applicable.\n\n There are {count} vehicle(s) available:"]
    discounts = False

    for i, vehicle in enumerate(limited_vehicles, start=1):
        try:
            price_data = extract_prices(vehicle.get("lightning", {}).get("advancedPricingStack", []))
            formatted_price = format_vehicle_price(price_data) if price_data else f"${vehicle.get('our_price', 'N/A')}"

            discounts = True if formatted_price.startswith("MSRP:") else False
            summaries.append(f"{i}. {formatted_price}")
        except Exception as e:
            print(f"Error processing vehicle pricing: {e}")
            continue

    if discounts:
        summaries.append("These vehicles come with dealer and customer cash discounts, and you may be eligible for additional incentives. Would you like me to connect you with a sales expert to discuss this further?")
    else:
        summaries.append("While this vehicle doesn’t currently show any listed discounts, you might still be eligible for exclusive incentives and rebates. Would you like me to connect you with a sales expert to explore your options?")
    return "\n".join(summaries)



# ---------------------------
# Exported Tools
# ---------------------------

TOOLS = [
    book_appointment,
    get_inventory_search,
    get_appointment_details,
    capture_contact_details,
    get_vehicle_prices,
]
TOOLS_SCHEMA = [
    convert_to_function(book_appointment_schema),
    convert_to_function(get_inventory_search_schema),
    convert_to_function(get_appointment_details_schema),
    convert_to_function(capture_contact_details_schema),
    convert_to_function(get_vehicle_prices_schema),
]
