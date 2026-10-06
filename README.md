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
* **SvelteKit + ASP.NET Core UI/API**: The compiled frontend and API share one public origin and one local host port.

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

P07 uses one public application endpoint with private internal services:

```text
Browser
   │
   │ HTTPS
   ▼
Cloudflare
   │
   │ cloudflared tunnel
   ▼
127.0.0.1:8007
   │
   ▼
┌──────────────────────────────────────────┐
│ p07-api                                  │
│ ASP.NET Core + compiled SvelteKit SPA    │
│ container :8080 → host 127.0.0.1:8007  │
└───────────────────┬──────────────────────┘
                    │
                    │ private Docker network
                    ▼
          ┌──────────────────────┐
          │ p07-agent-runtime    │
          │ FastAPI :8001        │
          └──────────┬───────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │ p07-mcp              │
          │ FastAPI/MCP :8002    │
          └──────────────────────┘
```

Only `127.0.0.1:8007` is published on the host. Agent Runtime and MCP ports are not host-published.

Swagger and MCP documentation are exposed through read-only frontend tabs from the same public origin; the underlying Agent/MCP services remain private.

### Shared Portfolio Documentation
All architectural specifications, deployment runbooks, and migration plans for P07 are maintained centrally in the shared portfolio documentation repository:

* **Architecture Specifications:** `docs/P07/ARCHITECTURE.md` (Shared location: `/mnt/f/Portfolios/docs/P07/ARCHITECTURE.md`)
* **Deployment Runbook:** `docs/P07/DEPLOYMENT.md` (Shared location: `/mnt/f/Portfolios/docs/P07/DEPLOYMENT.md`)
* **Migration Plan:** `docs/P07/MIGRATION_PLAN.md` (Shared location: `/mnt/f/Portfolios/docs/P07/MIGRATION_PLAN.md`)

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

### 1. Environment Configuration

Copy `.env.example` to `.env` and configure runtime values:

```bash
cp .env.example .env
```

Secrets are injected at runtime and are not committed to Git.

### 3. Running the Application

Launch the production multi-service stack:

```bash
docker compose up -d
```

The single public application endpoint is:

```text
http://127.0.0.1:8007
```

Configure Cloudflare Tunnel to target exactly:

```text
http://127.0.0.1:8007
```

The ASP.NET Core container serves both the compiled SvelteKit frontend and the API. Agent Runtime and MCP remain private inside the Docker network.

For frontend-only development:

```bash
cd frontend
npm ci
npm run check
npm run dev
```

Production traffic does not use the frontend development server.

---

## 🧪 Running Automated Tests

### 1. Legacy regression suite
```bash
pytest tests/ -v
```

### 2. ASP.NET Core Backend Test Suite (.NET 10)
```bash
cd backend && dotnet test
```

### 3. Python Agent Runtime Suite
```bash
PYTHONPATH=agent-runtime pytest agent-runtime/tests/ -v
```

### 4. Custom MCP Server Suite
```bash
PYTHONPATH=mcp-server pytest mcp-server/tests/ -v
```

---

## 🔄 Legacy Migration Status

The original Streamlit implementation is retained temporarily for regression coverage while the production architecture migrates to the SvelteKit + ASP.NET Core + Agent Runtime + MCP stack. Legacy components should be retired only after dependency/reference analysis and a passing CI migration gate.

---

## ⚠️ System Limitations & Constraints

* **Application-Level Python Isolation**: Python execution is governed by process timeouts and workspace directory confinement. It is NOT an OS-level kernel sandbox or containerized execution environment (Docker/seccomp/cgroups).
* **Local Single-User Scope**: Designed for local developer workstation assistance. Multi-tenant deployment would require containerized sandboxing per tenant.
* **Ephemeral Confirmation State**: Human approval state in the Streamlit web interface is held in user session state memory and is ephemeral per session.
* **TOCTOU Symlink Limitation**: File operations use standard Python filesystem primitives; a theoretical Time-of-Check to Time-of-Use symlink race exists under unprivileged local file execution.
