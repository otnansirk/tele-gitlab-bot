from fastapi import FastAPI, APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from services.callback_gitlab import callback_gitlab
from dotenv import load_dotenv

from services import telegram_handler


app = FastAPI()
callback_route = APIRouter(prefix="/api/callbacks")

load_dotenv()

@app.on_event("startup")
async def startup_event():
    """Set Telegram bot webhook."""
    await telegram_handler.set_webhook()

@callback_route.post("/")
async def handle_webhook_gitlab(request: Request):
    try:
        data = await request.json()
        return callback_gitlab(data)
    except Exception as e:
        print(e)
        return JSONResponse(
            status_code=400, 
            content={
                "data": {},
                "meta": {
                    "code": "error",
                    "message": "Error"
                }
            }
        )

@callback_route.post("/telegram")
async def handle_webhook_telegram(request: Request):
    try:
        data = await request.json()
        await telegram_handler.updater(data)
    except Exception as e:
        print(e)
        return JSONResponse(
            status_code=400, 
            content={
                "data": {},
                "meta": {
                    "code": "error",
                    "message": "Error"
                }
            }
        )


app.include_router(callback_route)