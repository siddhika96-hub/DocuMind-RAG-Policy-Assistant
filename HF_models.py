import requests
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv("HF_TOKEN")

response = requests.get(
    "https://router.huggingface.co/v1/models",
    headers={"Authorization": f"Bearer {token}"}
)

data = response.json()
for model in data.get("data", [])[:20]:
    print(model["id"])