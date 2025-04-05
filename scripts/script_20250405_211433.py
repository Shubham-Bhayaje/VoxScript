import subprocess
import time
from plyer import notification

# Step 1: Install plyer programmatically if not already installed
try:
    import plyer
except ImportError:
    subprocess.check_call(["pip", "install", "plyer"])

# Step 2: Schedule the reminder for tomorrow
def remind_tomorrow():
    # Calculate the time for tomorrow (24 hours from now)
    seconds_in_a_day = 24 * 60 * 60
    
    # Wait for 24 hours
    time.sleep(seconds_in_a_day)
    
    # Show the reminder notification
    notification.notify(
        title="Reminder",
        message="Finish work!",
        timeout=10  # Notification will last for 10 seconds
    )

# Run the function to remind tomorrow
remind_tomorrow()