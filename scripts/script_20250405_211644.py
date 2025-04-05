# Create a file named 'task.txt' in the current directory
file_name = "task.txt"

try:
    with open(file_name, "w") as file:
        file.write("This is your new task file.\n")
        print(f"File '{file_name}' has been created successfully in the current directory.")
except Exception as e:
    print(f"An error occurred: {e}")