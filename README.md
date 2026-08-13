# Autonomous Developer Workstation & Sandboxed Workspace Agent

A portfolio-grade autonomous developer workstation agent providing controlled tool execution inside a sandboxed workspace environment.

It features **workspace-level filesystem isolation**, a **centralized tool permission matrix**, **controlled Python subprocess execution**, **SQLite schema inspection and query validation**, and a **Human-in-the-Loop confirmation gate** for higher-risk or destructive actions.

---

## 🌟 Core Capabilities

* **Agentic Orchestration & Tool Calling**: Multi-step AI reasoning loop connecting to OpenAI or Google Gemini APIs for intelligent tool selection (`list_files`, `read_file`, `write_file`, `delete_file`, `execute_python`, `inspect_schema`, `query_database`).
* **Workspace-Level Filesystem Sandbox**: Restricts all file operations strictly to an explicitly configured workspace root directory. Defends against path traversal (`../`), absolute host path escapes, and symlink dereferencing outside the root.
* **Centralized Permission Matrix**: Categorizes tool operations into explicit risk levels (`READ`, `WRITE`, `EXECUTE`, `DATABASE`, `DESTRUCTIVE`).
* **Human-in-the-Loop Gate**: Automatically intercepts higher-risk or destructive operations (e.g. file deletion, schema/data mutations, destructive SQL) and pauses execution for explicit user approval.
* **Controlled Python Execution**: Executes Python scripts inside workspace context with strict timeout limits (default 10s) and stdout/stderr capture.
* **SQLite / SQL Query Guard**: Validates SQL statements prior to database execution, differentiating safe `READ-ONLY` SELECT queries from `MUTATING` or `DESTRUCTIVE` SQL (DROP, DELETE, UPDATE, ALTER).
* **Streamlit Dashboard Interface**: Modern, interactive UI with security authentication gate (`APP_ACCESS_KEY`), session management, workspace explorer, and interactive human approval widgets.

---

## 🔒 Security Model

P07 implements a multi-layer defense-in-depth security model:

```text
Workspace-Level Filesystem Boundary
               +
  Centralized Permission Gate
               +
    Human-in-the-Loop Gate
               +
Application-Level Python Restriction
```

1. **Workspace Filesystem Boundary**: Every relative or absolute path argument resolved by the sandbox MUST satisfy `.relative_to(workspace_root)` validation.
2. **Authoritative Permission Layer**: The permission gate and sandbox enforce security rules authoritatively; LLM prompt directives or generated code CANNOT override backend permission checks.
3. **Application-Level Execution Restriction**: Python script execution is restricted via process-level timeouts and working-directory constraints. It is an application-level restriction, not a kernel-isolated container.

---

## 🏗️ Architecture Overview

```text
User Directive
      │
      ▼
Streamlit UI (APP_ACCESS_KEY Auth Gate)
      │
      ▼
Agent Orchestrator (LLM Tool Calling Loop)
      │
      ▼
Permission Gate & SQL Guard (Evaluates Action Risk & Mutation Status)
      │
      ├── Low-Risk (READ) ──────────────────┐
      └── High-Risk / Mutation / Delete ────┤
                                            ▼
                                Human-in-the-Loop Gate
                                (Pauses execution for user UI approval)
                                            │
                                            ▼
                                    Workspace Sandbox
                         (Strict root path resolution & boundary check)
                                            │
                        ┌───────────────────┴───────────────────┐
                        ▼                                       ▼
             Filesystem Operations                     Python Subprocess / SQLite Engine
           (list, read, write, delete)                 (Timeout & directory restricted)
```

---

## 💬 Agent Demonstration Flows

### Example 1: Read-Only Workspace Inspection
```text
User Directive:
"List all files in my workspace directory and read notes.txt."

Execution Steps:
1. Agent selects tool `list_files` with `sub_dir="."`.
2. Permission Gate checks `list_files` -> PermissionLevel.READ (Low Risk) -> ALLOWED.
3. Workspace Sandbox resolves path against workspace_root.
4. Tool returns list of files inside workspace.
5. Agent selects tool `read_file` with `file_path="notes.txt"`.
6. Permission Gate checks `read_file` -> PermissionLevel.READ -> ALLOWED.
7. Workspace Sandbox verifies path boundary and reads file content.
8. Agent synthesizes final answer summarizing workspace directory content and file text.
```

### Example 2: Protected Destructive Action (Human Approval Gate)
```text
User Directive:
"Delete obsolete_file.py from the workspace."

Execution Steps:
1. Agent selects tool `delete_file` with `file_path="obsolete_file.py"`.
2. Permission Gate evaluates action -> PermissionLevel.DESTRUCTIVE / `is_destructive=True`.
3. Execution pauses; Orchestrator returns status `NEEDS_CONFIRMATION` payload.
4. Streamlit UI renders alert: "⚠️ HUMAN CONFIRMATION REQUIRED FOR DESTRUCTIVE ACTION: delete_file on obsolete_file.py".
5. User reviews request and clicks "✅ Approve & Execute Action".
6. Orchestrator executes tool with `user_confirmed=True`.
7. Workspace Sandbox unlinks target file inside workspace boundary.
8. UI notifies user of successful deletion.
```

---

## 🚀 Quickstart Guide

### 1. Installation

Clone the repository and install dependencies:

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Example `.env`:
```ini
APP_ACCESS_KEY=admin123
AI_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
WORKSPACE_DIR=workspace
MAX_PYTHON_TIMEOUT_SECONDS=10
REQUIRE_HUMAN_CONFIRMATION_FOR_MUTATION=true
```

### 3. Running the Web Application

Launch the Streamlit interface:

```bash
streamlit run app.py
```

Open `http://localhost:8501`, log in using your `APP_ACCESS_KEY` (`admin123`), explore the workspace, execute agent tasks, and manage human confirmation requests!

---

## 🧪 Running Unit Tests

Run the complete test suite using `pytest` or `unittest`:

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

Or:

```bash
pytest tests/
```

Expect 100% pass rate (19/19 tests passing).

---

## ⚠️ System Limitations & Constraints

* **Application-Level Python Isolation**: Python execution is governed by process timeouts and workspace directory confinement. It is NOT an OS-level kernel sandbox or containerized execution environment (Docker/seccomp/cgroups).
* **Local Single-User Scope**: Designed for local developer workstation assistance. Multi-tenant deployment would require containerized sandboxing per tenant.
* **Ephemeral Confirmation State**: Human approval state in the Streamlit web interface is held in user session state memory and is ephemeral per session.
* **TOCTOU Symlink Limitation**: File operations use standard Python filesystem primitives; a theoretical Time-of-Check to Time-of-Use symlink race exists under unprivileged local file execution.
