import os
import requests
import datetime

def get_holiday ():
    tomorrow = datetime.datetime.now()+datetime.timedelta(days=1, hours=3)
    next_day = tomorrow+datetime.timedelta(days=1, hours=3)
    params = {
        "key": os.getenv("HOLIDAY_KEY"),
        "timeMin": tomorrow.strftime("%Y-%m-%d")+"T00:00:00+07:00",
        "timeMax": next_day.strftime("%Y-%m-%d")+"T00:00:00+07:00"
    }

    res = requests.get(
        os.getenv("HOLIDAY_URL"),
        params=params
    )
    data = res.json()

    holidays = []
    for holiday in data.get("items"):
        if holiday.get("start", {}).get("date") == tomorrow.strftime("%Y-%m-%d"):
            holidays.append(holiday.get("summary"))

    return holidays