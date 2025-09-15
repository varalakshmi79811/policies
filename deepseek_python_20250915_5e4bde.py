import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime, date
import traceback
import os

# Configure Streamlit page
st.set_page_config(
    page_title="Policy Management System",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API base URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

# Custom CSS for clean, structured interface
st.markdown("""
<style>
    .main-header {
        font-size: 28px;
        color: #2c3e50;
        font-weight: 600;
        margin-bottom: 20px;
        padding-bottom: 15px;
        border-bottom: 2px solid #e9ecef;
    }
    
    .section-header {
        font-size: 20px;
        color: #2c3e50;
        font-weight: 600;
        margin: 25px 0 15px 0;
        padding-bottom: 10px;
        border-bottom: 1px solid #e9ecef;
    }
    
    .card {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        border: 1px solid #e9ecef;
    }
    
    .stat-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 8px;
        border-left: 4px solid #3498db;
        margin: 10px 0;
    }
    
    .nav-item {
        padding: 12px 15px;
        border-radius: 6px;
        margin: 5px 0;
        font-weight: 500;
        color: #495057;
        transition: all 0.2s;
    }
    
    .nav-item:hover {
        background-color: #e9ecef;
        color: #2c3e50;
    }
    
    .nav-item.active {
        background-color: #e3f2fd;
        color: #1565c0;
        border-left: 4px solid #1565c0;
    }
    
    .button-primary {
        background-color: #1976d2;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 6px;
        font-weight: 500;
    }
    
    .button-secondary {
        background-color: #f8f9fa;
        color: #495057;
        border: 1px solid #dee2e6;
        padding: 10px 20px;
        border-radius: 6px;
        font-weight: 500;
    }
    
    .policy-name {
        font-size: 18px;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 8px;
    }
    
    .policy-detail {
        color: #6c757d;
        margin: 5px 0;
        font-size: 14px;
    }
    
    .quick-action {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s;
        border: 1px solid #e9ecef;
    }
    
    .quick-action:hover {
        background-color: #e9ecef;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .chat-message {
        padding: 15px;
        margin: 10px 0;
        border-radius: 8px;
        background-color: #f8f9fa;
        border-left: 4px solid #e9ecef;
    }
    
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #1976d2;
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
                if files:
                    response = requests.post(url, data=data or {}, files=files, timeout=timeout)
                else:
                    response = requests.post(url, data=data or {}, timeout=timeout)
            else:
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
    try:
        text = (user_input or "").strip()
        lower = text.lower()

        if lower in {"show all policies", "list all policies", "show me all policies"}:
            res = call_api("/policies")
            if not res.get("success"):
                return f"Failed to load policies: {res.get('message','Unknown error')}"
            items = res["data"]
            if not items:
                return "No policies found."
            st.session_state["last_search_results"] = items
            lines = [f"Found {len(items)} policies.", "\n## All Policies\n"]
            for i, p in enumerate(items, 1):
                lines.append(f"**{i}. {p.get('name','Unnamed')}**")
                lines.append(f"- Type: {p.get('type','N/A')} | Scope: {p.get('scope','N/A')}")
                lines.append(f"- Effective: {p.get('effective_date','N/A')}")
                if p.get('expiry_date'):
                    lines.append(f"- Expires: {p.get('expiry_date')}")
                lines.append("")
            return "\n".join(lines)

        looks_like_file_op = any(k in lower for k in ["file", "files", "document", "attach", "upload", "replace"])
        if looks_like_file_op and attached_files:
            policy_name = None
            if " to " in lower:
                policy_name = text.split(" to ", 1)[1].strip().strip("'\"")
                
            if not policy_name:
                last_results = st.session_state.get("last_search_results")
                if last_results and len(last_results) == 1:
                    policy_name = last_results[0].get("name")

            if not policy_name:
                return "Please mention the policy name, e.g., 'Add this file to Customer Refund Policy'."

            all_res = call_api("/policies")
            if not all_res.get("success"):
                return f"Could not fetch policies: {all_res.get('message','unknown error')}"
            all_policies = all_res["data"]
            matches = [p for p in all_policies if (p.get("name","").strip().lower() == policy_name.strip().lower())]

            if len(matches) == 0:
                return f"Policy '{policy_name}' not found. Try 'Show all policies' and copy the exact name."
            if len(matches) > 1:
                opts = "\n".join([f"- {p['name']} (id: {p['id']})" for p in matches])
                return f"Multiple '{policy_name}'. Please specify the ID next time:\n{opts}"

            target = matches[0]
            files_param = [
                ("files", (uf.name, uf.getvalue(), (uf.type or "application/octet-stream")))
                for uf in attached_files
            ]
            upload = requests.post(f"{API_BASE_URL}/policies/{target['id']}/files", files=files_param, timeout=60)
            if upload.status_code in (200, 201):
                return f"Uploaded {len(attached_files)} file(s) to {target['name']}."
            return f"Failed to upload files: {upload.text}"

        chat_response = requests.post(f"{API_BASE_URL}/chat", json={"message": text}, timeout=30)
        if chat_response.status_code != 200:
            return f"Chat service error: {chat_response.status_code}"
        chat_result = chat_response.json()
        ai_response = chat_result.get("response", "No response received")
        data = chat_result.get("data", {}) or {}
        action = data.get("action")

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
                    "Successfully created policy via chat\n\n"
                    f"**Name:** {name} | **Type:** {ptype} | **Scope:** {payload['scope']}\n"
                    f"**Effective:** {payload['effective_date']}\n\n"
                    f"{ai_response}"
                )
            return f"Create failed: {create_res.get('error','Unknown error')}"

        if action == "search":
            results = data.get("results", [])
            st.session_state["last_search_results"] = results
        return ai_response

    except Exception as e:
        return f"Chat error: {e}"

def display_policy_card(policy):
    with st.container():
        st.markdown(f"""
        <div class="card">
            <div class="policy-name">{policy['name']}</div>
            <div class="policy-detail"><strong>Type:</strong> {policy['type']} | <strong>Scope:</strong> {policy['scope']}</div>
            <div class="policy-detail"><strong>Description:</strong> {policy['description']}</div>
            <div class="policy-detail"><strong>Effective:</strong> {policy['effective_date']} | <strong>Expires:</strong> {policy.get('expiry_date', 'No expiry')}</div>
            <div class="policy-detail"><strong>Documents:</strong> {len(policy.get('documents', []))} files</div>
        </div>
        """, unsafe_allow_html=True)

def main():
    st.markdown('<div class="main-header">Policy Management System</div>', unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("""
        <div style="padding: 15px 0; border-bottom: 1px solid #e9ecef; margin-bottom: 15px;">
            <div style="font-size: 18px; font-weight: 600; color: #2c3e50;">Navigation</div>
        </div>
        """, unsafe_allow_html=True)
        
        pages = [
            "AI Assistant", 
            "All Policies", 
            "Add Policy", 
            "Search Policies", 
            "Statistics"
        ]
        
        for i, page in enumerate(pages):
            is_active = st.session_state.get('current_page', 'AI Assistant') == page
            active_class = "active" if is_active else ""
            if st.button(page, key=f"nav_{i}", use_container_width=True):
                st.session_state.current_page = page
                st.rerun()
        
        st.markdown("---")
        
        # System status
        st.markdown("""
        <div style="font-size: 16px; font-weight: 600; color: #2c3e50; margin-bottom: 10px;">
            System Status
        </div>
        """, unsafe_allow_html=True)
        
        try:
            api_test = call_api("/", timeout=3)
            if api_test["success"]:
                st.success("API Connected", icon="✅")
                api_data = api_test["data"]
                st.caption(f"Version: {api_data.get('version', 'Unknown')}")
            else:
                st.error("API Offline", icon="❌")
        except:
            st.error("API Offline", icon="❌")
        
        try:
            stats_result = call_api("/stats", timeout=5)
            if stats_result["success"]:
                stats = stats_result["data"]
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Policies", stats.get('total_policies', 0))
                with col2:
                    st.metric("Active Policies", stats.get('active_policies', 0))
        except:
            pass
    
    # Page routing
    current_page = st.session_state.get('current_page', 'AI Assistant')
    
    if current_page == "AI Assistant":
        chat_assistant_page()
    elif current_page == "All Policies":
        all_policies_page()
    elif current_page == "Add Policy":
        add_policy_page()
    elif current_page == "Search Policies":
        search_policies_page()
    elif current_page == "Statistics":
        statistics_page()

def chat_assistant_page():
    st.markdown('<div class="section-header">AI Policy Assistant</div>', unsafe_allow_html=True)
    st.write("Chat with your AI assistant to manage policies using natural language.")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hello! I'm your AI Policy Assistant. I can help you:\n\n• View policies: 'Show me all HR policies'\n• Create policies: 'Add a new IT policy called Security Guidelines'\n• Search policies: 'Find policies about remote work'\n• Update policies: 'Update the leave policy'\n• Get statistics: 'Show me policy statistics'\n\nTry saying: 'Add a new HR policy called Test Policy for All Employees about remote work guidelines'"
            }
        ]
    
    # Display chat messages
    for message in st.session_state.messages:
        message_class = "user-message" if message["role"] == "user" else ""
        st.markdown(f"""
        <div class="chat-message {message_class}">
            {message["content"]}
        </div>
        """, unsafe_allow_html=True)
            
    attached_files = st.file_uploader(
        "Attach documents (optional)",
        accept_multiple_files=True,
        type=['pdf', 'doc', 'docx', 'txt']
    )

    # Chat input
    if prompt := st.chat_input("Type your message..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.spinner("Processing your request..."):
            response = enhanced_chat_with_ai(prompt, attached_files=attached_files)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
    
    st.markdown("---")
    st.markdown('<div class="section-header">Quick Actions</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    action_buttons = [
        ("Show All Policies", "Show me all policies"),
        ("Create Test Policy", "Add a new HR policy called 'Quick Test Policy' for All Employees about testing the system"),
        ("HR Policies", "Show me all HR policies"),
        ("Statistics", "Show me policy statistics")
    ]
    
    for i, (label, command) in enumerate(action_buttons):
        with [col1, col2, col3, col4][i]:
            if st.button(label, key=f"quick_{i}", use_container_width=True):
                response = enhanced_chat_with_ai(command, attached_files=attached_files)
                st.session_state.messages.append({"role": "user", "content": command})
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()
    
    with st.expander("Example Commands"):
        st.markdown("""
        **Create Policies:**
        - Add a new HR policy called 'Remote Work Guidelines' for All Employees
        - Create an IT policy about password security for IT Department
        - Add a Customer policy called 'Service Standards' for Customer Service Team
        
        **View Policies:**
        - Show me all policies
        - List all HR policies 
        - Find policies about security
        
        **Get Information:**
        - How many policies do we have?
        - Show me expired policies
        - What's the system status?
        """)

def all_policies_page():
    st.markdown('<div class="section-header">All Policies</div>', unsafe_allow_html=True)
    
    with st.spinner("Loading policies..."):
        result = call_api("/policies")
    
    if result["success"]:
        policies = result["data"]
        st.success(f"Found {len(policies)} policies")
        
        for i, policy in enumerate(policies):
            display_policy_card(policy)
            
            col1, col2, col3 = st.columns(3)
 
            with col1:
                if st.button("View Details", key=f"view_{i}", use_container_width=True):
                    with st.expander(f"{policy['name']} - Details", expanded=True):
                        st.json(policy)
 
            with col2:
                if st.button("Edit", key=f"edit_{i}", use_container_width=True):
                    st.warning(f"Edit functionality for '{policy['name']}' is not fully implemented yet.")
                    st.info("Use the Chat Assistant: 'Update [Policy Name] [field] to [new value]'")
 
            with col3:
                if st.button("Delete", key=f"delete_{i}", use_container_width=True, type="secondary"):
                    if st.button(f"Confirm Delete '{policy['name']}'", key=f"confirm_delete_{i}", use_container_width=True):
                        with st.spinner("Deleting policy..."):
                            delete_result = call_api(f"/policies/{policy['id']}", method="DELETE")
                            if delete_result["success"]:
                                st.success(f"Deleted '{policy['name']}'")
                                st.rerun()
                            else:
                                st.error(f"Failed to delete: {delete_result.get('message', 'Unknown error')}")

def add_policy_page():
    st.markdown('<div class="section-header">Add New Policy</div>', unsafe_allow_html=True)
    st.write("Create a new policy with all required details and optional documents.")

    if "policy_created" not in st.session_state:
        st.session_state.policy_created = False
    if "last_policy_name" not in st.session_state:
        st.session_state.last_policy_name = ""

    ALLOWED_TYPES = ["HR", "IT", "Leave", "Customer"]
    ALLOWED_FILE_TYPES = ['pdf', 'doc', 'docx', 'txt']
    MAX_TOTAL_UPLOAD_MB = 25

    def _total_upload_size(files) -> int:
        try:
            return sum(len(f.getvalue()) for f in files) if files else 0
        except Exception:
            return 0

    with st.form("add_policy_form", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input(
                "Policy Name *",
                placeholder="e.g., Remote Work Policy"
            )
            type_option = st.selectbox(
                "Policy Type *", ALLOWED_TYPES, index=0
            )
            scope = st.text_input(
                "Scope *",
                placeholder="e.g., All Employees",
                value="All Employees"
            )

        with col2:
            effective_date = st.date_input(
                "Effective Date *", value=date.today()
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
            type=ALLOWED_FILE_TYPES
        )

        colc1, colc2 = st.columns([1, 2])
        with colc1:
            run_dup_check = st.checkbox("Check duplicate name", value=True)

        submitted = st.form_submit_button("Create Policy", use_container_width=True, type="primary")

    if submitted:
        errors = []
        if not name or not name.strip():
            errors.append("Policy Name is required.")
        if type_option not in ALLOWED_TYPES:
            errors.append(f"Policy Type must be one of: {', '.join(ALLOWED_TYPES)}.")
        if not scope or not scope.strip():
            errors.append("Scope is required.")
        if not description or not description.strip():
            errors.append("Description is required.")
        if uploaded_files:
            total_size = _total_upload_size(uploaded_files)
            if total_size > MAX_TOTAL_UPLOAD_MB * 1024 * 1024:
                errors.append(f"Total upload size exceeds {MAX_TOTAL_UPLOAD_MB} MB.")
        if errors:
            st.error("Please fix the following:")
            for e in errors:
                st.write(f"- {e}")
            return

        if run_dup_check:
            with st.spinner("Checking for duplicate policy names..."):
                all_res = call_api("/policies")
                if all_res.get("success"):
                    existing = all_res["data"]
                    dup = next((p for p in existing if p.get("name", "").strip().lower() == name.strip().lower()), None)
                    if dup:
                        st.warning(
                            f"A policy with the name {name.strip()} already exists "
                            f"(ID: {dup.get('id', 'unknown')}, Type: {dup.get('type', 'N/A')})."
                        )

        policy_data = {
            "name": name.strip(),
            "type": type_option,
            "scope": scope.strip(),
            "description": description.strip(),
            "effective_date": effective_date.isoformat(),
        }
        if expiry_date:
            policy_data["expiry_date"] = expiry_date.isoformat()

        files_param = None
        if uploaded_files:
            files_param = [
                ("files", (uf.name, uf.getvalue(), (uf.type or "application/octet-stream")))
                for uf in uploaded_files
            ]

        with st.spinner("Creating policy..."):
            result = call_api("/policies", method="POST", data=policy_data, files=files_param)

        if result.get("success"):
            payload = result.get("data", {})
            msg = (
                payload.get("message")
                or f"Policy '{policy_data['name']}' created successfully."
            )
            st.success(f"{msg}")

            st.session_state.policy_created = True
            st.session_state.last_policy_name = policy_data["name"]

            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("Create Another Policy", use_container_width=True):
                    st.session_state.policy_created = False
                    st.rerun()
            with c2:
                if st.button("View All Policies", use_container_width=True):
                    st.session_state.current_page = "All Policies"
                    st.rerun()
            with c3:
                if st.button("Open Chat Assistant", use_container_width=True):
                    st.session_state.current_page = "AI Assistant"
                    st.rerun()

        else:
            status = result.get("status_code", "Unknown")
            api_err = result.get("error", "Unknown error")
            st.error(f"Failed to create policy (HTTP {status})")
            with st.expander("Error Details", expanded=True):
                st.write(api_err)

            if status == 422:
                st.info("Tip: One or more required fields may be missing or invalid.")
            elif status == 500:
                st.info("Tip: Server error. Check FastAPI logs for the full traceback.")

def search_policies_page():
    st.markdown('<div class="section-header">Search Policies</div>', unsafe_allow_html=True)
    
    search_query = st.text_input("Search policies:", placeholder="Enter policy name, type, or keywords...")
    
    if st.button("Search", use_container_width=True) or search_query:
        if search_query:
            with st.spinner("Searching..."):
                all_policies_result = call_api("/policies")
                
                if all_policies_result["success"]:
                    all_policies = all_policies_result["data"]
                    
                    query_lower = search_query.lower()
                    policies = [
                        p for p in all_policies
                        if query_lower in p.get('name', '').lower() or
                           query_lower in p.get('description', '').lower() or
                           query_lower in p.get('type', '').lower() or
                           query_lower in p.get('scope', '').lower()
                    ]
                    
                    if policies:
                        st.success(f"Found {len(policies)} matching policies")
                        for policy in policies:
                            display_policy_card(policy)
                    else:
                        st.info("No policies found matching your search.")
                else:
                    st.error(f"Failed to load policies: {all_policies_result.get('message', 'Unknown error')}")
        else:
            st.info("Enter a search term to find policies.")

def statistics_page():
    st.markdown('<div class="section-header">System Statistics</div>', unsafe_allow_html=True)
    
    with st.spinner("Loading statistics..."):
        stats_result = call_api("/stats")
    
    if stats_result["success"]:
        stats = stats_result["data"]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <h3>{stats.get('total_policies', 0)}</h3>
                <p>Total Policies</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <h3>{stats.get('active_policies', 0)}</h3>
                <p>Active</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="stat-card">
                <h3>{stats.get('expired_policies', 0)}</h3>
                <p>Expired</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            policy_types = stats.get('policy_types', {})
            st.markdown(f"""
            <div class="stat-card">
                <h3>{len(policy_types)}</h3>
                <p>Types</p>
            </div>
            """, unsafe_allow_html=True)
        
        if policy_types:
            st.markdown("---")
            st.markdown('<div class="section-header">Policies by Type</div>', unsafe_allow_html=True)
            
            type_df = pd.DataFrame(
                list(policy_types.items()),
                columns=['Type', 'Count']
            )
            
            col1, col2 = st.columns(2)
            with col1:
                st.dataframe(type_df, use_container_width=True)
            with col2:
                st.bar_chart(type_df.set_index('Type'))
        
        st.markdown("---")
        st.markdown('<div class="section-header">System Information</div>', unsafe_allow_html=True)
        st.info(f"Last Updated: {stats.get('timestamp', 'Unknown')}")
        st.info("API Status: Online")
        
    else:
        st.error(f"Failed to load statistics: {stats_result['message']}")

if __name__ == "__main__":
    main()