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

# --- Minimal Light SaaS CSS Injection ---
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
    
    /* Global Background - Crisp Off-White */
    .stApp {
        background-color: #FAFAFA !important; 
        background-image: none !important;
        color: #18181B !important; 
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
        background: #FFFFFF;
        border: 1px solid #E4E4E7;
        border-radius: 16px;
        padding: 48px 40px;
        width: 100%;
        max-width: 440px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -4px rgba(0, 0, 0, 0.02);
        text-align: center;
    }
    
    .login-logo {
        width: 48px;
        height: 48px;
        background: #FFFFFF;
        border: 1px solid #E4E4E7;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        margin: 0 auto 24px auto;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    .login-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #09090B;
        margin-bottom: 8px;
        letter-spacing: -0.02em;
    }
    
    .login-subtitle {
        font-size: 0.95rem;
        color: #71717A;
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
    
    /* Primary Black Button */
    button[kind="primary"] {
        background: #18181B !important;
        color: #FFFFFF !important;
        border: 1px solid #18181B !important;
    }
    button[kind="primary"]:hover {
        background: #27272A !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }

    /* Secondary White/Gray Button */
    button[kind="secondary"] {
        background: #FFFFFF !important;
        color: #18181B !important;
        border: 1px solid #E4E4E7 !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    }
    button[kind="secondary"]:hover {
        background: #F4F4F5 !important;
        border-color: #D4D4D8 !important;
    }

    /* Input Fields */
    .stTextInput input {
        background-color: #FFFFFF !important;
        border: 1px solid #E4E4E7 !important;
        color: #18181B !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
        font-size: 0.95rem !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important;
    }
    .stTextInput input:focus {
        border-color: #18181B !important;
        box-shadow: 0 0 0 1px #18181B !important;
    }
    .stTextInput input::placeholder {
        color: #A1A1AA !important;
    }

    /* --- DASHBOARD STYLES --- */
    .nav-brand {
        font-size: 1.1rem;
        font-weight: 600;
        color: #18181B;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .workspace-header {
        font-size: 2rem;
        font-weight: 600;
        color: #09090B;
        margin-bottom: 8px;
        letter-spacing: -0.02em;
    }
    
    .workspace-sub {
        color: #71717A;
        font-size: 1rem;
        margin-bottom: 32px;
    }

    /* File Uploader styling */
    [data-testid="stFileUploadDropzone"] {
        background-color: #FFFFFF !important;
        border: 1px dashed #D4D4D8 !important;
        border-radius: 12px !important;
        padding: 40px !important;
        transition: all 0.2s ease;
    }
    [data-testid="stFileUploadDropzone"]:hover {
        border-color: #18181B !important;
        background-color: #FAFAFA !important;
    }
    [data-testid="stFileUploadDropzone"] * {
        color: #71717A !important;
    }
    
    /* Metrics */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E4E4E7;
        padding: 16px 20px;
        border-radius: 12px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    }
    div[data-testid="stMetricLabel"] {
        color: #71717A !important;
        font-weight: 500 !important;
    }
    div[data-testid="stMetricValue"] {
        color: #18181B !important;
    }
    
    /* Dataframes */
    [data-testid="stDataFrame"] {
        border: 1px solid #E4E4E7;
        border-radius: 12px;
        overflow: hidden;
        background: #FFFFFF;
    }
    
    /* Labels and small text */
    p, label {
        color: #3F3F46 !important;
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

    # Centered column layout
    _, col, _ = st.columns([1, 1.2, 1])
    
    with col:
        st.markdown(f"""
        <div class="login-wrapper">
            <div class="login-card">
                <div class="login-logo">⚡</div>
                <div class="login-title">Welcome back</div>
                <div class="login-subtitle">Sign in to manage Campaign Manager 360</div>
                <a href="{auth_url}" target="_blank" style="text-decoration: none;">
                    <button style="width: 100%; background: #18181B; color: #FFFFFF; border: none; padding: 12px; border-radius: 8px; font-weight: 500; cursor: pointer; font-family: Inter, sans-serif; transition: background 0.2s; box-shadow: 0 1px 2px rgba(0,0,0,0.1);">
                        Connect Google Account
                    </button>
                </a>
                <div style="margin: 24px 0; display: flex; align-items: center; color: #A1A1AA; font-size: 0.85rem;">
                    <div style="flex-grow: 1; height: 1px; background: #E4E4E7;"></div>
                    <span style="padding: 0 12px;">or paste code</span>
                    <div style="flex-grow: 1; height: 1px; background: #E4E4E7;"></div>
                </div>
        """, unsafe_allow_html=True)
        
        # Input mapped to visual card
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
    nav_col1, nav_col2, nav_col3 = st.columns([2, 1.5, 0.5])
    with nav_col1:
        st.markdown("<div class='nav-brand'>⚡ CM360 Workspace</div>", unsafe_allow_html=True)
    with nav_col2:
        selected_profile_key = st.selectbox("Profile", options=list(profile_dict.keys()), label_visibility="collapsed")
        profile_id = profile_dict[selected_profile_key]
    with nav_col3:
        if st.button("Log out", type="secondary", use_container_width=True):
            del st.session_state['creds']
            st.rerun()
            
    st.markdown("<hr style='border: none; height: 1px; background-color: #E4E4E7; margin: 0 0 40px 0;'>", unsafe_allow_html=True)

    # --- Main Workspace Content ---
    _, main_col, _ = st.columns([1, 4, 1]) 
    
    with main_col:
        st.markdown("<div class='workspace-header'>Generate Event Tags</div>", unsafe_allow_html=True)
        st.markdown("<div class='workspace-sub'>Upload your structured CSV to create tags in bulk.</div>", unsafe_allow_html=True)

        uploaded_file = st.file_uploader("Drop your CSV file here", type=["csv"], label_visibility="collapsed")

        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            df.columns = df.columns.str.strip()
            
            required_cols = {'Tag Name', 'Level', 'Parent ID', 'Tag Type', 'Tag URL'}
            missing_cols = required_cols - set(df.columns)

            if missing_cols:
                st.error(f"❌ Invalid format. Missing columns: `{', '.join(missing_cols)}`")
            else:
                st.markdown("<br><p style='font-size: 0.8rem; color: #71717A; margin-bottom: 8px; font-weight: 600; letter-spacing: 0.05em;'>DATA PREVIEW</p>", unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True, height=200)

                invalid_urls = df[~df['Tag URL'].astype(str).str.startswith('https://')]
                if not invalid_urls.empty:
                    st.warning(f"⚠️ Warning: {len(invalid_urls)} row(s) contain non-HTTPS URLs.")

                st.markdown("<br>", unsafe_allow_html=True)
                
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

                    st.markdown("<br><p style='font-size: 0.8rem; color: #71717A; margin-bottom: 8px; font-weight: 600; letter-spacing: 0.05em;'>EXECUTION SUMMARY</p>", unsafe_allow_html=True)
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Total Executed", len(df))
                    m2.metric("Successful", success_count)
                    m3.metric("Failed", fail_count)

                    res_df = pd.DataFrame(results)
                    st.dataframe(res_df, use_container_width=True)

                    csv_export = res_df.to_csv(index=False).encode('utf-8')
                    st.download_button("Download Audit Log", data=csv_export, file_name="tag_log.csv", mime="text/csv", type="secondary")

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
    if 'creds' not in st.session_state or not st.session_state.creds or not st.session_state.creds.valid:
        render_login_page()
    else:
        render_workspace(st.session_state.creds)

if __name__ == "__main__":
    main()
