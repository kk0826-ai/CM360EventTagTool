import streamlit as st
import pandas as pd
import json
import io
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# --- Page Config (Must be first) ---
st.set_page_config(page_title="CM360 Workspace", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

# --- API Config ---
SCOPES = ['https://www.googleapis.com/auth/dfatrafficking']
API_SERVICE_NAME = 'dfareporting'
API_VERSION = 'v5'

if "client_secrets" not in st.secrets:
    st.error("⚠️ Missing 'client_secrets' in Streamlit secrets configuration.")
    st.stop()

# --- High-Contrast SaaS CSS Injection ---
st.markdown("""
    <style>
    /* Import Inter Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Hide Default Streamlit Chrome */
    #MainMenu, header, footer {display: none !important;}
    section[data-testid="stSidebar"] {display: none !important;}
    
    /* Global App Background - Cool Light Gray for contrast */
    .stApp {
        background-color: #F4F4F5 !important;
        color: #18181B !important;
    }

    /* --- LOGIN PAGE STYLES --- */
    .login-container {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 80vh;
    }
    
    .login-card {
        background: #FFFFFF;
        border: 1px solid #E4E4E7;
        border-radius: 16px;
        padding: 40px;
        width: 100%;
        max-width: 420px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01);
    }
    
    .login-header {
        text-align: center;
        margin-bottom: 32px;
    }
    
    .login-logo {
        width: 48px;
        height: 48px;
        background: #18181B;
        color: #FFFFFF;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        margin: 0 auto 16px auto;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }
    
    .login-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #09090B;
        margin-bottom: 6px;
        letter-spacing: -0.02em;
    }
    
    .login-subtitle {
        font-size: 0.9rem;
        color: #71717A;
    }

    /* Step Indicators */
    .step-box {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 12px;
    }
    .step-num {
        background: #F4F4F5;
        color: #18181B;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.75rem;
        font-weight: 700;
        border: 1px solid #E4E4E7;
    }
    .step-text {
        font-size: 0.9rem;
        font-weight: 600;
        color: #3F3F46;
    }

    /* --- OVERRIDE STREAMLIT ELEMENTS --- */
    .stButton>button {
        width: 100%;
        border-radius: 8px !important;
        font-weight: 500 !important;
        height: 44px;
        transition: all 0.2s ease;
    }
    
    /* Primary Action Button (Login / Generate) */
    button[kind="primary"] {
        background: #18181B !important;
        color: #FFFFFF !important;
        border: none !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }
    button[kind="primary"]:hover {
        background: #27272A !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.12) !important;
    }

    /* Secondary Button (Logout / Download) */
    button[kind="secondary"] {
        background: #FFFFFF !important;
        color: #18181B !important;
        border: 1px solid #E4E4E7 !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important;
    }
    button[kind="secondary"]:hover {
        background: #F4F4F5 !important;
        border-color: #D4D4D8 !important;
    }

    /* Input Fields */
    .stTextInput input {
        background-color: #FFFFFF !important;
        border: 1px solid #D4D4D8 !important;
        color: #18181B !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
        font-size: 0.95rem !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02) inset !important;
    }
    .stTextInput input:focus {
        border-color: #2563EB !important;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2) !important;
    }

    /* --- DASHBOARD WORKSPACE STYLES --- */
    .top-nav {
        background: #FFFFFF;
        border-bottom: 1px solid #E4E4E7;
        padding: 16px 32px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 32px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    
    .workspace-card {
        background: #FFFFFF;
        border: 1px solid #E4E4E7;
        border-radius: 12px;
        padding: 32px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);
        margin-bottom: 24px;
    }

    .workspace-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #09090B;
        margin-bottom: 4px;
    }
    
    .workspace-sub {
        color: #71717A;
        font-size: 0.95rem;
        margin-bottom: 24px;
    }

    /* Uploader & DataFrames */
    [data-testid="stFileUploadDropzone"] {
        background-color: #FAFAFA !important;
        border: 1px dashed #D4D4D8 !important;
        border-radius: 8px !important;
        padding: 32px !important;
    }
    [data-testid="stFileUploadDropzone"]:hover {
        background-color: #F4F4F5 !important;
        border-color: #A1A1AA !important;
    }
    
    [data-testid="stDataFrame"] {
        border: 1px solid #E4E4E7;
        border-radius: 8px;
        background: #FFFFFF;
    }

    /* Metrics */
    div[data-testid="stMetric"] {
        background-color: #FAFAFA;
        border: 1px solid #E4E4E7;
        padding: 16px 20px;
        border-radius: 8px;
    }
    div[data-testid="stMetricLabel"] {
        color: #71717A !important;
        font-weight: 500 !important;
    }
    div[data-testid="stMetricValue"] {
        color: #09090B !important;
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

    # Centered layout using columns
    _, col, _ = st.columns([1, 1.2, 1])
    
    with col:
        st.markdown(f"""
        <div class="login-container">
            <div class="login-card">
                <div class="login-header">
                    <div class="login-logo">⚡</div>
                    <div class="login-title">Sign in to CM360</div>
                    <div class="login-subtitle">Connect your Google account to continue</div>
                </div>
                
                <div class="step-box">
                    <div class="step-num">1</div>
                    <div class="step-text">Generate Google Auth Code</div>
                </div>
                <a href="{auth_url}" target="_blank" style="text-decoration: none;">
                    <button style="width: 100%; background: #FFFFFF; color: #18181B; border: 1px solid #E4E4E7; padding: 10px; border-radius: 8px; font-weight: 500; cursor: pointer; font-family: Inter, sans-serif; box-shadow: 0 1px 2px rgba(0,0,0,0.05); margin-bottom: 24px;">
                        Open Google Login Tab ↗
                    </button>
                </a>

                <div class="step-box">
                    <div class="step-num">2</div>
                    <div class="step-text">Paste Code to Authenticate</div>
                </div>
        """, unsafe_allow_html=True)
        
        # Streamlit Input (Visually tucked under Step 2)
        auth_code = st.text_input("Auth Code", label_visibility="collapsed", placeholder="Enter the code here...")
        
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

    # --- Top Navigation Bar (Full Width) ---
    st.markdown("""
        <div class='top-nav' style='margin-top: -3rem; margin-left: -3rem; margin-right: -3rem;'>
            <div style='font-weight: 700; font-size: 1.1rem; color: #18181B; display: flex; align-items: center; gap: 8px;'>
                <div style='background: #18181B; color: white; padding: 4px 8px; border-radius: 6px; font-size: 0.9rem;'>⚡</div>
                CM360 Tags Workspace
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- Profile & Logout Controls (Positioned right below nav) ---
    nav_c1, nav_c2, nav_c3, nav_c4 = st.columns([6, 2, 0.2, 1])
    with nav_c2:
        selected_profile_key = st.selectbox("Active Profile", options=list(profile_dict.keys()), label_visibility="collapsed")
        profile_id = profile_dict[selected_profile_key]
    with nav_c4:
        if st.button("Log out", type="secondary"):
            del st.session_state['creds']
            st.rerun()
            
    st.markdown("<br>", unsafe_allow_html=True)

    # --- Main Workspace Content ---
    _, main_col, _ = st.columns([1, 6, 1]) 
    
    with main_col:
        st.markdown("""
            <div class='workspace-card'>
                <div class='workspace-header'>Generate Event Tags</div>
                <div class='workspace-sub'>Upload your structured CSV to create impression and click tags in bulk.</div>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader("Drop your CSV file here", type=["csv"], label_visibility="collapsed")

        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            df.columns = df.columns.str.strip()
            
            required_cols = {'Tag Name', 'Level', 'Parent ID', 'Tag Type', 'Tag URL'}
            missing_cols = required_cols - set(df.columns)

            if missing_cols:
                st.error(f"❌ Invalid format. Missing columns: `{', '.join(missing_cols)}`")
            else:
                st.markdown("<p style='font-size: 0.8rem; color: #71717A; margin-top: 24px; font-weight: 600; letter-spacing: 0.05em;'>DATA PREVIEW</p>", unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True, height=200)

                invalid_urls = df[~df['Tag URL'].astype(str).str.startswith('https://')]
                if not invalid_urls.empty:
                    st.warning(f"⚠️ Warning: {len(invalid_urls)} row(s) contain non-HTTPS URLs.")

                st.markdown("<br>", unsafe_allow_html=True)
                
                # Execution Trigger
                if st.button("🚀 Generate Tags in CM360", type="primary"):
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
                    st.markdown("<br><p style='font-size: 0.8rem; color: #71717A; margin-bottom: 8px; font-weight: 600; letter-spacing: 0.05em;'>EXECUTION SUMMARY</p>", unsafe_allow_html=True)
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Total Executed", len(df))
                    m2.metric("Successful", success_count)
                    m3.metric("Failed", fail_count)

                    res_df = pd.DataFrame(results)
                    st.dataframe(res_df, use_container_width=True)

                    csv_export = res_df.to_csv(index=False).encode('utf-8')
                    st.download_button("Download Audit Log", data=csv_export, file_name="tag_log.csv", mime="text/csv", type="secondary")

        # Close workspace card HTML
        st.markdown("</div>", unsafe_allow_html=True)

        # Download Template Link
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
