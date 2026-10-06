"""
Autonomous Workstation Agent Orchestrator Engine for Agent Runtime.
Integrates MCP Tool execution and Human-in-the-Loop approval lifecycle.
"""

from typing import Dict, Any, List, Optional
import json
import logging
from app.config import RuntimeConfig
from app.security.fs_sandbox import WorkspaceSandbox
from app.security.permissions import PermissionGate, PermissionLevel, ActionPermissionRequest
from app.security.approval_manager import ApprovalManager, ApprovalRecord
from app.tools.base import BaseTool, ToolResult
from app.tools.mcp_client import MCPClient
from app.tools.mcp_tools import (
    MCPListFilesTool,
    MCPReadFileTool,
    MCPInspectSchemaTool,
    MCPWriteFileTool,
    MCPDeleteFileTool,
    MCPQueryDatabaseTool
)
from app.tools.python_tools import ExecutePythonTool
from app.providers.factory import ProviderFactory
from app.providers.base import BaseLLMProvider
from app.security.sanitizer import sanitize_error_message

logger = logging.getLogger("p07.orchestrator")


class AgentOrchestrator:
    """Coordinates multi-step tool execution with permission gates, MCP client, and LLM providers."""

    def __init__(
        self,
        sandbox: Optional[WorkspaceSandbox] = None,
        mcp_client: Optional[MCPClient] = None,
        approval_manager: Optional[ApprovalManager] = None
    ):
        self.sandbox = sandbox or WorkspaceSandbox(RuntimeConfig.get_workspace_dir())
        self.mcp_client = mcp_client or MCPClient(workspace_root=self.sandbox.workspace_root)
        self.approval_manager = approval_manager or ApprovalManager()
        self.permission_gate = PermissionGate(enforce_human_confirmation=RuntimeConfig.require_human_confirmation())

        # Register tools
        self.tools: Dict[str, BaseTool] = {}
        self._register_tools()

    def _register_tools(self):
        tool_instances = [
            MCPListFilesTool(self.mcp_client),
            MCPReadFileTool(self.mcp_client),
            MCPInspectSchemaTool(self.mcp_client),
            MCPWriteFileTool(self.mcp_client),
            MCPDeleteFileTool(self.mcp_client),
            MCPQueryDatabaseTool(self.mcp_client),
            ExecutePythonTool(self.sandbox, default_timeout=RuntimeConfig.get_python_timeout())
        ]
        for t in tool_instances:
            self.tools[t.name] = t


    def execute_tool(
        self,
        tool_name: str,
        tool_kwargs: Dict[str, Any],
        session_id: str = "default_session",
        user_confirmed: bool = False
    ) -> Dict[str, Any]:
        if tool_name not in self.tools:
            return {
                "status": "error",
                "message": f"Unknown tool '{tool_name}'"
            }

        tool = self.tools[tool_name]
        resource = str(tool_kwargs.get("file_path") or tool_kwargs.get("sub_dir") or tool_kwargs.get("db_filename") or "workspace")

        perm_request = ActionPermissionRequest(
            tool_name=tool.name,
            action_type=tool.permission_level,
            resource=resource,
            details=tool_kwargs,
            is_destructive=tool.is_destructive
        )

        if not user_confirmed:
            eval_res = self.permission_gate.evaluate_request(perm_request)
            if eval_res["status"] == "NEEDS_CONFIRMATION":
                # Create signed and bounded pending approval
                approval = self.approval_manager.create_approval(
                    session_id=session_id,
                    tool_name=tool_name,
                    resource=resource,
                    tool_kwargs=tool_kwargs,
                    reason=eval_res["reason"],
                    is_destructive=tool.is_destructive
                )
                return {
                    "status": "NEEDS_CONFIRMATION",
                    "approval_id": approval.approval_id,
                    "session_id": session_id,
                    "reason": eval_res["reason"],
                    "tool_name": tool_name,
                    "tool_kwargs": tool_kwargs,
                    "resource": resource,
                    "is_destructive": tool.is_destructive,
                    "expires_at": approval.expires_at_utc
                }

        res: ToolResult = tool.run(**tool_kwargs)
        if res.success:
            return {
                "status": "success",
                "output": res.output,
                "tool_name": tool_name
            }
        else:
            return {
                "status": "error",
                "message": res.error,
                "tool_name": tool_name
            }

    async def process_task(
        self,
        task_prompt: str,
        session_id: str = "default_session",
        provider_name: str = "offline",
        model_name: Optional[str] = None,
        max_steps: int = 5,
        user_confirmed: bool = False
    ) -> Dict[str, Any]:
        if not task_prompt.strip():
            return {"status": "error", "message": "Task prompt cannot be empty."}

        provider = ProviderFactory.create_provider(provider_name, model_name)
        messages = [
            {"role": "system", "content": "You are an autonomous workstation agent helping manage files and execute tasks."},
            {"role": "user", "content": task_prompt}
        ]

        steps_log = []
        try:
            response = await provider.generate_response(messages)

            # If tool calls returned
            if response.tool_calls:
                for idx, tc in enumerate(response.tool_calls, start=1):
                    tool_res = self.execute_tool(
                        tc.tool_name,
                        tc.arguments,
                        session_id=session_id,
                        user_confirmed=user_confirmed
                    )

                    if tool_res.get("status") == "NEEDS_CONFIRMATION":
                        return {
                            "status": "needs_confirmation",
                            "pendingConfirmation": {
                                "approvalId": tool_res["approval_id"],
                                "sessionId": session_id,
                                "toolName": tool_res["tool_name"],
                                "resource": tool_res["resource"],
                                "reason": tool_res["reason"],
                                "toolKwargs": tool_res["tool_kwargs"],
                                "isDestructive": tool_res["is_destructive"],
                                "expiresAt": tool_res["expires_at"]
                            },
                            "steps": steps_log,
                            "finalAnswer": f"Action '{tc.tool_name}' on '{tool_res['resource']}' requires human confirmation."
                        }

                    steps_log.append({
                        "step": idx,
                        "tool": tc.tool_name,
                        "output": tool_res.get("output") or tool_res.get("message")
                    })

                final_text = f"Executed {len(response.tool_calls)} tool action(s). Output:\n{json.dumps([s['output'] for s in steps_log], indent=2)}"
                return {
                    "status": "success",
                    "finalAnswer": final_text,
                    "steps": steps_log,
                    "pendingConfirmation": None
                }

            return {
                "status": "success",
                "finalAnswer": response.content or "Task completed.",
                "steps": steps_log,
                "pendingConfirmation": None
            }

        except Exception as e:
            clean_err = sanitize_error_message(e)
            return {
                "status": "error",
                "errorMessage": clean_err,
                "finalAnswer": f"Error executing task: {clean_err}",
                "steps": steps_log
            }

    async def process_approval(
        self,
        session_id: str,
        approval_id: str,
        decision: str,
        supplied_kwargs: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Processes an explicit human approval or rejection decision."""
        valid, msg, record = self.approval_manager.evaluate_decision(
            approval_id=approval_id,
            session_id=session_id,
            decision=decision,
            supplied_kwargs=supplied_kwargs
        )

        if not valid:
            return {
                "sessionId": session_id,
                "status": "error",
                "errorMessage": msg,
                "finalAnswer": f"Approval evaluation failed: {msg}",
                "steps": []
            }

        if decision.strip().lower() == "reject":
            return {
                "sessionId": session_id,
                "status": "rejected",
                "finalAnswer": f"User rejected tool action '{record.tool_name}' on '{record.resource}'.",
                "steps": [
                    {
                        "step": 1,
                        "tool": record.tool_name,
                        "output": "Action was explicitly rejected by user."
                    }
                ]
            }

        # If approved, execute the tool action
        tool = self.tools.get(record.tool_name)
        if not tool:
            return {
                "sessionId": session_id,
                "status": "error",
                "errorMessage": f"Tool '{record.tool_name}' is not registered.",
                "finalAnswer": f"Error: Tool '{record.tool_name}' not available.",
                "steps": []
            }

        res: ToolResult = tool.run(**record.tool_kwargs)
        if res.success:
            return {
                "sessionId": session_id,
                "status": "success",
                "finalAnswer": f"Successfully executed approved action '{record.tool_name}'. Output:\n{res.output}",
                "steps": [
                    {
                        "step": 1,
                        "tool": record.tool_name,
                        "output": res.output
                    }
                ]
            }
        else:
            return {
                "sessionId": session_id,
                "status": "error",
                "errorMessage": res.error,
                "finalAnswer": f"Failed to execute approved action '{record.tool_name}': {res.error}",
                "steps": [
                    {
                        "step": 1,
                        "tool": record.tool_name,
                        "output": res.error
                    }
                ]
            }
