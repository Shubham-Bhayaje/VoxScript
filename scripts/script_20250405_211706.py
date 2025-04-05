import os

# File name to delete
file_name = "task.txt"

try:
    # Check if the file exists
    if os.path.exists(file_name):
        # Delete the file
        os.remove(file_name)
        print(f"File '{file_name}' has been deleted successfully.")
    else:
        print(f"File '{file_name}' does not exist.")
except Exception as e:
    print(f"An error occurred: {e}")