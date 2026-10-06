"""
API integration and security tests for Python Agent Runtime FastAPI service.
"""

import pytest
import time
from httpx import AsyncClient, ASGITransport
from app.main import app, orchestrator


@pytest.mark.asyncio
async def test_health_check_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Healthy"
        assert data["service"] == "P07.AgentRuntime"


@pytest.mark.asyncio
async def test_agent_chat_unauthorized_without_key():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/agent/chat",
            json={"message": "List files", "provider": "offline"}
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_agent_chat_authorized_with_key():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/agent/chat",
            json={"message": "List files", "provider": "offline"},
            headers={"X-Internal-Service-Key": "p07_dev_internal_key"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["steps"]) >= 1


@pytest.mark.asyncio
async def test_hitl_approval_lifecycle_and_security_controls():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Trigger a write directive -> must return needs_confirmation
        chat_resp = await client.post(
            "/api/v1/agent/chat",
            json={"message": "Write a report to output.txt", "sessionId": "sess_hitl_1", "provider": "offline"},
            headers={"X-Internal-Service-Key": "p07_dev_internal_key"}
        )
        assert chat_resp.status_code == 200
        chat_data = chat_resp.json()
        assert chat_data["status"] == "needs_confirmation"
        assert chat_data["pendingConfirmation"] is not None

        pending = chat_data["pendingConfirmation"]
        approval_id = pending["approvalId"]
        session_id = pending["sessionId"]
        tool_kwargs = pending["toolKwargs"]
        assert pending["toolName"] == "write_file"
        assert session_id == "sess_hitl_1"

        # 2. Test Security: Session mismatch rejection
        mismatch_resp = await client.post(
            "/api/v1/agent/approve",
            json={
                "sessionId": "wrong_session_id",
                "approvalId": approval_id,
                "decision": "approve",
                "toolKwargs": tool_kwargs
            },
            headers={"X-Internal-Service-Key": "p07_dev_internal_key"}
        )
        assert mismatch_resp.status_code == 400
        assert "Security Violation" in mismatch_resp.text

        # 3. Test Security: Argument tampering detection
        tampered_kwargs = dict(tool_kwargs)
        tampered_kwargs["file_path"] = "hacked.txt"
        tamper_resp = await client.post(
            "/api/v1/agent/approve",
            json={
                "sessionId": session_id,
                "approvalId": approval_id,
                "decision": "approve",
                "toolKwargs": tampered_kwargs
            },
            headers={"X-Internal-Service-Key": "p07_dev_internal_key"}
        )
        assert tamper_resp.status_code == 400
        assert "Security Violation" in tamper_resp.text

        # 4. Valid Approval Execution
        approve_resp = await client.post(
            "/api/v1/agent/approve",
            json={
                "sessionId": session_id,
                "approvalId": approval_id,
                "decision": "approve",
                "toolKwargs": tool_kwargs
            },
            headers={"X-Internal-Service-Key": "p07_dev_internal_key"}
        )
        assert approve_resp.status_code == 200
        approve_data = approve_resp.json()
        assert approve_data["status"] == "success"
        assert len(approve_data["steps"]) == 1
        assert approve_data["steps"][0]["tool"] == "write_file"

        # 5. Test Security: Replay / duplicate approval rejected
        replay_resp = await client.post(
            "/api/v1/agent/approve",
            json={
                "sessionId": session_id,
                "approvalId": approval_id,
                "decision": "approve",
                "toolKwargs": tool_kwargs
            },
            headers={"X-Internal-Service-Key": "p07_dev_internal_key"}
        )
        assert replay_resp.status_code == 200
        replay_data = replay_resp.json()
        assert replay_data["status"] == "error"
        assert "already been processed" in replay_data["errorMessage"]


@pytest.mark.asyncio
async def test_hitl_rejection_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Trigger destructive directive
        chat_resp = await client.post(
            "/api/v1/agent/chat",
            json={"message": "Delete file to_delete.txt", "sessionId": "sess_reject_1", "provider": "offline"},
            headers={"X-Internal-Service-Key": "p07_dev_internal_key"}
        )
        assert chat_resp.status_code == 200
        pending = chat_resp.json()["pendingConfirmation"]
        assert pending["toolName"] == "delete_file"
        assert pending["isDestructive"] is True

        # Reject the action
        reject_resp = await client.post(
            "/api/v1/agent/approve",
            json={
                "sessionId": "sess_reject_1",
                "approvalId": pending["approvalId"],
                "decision": "reject"
            },
            headers={"X-Internal-Service-Key": "p07_dev_internal_key"}
        )
        assert reject_resp.status_code == 200
        reject_data = reject_resp.json()
        assert reject_data["status"] == "rejected"
        assert "rejected" in reject_data["finalAnswer"]


@pytest.mark.asyncio
async def test_hitl_expiry_handling():
    # Create an expired approval record manually in orchestrator manager
    approval = orchestrator.approval_manager.create_approval(
        session_id="sess_exp_1",
        tool_name="write_file",
        resource="exp.txt",
        tool_kwargs={"file_path": "exp.txt", "content": "test"},
        reason="Test expiry",
        ttl_seconds=-10  # Expired 10 seconds ago
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/agent/approve",
            json={
                "sessionId": "sess_exp_1",
                "approvalId": approval.approval_id,
                "decision": "approve"
            },
            headers={"X-Internal-Service-Key": "p07_dev_internal_key"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "error"
        assert "expired" in data["errorMessage"].lower()


@pytest.mark.asyncio
async def test_database_query_and_approval_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Database schema inspection does not require approval
        schema_resp = await client.post(
            "/api/v1/agent/chat",
            json={"message": "Inspect database schema for app_data.db", "sessionId": "sess_db_1", "provider": "offline"},
            headers={"X-Internal-Service-Key": "p07_dev_internal_key"}
        )
        assert schema_resp.status_code == 200
        schema_data = schema_resp.json()
        assert schema_data["status"] == "success"

        # 2. Database mutation request via direct engine execution triggers confirmation
        approval = orchestrator.approval_manager.create_approval(
            session_id="sess_db_mut_1",
            tool_name="query_database",
            resource="app_data.db",
            tool_kwargs={"sql_query": "CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, msg TEXT);", "db_filename": "app_data.db"},
            reason="Database table creation mutation"
        )
        assert approval.approval_id is not None

        # 3. Approve database mutation
        approve_resp = await client.post(
            "/api/v1/agent/approve",
            json={
                "sessionId": "sess_db_mut_1",
                "approvalId": approval.approval_id,
                "decision": "approve",
                "toolKwargs": {"sql_query": "CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, msg TEXT);", "db_filename": "app_data.db"}
            },
            headers={"X-Internal-Service-Key": "p07_dev_internal_key"}
        )
        assert approve_resp.status_code == 200
        approve_data = approve_resp.json()
        assert approve_data["status"] == "success"
