"""
Autonomous Developer Workstation & Sandboxed Workspace Agent — Streamlit Web Application.

A modern, production-grade interface demonstrating an agentic workstation agent with
workspace-level filesystem isolation, tool permission matrix, Python execution, SQLite engine,
and Human-in-the-Loop confirmation gate.
"""

import streamlit as st
import json
from pathlib import Path
from config.settings import Config
from utils.security import verify_access_key, sanitize_error_message
from sandbox.fs_sandbox import WorkspaceSandbox, PathTraversalError
from agent.orchestrator import WorkstationAgentOrchestrator
from database.sql_guard import SQLGuard


# Page Configuration
st.set_page_config(
    page_title="Autonomous Developer Workstation Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


def init_session_state():
    """Initializes Streamlit session state."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if "sandbox" not in st.session_state:
        st.session_state.sandbox = WorkspaceSandbox(Config.get_workspace_dir())

    if "orchestrator" not in st.session_state:
        st.session_state.orchestrator = WorkstationAgentOrchestrator(st.session_state.sandbox)

    if "pending_confirmation" not in st.session_state:
        st.session_state.pending_confirmation = None

    if "task_history" not in st.session_state:
        st.session_state.task_history = []


def render_login():
    """Renders Security Authentication Gate."""
    st.markdown("<h2 style='text-align: center;'>🔐 Autonomous Workstation Agent</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888;'>Enter access key to unlock sandboxed workstation agent.</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            access_key = st.text_input("Access Key", type="password", placeholder="Enter APP_ACCESS_KEY")
            submit = st.form_submit_button("Authenticate & Access", use_container_width=True)

            if submit:
                expected = Config.get_app_access_key()
                if verify_access_key(access_key, expected):
                    st.session_state.authenticated = True
                    st.success("Authentication successful!")
                    st.rerun()
                else:
                    st.error("Invalid access key.")


def render_app():
    """Renders main workstation dashboard."""
    init_session_state()
    orchestrator = st.session_state.orchestrator
    sandbox = st.session_state.sandbox

    # Sidebar Controls
    with st.sidebar:
        st.title("⚙️ Security & Controls")

        st.markdown("### Workspace Sandbox")
        st.code(str(sandbox.workspace_root), language="text")

        st.markdown("### Human-in-the-Loop")
        confirm_enabled = st.checkbox(
            "Enforce Human Approval for Mutations",
            value=Config.require_human_confirmation()
        )
        orchestrator.permission_gate.enforce_human_confirmation = confirm_enabled

        st.divider()
        st.markdown("### System Tools")
        for tool_name, tool in orchestrator.tools.items():
            icon = "🔴" if tool.is_destructive else ("🟡" if tool.permission_level.name in ("WRITE", "EXECUTE", "DATABASE") else "🟢")
            st.caption(f"{icon} `{tool_name}` — {tool.permission_level.name}")

        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()

    # Main Workspace Area
    st.title("🤖 Autonomous Developer Workstation Agent")
    st.caption("Sandboxed File Operations, Python Subprocess Execution, SQLite Text-to-SQL & Human Approval Gate")

    # Render Human Confirmation Alert if pending
    if st.session_state.pending_confirmation:
        pending = st.session_state.pending_confirmation
        st.warning("⚠️ **HUMAN CONFIRMATION REQUIRED FOR SENSITIVE ACTION**")

        st.markdown(f"**Action Requested:** `{pending['tool_name']}`")
        st.markdown(f"**Target Resource:** `{pending['resource']}`")
        st.markdown(f"**Reason:** {pending['reason']}")

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("✅ Approve & Execute Action", type="primary", use_container_width=True):
                res = orchestrator.execute_tool_call(
                    pending['tool_name'],
                    pending['tool_kwargs'],
                    user_confirmed=True
                )
                st.session_state.pending_confirmation = None
                if res.get("status") == "success":
                    st.success(f"Action executed successfully: {res.get('output')}")
                else:
                    st.error(f"Execution failed: {res.get('message')}")
                st.rerun()

        with col_b:
            if st.button("❌ Deny & Reject Action", use_container_width=True):
                st.session_state.pending_confirmation = None
                st.info("Action rejected by user.")
                st.rerun()

        st.divider()

    tab1, tab2, tab3, tab4 = st.tabs([
        "🤖 Agent Task Console",
        "📂 Workspace Explorer",
        "🗄️ SQLite Database Inspector",
        "🛡️ Path Sandbox & SQL Guard Tester"
    ])

    # TAB 1: AGENT TASK CONSOLE
    with tab1:
        st.subheader("1. Agent Task Execution")

        user_prompt = st.text_area(
            "Enter user task or directive for agent:",
            placeholder="e.g. List all files in the workspace and inspect app_data.db schema.",
            height=100
        )

        col1, col2 = st.columns(2)
        with col1:
            provider_choice = st.selectbox("AI Provider", ["openai", "gemini"], index=0)
        with col2:
            max_steps = st.slider("Max Reasoning Steps", 1, 10, 5)

        if st.button("🚀 Execute Agent Task", type="primary"):
            if not user_prompt.strip():
                st.warning("Please enter a task prompt.")
            else:
                with st.spinner("Agent evaluating task and selecting tools..."):
                    result = orchestrator.process_task(user_prompt, provider_choice, max_steps)

                if result.get("status") == "success":
                    st.markdown("### Agent Output")
                    st.markdown(result.get("final_answer", ""))

                    steps = result.get("steps", [])
                    if steps:
                        st.markdown("#### Tool Execution Steps")
                        for s in steps:
                            with st.expander(f"Step {s['step']}: Tool `{s['tool']}`"):
                                st.json(s.get("result", {}))
                else:
                    st.error(f"Task processing error: {result.get('message')}")

    # TAB 2: WORKSPACE EXPLORER
    with tab2:
        st.subheader("2. Sandboxed Workspace Explorer")

        try:
            files = sandbox.list_files(".")
            if not files:
                st.info("Workspace directory is empty.")
            else:
                st.markdown("#### Files inside Workspace Sandbox")
                for f in files:
                    icon = "📁" if f["is_dir"] else "📄"
                    st.markdown(f"- {icon} `{f['relative_path']}` ({f['size_bytes']} bytes)")
        except Exception as e:
            st.error(f"Error listing workspace files: {sanitize_error_message(e)}")

        st.divider()
        st.markdown("#### Create File in Sandbox")
        with st.form("create_file_form"):
            new_fname = st.text_input("Relative File Path", placeholder="notes.txt")
            new_content = st.text_area("File Content", placeholder="Write text here...")
            if st.form_submit_button("Create File"):
                if not new_fname.strip():
                    st.warning("Enter valid filename.")
                else:
                    try:
                        rel = sandbox.write_file(new_fname, new_content)
                        st.success(f"Created file `{rel}` in workspace sandbox!")
                        st.rerun()
                    except PathTraversalError as pte:
                        st.error(f"Path Traversal Blocked: {pte}")
                    except Exception as e:
                        st.error(f"Error: {sanitize_error_message(e)}")

    # TAB 3: SQLITE INSPECTOR
    with tab3:
        st.subheader("3. SQLite Database Inspector")

        schema_res = orchestrator.sqlite_engine.get_schema("app_data.db")
        if schema_res.get("status") == "success":
            st.json(schema_res["tables"])
        else:
            st.info(f"Database status: {schema_res.get('message')}")

        st.divider()
        st.markdown("#### Execute SQL Query")
        sql_input = st.text_input("Enter SQL Query:", value="SELECT name FROM sqlite_master WHERE type='table';")

        if st.button("Run SQL Query"):
            res = orchestrator.execute_tool_call(
                "query_database",
                {"sql_query": sql_input, "db_filename": "app_data.db"}
            )
            if res.get("status") == "NEEDS_CONFIRMATION":
                st.session_state.pending_confirmation = res
                st.rerun()
            elif res.get("status") == "success":
                st.json(res.get("output"))
            else:
                st.error(res.get("message"))

    # TAB 4: PATH SANDBOX & SQL GUARD TESTER
    with tab4:
        st.subheader("4. Security Boundary Tester")

        st.markdown("#### Path Traversal Defense Test")
        test_path = st.text_input("Test Path Resolution:", value="../../Windows/System32/config/SAM")
        if st.button("Test Path Resolution"):
            try:
                resolved = sandbox.resolve_path(test_path)
                st.warning(f"Path resolved inside workspace: {resolved}")
            except PathTraversalError as pte:
                st.success(f"🛡️ Path Traversal Blocked as expected!\n\nError: `{pte}`")

        st.divider()
        st.markdown("#### SQL Mutation Guard Test")
        test_sql = st.text_input("Test SQL Statement Analysis:", value="DROP TABLE users;")
        if st.button("Analyze SQL Statement"):
            analysis = SQLGuard.analyze_query(test_sql)
            st.markdown(f"**Classification:** `{analysis.classification.name}`")
            st.markdown(f"**Statement Type:** `{analysis.statement_type}`")
            st.markdown(f"**Safe Read:** `{analysis.is_safe_read}`")
            st.markdown(f"**Requires Human Approval:** `{analysis.requires_human_confirmation}`")
            st.markdown(f"**Reason:** {analysis.reason}")


def main():
    """Main application entrypoint."""
    init_session_state()
    if not st.session_state.authenticated:
        render_login()
    else:
        render_app()


if __name__ == "__main__":
    main()
