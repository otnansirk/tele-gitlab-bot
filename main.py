from fastapi import FastAPI, APIRouter, Request, HTTPException
from services import gitlab_handler
from fastapi.responses import JSONResponse
from services import telegram_handler
from dotenv import load_dotenv


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
        return gitlab_handler.updater(data)
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