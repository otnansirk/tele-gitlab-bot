from fastapi import FastAPI, APIRouter, Request, HTTPException
from services import gitlab_handler
from fastapi.responses import JSONResponse
from services import telegram_handler
from services import meet_hanlder
from services import calendar_handler
from services import helper
from dotenv import load_dotenv


app = FastAPI()
callback_route = APIRouter(prefix="/api")

load_dotenv()

@app.get("/")
async def root():
    await telegram_handler.set_webhook()
    return "Service running"

@callback_route.get("/dev-daily-meeting")
async def dev_daily_meeting(request: Request):
    try:
        mentioned_member = request.query_params.get("mention")
        await meet_hanlder.generate(meeting_name="mrp-dev-daily-meeting", title="MRP DEV Daily Meeting", message=mentioned_member)
        return helper.res_success()
    except Exception as e:
        print(e, "ERROR /dev-daily-meeting")
        return helper.res_error()

@callback_route.get("/holiday")
async def holiday(request: Request):
    try:
        return calendar_handler.get_holiday()
    except Exception as e:
        print(e, "ERROR /dev-daily-meeting")
        return helper.res_error()

@callback_route.post("/callbacks/gitlab")
async def handle_webhook_gitlab(request: Request):
    try:
        data = await request.json()
        print("Request Gitlab : ", data)
        await gitlab_handler.updater(data)
        return helper.res_success(data)
    except Exception as e:
        print(e, "ERROR /callbacks/gitlab")
        return helper.res_error()

@callback_route.post("/callbacks/telegram")
async def handle_webhook_telegram(request: Request):
    try:
        data = await request.json()
        print("Request Telegram : ", data)
        await telegram_handler.updater(data)
        return helper.res_success()
    except Exception as e:
        print(e, "ERROR /callbacks/telegram")
        return helper.res_error()


app.include_router(callback_route)