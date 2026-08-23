from fastapi import APIRouter, HTTPException

from backend.models.schemas import ChatRequest, ChatResponse
from backend.services.agent_service import AgentService
from backend.services.auth_service import get_user_context


router = APIRouter(
    prefix="/api",
    tags=["ParcelPilot AI Agent"],
)


agent_service = AgentService()


@router.post(
    "/chat",
    response_model=ChatResponse,
)
def chat(request: ChatRequest):

    # ----------------------------------------------------------
    # GET AUTHENTICATED USER CONTEXT
    # ----------------------------------------------------------
    user_context = get_user_context(
        request.username
    )

    if not user_context:
        raise HTTPException(
            status_code=401,
            detail="Invalid or unknown user."
        )

    # ----------------------------------------------------------
    # SEND QUERY TO AGENT
    # ----------------------------------------------------------
    result = agent_service.handle_query(
        query=request.query,
        user_context=user_context,
    )

    return result


@router.get("/health")
def health_check():

    return {
        "status": "healthy",
        "service": "ParcelPilot AI Agent",
    }