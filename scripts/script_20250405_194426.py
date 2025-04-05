import datetime

# Define a dictionary of special dates
special_days = {
    "01-01": "New Year's Day",
    "02-14": "Valentine's Day",
    "07-04": "Independence Day",
    "12-25": "Christmas Day",
    # Add more special dates here
}

# Get today's date
today = datetime.date.today()

# Format today's date as MM-DD
today_str = today.strftime("%m-%d")

# Check if today is a special day
if today_str in special_days:
    print(f"Today ({today}) is special because it's {special_days[today_str]}!")
else:
    print(f"Today ({today}) is not a special day.")