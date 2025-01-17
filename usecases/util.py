import inspect
from functools import wraps

parameter_descriptions = {
    "vin": "Vehicle Identification Number.",
    "stock_number": "Stock number of the vehicle.",
    "vehicle_type": "Type of the vehicle (e.g., SUV, Sedan).",
    "year": "Manufacturing year of the vehicle.",
    "make": "Vehicle manufacturer (e.g., Toyota).",
    "model": "Vehicle model (e.g., Corolla).",
    "trim": "Vehicle trim level.",
    "style": "Vehicle body style.",
    "exterior_color": "Exterior color of the vehicle.",
    "interior_color": "Interior color of the vehicle.",
    "certified": "Whether the vehicle is certified pre-owned.",
    "min_price": "Minimum price range for the vehicle.",
    "max_price": "Maximum price range for the vehicle.",
    "fuel_type": "Type of fuel used by the vehicle.",
    "transmission": "Transmission type (e.g., Automatic, Manual).",
    "drive_type": "Drive type (e.g., AWD, FWD, RWD).",
    "doors": "Number of doors.",
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
                        "type": "string" if annotation == str else "unknown",
                        "description": parameter_descriptions.get(name, ""),
                    }
                    for name, annotation in func.__annotations__.items()
                },
                "required": required_args,
            },
        }

    wrapper_func.get_schema = get_schema
    return wrapper_func
