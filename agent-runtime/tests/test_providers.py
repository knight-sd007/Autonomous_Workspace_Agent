"""
Unit tests for LLM Providers, MCP Tool Wrappers, and Agent Orchestrator.
"""

import pytest
from app.providers.offline_provider import OfflineProvider
from app.providers.factory import ProviderFactory
from app.orchestrator.engine import AgentOrchestrator
from app.security.fs_sandbox import WorkspaceSandbox
from app.tools.mcp_client import MCPClient
from pathlib import Path
import tempfile


@pytest.mark.asyncio
async def test_offline_provider_list_files_matching():
    provider = OfflineProvider()
    res = await provider.generate_response([{"role": "user", "content": "Please list all files in the workspace."}])
    assert len(res.tool_calls) == 1
    assert res.tool_calls[0].tool_name == "list_files"


@pytest.mark.asyncio
async def test_offline_provider_read_file_matching():
    provider = OfflineProvider()
    res = await provider.generate_response([{"role": "user", "content": "Please read notes.txt"}])
    assert len(res.tool_calls) == 1
    assert res.tool_calls[0].tool_name == "read_file"


@pytest.mark.asyncio
async def test_offline_provider_schema_matching():
    provider = OfflineProvider()
    res = await provider.generate_response([{"role": "user", "content": "Please inspect database schema"}])
    assert len(res.tool_calls) == 1
    assert res.tool_calls[0].tool_name == "inspect_schema"


@pytest.mark.asyncio
async def test_offline_provider_write_matching():
    provider = OfflineProvider()
    res = await provider.generate_response([{"role": "user", "content": "Please write output to output.txt"}])
    assert len(res.tool_calls) == 1
    assert res.tool_calls[0].tool_name == "write_file"


@pytest.mark.asyncio
async def test_offline_provider_delete_matching():
    provider = OfflineProvider()
    res = await provider.generate_response([{"role": "user", "content": "Please delete to_delete.txt"}])
    assert len(res.tool_calls) == 1
    assert res.tool_calls[0].tool_name == "delete_file"


@pytest.mark.asyncio
async def test_offline_provider_generic_response():
    provider = OfflineProvider()
    res = await provider.generate_response([{"role": "user", "content": "Hello agent!"}])
    assert len(res.tool_calls) == 0
    assert "[Offline Fallback]" in (res.content or "")


@pytest.mark.asyncio
async def test_orchestrator_process_task_offline_with_mcp():
    with tempfile.TemporaryDirectory() as temp_dir:
        sandbox = WorkspaceSandbox(temp_dir)
        sandbox.write_file("notes.txt", "Hello from test workspace!")

        mcp_client = MCPClient(workspace_root=Path(temp_dir))
        orchestrator = AgentOrchestrator(sandbox=sandbox, mcp_client=mcp_client)
        result = await orchestrator.process_task("List files in directory", provider_name="offline")

        assert result["status"] == "success"
        assert len(result["steps"]) >= 1
        assert result["steps"][0]["tool"] == "list_files"


@pytest.mark.asyncio
async def test_python_execution_env_sanitization():
    """Verify SEC-01: Python subprocess does NOT inherit secret environment variables."""
    with tempfile.TemporaryDirectory() as temp_dir:
        sandbox = WorkspaceSandbox(temp_dir)
        orchestrator = AgentOrchestrator(sandbox=sandbox)

        # Execute python script inspecting environment
        code = (
            "import os\n"
            "print('HAS_SECRET:', 'OPENAI_API_KEY' in os.environ)\n"
        )
        res = orchestrator.execute_tool("execute_python", {"code_snippet": code}, user_confirmed=True)
        assert res["status"] == "success"
        assert "HAS_SECRET: False" in res["output"]
