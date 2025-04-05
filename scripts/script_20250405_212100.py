import tkinter as tk

# Function to move the car
def move_car():
    global car_x
    car_x += 5  # Increment the car's position
    canvas.coords(car, car_x, car_y, car_x + car_width, car_y + car_height)  # Update car position
    
    # Loop the car movement when it reaches the edge
    if car_x > window_width:
        car_x = -car_width  # Reset position to start from the left
    
    root.after(50, move_car)  # Call this function again after 50 ms

# Create the main window
root = tk.Tk()
root.title("Moving Car GUI")

# Window dimensions
window_width = 800
window_height = 400
root.geometry(f"{window_width}x{window_height}")

# Create a canvas widget
canvas = tk.Canvas(root, width=window_width, height=window_height, bg="lightblue")
canvas.pack()

# Car dimensions and initial position
car_width = 100
car_height = 50
car_x = 50  # Initial x-coordinate
car_y = window_height - car_height - 50  # Position near the bottom

# Create the car (a rectangle)
car = canvas.create_rectangle(car_x, car_y, car_x + car_width, car_y + car_height, fill="red")

# Add wheels (circles)
wheel_radius = 10
canvas.create_oval(car_x + 10, car_y + car_height, car_x + 30, car_y + car_height + 2 * wheel_radius, fill="black")
canvas.create_oval(car_x + car_width - 30, car_y + car_height, car_x + car_width - 10, car_y + car_height + 2 * wheel_radius, fill="black")

# Start moving the car
move_car()

# Run the GUI event loop
root.mainloop()