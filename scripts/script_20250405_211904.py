# File name to read
file_name = "cloud_essay.txt"

try:
    # Open and read the file
    with open(file_name, "r") as file:
        content = file.read()
        print("The content of the file is as follows:\n")
        print(content)
except FileNotFoundError:
    print(f"The file '{file_name}' does not exist. Please ensure it has been created.")
except Exception as e:
    print(f"An error occurred: {e}")