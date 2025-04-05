import datetime
import holidays

# Get today's date
today = datetime.date.today()

# Get a list of holidays in your country (e.g., United States)
us_holidays = holidays.UnitedStates()

# Check if today is a holiday
if today in us_holidays:
    print(f"Today ({today}) is a holiday: {us_holidays[today]}!")
else:
    print(f"Today ({today}) is not a holiday.")