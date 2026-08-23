from fastapi import FastAPI
from app.routers import documents, chat

app = FastAPI(title="Intelligent Policy & Knowledge Assistant")

app.include_router(documents.router)
app.include_router(chat.router)


@app.get("/")
def root():
    return {"status": "running"}