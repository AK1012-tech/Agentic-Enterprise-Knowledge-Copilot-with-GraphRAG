from fastapi import APIRouter

from app.api.schemas.feedback_schema import FeedbackRequest, FeedbackResponse
from app.database.repository import DemoRepository

router = APIRouter(tags=["feedback"])


@router.post("/feedback", response_model=FeedbackResponse)
def feedback(request: FeedbackRequest) -> FeedbackResponse:
    DemoRepository.instance().save_feedback(request.model_dump())
    return FeedbackResponse(status="recorded")

