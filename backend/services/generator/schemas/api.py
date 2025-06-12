from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="The user's message to the chatbot",
    )
    lesson_id: None | int = Field(
        None,
        description="Optional lesson ID to filter results",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Can you explain recursion from the Data Structures course?",
            },
        }


# TODO: improve this response schema. see https://claude.ai/share/39d65386-d35f-4012-9603-e3f9065ead3b
class ChatResponse(BaseModel):
    response: str = Field(..., description="The chatbot's response")
    sources: list[str] = Field(
        default_factory=list,
        description="Source references for the response",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "response": """Recursion is a programming concept where a
                function calls itself...""",
                "sources": ["Data Structures - Lecture 5 (00:15:30)"],
                # TODO: update sources format
            },
        }
