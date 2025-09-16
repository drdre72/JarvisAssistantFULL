# main.py

from utils.helper import format_data, validate_input
from libs.custom_lib import CustomClass

def main():
    # Example input data
    input_data = "Sample input"
    
    # Validate the input
    if validate_input(input_data):
        # Format the data
        formatted_data = format_data(input_data)
        
        # Create an instance of CustomClass and perform an action
        custom_instance = CustomClass()
        result = custom_instance.perform_action(formatted_data)
        
        print("Result:", result)
    else:
        print("Invalid input.")

if __name__ == "__main__":
    main()