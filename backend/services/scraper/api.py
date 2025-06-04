from fastapi import FastAPI
from pydantic import BaseModel

from downloader.core.downloader import download_course_videos
from scraper.scrapers.openfing_scraper import OpenFingScraper
from shared.middleware.logging import RequestLogginMiddleware
from shared.middleware.timing import TimingMiddleware

app = FastAPI()
app.add_middleware(TimingMiddleware)
app.add_middleware(RequestLogginMiddleware)
openfing_scraper = OpenFingScraper()


class DownloadVideosRequest(BaseModel):
    course_acronym: str
    class_number: int


@app.get("/courses-acronyms")
async def get_acronyms():
    c = openfing_scraper.get_acronyms()
    return {"message": c}


@app.put("/courses-acronyms")
async def get():
    return {"status": openfing_scraper.update_acronyms()}


@app.get("/courses-acronyms/{course_acronym}")
async def get_course_classes(course_acronym: str):
    return {"status": openfing_scraper.get_classes(course_acronym)}


@app.put("/courses-acronyms/{course_acronym}")
async def update_course(course_acronym: str):
    c = openfing_scraper.update_course(course_acronym)
    return {"status": c}


@app.post("/download-video/")
async def download_video(request: DownloadVideosRequest):
    p = download_course_videos(
        course_id=request.course_acronym,
        start_class=request.class_number,
        end_class=request.class_number,
    )
    return p
