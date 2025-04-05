import datetime
import holidays

# Get today's date
today = datetime.date.today()

# Specify the country for holidays (e.g., "US" for the United States)
us_holidays = holidays.US()

# Check if today is a holiday
if today in us_holidays:
    print(f"Today is a holiday: {us_holidays[today]}")
else:
    print("Today is not a holiday in the US.")

# Additional idea: Fetch historical events or fun facts using an API
# You could use an API like Wikipedia or a history-related API for more facts about today.