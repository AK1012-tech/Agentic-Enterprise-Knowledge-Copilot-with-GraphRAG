from fastapi import APIRouter

from app.api.schemas.chat_schema import ChatRequest, ChatResponse
from app.workflows.agentic_workflow import AgenticGraphRagWorkflow
from app.utils.config import get_settings

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    workflow = AgenticGraphRagWorkflow(settings=get_settings())
    result = workflow.answer(request)
    return ChatResponse(**result)

