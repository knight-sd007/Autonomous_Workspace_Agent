"""
Tests for Custom MCP Server and Protocol Endpoints.
"""

import pytest
import tempfile
import sqlite3
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from app.server import WorkspaceMCPServer
from app.main import app


def test_mcp_server_tool_discovery():
    server = WorkspaceMCPServer()
    tools = server.list_tools()

    tool_names = [t["name"] for t in tools]
    assert "list_files" in tool_names
    assert "read_file" in tool_names
    assert "inspect_schema" in tool_names
    assert "write_file" in tool_names
    assert "delete_file" in tool_names


def test_mcp_server_call_read_and_list():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        test_file = temp_path / "hello.txt"
        test_file.write_text("Hello MCP World!", encoding="utf-8")

        server = WorkspaceMCPServer(workspace_root=temp_path)
        list_res = server.call_tool("list_files", {"sub_dir": "."})
        assert list_res["isError"] is False
        assert "hello.txt" in list_res["content"][0]["text"]

        read_res = server.call_tool("read_file", {"file_path": "hello.txt"})
        assert read_res["isError"] is False
        assert "Hello MCP World!" in read_res["content"][0]["text"]


def test_mcp_server_inspect_schema():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        db_path = temp_path / "app_data.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT NOT NULL);")
        conn.commit()
        conn.close()

        server = WorkspaceMCPServer(workspace_root=temp_path)
        schema_res = server.call_tool("inspect_schema", {"db_filename": "app_data.db"})
        assert schema_res["isError"] is False
        assert "users" in schema_res["content"][0]["text"]


def test_mcp_server_write_file():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        server = WorkspaceMCPServer(workspace_root=temp_path)

        # Write new file
        res = server.call_tool("write_file", {"file_path": "notes.txt", "content": "Initial content"})
        assert res["isError"] is False
        assert (temp_path / "notes.txt").read_text(encoding="utf-8") == "Initial content"

        # Append to file
        res2 = server.call_tool("write_file", {"file_path": "notes.txt", "content": " + Appended", "append": True})
        assert res2["isError"] is False
        assert (temp_path / "notes.txt").read_text(encoding="utf-8") == "Initial content + Appended"

        # Nested directory write
        res3 = server.call_tool("write_file", {"file_path": "subdir/nested.txt", "content": "Nested file"})
        assert res3["isError"] is False
        assert (temp_path / "subdir" / "nested.txt").read_text(encoding="utf-8") == "Nested file"


def test_mcp_server_delete_file():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        test_file = temp_path / "to_delete.txt"
        test_file.write_text("Delete me", encoding="utf-8")

        server = WorkspaceMCPServer(workspace_root=temp_path)
        res = server.call_tool("delete_file", {"file_path": "to_delete.txt"})
        assert res["isError"] is False
        assert not test_file.exists()

        # Delete non-existent file
        res_nonexistent = server.call_tool("delete_file", {"file_path": "to_delete.txt"})
        assert res_nonexistent["isError"] is True


def test_mcp_server_path_traversal_blocked():
    with tempfile.TemporaryDirectory() as temp_dir:
        server = WorkspaceMCPServer(workspace_root=Path(temp_dir))
        res = server.call_tool("read_file", {"file_path": "../../etc/passwd"})
        assert res["isError"] is True
        assert "Path traversal blocked" in res["content"][0]["text"]

        res_write = server.call_tool("write_file", {"file_path": "../escape.txt", "content": "danger"})
        assert res_write["isError"] is True
        assert "Path traversal blocked" in res_write["content"][0]["text"]

        res_del = server.call_tool("delete_file", {"file_path": "/etc/shadow"})
        assert res_del["isError"] is True
        assert "Path traversal blocked" in res_del["content"][0]["text"]


def test_mcp_server_query_database_and_sqlguard():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        server = WorkspaceMCPServer(workspace_root=temp_path)

        # 1. Create table with allow_mutation=True
        create_res = server.call_tool(
            "query_database",
            {"sql_query": "CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, price REAL);", "allow_mutation": True}
        )
        assert create_res["isError"] is False

        # 2. Block unapproved mutation
        blocked_res = server.call_tool(
            "query_database",
            {"sql_query": "INSERT INTO products (name, price) VALUES ('Widget', 19.99);", "allow_mutation": False}
        )
        assert blocked_res["isError"] is True
        assert "Security Guard Blocked" in blocked_res["content"][0]["text"]

        # 3. Allow approved mutation
        insert_res = server.call_tool(
            "query_database",
            {"sql_query": "INSERT INTO products (name, price) VALUES ('Widget', 19.99);", "allow_mutation": True}
        )
        assert insert_res["isError"] is False

        # 4. Read query (SELECT) works without allow_mutation
        select_res = server.call_tool(
            "query_database",
            {"sql_query": "SELECT * FROM products;", "allow_mutation": False}
        )
        assert select_res["isError"] is False
        assert "Widget" in select_res["content"][0]["text"]

        # 5. Dangerous multi-statement / comment injection blocked
        inject_res = server.call_tool(
            "query_database",
            {"sql_query": "SELECT * FROM products; DROP TABLE products; --", "allow_mutation": False}
        )
        assert inject_res["isError"] is True


@pytest.mark.asyncio
async def test_mcp_api_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Health
        health_resp = await client.get("/health")
        assert health_resp.status_code == 200
        assert health_resp.json()["status"] == "Healthy"

        # Unauthorized tools/list
        unauth_resp = await client.get("/tools/list")
        assert unauth_resp.status_code == 401

        # Authorized tools/list
        auth_resp = await client.get("/tools/list", headers={"X-Internal-Service-Key": "p07_dev_internal_key"})
        assert auth_resp.status_code == 200
        tools = auth_resp.json()["tools"]
        assert len(tools) >= 5

        # Authorized JSON-RPC call
        rpc_resp = await client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
            headers={"X-Internal-Service-Key": "p07_dev_internal_key"}
        )
        assert rpc_resp.status_code == 200
        assert "tools" in rpc_resp.json()["result"]
