# main.py
from fastapi import FastAPI

from Logic.Scrapers.VideoDownloader import VideoDownloader
from Logic.Scrapers.OpenFingScraper import OpenFingScraper
import asyncio 
from pydantic import BaseModel

app = FastAPI()
openfing_scraper = OpenFingScraper()
videoDownloader = VideoDownloader();   

class CourseAcronymRequest(BaseModel):
    # Define fields if needed
    pass

class OpenFingScraperRequest(BaseModel):
    # Define fields if needed
    pass

class DownloadVideosRequest(BaseModel):
    course_acronym: str
    class_number: int

@app.get("/courses-acronyms")
def scrapePage():
    openfing_scraper.course_list_scraper.acronym_scraper()
    return {"message": "Scraping started"}

@app.get("/status")
async def getStatus():
    return {"status": openfing_scraper.get_status()}

@app.get("/{course_acronym}")
async def scrapeCourse(course_acronym: str):
    return {"status": openfing_scraper.scrape_course(course_acronym)}

@app.post("/courses-acronyms")
async def scrapePage(request: CourseAcronymRequest):
    openfing_scraper.course_list_scraper.acronym_scraper()
    return {"message": "Scraping started"}

@app.post("/openfing-scraper/")
async def scrapeCourse(request: OpenFingScraperRequest):
    return {"status": openfing_scraper.scrape_openfing()}

@app.get("/openfing-scraper/do-scrape")
async def scrapeCourse():
    return {"status": openfing_scraper.do_scrape_openfing()}

@app.post("/download-videos/")
async def downloadVideos(request: DownloadVideosRequest):
    videoDownloader.procces_video(request.course_acronym, request.class_number)
    return {"status": "Download Finished"}

