# main.py
import asyncio
from fastapi import FastAPI

app = FastAPI()

@app.get("/transcribe/{course_acronym}/{class_number}")
async def root():
    OpenFingScraper().main()
    return {"message": "Started scraping"}

@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}

