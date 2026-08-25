import streamlit as st
import pandas as pd
import json
import io
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# --- Page Config (Must be first) ---
st.set_page_config(page_title="CM360 Tags | Workspace", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

# --- API Config ---
SCOPES = ['https://www.googleapis.com/auth/dfatrafficking']
API_SERVICE_NAME = 'dfareporting'
API_VERSION = 'v5'

if "client_secrets" not in st.secrets:
    st.error("⚠️ Missing 'client_secrets' in Streamlit secrets configuration.")
    st.stop()

# --- Advanced SaaS CSS Injection ---
st.markdown("""
    <style>
    /* Import Inter Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Hide Default Streamlit UI */
    #MainMenu, header, footer {display: none !important;}
    section[data-testid="stSidebar"] {display: none !important;}
    
    /* Global Background */
    .stApp {
        background-color: #000000;
        color: #EDEDED;
        background-image: radial-gradient(circle at 50% 0%, #1a1a2e 0%, #000000 70%);
        background-attachment: fixed;
    }

    /* --- LOGIN PAGE STYLES --- */
    .login-wrapper {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin-top: 8vh;
    }
    
    .login-card {
        background: #0A0A0A;
        border: 1px solid #222222;
        border-radius: 16px;
        padding: 48px 40px;
        width: 100%;
        max-width: 440px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 1);
        text-align: center;
    }
    
    .login-logo {
        width: 48px;
        height: 48px;
        background: linear-gradient(135deg, #3B82F6, #8B5CF6);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        margin: 0 auto 24px auto;
    }
    
    .login-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #FFFFFF;
        margin-bottom: 8px;
    }
    
    .login-subtitle {
        font-size: 0.95rem;
        color: #A1A1AA;
        margin-bottom: 32px;
        line-height: 1.5;
    }

    /* Override Streamlit Buttons */
    .stButton>button {
        width: 100%;
        border-radius: 8px !important;
        font-weight: 500 !important;
        height: 44px;
        transition: all 0.2s ease;
    }
    
    button[kind="primary"] {
        background: #FFFFFF !important;
        color: #000000 !important;
        border: none !important;
    }
    button[kind="primary"]:hover {
        background: #E5E5E5 !important;
        transform: translateY(-1px);
    }

    button[kind="secondary"] {
        background: #111111 !important;
        color: #FFFFFF !important;
        border: 1px solid #333333 !important;
    }
    button[kind="secondary"]:hover {
        background: #1A1A1A !important;
        border-color: #444444 !important;
    }

    /* Input Fields */
    .stTextInput input {
        background-color: #0A0A0A !important;
        border: 1px solid #333333 !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
        font-size: 0.95rem !important;
    }
    .stTextInput input:focus {
        border-color: #3B82F6 !important;
        box-shadow: 0 0 0 1px #3B82F6 !important;
    }

    /* --- DASHBOARD STYLES --- */
    .top-nav {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 32px;
        border-bottom: 1px solid #1A1A1A;
        background: rgba(0,0,0,0.5);
        backdrop-filter: blur(10px);
        margin-bottom: 40px;
    }
    
    .nav-brand {
        font-size: 1.1rem;
        font-weight: 600;
        color: #FFFFFF;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .workspace-container {
        max-width: 900px;
        margin: 0 auto;
        padding: 0 24px;
    }
    
    .workspace-header {
        font-size: 2rem;
        font-weight: 600;
        color: #FFFFFF;
        margin-bottom: 8px;
        letter-spacing: -0.02em;
    }
    
    .workspace-sub {
        color: #A1A1AA;
        font-size: 1rem;
        margin-bottom: 32px;
    }

    /* File Uploader styling */
    [data-testid="stFileUploadDropzone"] {
        background-color: #0A0A0A !important;
        border: 1px dashed #333333 !important;
        border-radius: 12px !important;
        padding: 40px !important;
        transition: all 0.2s ease;
    }
    [data-testid="stFileUploadDropzone"]:hover {
        border-color: #444444 !important;
        background-color: #0F0F0F !important;
    }
    
    /* Metrics */
    div[data-testid="stMetric"] {
        background-color: #0A0A0A;
        border: 1px solid #222222;
        padding: 16px 20px;
        border-radius: 12px;
    }
    div[data-testid="stMetricLabel"] {
        color: #A1A1AA !important;
        font-weight: 500 !important;
    }
    div[data-testid="stMetricValue"] {
        color: #FFFFFF !important;
    }
    
    /* Dataframes */
    [data-testid="stDataFrame"] {
        border: 1px solid #222222;
        border-radius: 12px;
        overflow: hidden;
    }
    </style>
""", unsafe_allow_html=True)


# ==========================================
# 1. AUTHENTICATION & LOGIN VIEW
# ==========================================
def render_login_page():
    if 'oauth_flow' not in st.session_state:
        try:
            client_config = json.loads(st.secrets["client_secrets"])
            flow = InstalledAppFlow.from_client_config(
                client_config, 
                SCOPES, 
                redirect_uri='urn:ietf:wg:oauth:2.0:oob'
            )
            st.session_state.oauth_flow = flow
            auth_url, _ = flow.authorization_url(prompt='consent')
            st.session_state.auth_url = auth_url
        except Exception as e:
            st.error(f"Configuration Error: {e}")
            return None

    auth_url = st.session_state.auth_url

    # Centered column layout to act as a spacer
    _, col, _ = st.columns([1, 1.2, 1])
    
    with col:
        st.markdown(f"""
        <div class="login-wrapper">
            <div class="login-card">
                <div class="login-logo">⚡</div>
                <div class="login-title">Welcome back</div>
                <div class="login-subtitle">Sign in to manage Campaign Manager 360</div>
                <a href="{auth_url}" target="_blank" style="text-decoration: none;">
                    <button style="width: 100%; background: #FFFFFF; color: #000000; border: none; padding: 12px; border-radius: 8px; font-weight: 500; cursor: pointer; font-family: Inter, sans-serif; transition: background 0.2s;">
                        Connect Google Account
                    </button>
                </a>
                <div style="margin: 24px 0; display: flex; align-items: center; color: #333; font-size: 0.85rem;">
                    <div style="flex-grow: 1; height: 1px; background: #222;"></div>
                    <span style="padding: 0 12px; color: #666;">or paste code</span>
                    <div style="flex-grow: 1; height: 1px; background: #222;"></div>
                </div>
        """, unsafe_allow_html=True)
        
        # Streamlit input rendered inside the faked HTML card visually
        auth_code = st.text_input("Auth Code", label_visibility="collapsed", placeholder="Paste authorization code...")
        
        if auth_code:
            try:
                st.session_state.oauth_flow.fetch_token(code=auth_code)
                st.session_state.creds = st.session_state.oauth_flow.credentials
                
                del st.session_state['oauth_flow']
                del st.session_state['auth_url']
                st.rerun()
            except Exception as e:
                st.error("Invalid or expired code. Please try again.")
                if 'oauth_flow' in st.session_state:
                    del st.session_state['oauth_flow']
                    del st.session_state['auth_url']
        
        st.markdown("</div></div>", unsafe_allow_html=True)


# ==========================================
# 2. MAIN SAAS WORKSPACE VIEW
# ==========================================
def render_workspace(creds):
    service = build(API_SERVICE_NAME, API_VERSION, credentials=creds)

    # Fetch profiles silently
    try:
        profiles_response = service.userProfiles().list().execute()
        profiles = profiles_response.get('items', [])
        if not profiles:
            st.error("No active CM360 profiles found for this user.")
            st.stop()
        profile_dict = {f"{p['userName']} ({p['accountId']})": p['profileId'] for p in profiles}
    except Exception as e:
        st.error(f"API Error: {e}")
        st.stop()

    # --- Top Navigation Bar ---
    # We use columns to layout the top bar seamlessly
    nav_col1, nav_col2, nav_col3 = st.columns([2, 1.5, 0.5])
    with nav_col1:
        st.markdown("<div class='nav-brand'>⚡ CM360 Workspace</div>", unsafe_allow_html=True)
    with nav_col2:
        # Integrated profile selector in the nav bar
        selected_profile_key = st.selectbox("Profile", options=list(profile_dict.keys()), label_visibility="collapsed")
        profile_id = profile_dict[selected_profile_key]
    with nav_col3:
        # Logout button
        if st.button("Log out", type="secondary", use_container_width=True):
            del st.session_state['creds']
            st.rerun()
            
    st.markdown("<hr style='border: none; height: 1px; background-color: #1A1A1A; margin: 0 0 40px 0;'>", unsafe_allow_html=True)

    # --- Main Workspace Content ---
    _, main_col, _ = st.columns([1, 4, 1]) # Center the content
    
    with main_col:
        st.markdown("<div class='workspace-header'>Generate Event Tags</div>", unsafe_allow_html=True)
        st.markdown("<div class='workspace-sub'>Upload your structured CSV to create tags in bulk.</div>", unsafe_allow_html=True)

        # File Uploader
        uploaded_file = st.file_uploader("Drop your CSV file here", type=["csv"], label_visibility="collapsed")

        # Action Area
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            df.columns = df.columns.str.strip()
            
            required_cols = {'Tag Name', 'Level', 'Parent ID', 'Tag Type', 'Tag URL'}
            missing_cols = required_cols - set(df.columns)

            if missing_cols:
                st.error(f"❌ Invalid format. Missing columns: `{', '.join(missing_cols)}`")
            else:
                st.markdown("<br><p style='font-size: 0.9rem; color: #A1A1AA; margin-bottom: 8px; font-weight: 500;'>DATA PREVIEW</p>", unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True, height=200)

                invalid_urls = df[~df['Tag URL'].astype(str).str.startswith('https://')]
                if not invalid_urls.empty:
                    st.warning(f"⚠️ Warning: {len(invalid_urls)} row(s) contain non-HTTPS URLs.")

                st.markdown("<br>", unsafe_allow_html=True)
                
                # Execution Trigger
                if st.button("Generate Tags", type="primary"):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    results = []
                    
                    success_count, fail_count = 0, 0

                    for index, row in df.iterrows():
                        tag_name = str(row['Tag Name']).strip()
                        level = str(row['Level']).strip().upper()
                        parent_id = str(row['Parent ID']).strip()
                        
                        payload = {
                            "name": tag_name,
                            "status": "ENABLED", 
                            "type": str(row['Tag Type']).strip(),
                            "url": str(row['Tag URL']).strip()
                        }
                        
                        if level == 'ADVERTISER': payload["advertiserId"] = parent_id
                        elif level == 'CAMPAIGN': payload["campaignId"] = parent_id
                        else:
                            results.append({"Tag Name": tag_name, "Status": "FAILED", "Details": "Invalid Level", "ID": None})
                            fail_count += 1
                            continue

                        try:
                            req = service.eventTags().insert(profileId=profile_id, body=payload)
                            res = req.execute()
                            results.append({"Tag Name": tag_name, "Status": "SUCCESS", "Details": "-", "ID": res.get('id')})
                            success_count += 1
                        except Exception as e:
                            results.append({"Tag Name": tag_name, "Status": "FAILED", "Details": str(e), "ID": None})
                            fail_count += 1

                        progress_bar.progress((index + 1) / len(df))
                        status_text.caption(f"Processing: {tag_name}")

                    # Results Dashboard
                    st.markdown("<br><p style='font-size: 0.9rem; color: #A1A1AA; margin-bottom: 8px; font-weight: 500;'>EXECUTION SUMMARY</p>", unsafe_allow_html=True)
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Total Executed", len(df))
                    m2.metric("Successful", success_count)
                    m3.metric("Failed", fail_count)

                    res_df = pd.DataFrame(results)
                    st.dataframe(res_df, use_container_width=True)

                    csv_export = res_df.to_csv(index=False).encode('utf-8')
                    st.download_button("Download Audit Log", data=csv_export, file_name="tag_log.csv", mime="text/csv", type="secondary")

        # Download Template Link (always available at the bottom)
        st.markdown("<br><br>", unsafe_allow_html=True)
        with st.expander("Need a starter template?"):
            sample_df = pd.DataFrame([{
                "Tag Name": "Example_Pixel",
                "Level": "CAMPAIGN",
                "Parent ID": "123456",
                "Tag Type": "IMPRESSION_IMAGE_EVENT_TAG",
                "Tag URL": "https://pixel.example.com"
            }])
            buffer = io.BytesIO()
            sample_df.to_csv(buffer, index=False)
            st.download_button("Download CSV Template", data=buffer.getvalue(), file_name="template.csv", mime="text/csv", type="secondary")


# ==========================================
# APP ROUTING LOGIC
# ==========================================
def main():
    # If not authenticated, show ONLY the login page
    if 'creds' not in st.session_state or not st.session_state.creds or not st.session_state.creds.valid:
        render_login_page()
    # If authenticated, show ONLY the workspace
    else:
        render_workspace(st.session_state.creds)

if __name__ == "__main__":
    main()
