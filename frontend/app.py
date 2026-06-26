import streamlit as st
import requests

# ── CONFIG ────────────────────────────────────────────────────────
API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="SQL Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── STYLES ────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Hide streamlit branding */
#MainMenu, footer, header {visibility: hidden;}

/* Main background */
.stApp { background-color: #0f1117; }

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #1a1d27;
    border-right: 1px solid #2d3148;
}
[data-testid="stSidebar"] * { color: #f1f5f9 !important; }

/* All text */
* { color: #f1f5f9; font-family: 'Inter', sans-serif; }

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background-color: #1a1d27 !important;
    border: 1px solid #2d3148 !important;
    color: #f1f5f9 !important;
    border-radius: 8px !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #6c63ff !important;
    box-shadow: 0 0 0 2px rgba(108,99,255,0.2) !important;
}

/* Select box */
.stSelectbox > div > div {
    background-color: #1a1d27 !important;
    border: 1px solid #2d3148 !important;
    border-radius: 8px !important;
    color: #f1f5f9 !important;
}

/* Buttons */
.stButton > button {
    background-color: #6c63ff !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.5rem 1.5rem !important;
    font-weight: 500 !important;
    width: 100% !important;
    transition: background 0.2s !important;
}
.stButton > button:hover {
    background-color: #8b85ff !important;
}

/* Secondary button style */
.secondary-btn > button {
    background-color: #22263a !important;
    color: #94a3b8 !important;
    border: 1px solid #2d3148 !important;
}
.secondary-btn > button:hover {
    background-color: #2d3148 !important;
    color: #f1f5f9 !important;
}

/* User message bubble */
.user-msg {
    background-color: #6c63ff;
    color: white !important;
    padding: 12px 16px;
    border-radius: 16px 16px 4px 16px;
    margin: 8px 0 8px 15%;
    font-size: 14px;
    line-height: 1.6;
}

/* Assistant message bubble */
.assistant-msg {
    background-color: #1a1d27;
    border: 1px solid #2d3148;
    padding: 12px 16px;
    border-radius: 16px 16px 16px 4px;
    margin: 8px 15% 8px 0;
    font-size: 14px;
    line-height: 1.6;
}

/* SQL code block */
.sql-block {
    background-color: #141720;
    border: 1px solid #2d3148;
    border-left: 3px solid #6c63ff;
    border-radius: 8px;
    padding: 16px;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 13px;
    color: #a9dc76 !important;
    margin: 12px 0;
    white-space: pre-wrap;
    word-break: break-word;
}

/* Explanation block */
.explanation-block {
    background-color: #22263a;
    border-left: 3px solid #22c55e;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    font-size: 13px;
    color: #94a3b8 !important;
    margin: 8px 0;
    line-height: 1.7;
}

/* Intent badge */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
}
.badge-generate { background: #2d1f5e; color: #a78bfa; }
.badge-explain  { background: #1e3a5f; color: #60a5fa; }
.badge-optimise { background: #3d2000; color: #fb923c; }
.badge-convert  { background: #052e2e; color: #2dd4bf; }
.badge-general  { background: #1f2937; color: #9ca3af; }

/* Schema card */
.schema-card {
    background-color: #22263a;
    border: 1px solid #2d3148;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 6px 0;
    cursor: pointer;
    transition: all 0.2s;
}
.schema-card:hover { border-color: #6c63ff; }
.schema-card.active {
    border-left: 3px solid #6c63ff;
    background-color: #2d1f5e22;
}
.schema-name { font-weight: 600; font-size: 14px; }
.schema-platform {
    font-size: 11px;
    color: #94a3b8;
    margin-top: 2px;
}

/* Platform colors */
.platform-postgresql { color: #60a5fa; }
.platform-mysql      { color: #fb923c; }
.platform-sqlite     { color: #4ade80; }
.platform-sqlserver  { color: #f87171; }

/* Divider */
.divider {
    border: none;
    border-top: 1px solid #2d3148;
    margin: 16px 0;
}

/* Empty state */
.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: #4b5563;
}
.empty-state h3 { font-size: 18px; color: #6b7280; margin-bottom: 8px; }
.empty-state p  { font-size: 14px; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background-color: #1a1d27;
    border-radius: 8px;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    background-color: transparent !important;
    color: #94a3b8 !important;
    border-radius: 6px !important;
}
.stTabs [aria-selected="true"] {
    background-color: #6c63ff !important;
    color: white !important;
}

/* Form label */
label { color: #94a3b8 !important; font-size: 13px !important; }

/* Success/error messages */
.stSuccess { background-color: #052e16 !important; }
.stError   { background-color: #3d0000 !important; }

/* Expander */
.streamlit-expanderHeader {
    background-color: #1a1d27 !important;
    border: 1px solid #2d3148 !important;
    border-radius: 8px !important;
    color: #94a3b8 !important;
}
</style>
""", unsafe_allow_html=True)


# ── SESSION STATE ─────────────────────────────────────────────────
def init_session():
    defaults = {
        "token": None,
        "user": None,
        "schemas": [],
        "active_schema": None,
        "messages": [],
        "page": "login"
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_session()


# ── API HELPERS ───────────────────────────────────────────────────
def api_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}

def api_post(endpoint, data=None, form=False):
    try:
        if form:
            r = requests.post(f"{API_URL}{endpoint}", data=data)
        else:
            r = requests.post(
                f"{API_URL}{endpoint}",
                json=data,
                headers=api_headers()
            )
        return r.json(), r.status_code
    except Exception as e:
        return {"detail": str(e)}, 500

def api_get(endpoint):
    try:
        r = requests.get(f"{API_URL}{endpoint}", headers=api_headers())
        return r.json(), r.status_code
    except Exception as e:
        return {"detail": str(e)}, 500

def api_patch(endpoint, data=None):
    try:
        r = requests.patch(
            f"{API_URL}{endpoint}",
            json=data,
            headers=api_headers()
        )
        return r.json(), r.status_code
    except Exception as e:
        return {"detail": str(e)}, 500

def api_delete(endpoint):
    try:
        r = requests.delete(f"{API_URL}{endpoint}", headers=api_headers())
        return r.status_code
    except Exception as e:
        return 500


# ── AUTH PAGES ────────────────────────────────────────────────────
def login_page():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("## ⚡ SQL Assistant")
        st.markdown(
            "<p style='color:#94a3b8;margin-bottom:32px;'>"
            "Your AI-powered database companion</p>",
            unsafe_allow_html=True
        )

        tab_login, tab_register = st.tabs(["Sign in", "Create account"])

        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)
            email = st.text_input("Email", key="login_email",
                                  placeholder="you@example.com")
            password = st.text_input("Password", type="password",
                                     key="login_password",
                                     placeholder="••••••••")
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Sign in", key="login_btn"):
                if email and password:
                    data, status = api_post(
                        "/auth/login",
                        {"username": email, "password": password},
                        form=True
                    )
                    if status == 200:
                        st.session_state.token = data["access_token"]
                        st.session_state.user = data["user"]
                        st.session_state.page = "app"
                        st.rerun()
                    else:
                        st.error(data.get("detail", "Login failed."))
                else:
                    st.warning("Please enter email and password.")

        with tab_register:
            st.markdown("<br>", unsafe_allow_html=True)
            full_name = st.text_input("Full name", key="reg_name",
                                      placeholder="Het Patel")
            reg_email = st.text_input("Email", key="reg_email",
                                      placeholder="you@example.com")
            reg_password = st.text_input("Password", type="password",
                                         key="reg_password",
                                         placeholder="Min 6 characters")
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Create account", key="register_btn"):
                if reg_email and reg_password and full_name:
                    data, status = api_post("/auth/register", {
                        "email": reg_email,
                        "password": reg_password,
                        "full_name": full_name
                    })
                    if status == 201:
                        st.success("Account created! Please sign in.")
                    else:
                        st.error(data.get("detail", "Registration failed."))
                else:
                    st.warning("Please fill all fields.")


# ── SIDEBAR ───────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        # User info
        user = st.session_state.user
        st.markdown(
            f"<p style='font-size:13px;color:#94a3b8;margin:0;'>Signed in as</p>"
            f"<p style='font-weight:600;margin:2px 0 16px;'>"
            f"{user.get('full_name') or user.get('email')}</p>",
            unsafe_allow_html=True
        )

        st.markdown('<hr class="divider">', unsafe_allow_html=True)

        # New schema button
        if st.button("+ Add Schema", key="add_schema_btn"):
            st.session_state.page = "add_schema"
            st.rerun()

        st.markdown(
            "<p style='font-size:11px;color:#4b5563;"
            "letter-spacing:1px;text-transform:uppercase;"
            "margin:16px 0 8px;'>My Schemas</p>",
            unsafe_allow_html=True
        )

        # Load schemas
        schemas, status = api_get("/schemas/")
        if status == 200:
            st.session_state.schemas = schemas
            if schemas:
                for schema in schemas:
                    is_active = schema.get("is_active", False)
                    platform = schema.get("platform", "")
                    card_class = "schema-card active" if is_active else "schema-card"
                    active_indicator = "⚡ " if is_active else ""

                    platform_colors = {
                        "postgresql": "#60a5fa",
                        "mysql": "#fb923c",
                        "sqlite": "#4ade80",
                        "sqlserver": "#f87171"
                    }
                    p_color = platform_colors.get(platform, "#94a3b8")

                    col_name, col_action = st.columns([4, 1])
                    with col_name:
                        st.markdown(
                            f"""<div class="{card_class}">
                                <div class="schema-name">
                                    {active_indicator}{schema['name']}
                                </div>
                                <div class="schema-platform" 
                                     style="color:{p_color}">
                                    {platform.upper()}
                                </div>
                            </div>""",
                            unsafe_allow_html=True
                        )
                    with col_action:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if not is_active:
                            if st.button("▶", key=f"activate_{schema['id']}",
                                        help="Activate this schema"):
                                api_patch(f"/schemas/{schema['id']}/activate")
                                st.session_state.messages = []
                                st.session_state.active_schema = schema
                                st.rerun()
                        else:
                            st.markdown(
                                "<span style='color:#6c63ff;font-size:18px;"
                                "padding-top:8px;display:block;'>✓</span>",
                                unsafe_allow_html=True
                            )
            else:
                st.markdown(
                    "<p style='color:#4b5563;font-size:13px;"
                    "text-align:center;padding:16px 0;'>"
                    "No schemas yet.<br>Add one to start.</p>",
                    unsafe_allow_html=True
                )

        st.markdown('<hr class="divider">', unsafe_allow_html=True)

        # Logout
        with st.container():
            st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
            if st.button("Sign out", key="logout_btn"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                init_session()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)


# ── ADD SCHEMA PAGE ───────────────────────────────────────────────
def add_schema_page():
    render_sidebar()

    st.markdown("## Add Schema")
    st.markdown(
        "<p style='color:#94a3b8;margin-bottom:24px;'>"
        "Connect your database or paste your schema DDL</p>",
        unsafe_allow_html=True
    )

    schema_name = st.text_input("Schema name",
                                 placeholder="e.g. ecommerce_db")
    platform = st.selectbox(
        "Platform",
        ["postgresql", "mysql", "sqlite", "sqlserver"],
        format_func=lambda x: {
            "postgresql": "PostgreSQL",
            "mysql": "MySQL",
            "sqlite": "SQLite",
            "sqlserver": "SQL Server"
        }[x]
    )

    tab_paste, tab_connect, tab_upload = st.tabs([
        "Paste DDL", "Connect Database", "Upload .sql"
    ])

    with tab_paste:
        st.markdown("<br>", unsafe_allow_html=True)
        ddl = st.text_area(
            "Paste your CREATE TABLE statements here",
            height=200,
            placeholder="CREATE TABLE users (\n    id SERIAL PRIMARY KEY,\n    ...);"
        )
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Save Schema", key="save_ddl"):
            if schema_name and ddl:
                data, status = api_post("/schemas/", {
                    "name": schema_name,
                    "platform": platform,
                    "schema_content": ddl,
                    "source": "manual"
                })
                if status == 201:
                    st.success(f"Schema '{schema_name}' saved successfully!")
                    st.session_state.page = "app"
                    st.rerun()
                else:
                    st.error(data.get("detail", "Failed to save schema."))
            else:
                st.warning("Please enter a schema name and DDL.")

    with tab_connect:
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            host = st.text_input("Host", value="localhost",
                                  key="mcp_host")
            database = st.text_input("Database name", key="mcp_db",
                                      placeholder="my_database")
            username = st.text_input("Username", key="mcp_user",
                                      placeholder="postgres")
        with col2:
            port_defaults = {
                "postgresql": 5432, "mysql": 3306,
                "sqlite": 0, "sqlserver": 1433
            }
            port = st.number_input("Port",
                                    value=port_defaults.get(platform, 5432),
                                    key="mcp_port")
            db_password = st.text_input("Password", type="password",
                                         key="mcp_password")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Connect & Extract Schema", key="mcp_connect"):
            if schema_name and database and username:
                with st.spinner("Connecting to database..."):
                    data, status = api_post("/mcp/connect", {
                        "name": schema_name,
                        "platform": platform,
                        "host": host,
                        "port": port,
                        "database": database,
                        "username": username,
                        "password": db_password
                    })
                if status == 201:
                    st.success("Connected and schema extracted successfully!")
                    st.session_state.page = "app"
                    st.rerun()
                else:
                    st.error(data.get("detail", "Connection failed."))
            else:
                st.warning("Please fill all required fields.")

    with tab_upload:
        st.markdown("<br>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Upload a .sql file",
            type=["sql"],
            help="Upload a .sql file containing your CREATE TABLE statements"
        )
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Upload & Save", key="upload_sql"):
            if schema_name and uploaded_file:
                files = {"file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    "text/plain"
                )}
                try:
                    r = requests.post(
                        f"{API_URL}/schemas/upload"
                        f"?name={schema_name}&platform={platform}",
                        files=files,
                        headers=api_headers()
                    )
                    data = r.json()
                    if r.status_code == 201:
                        st.success("Schema uploaded successfully!")
                        st.session_state.page = "app"
                        st.rerun()
                    else:
                        st.error(data.get("detail", "Upload failed."))
                except Exception as e:
                    st.error(str(e))
            else:
                st.warning("Please enter a schema name and upload a file.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
    if st.button("← Back to chat", key="back_btn"):
        st.session_state.page = "app"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ── CHAT PAGE ─────────────────────────────────────────────────────
def chat_page():
    render_sidebar()

    # Get active schema
    active_schema = None
    schemas = st.session_state.schemas
    for s in schemas:
        if s.get("is_active"):
            active_schema = s
            break

    # Top bar
    col_title, col_platform = st.columns([3, 1])
    with col_title:
        if active_schema:
            platform_colors = {
                "postgresql": "#60a5fa", "mysql": "#fb923c",
                "sqlite": "#4ade80",    "sqlserver": "#f87171"
            }
            p_color = platform_colors.get(
                active_schema.get("platform", ""), "#94a3b8"
            )
            st.markdown(
                f"<h3 style='margin:0;'>⚡ {active_schema['name']}"
                f"<span style='font-size:13px;color:{p_color};"
                f"margin-left:10px;font-weight:400;'>"
                f"{active_schema.get('platform','').upper()}</span></h3>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                "<h3 style='margin:0;color:#4b5563;'>"
                "No schema selected</h3>",
                unsafe_allow_html=True
            )

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # Empty state
    if not active_schema:
        st.markdown("""
        <div class="empty-state">
            <h3>No schema selected</h3>
            <p>Add a schema from the sidebar to start chatting</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Chat messages
    chat_container = st.container()
    with chat_container:
        if not st.session_state.messages:
            st.markdown(f"""
            <div class="empty-state">
                <h3>Start a conversation</h3>
                <p>Ask anything about your <strong
                   style="color:#f1f5f9">{active_schema['name']}</strong>
                   database</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    st.markdown(
                        f'<div class="user-msg">{msg["content"]}</div>',
                        unsafe_allow_html=True
                    )
                else:
                    # Intent badge
                    intent = msg.get("intent", "general")
                    badge_class = f"badge badge-{intent}"
                    st.markdown(
                        f'<span class="{badge_class}">{intent}</span>',
                        unsafe_allow_html=True
                    )

                    # SQL block if present
                    if msg.get("sql"):
                        st.markdown(
                            f'<div class="sql-block">{msg["sql"]}</div>',
                            unsafe_allow_html=True
                        )
                        # Copy button
                        col_copy, _ = st.columns([1, 4])
                        with col_copy:
                            if st.button("Copy SQL",
                                        key=f"copy_{id(msg)}"):
                                st.code(msg["sql"], language="sql")

                    # Explanation
                    if msg.get("content"):
                        with st.expander(
                            "Explanation", expanded=not msg.get("sql")
                        ):
                            st.markdown(
                                f'<div class="explanation-block">'
                                f'{msg["content"]}</div>',
                                unsafe_allow_html=True
                            )

    st.markdown("<br>", unsafe_allow_html=True)

    # Input area
    col_input, col_send = st.columns([5, 1])
    with col_input:
        user_input = st.text_input(
            "message",
            label_visibility="collapsed",
            placeholder="Ask anything about your database...",
            key="chat_input"
        )
    with col_send:
        send = st.button("Send ➤", key="send_btn")

    # Handle send
    if send and user_input.strip():
        # Add user message to state
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })

        # Call API
        with st.spinner("Thinking..."):
            data, status = api_post("/chat/", {
                "message": user_input,
                "schema_id": str(active_schema["id"])
            })

        if status == 200:
            st.session_state.messages.append({
                "role": "assistant",
                "content": data.get("explanation") or data.get("message", ""),
                "sql": data.get("sql_output"),
                "intent": data.get("intent", "general")
            })
        else:
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"Error: {data.get('detail', 'Something went wrong.')}",
                "sql": None,
                "intent": "general"
            })

        st.rerun()


# ── ROUTER ────────────────────────────────────────────────────────
if not st.session_state.token:
    login_page()
elif st.session_state.page == "add_schema":
    add_schema_page()
else:
    chat_page()