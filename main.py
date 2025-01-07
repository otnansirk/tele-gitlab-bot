from fastapi import FastAPI, APIRouter, Request, HTTPException
from services import gitlab_handler
from fastapi.responses import JSONResponse
from services import telegram_handler
from services import meet_hanlder
from services import calendar_handler
from services import helper
from dotenv import load_dotenv


app = FastAPI()
api_route = APIRouter(prefix="/api")

load_dotenv()

@app.get("/")
async def root():
    return "Service running"

@app.get("/set-webhook")
async def set_webhook():
    return await telegram_handler.set_webhook()

@api_route.get("/dev-daily-meeting")
async def dev_daily_meeting(request: Request):
    try:
        mentioned_member = request.query_params.get("mention")
        await meet_hanlder.generate(meeting_name="mrp-dev-daily-meeting", title="MRP DEV Daily Meeting", message=mentioned_member)
        return helper.res_success()
    except Exception as e:
        print(e, "ERROR /dev-daily-meeting")
        return helper.res_error()

@api_route.get("/montly-holiday")
async def monthly_holiday():
    try:
        return await telegram_handler.monthly_holiday()
        return helper.res_success()
    except Exception as e:
        print(e, "ERROR /holiday")
        return helper.res_error()

@api_route.post("/callbacks/gitlab")
async def handle_webhook_gitlab(request: Request):
    try:
        data = await request.json()
        print("Request Gitlab : ", data)
        await gitlab_handler.updater(data)
        return helper.res_success(data)
    except Exception as e:
        print(e, "ERROR /callbacks/gitlab")
        return helper.res_error()

@api_route.post("/callbacks/telegram")
async def handle_webhook_telegram(request: Request):
    try:
        data = await request.json()
        print("Request Telegram : ", data)
        await telegram_handler.updater(data)
        return helper.res_success()
    except Exception as e:
        print(e, "ERROR /callbacks/telegram")
        return helper.res_error()


app.include_router(api_route)