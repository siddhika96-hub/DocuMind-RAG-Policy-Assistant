from fastapi import Header, HTTPException
from dotenv import load_dotenv
import os

load_dotenv()
API_SECRET_KEY = os.getenv("API_SECRET_KEY")


def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")