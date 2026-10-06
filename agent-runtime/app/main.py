"""
FastAPI Entrypoint for Internal Python Agent Runtime Service.
"""

from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.config import RuntimeConfig
from app.security.sanitizer import verify_service_key
from app.orchestrator.engine import AgentOrchestrator

app = FastAPI(
    title="P07 Python Agent Runtime",
    version="1.0.0",
    docs_url=None,  # Internal service, disable public docs endpoint
    redoc_url=None
)

orchestrator = AgentOrchestrator()


class AgentChatRequestModel(BaseModel):
    message: str = Field(..., min_length=1)
    sessionId: Optional[str] = None
    provider: str = Field(default="offline")
    model: Optional[str] = None
    maxSteps: int = Field(default=5, ge=1, le=15)
    userConfirmed: bool = Field(default=False)


class AgentApprovalRequestModel(BaseModel):
    sessionId: str = Field(..., min_length=1)
    approvalId: str = Field(..., min_length=1)
    decision: str = Field(..., pattern="^(approve|reject)$")
    toolKwargs: Optional[Dict[str, Any]] = None


@app.get("/health")
async def health_check(x_internal_service_key: Optional[str] = Header(None)):
    return {
        "status": "Healthy",
        "service": "P07.AgentRuntime",
        "version": "1.0.0"
    }


@app.post("/api/v1/agent/chat")
async def execute_agent_chat(
    req: AgentChatRequestModel,
    x_internal_service_key: Optional[str] = Header(None)
):
    expected_key = RuntimeConfig.get_service_key()
    if not x_internal_service_key or not verify_service_key(x_internal_service_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid internal service key."
        )

    session_id = req.sessionId or "default_session"
    res = await orchestrator.process_task(
        task_prompt=req.message,
        session_id=session_id,
        provider_name=req.provider,
        model_name=req.model,
        max_steps=req.maxSteps,
        user_confirmed=req.userConfirmed
    )

    return {
        "sessionId": session_id,
        "status": res.get("status", "success"),
        "finalAnswer": res.get("finalAnswer", ""),
        "steps": res.get("steps", []),
        "pendingConfirmation": res.get("pendingConfirmation"),
        "errorMessage": res.get("errorMessage")
    }


@app.post("/api/v1/agent/approve")
async def execute_agent_approval(
    req: AgentApprovalRequestModel,
    x_internal_service_key: Optional[str] = Header(None)
):
    expected_key = RuntimeConfig.get_service_key()
    if not x_internal_service_key or not verify_service_key(x_internal_service_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid internal service key."
        )

    res = await orchestrator.process_approval(
        session_id=req.sessionId,
        approval_id=req.approvalId,
        decision=req.decision,
        supplied_kwargs=req.toolKwargs
    )

    if res.get("status") == "error":
        # Check if security integrity or session violation
        err_msg = res.get("errorMessage", "")
        if "Security Violation" in err_msg or "mismatch" in err_msg or "modified" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=err_msg
            )

    return res
