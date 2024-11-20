from fastapi import FastAPI, APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from services.callback_gitlab import callback_gitlab
from dotenv import load_dotenv


app = FastAPI()
callback_route = APIRouter(prefix="/api/callbacks")

load_dotenv()

@callback_route.post("/")
async def root(request: dict):
    try:
        return callback_gitlab(request)
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