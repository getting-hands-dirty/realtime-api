import inspect
from functools import wraps

from bs4 import BeautifulSoup

parameter_descriptions = {
    "vin": "Vehicle Identification Number.",
    "stock_number": "Stock number of the vehicle.",
    "vehicle_type": "Type of the vehicle (e.g., SUV, Sedan).",
    "year": "Manufacturing year of the vehicle. (int)",
    "make": "Vehicle manufacturer (e.g., Toyota).",
    "model": "Vehicle model (e.g., Corolla).",
    "trim": "Vehicle trim level.",
    "style": "Vehicle body style.",
    "exterior_color": "Exterior color of the vehicle.",
    "interior_color": "Interior color of the vehicle.",
    "certified": "Whether the vehicle is certified pre-owned. (true/false)",
    "min_price": "Minimum price range for the vehicle.",
    "max_price": "Maximum price range for the vehicle.",
    "fuel_type": "Type of fuel used by the vehicle.",
    "transmission": "Transmission type (e.g., Automatic, Manual).",
    "drive_type": "Drive type (e.g., AWD, FWD, RWD).",
    "doors": "Number of doors. (int)",
    "description": "Description of the vehicle any generic information.",
}


def tool(func):
    @wraps(func)  # Preserve the original function's metadata
    def wrapper_func(*args, **kwargs):
        return func(*args, **kwargs)

    # Attach the get_schema function as an attribute of wrapper_func.
    def get_schema():
        # Inspect the function signature
        sig = inspect.signature(func)

        # Extract required and optional arguments
        required_args = [
            param.name
            for param in sig.parameters.values()
            if param.default is param.empty
            and param.kind in (param.POSITIONAL_OR_KEYWORD, param.KEYWORD_ONLY)
        ]
        optional_args = [
            param.name
            for param in sig.parameters.values()
            if param.default is not param.empty
        ]

        # Build the schema
        return {
            "type": "function",
            "name": func.__name__,
            "description": func.__doc__.strip() if func.__doc__ else "",
            "parameters": {
                "type": "object",
                "properties": {
                    name: {
                        "type": "string",
                        "description": parameter_descriptions.get(name, ""),
                    }
                    for name, annotation in func.__annotations__.items()
                },
                "required": required_args,
            },
        }

    wrapper_func.get_schema = get_schema
    return wrapper_func


def convert_to_function(schema):
    # Extract necessary fields from the input object
    input_obj = schema.args_schema.model_json_schema()
    title = schema.name
    description = schema.description
    properties = input_obj.get("properties", {})

    # Build the output properties
    output_properties = {}
    for key, value in properties.items():
        output_properties[key] = {
            "type": value.get("type", ""),
            "description": value.get("description", ""),
        }
        # Add enum if default is provided
        if "enum" in value:
            current_value = value["enum"]
            if current_value is not None:
                output_properties[key]["enum"] = current_value

    # Create the output structure
    output = {
        "type": "function",
        "name": title,  # Fixed name as per output example
        "description": description,
        "parameters": {
            "type": "object",
            "properties": output_properties,
            "required": list(properties.keys()),  # All properties are required
        },
    }

    return output


def extract_prices(html):
    soup = BeautifulSoup(html, "html.parser")
    price_data = {}

    for block in soup.select("div.price-block"):
        label = block.select_one("span.price-label")
        price = block.select_one("span.price")

        if label and price:
            label_text = label.get_text(strip=True).replace("*", "")
            price_text = price.get_text(strip=True).replace("$", "").replace(",", "")
            price_data[label_text] = float(price_text)

    return {
        "msrp": price_data.get("MSRP"),
        "dealer_discount": price_data.get("Dealer Discount"),
        "customer_cash": price_data.get("Customer Cash"),
        "total_savings": price_data.get("Total Savings"),
        "final_price": price_data.get("Final Price"),
    }


def format_vehicle_price(price_data: dict) -> str:
    if all(v is None for v in price_data.values()):
        return ""

    if price_data["msrp"] and all(
        price_data.get(k) is None
        for k in ["dealer_discount", "customer_cash", "total_savings", "final_price"]
    ):
        return f"Our Price: ${price_data['msrp']:,.2f}"

    # MSRP + Discounts
    discount_keys = []
    if price_data["dealer_discount"]:
        discount_keys.append("Dealer Discount")
    if price_data["customer_cash"]:
        discount_keys.append("Customer Cash")
    if price_data["total_savings"]:
        discount_keys.append("Total Savings")

    msg = f"MSRP: ${price_data['msrp']:,.2f}. After applying {' and '.join(discount_keys)}, the final price is ${price_data['final_price']:,.2f}."
    return msg