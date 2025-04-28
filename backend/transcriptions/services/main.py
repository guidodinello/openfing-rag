from Logic.Procesor import Procesor
from fastapi import FastAPI, Response, status, HTTPException
from typing import Optional

app = FastAPI()
procesor = Procesor()

@app.get("/transcribe/{course_acronym}/{class_number}?model_size={model_size}", status_code=status.HTTP_200_OK)
async def get_transcription(
    course_acronym: str,
    class_number: int,
    model_size: Optional[str] = None
):    
    isSuccesful, message = procesor.get_transcription(course_acronym, class_number,model_size)
    if not isSuccesful:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
    return {"message": message}

@app.put("/transcribe/{course_acronym}/{class_number}", status_code=status.HTTP_200_OK)
async def update_transcription(
    course_acronym: str,
    class_number: int,
    model_size: Optional[str] = "base",
    language: Optional[str] = "es"
):
    isSuccesful, message = procesor.update_transcription(course_acronym, class_number, model_size, language)
    if not isSuccesful:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    return {"message": "Started scraping"}