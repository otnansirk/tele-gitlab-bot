import os
import requests
import datetime
from calendar import monthrange

def get_holiday(start_date: str, end_date: str):
    params = {
        "key": os.getenv("HOLIDAY_KEY"),
        "timeMin": start_date+"T00:00:00+07:00",
        "timeMax": end_date+"T00:00:00+07:00"
    }
    res = requests.get(
        os.getenv("HOLIDAY_URL"),
        params=params
    )
    data = res.json()

    holidays = []
    for holiday in data.get("items"):
        holidays.append({
            "date": {
                "start": holiday.get("start", {}).get("date"),
                "end"  : holiday.get("end", {}).get("date"),
            },
            "title": holiday.get("summary")
        })

    return holidays

def monthly_holiday():

    # Get the current date
    now = datetime.datetime.now()
    # Get the first day of the current month
    start_of_month = now.replace(day=1)
    # Get the last day of the current month
    last_day = monthrange(now.year, now.month)[1]
    end_of_month = now.replace(day=last_day)
    # Format the output
    start_date = start_of_month.strftime("%Y-%m-%d")
    end_date = end_of_month.strftime("%Y-%m-%d")

    return get_holiday(start_date, end_date)

def holiday_in_30_days():
    tomorrow   = datetime.datetime.now()+datetime.timedelta(days=1, hours=3)
    next_day   = tomorrow+datetime.timedelta(days=30, hours=3)
    start_date = tomorrow.strftime("%Y-%m-%d")
    end_date   = next_day.strftime("%Y-%m-%d")

    return get_holiday(start_date, end_date)