# Architecture & Engineering Specifications — Autonomous Developer Workstation Agent

## 1. System Architecture

The Autonomous Developer Workstation Agent provides controlled tool execution inside a sandboxed workspace root directory.

## 2. Core Modules

### 2.1 Configuration Layer (`config/settings.py`)
- Manages settings dynamically from `st.secrets`, `.env`, or environment variables.
- Configures workspace directory root, Python process timeout (default 10s), and human confirmation policy.

### 2.2 Filesystem Sandbox (`sandbox/fs_sandbox.py`)
- `WorkspaceSandbox`: Validates and resolves all path requests strictly against `workspace_root`.
- Defends against path traversal (`../`), absolute host escapes, and symlinks resolving outside the root directory.
- Raises `PathTraversalError` or `SecurityViolationError` on violation.

### 2.3 Security & Permissions (`security/permissions.py`)
- `PermissionLevel`: Categorizes tool actions into `READ`, `WRITE`, `EXECUTE`, `DATABASE`, `DESTRUCTIVE`.
- `PermissionGate`: Intercepts tool calls and mandates human approval for destructive operations or mutations.

### 2.4 Controlled Python Subprocess Executor (`execution/python_runner.py`)
- `PythonRunner`: Spawns temporary Python scripts inside the workspace directory.
- Enforces timeout limits and captures stdout/stderr and exit code safely without crashing the main process.

### 2.5 Database Engine & SQL Guard (`database/`)
- `SQLGuard`: Parses SQL queries and classifies them into `READ_ONLY` (SELECT), `MUTATING` (INSERT, UPDATE, DELETE, ALTER), `DESTRUCTIVE` (DROP, TRUNCATE), or `INVALID`.
- `SQLiteEngine`: Manages SQLite connections inside workspace sandbox and executes queries based on permission status.

### 2.6 Agent Orchestrator (`agent/orchestrator.py`)
- `WorkstationAgentOrchestrator`: Manages tool registry (`list_files`, `read_file`, `write_file`, `delete_file`, `execute_python`, `inspect_schema`, `query_database`).
- Evaluates tool calls against `PermissionGate`. If human confirmation is required, returns a pending confirmation payload for user UI approval before resuming execution.
