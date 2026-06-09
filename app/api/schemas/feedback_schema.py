from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    session_id: str
    question: str
    answer: str
    rating: int = Field(ge=1, le=5)
    comment: str = ""


class FeedbackResponse(BaseModel):
    status: str

