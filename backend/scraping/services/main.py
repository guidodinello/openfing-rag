# main.py
from fastapi import FastAPI
from Logic.Scrapers.OpenFingScraper import OpenFingScraper
import asyncio 

app = FastAPI()
openfing_scraper = OpenFingScraper()
   
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

@app.get("/openfing-scraper/")
async def scrapeCourse():
    return {"status": openfing_scraper.scrape_openfing()}

@app.get("/download-videos/{course_acronym}/{class_number}")
async def downloadVideos(course_acronym: str, class_number: int):
    # asyncio.run(openfing_scraper.download_videos(course_acronym, class_number))
    return {"message": "Downloading started"}

