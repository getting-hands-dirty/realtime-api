import inspect
from functools import wraps

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


def convert_to_function(input_obj):
    # Extract necessary fields from the input object
    description = input_obj.get("description", "")
    title = input_obj.get("title", "")
    properties = input_obj.get("properties", {})

    # Build the output properties
    output_properties = {}
    for key, value in properties.items():
        output_properties[key] = {
            "type": value.get("type", ""),
            "description": parameter_descriptions.get(key, ""),
        }
        # Add enum if default is provided
        if "default" in value:
            current_value = value["default"]
            if current_value is not None:
                output_properties[key]["enum"] = value["default"]

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
