import inspect


def tool(func):

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
                    name: {"type": "string" if annotation == str else "unknown"}
                    for name, annotation in func.__annotations__.items()
                },
                "required": required_args,
            },
        }

    wrapper_func.get_schema = get_schema
    return wrapper_func
