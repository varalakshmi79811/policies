import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime, date
import traceback
import os

# Configure Streamlit page
st.set_page_config(
    page_title="Policy Management System - Fixed",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API base URL

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        border-bottom: 3px solid #1f77b4;
        padding-bottom: 1rem;
    }
    
    .chat-message {
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
    }
    
    .policy-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        background-color: #fafafa;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

def call_api(endpoint, method="GET", data=None, files=None, timeout=30):
    try:
        url = f"{API_BASE_URL}{endpoint}"

        if method == "GET":
            response = requests.get(url, timeout=timeout)

        elif method == "POST":
            if endpoint == "/policies":
                # FastAPI expects form fields (data=...) and optional files (files=...)
                if files:
                    response = requests.post(url, data=data or {}, files=files, timeout=timeout)
                else:
                    response = requests.post(url, data=data or {}, timeout=timeout)
            else:
                # Other POSTs usually accept JSON (unless you have more upload endpoints)
                if files:
                    response = requests.post(url, data=data or {}, files=files, timeout=timeout)
                elif data:
                    response = requests.post(url, json=data, timeout=timeout)
                else:
                    response = requests.post(url, timeout=timeout)

        elif method == "PUT":
            response = requests.put(url, json=data or {}, timeout=timeout)

        elif method == "DELETE":
            response = requests.delete(url, timeout=timeout)

        else:
            return {"success": False, "message": f"Unsupported method {method}"}

        if response.status_code in [200, 201, 202]:
            try:
                return {"success": True, "data": response.json(), "status_code": response.status_code}
            except ValueError:
                return {"success": True, "data": response.text, "status_code": response.status_code}
        else:
            try:
                error_detail = response.json()
            except Exception:
                error_detail = response.text
            return {
                "success": False,
                "error": error_detail,
                "status_code": response.status_code,
                "message": f"API Error: {response.status_code}",
            }

    except requests.exceptions.Timeout:
        return {"success": False, "message": "Request timed out", "error": "timeout"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "message": "Cannot connect to API", "error": "connection"}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {str(e)}", "error": str(e)}


def enhanced_chat_with_ai(user_input: str, attached_files=None):
    """
    Minimal chat handler that:
    - Shows all policies deterministically (no LLM)
    - Creates a policy (with files if attached)
    - Adds files to an existing policy when message mentions "file/document" and a policy name
    - Otherwise, falls back to /chat (LLM) for guidance/search/stats
    """
    try:
        text = (user_input or "").strip()
        lower = text.lower()

        # --- Fast path: Show all policies (skip LLM) ---
        if lower in {"show all policies", "list all policies", "show me all policies"}:
            res = call_api("/policies")
            if not res.get("success"):
                return f"❌ Failed to load policies: {res.get('message','Unknown error')}"
            items = res["data"]
            if not items:
                return "ℹ️ No policies found."
            st.session_state["last_search_results"] = items  # remember for next action
            lines = [f"✅ Found {len(items)} policies.", "\n### 📋 All Policies\n"]
            for i, p in enumerate(items, 1):
                lines.append(f"**{i}. 📄 {p.get('name','Unnamed')}**")
                lines.append(f" - **Type:** {p.get('type','N/A')}  •  **Scope:** {p.get('scope','N/A')}")
                lines.append(f" - **Effective:** {p.get('effective_date','N/A')}")
                if p.get('expiry_date'):
                    lines.append(f" - **Expires:** {p.get('expiry_date')}")
                lines.append("")
            return "\n".join(lines)

        # --- If message looks like file operation and files are attached, upload to a policy ---
        looks_like_file_op = any(k in lower for k in ["file", "files", "document", "attach", "upload", "replace"])
        if looks_like_file_op and attached_files:
            # Try to grab a policy name after "to "
            policy_name = None
            if " to " in lower:
                policy_name = text.split(" to ", 1)[1].strip().strip("'\"")

            # If not found, use last single search result if available
            if not policy_name:
                last_results = st.session_state.get("last_search_results")
                if last_results and len(last_results) == 1:
                    policy_name = last_results[0].get("name")

            if not policy_name:
                return "❌ Please mention the policy name, e.g., “Add this file to **Customer Refund Policy**”."

            # Find policy by name (case-insensitive)
            all_res = call_api("/policies")
            if not all_res.get("success"):
                return f"❌ Could not fetch policies: {all_res.get('message','unknown error')}"
            all_policies = all_res["data"]
            matches = [p for p in all_policies if (p.get("name","").strip().lower() == policy_name.strip().lower())]

            if len(matches) == 0:
                return f"❌ Policy '{policy_name}' not found. Try **Show all policies** and copy the exact name."
            if len(matches) > 1:
                opts = "\n".join([f"- {p['name']} (id: `{p['id']}`)" for p in matches])
                return f"⚠️ Multiple '{policy_name}'. Please specify the **ID** next time:\n{opts}"

            target = matches[0]
            files_param = [
                ("files", (uf.name, uf.getvalue(), (uf.type or "application/octet-stream")))
                for uf in attached_files
            ]
            # Upload to backend
            upload = requests.post(f"{API_BASE_URL}/policies/{target['id']}/files", files=files_param, timeout=60)
            if upload.status_code in (200, 201):
                return f"✅ Uploaded {len(attached_files)} file(s) to **{target['name']}**."
            return f"❌ Failed to upload files: {upload.text}"

        # --- Regular chat: let LLM handle add/update/search/stats text ---
        chat_response = requests.post(f"{API_BASE_URL}/chat", json={"message": text}, timeout=30)
        if chat_response.status_code != 200:
            return f"❌ Chat service error: {chat_response.status_code}"
        chat_result = chat_response.json()
        ai_response = chat_result.get("response", "No response received")
        data = chat_result.get("data", {}) or {}
        action = data.get("action")

        # Create policy via API if LLM extracted fields (and include attached files if any)
        if action == "add":
            extracted = data.get("extracted_data", {}) or {}
            name = extracted.get("name")
            ptype = extracted.get("type")
            if not name or not ptype:
                return ai_response

            payload = {
                "name": name,
                "type": ptype,
                "scope": extracted.get("scope") or "All Employees",
                "description": extracted.get("description") or f"Auto-created {ptype} policy: {name}",
                "effective_date": extracted.get("effective_date") or date.today().isoformat(),
            }
            if extracted.get("expiry_date"):
                payload["expiry_date"] = extracted["expiry_date"]

            files_param = None
            if attached_files:
                files_param = [
                    ("files", (uf.name, uf.getvalue(), (uf.type or "application/octet-stream")))
                    for uf in attached_files
                ]
            create_res = call_api("/policies", method="POST", data=payload, files=files_param)
            if create_res["success"]:
                return (
                    "✅ **Successfully created policy via chat!**\n\n"
                    f"**Name:** {name}  •  **Type:** {ptype}  •  **Scope:** {payload['scope']}\n"
                    f"**Effective:** {payload['effective_date']}\n\n"
                    f"*AI:* {ai_response}"
                )
            return f"❌ Create failed: {create_res.get('error','Unknown error')}"

        # Everything else: return what the LLM/agents produced (search/stats/update/delete guidance)
        # (If search returned results, you can stash them for next step here)
        if action == "search":
            results = data.get("results", [])
            st.session_state["last_search_results"] = results
        return ai_response

    except Exception as e:
        return f"❌ Chat error: {e}"



        
def display_policy_card(policy):
    """Display a policy in a card format"""
    with st.container():
        st.markdown(f"""
        <div class="policy-card">
            <h4>📄 {policy['name']}</h4>
            <p><strong>Type:</strong> {policy['type']} | <strong>Scope:</strong> {policy['scope']}</p>
            <p><strong>Description:</strong> {policy['description']}</p>
            <p><strong>Effective:</strong> {policy['effective_date']} | <strong>Expires:</strong> {policy.get('expiry_date', 'No expiry')}</p>
            <p><strong>Documents:</strong> {len(policy.get('documents', []))} files</p>
        </div>
        """, unsafe_allow_html=True)

def main():
    # Main header
    st.markdown('<h1 class="main-header">📋 AI-Powered Policy Management System</h1>', unsafe_allow_html=True)
    
    # Sidebar navigation
    with st.sidebar:
        st.title("🧭 Navigation")
        page = st.selectbox(
            "Choose a page:",
            [
                "🤖 AI Chat Assistant", 
                "📋 All Policies", 
                "➕ Add Policy", 
                "🔍 Search Policies", 
                "📊 Statistics"
            ]
        )
        
        st.markdown("---")
        
        # Quick system info
        try:
            api_test = call_api("/", timeout=3)
            if api_test["success"]:
                st.success("✅ API Connected")
                api_data = api_test["data"]
                st.info(f"**Version:** {api_data.get('version', 'Unknown')}")
            else:
                st.error("❌ API Offline")
        except:
            st.error("❌ API Offline")
        
        # Quick stats
        try:
            stats_result = call_api("/stats", timeout=5)
            if stats_result["success"]:
                stats = stats_result["data"]
                st.metric("Total Policies", stats.get('total_policies', 0))
                st.metric("Active Policies", stats.get('active_policies', 0))
        except:
            pass
    
    # Page routing
    if page == "🤖 AI Chat Assistant":
        chat_assistant_page()
    elif page == "📋 All Policies":
        all_policies_page()
    elif page == "➕ Add Policy":
        add_policy_page()
    elif page == "🔍 Search Policies":
        search_policies_page()
    elif page == "📊 Statistics":
        statistics_page()

def chat_assistant_page():
    st.header("🤖 AI Policy Assistant")
    st.write("💬 Chat with your AI assistant to manage policies using natural language.")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "👋 Hello! I'm your AI Policy Assistant. I can help you:\n\n• 📋 **View policies**: 'Show me all HR policies'\n• ➕ **Create policies**: 'Add a new IT policy called Security Guidelines'\n• 🔍 **Search policies**: 'Find policies about remote work'\n• ✏️ **Update policies**: 'Update the leave policy'\n• 📊 **Get statistics**: 'Show me policy statistics'\n\n**Try saying**: *'Add a new HR policy called Test Policy for All Employees about remote work guidelines'*"
            }
        ]
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    # Allow attaching files to be used by chat "Add/Update" flows
    attached_files = st.file_uploader(
        "Attach documents (optional)",
        accept_multiple_files=True,
        type=['pdf', 'doc', 'docx', 'txt']
    )

    # Chat input
    if prompt := st.chat_input("Type your message... (e.g., 'Add a new HR policy called Test Policy')"):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("🤖 Processing your request..."):
                response = enhanced_chat_with_ai(prompt, attached_files=attached_files)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Quick action buttons
    st.subheader("🚀 Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📋 Show All Policies", key="quick_all"):
            prompt = "Show me all policies"
            response = enhanced_chat_with_ai(prompt, attached_files=attached_files)
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
    
    with col2:
        if st.button("➕ Create Test Policy", key="quick_create"):
            prompt = "Add a new HR policy called 'Quick Test Policy' for All Employees about testing the system"
            response = enhanced_chat_with_ai(prompt, attached_files=attached_files)
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
    
    with col3:
        if st.button("🏢 HR Policies", key="quick_hr"):
            prompt = "Show me all HR policies"
            response = enhanced_chat_with_ai(prompt, attached_files=attached_files)
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
    
    with col4:
        if st.button("📊 Statistics", key="quick_stats"):
            prompt = "Show me policy statistics"
            response = enhanced_chat_with_ai(prompt, attached_files=attached_files)
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
    
    # Example prompts
    with st.expander("💡 Example Commands"):
        st.markdown("""
        **Create Policies:**
        - "Add a new HR policy called 'Remote Work Guidelines' for All Employees"
        - "Create an IT policy about password security for IT Department"
        - "Add a Customer policy called 'Service Standards' for Customer Service Team"
        
        **View Policies:**
        - "Show me all policies"
        - "List all HR policies" 
        - "Find policies about security"
        
        **Get Information:**
        - "How many policies do we have?"
        - "Show me expired policies"
        - "What's the system status?"
        """)

def all_policies_page():
    st.header("📋 All Policies")
    
    # Get all policies
    with st.spinner("📥 Loading policies..."):
        result = call_api("/policies")
    
    if result["success"]:
        policies = result["data"]
        st.success(f"✅ Found {len(policies)} policies")
        
        # Display policies
        for i, policy in enumerate(policies):
            display_policy_card(policy)
            
            # Action buttons
            # Action buttons
            col1, col2, col3 = st.columns(3)
 
            with col1:
                if st.button(f"👁️ View Details", key=f"view_{i}"):
                    with st.expander(f"📄 {policy['name']} - Details", expanded=True):
                        st.json(policy)
 
            with col2:
    # ✅ Implement Edit (guide to chat)
                if st.button(f"✏️ Edit", key=f"edit_{i}"):
                    st.warning(f"Edit functionality for '{policy['name']}' is not fully implemented yet.")
                    st.info("💡 Use the Chat Assistant: 'Update [Policy Name] [field] to [new value]'")
 
            with col3:
    # ✅ Implement Delete
                if st.button(f"🗑️ Delete", key=f"delete_{i}", type="secondary"):
        # Show confirmation
                    if st.button(f"⚠️ Confirm Delete '{policy['name']}'", key=f"confirm_delete_{i}"):
                        with st.spinner("🗑️ Deleting policy..."):
                            delete_result = call_api(f"/policies/{policy['id']}", method="DELETE")
                            if delete_result["success"]:
                                st.success(f"✅ Deleted '{policy['name']}'")
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to delete: {delete_result.get('message', 'Unknown error')}")
 

def add_policy_page():
    """
    Streamlit page: Add New Policy
    - Sends form fields as multipart/form-data to POST /policies
    - Supports multiple file uploads
    - Enforces valid types (HR, IT, Leave, Customer) to match backend & Cosmos PK
    """
    st.header("➕ Add New Policy")
    st.write("Create a new policy with all required details and optional documents.")

    # --- Session state flags ---
    if "policy_created" not in st.session_state:
        st.session_state.policy_created = False
    if "last_policy_name" not in st.session_state:
        st.session_state.last_policy_name = ""

    # --- Client-side config ---
    ALLOWED_TYPES = ["HR", "IT", "Leave", "Customer"]
    ALLOWED_FILE_TYPES = ['pdf', 'doc', 'docx', 'txt']
    MAX_TOTAL_UPLOAD_MB = 25  # safety limit for combined uploads

    # Small helper: total size of uploaded files
    def _total_upload_size(files) -> int:
        try:
            return sum(len(f.getvalue()) for f in files) if files else 0
        except Exception:
            # Fallback if getvalue not available
            return 0

    with st.form("add_policy_form", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input(
                "Policy Name *",
                placeholder="e.g., Remote Work Policy"
            )
            type_option = st.selectbox(
                "Policy Type *", ALLOWED_TYPES, index=0, help="Required. Matches DB partition key."
            )
            scope = st.text_input(
                "Scope *",
                placeholder="e.g., All Employees",
                value="All Employees"
            )

        with col2:
            effective_date = st.date_input(
                "Effective Date *", value=date.today(),
                help="Stored as YYYY-MM-DD"
            )
            no_expiry = st.checkbox("No expiry", value=True)
            expiry_date = None
            if not no_expiry:
                expiry_date = st.date_input("Expiry Date", value=date.today())

        description = st.text_area(
            "Description *",
            placeholder="Detailed policy description...",
            height=120
        )

        uploaded_files = st.file_uploader(
            "Upload Documents (Optional)",
            accept_multiple_files=True,
            type=ALLOWED_FILE_TYPES,
            help=f"Accepted: {', '.join(ALLOWED_FILE_TYPES)}"
        )

        # Optional duplicate check toggle
        colc1, colc2 = st.columns([1, 2])
        with colc1:
            run_dup_check = st.checkbox("Check duplicate name", value=True)
        with colc2:
            st.caption("If enabled, we'll warn if a policy with the same name already exists.")

        submitted = st.form_submit_button("🚀 Create Policy", type="primary")

    # --- Handle submit ---
    if submitted:
        # --- Client-side validations ---
        errors = []
        if not name or not name.strip():
            errors.append("Policy Name is required.")
        if type_option not in ALLOWED_TYPES:
            errors.append(f"Policy Type must be one of: {', '.join(ALLOWED_TYPES)}.")
        if not scope or not scope.strip():
            errors.append("Scope is required.")
        if not description or not description.strip():
            errors.append("Description is required.")
        # File validations
        if uploaded_files:
            total_size = _total_upload_size(uploaded_files)
            if total_size > MAX_TOTAL_UPLOAD_MB * 1024 * 1024:
                errors.append(f"Total upload size exceeds {MAX_TOTAL_UPLOAD_MB} MB.")
        if errors:
            st.error("❌ Please fix the following:")
            for e in errors:
                st.write(f"- {e}")
            return

        # Optional: duplicate name pre-check (case-insensitive)
        if run_dup_check:
            with st.spinner("🔎 Checking for duplicate policy names..."):
                all_res = call_api("/policies")
                if all_res.get("success"):
                    existing = all_res["data"]
                    dup = next((p for p in existing if p.get("name", "").strip().lower() == name.strip().lower()), None)
                    if dup:
                        st.warning(
                            f"⚠️ A policy with the name **{name.strip()}** already exists "
                            f"(ID: `{dup.get('id', 'unknown')}`, Type: `{dup.get('type', 'N/A')}`).\n\n"
                            f"You can still proceed, but consider using a unique name."
                        )

        # Prepare form data
        policy_data = {
            "name": name.strip(),
            "type": type_option,                      # must match Cosmos partition key
            "scope": scope.strip(),
            "description": description.strip(),
            "effective_date": effective_date.isoformat(),  # YYYY-MM-DD
        }
        if expiry_date:
            policy_data["expiry_date"] = expiry_date.isoformat()  # YYYY-MM-DD

        # Show what we will send
        with st.expander("🔍 Payload Preview (form fields)", expanded=False):
            st.json(policy_data)

        # Build multipart for files if any
        files_param = None
        if uploaded_files:
            files_param = [
                ("files", (uf.name, uf.getvalue(), (uf.type or "application/octet-stream")))
                for uf in uploaded_files
            ]

        # Create policy via API
        with st.spinner("🔄 Creating policy..."):
            result = call_api("/policies", method="POST", data=policy_data, files=files_param)

        # Handle response
        if result.get("success"):
            payload = result.get("data", {})
            # Normalize message
            msg = (
                payload.get("message")
                or f"Policy '{policy_data['name']}' created successfully."
            )
            st.success(f"✅ {msg}")

            # Show details
            with st.expander("📄 Created Policy (API Response)", expanded=True):
                st.json(payload)

            # Set flags and show next-step buttons
            st.session_state.policy_created = True
            st.session_state.last_policy_name = policy_data["name"]

            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("🔁 Create Another Policy"):
                    st.session_state.policy_created = False
                    st.experimental_rerun()
            with c2:
                if st.button("📋 View All Policies"):
                    # If you use a page router variable, set it; otherwise inform the user
                    st.info("Open the **All Policies** page from the sidebar to refresh the list.")
            with c3:
                if st.button("💬 Open Chat Assistant"):
                    st.info("Go to **AI Chat Assistant** from the sidebar.")

        else:
            status = result.get("status_code", "Unknown")
            api_err = result.get("error", "Unknown error")
            st.error(f"❌ Failed to create policy (HTTP {status})")
            with st.expander("🧾 Error Details", expanded=True):
                st.write(api_err)

            # Friendly hints
            if status == 422:
                st.info("Tip: One or more required fields may be missing or invalid.")
            elif status == 500:
                st.info("Tip: Server error. Check FastAPI logs for the full traceback.")
            else:
                st.info("Tip: Verify API_BASE_URL and that the backend is running.")

 

def search_policies_page():
    st.header("🔍 Search Policies")
    
    search_query = st.text_input("Search policies:", placeholder="Enter policy name, type, or keywords...")
    
    if st.button("🔍 Search") or search_query:
        if search_query:
            with st.spinner("🔍 Searching..."):
                # Get ALL policies and filter locally (most reliable)
                all_policies_result = call_api("/policies")
                
                if all_policies_result["success"]:
                    all_policies = all_policies_result["data"]
                    
                    # ✅ CASE-INSENSITIVE SEARCH
                    query_lower = search_query.lower()
                    policies = [
                        p for p in all_policies
                        if query_lower in p.get('name', '').lower() or
                           query_lower in p.get('description', '').lower() or
                           query_lower in p.get('type', '').lower() or
                           query_lower in p.get('scope', '').lower()
                    ]
                    
                    if policies:
                        st.success(f"✅ Found {len(policies)} matching policies")
                        for policy in policies:
                            display_policy_card(policy)
                    else:
                        st.info("ℹ️ No policies found matching your search.")
                else:
                    st.error(f"❌ Failed to load policies: {all_policies_result.get('message', 'Unknown error')}")
        else:
            st.info("ℹ️ Enter a search term to find policies.")

def statistics_page():
    st.header("📊 System Statistics")
    
    with st.spinner("📈 Loading statistics..."):
        stats_result = call_api("/stats")
    
    if stats_result["success"]:
        stats = stats_result["data"]
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <h2>{stats.get('total_policies', 0)}</h2>
                <p>📋 Total Policies</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <h2>{stats.get('active_policies', 0)}</h2>
                <p>✅ Active</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="stat-card">
                <h2>{stats.get('expired_policies', 0)}</h2>
                <p>⚠️ Expired</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            policy_types = stats.get('policy_types', {})
            st.markdown(f"""
            <div class="stat-card">
                <h2>{len(policy_types)}</h2>
                <p>🏷️ Types</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Policy types breakdown
        if policy_types:
            st.subheader("📊 Policies by Type")
            
            # Create DataFrame
            type_df = pd.DataFrame(
                list(policy_types.items()),
                columns=['Type', 'Count']
            )
            
            col1, col2 = st.columns(2)
            with col1:
                st.dataframe(type_df, use_container_width=True)
            with col2:
                st.bar_chart(type_df.set_index('Type'))
        
        # System info
        st.subheader("ℹ️ System Information")
        st.info(f"**Last Updated:** {stats.get('timestamp', 'Unknown')}")
        st.info(f"**API Status:** ✅ Online")
        
    else:
        st.error(f"❌ Failed to load statistics: {stats_result['message']}")

if __name__ == "__main__":
    main()
