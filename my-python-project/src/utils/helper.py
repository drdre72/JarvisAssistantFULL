def format_data(data):
    # Format the input data as needed
    return str(data).strip()

def validate_input(input_data):
    # Validate the input data
    if not isinstance(input_data, (str, int, float)):
        raise ValueError("Input must be a string, integer, or float.")
    return True