from fastapi import FastAPI, APIRouter, Request
from services.callback_gitlab import callback_gitlab
from dotenv import load_dotenv


app = FastAPI()
callback_route = APIRouter(prefix="/api/callbacks")

load_dotenv()

@callback_route.post("/")
async def root(request: dict):
    return callback_gitlab(request)

app.include_router(callback_route)