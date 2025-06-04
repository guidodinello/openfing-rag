from pydantic import BaseModel


class TranscriptionResponse(BaseModel):
    message: str


class TranscriptionUpdateRequest(BaseModel):
    model_size: str = "base"
    language: str = "es"
