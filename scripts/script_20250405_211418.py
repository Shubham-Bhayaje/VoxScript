import time
from plyer import notification

# Calculate time for tomorrow (24 hours from now)
seconds_in_a_day = 24 * 60 * 60

# Wait until tomorrow
time.sleep(seconds_in_a_day)

# Send a notification
notification.notify(
    title="Reminder",
    message="Finish work!",
    timeout=10  # Notification duration in seconds
)