from services.middlewares.TimingMiddleware import TimingMiddleware
from services.middlewares.RequestLogginMiddleware import RequestLogginMiddleware
from fastapi import FastAPI

from Logic.Scrapers.VideoDownloader import VideoDownloader
from Logic.Scrapers.OpenFingScraper import OpenFingScraper
import asyncio 
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(TimingMiddleware)
app.add_middleware(RequestLogginMiddleware)
openfing_scraper = OpenFingScraper()
videoDownloader = VideoDownloader()

class DownloadVideosRequest(BaseModel):
    course_acronym: str
    class_number: int

@app.get("/courses-acronyms")
async def get_acronyms():
    c= openfing_scraper.get_acronyms()
    return {"message": c}

@app.put("/courses-acronyms")
async def get():
    return {"status": openfing_scraper.update_acronyms()}

@app.get("/courses-acronyms/{course_acronym}")
async def get_classes(course_acronym: str):
    return {"status": openfing_scraper.get_classes(course_acronym)}

@app.put("/courses-acronyms/{course_acronym}")
async def update_course(course_acronym: str):
    c=openfing_scraper.update_course(course_acronym)
    return {"status": c}

@app.post("/download-videos/")
async def downloadVideos(request: DownloadVideosRequest):
    p= videoDownloader.process_video(request.course_acronym,request.class_number)
    return p

