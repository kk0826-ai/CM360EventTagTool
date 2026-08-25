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

# --- Ultra-Premium SaaS CSS Injection ---
st.markdown("""
<style>
/* Import Inter Font */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* Hide Default Streamlit Chrome */
#MainMenu, header, footer {display: none !important;}
section[data-testid="stSidebar"] {display: none !important;}
.stApp > header {background-color: transparent !important;}

/* Global App Background - Ultra Soft Gray */
.stApp {
    background-color: #F9FAFB !important;
    color: #111827 !important;
}

/* --- LOGIN PAGE STYLES --- */
.login-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 85vh;
}

.login-card {
    background: #FFFFFF;
    border: 1px solid #F3F4F6;
    border-radius: 20px;
    padding: 48px 40px;
    width: 100%;
    max-width: 440px;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01);
}

.login-logo {
    width: 52px;
    height: 52px;
    background: linear-gradient(135deg, #111827, #374151);
    color: #FFFFFF;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 26px;
    margin: 0 auto 24px auto;
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}

.login-title {
    font-size: 1.75rem;
    font-weight: 700;
    color: #111827;
    margin-bottom: 8px;
    letter-spacing: -0.03em;
    text-align: center;
}

.login-subtitle {
    font-size: 0.95rem;
    color: #6B7280;
    text-align: center;
    margin-bottom: 32px;
}

/* Modern Auth Button */
.auth-button {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    width: 100%;
    background: #FFFFFF;
    color: #374151;
    border: 1px solid #D1D5DB;
    padding: 12px 16px;
    border-radius: 10px;
    font-weight: 600;
    font-size: 0.95rem;
    cursor: pointer;
    transition: all 0.2s ease;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    margin-bottom: 24px;
}
.auth-button:hover {
    background: #F9FAFB;
    border-color: #9CA3AF;
}

/* Divider */
.divider-container {
    display: flex;
    align-items: center;
    text-align: center;
    margin: 24px 0;
}
.divider-line {
    flex: 1;
    border-bottom: 1px solid #E5E7EB;
}
.divider-text {
    padding: 0 16px;
    color: #9CA3AF;
    font-size: 0.85rem;
    font-weight: 500;
}

/* --- OVERRIDE STREAMLIT ELEMENTS --- */
.stButton>button {
    width: 100%;
    border-radius: 10px !important;
    font-weight: 600 !important;
    height: 48px;
    font-size: 0.95rem !important;
    transition: all 0.2s ease;
}

/* Primary Action Button */
button[kind="primary"] {
    background: #111827 !important;
    color: #FFFFFF !important;
    border: none !important;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06) !important;
}
button[kind="primary"]:hover {
    background: #374151 !important;
    transform: translateY(-1px);
    box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05) !important;
}

/* Secondary Button */
button[kind="secondary"] {
    background: #FFFFFF !important;
    color: #374151 !important;
    border: 1px solid #D1D5DB !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
}
button[kind="secondary"]:hover {
    background: #F9FAFB !important;
    border-color: #9CA3AF !important;
}

/* Input Fields */
.stTextInput p {
    font-weight: 500 !important;
    color: #374151 !important;
    font-size: 0.9rem !important;
}
.stTextInput input {
    background-color: #FFFFFF !important;
    border: 1px solid #D1D5DB !important;
    color: #111827 !important;
    border-radius: 10px !important;
    padding: 14px 16px !important;
    font-size: 1rem !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02) inset !important;
    transition: all 0.2s ease;
}
.stTextInput input:focus {
    border-color: #3B82F6 !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15) !important;
}
.stTextInput input::placeholder {
    color: #9CA3AF !important;
}

/* --- DASHBOARD WORKSPACE STYLES --- */
.top-nav {
    background: #FFFFFF;
    border-bottom: 1px solid #E5E7EB;
    padding: 16px 40px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 40px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}

.workspace-card {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 16px;
    padding: 40px;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02), 0 2px 4px -1px rgba(0,0,0,0.01);
    margin-bottom: 24px;
}

.workspace-header {
    font-size: 1.5rem;
    font-weight: 700;
    color: #111827;
    margin-bottom: 8px;
    letter-spacing: -0.02em;
}

.workspace-sub {
    color: #6B7280;
    font-size: 0.95rem;
    margin-bottom: 32px;
}

/* Uploader */
[data-testid="stFileUploadDropzone"] {
    background-color: #F9FAFB !important;
    border: 1px dashed #D1D5DB !important;
    border-radius: 12px !important;
    padding: 40px !important;
    transition: all 0.2s ease;
}
[data-testid="stFileUploadDropzone"]:hover {
    background-color: #F3F4F6 !important;
    border-color: #9CA3AF !important;
}

/* Dataframes */
[data-testid="stDataFrame"] {
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    background: #FFFFFF;
    overflow: hidden;
}

/* Metrics */
div[data-testid="stMetric"] {
    background-color: #FFFFFF;
    border: 1px solid #E5E7EB;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}
div[data-testid="stMetricLabel"] {
    color: #6B7280 !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
div[data-testid="stMetricValue"] {
    color: #111827 !important;
    font-weight: 700 !important;
    font-size: 2rem !important;
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
        # Note: HTML is kept strictly left-aligned so Streamlit doesn't render it as a code block
        st.markdown(f"""
<div class="login-container">
<div class="login-card">
<div class="login-logo">⚡</div>
<div class="login-title">Welcome back</div>
<div class="login-subtitle">Sign in to your CM360 workspace</div>
<a href="{auth_url}" target="_blank" style="text-decoration: none;">
<button class="auth-button">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M22.56 12.25C22.56 11.47 22.49 10.73 22.36 10H12V14.26H17.92C17.67 15.63 16.89 16.79 15.74 17.56V20.3H19.31C21.4 18.38 22.56 15.57 22.56 12.25Z" fill="#4285F4"/>
<path d="M12 23C14.97 23 17.46 22.02 19.31 20.3L15.74 17.56C14.74 18.23 13.48 18.63 12 18.63C9.13 18.63 6.7 16.69 5.82 14.1H2.15V16.94C3.96 20.53 7.7 23 12 23Z" fill="#34A853"/>
<path d="M5.82 14.1C5.59 13.43 5.46 12.73 5.46 12C5.46 11.27 5.59 10.57 5.82 9.9V7.06H2.15C1.41 8.54 1 10.22 1 12C1 13.78 1.41 15.46 2.15 16.94L5.82 14.1Z" fill="#FBBC05"/>
<path d="M12 5.38C13.62 5.38 15.07 5.94 16.21 7.02L19.38 3.85C17.45 2.05 14.97 1 12 1C7.7 1 3.96 3.47 2.15 7.06L5.82 9.9C6.7 7.31 9.13 5.38 12 5.38Z" fill="#EA4335"/>
</svg>
Continue with Google
</button>
</a>
<div class="divider-container">
<div class="divider-line"></div>
<div class="divider-text">Or paste access code</div>
<div class="divider-line"></div>
</div>
""", unsafe_allow_html=True)
        
        # Streamlit Input (Clean, modern look)
        auth_code = st.text_input("Authorization Code", label_visibility="collapsed", placeholder="Paste your code here...")
        
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
        
        # Close the div tags, left-aligned
        st.markdown("""
</div>
</div>
""", unsafe_allow_html=True)


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
<div style='font-weight: 700; font-size: 1.15rem; color: #111827; display: flex; align-items: center; gap: 10px;'>
<div style='background: linear-gradient(135deg, #111827, #374151); color: white; padding: 6px 10px; border-radius: 8px; font-size: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>⚡</div>
CM360 Workspace
</div>
</div>
""", unsafe_allow_html=True)

    # --- Profile & Logout Controls (Positioned right below nav) ---
    nav_c1, nav_c2, nav_c3, nav_c4 = st.columns([6, 2.5, 0.2, 1])
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
                st.markdown("<p style='font-size: 0.8rem; color: #6B7280; margin-top: 24px; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;'>Data Preview</p>", unsafe_allow_html=True)
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
                    st.markdown("<br><p style='font-size: 0.8rem; color: #6B7280; margin-bottom: 12px; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;'>Execution Summary</p>", unsafe_allow_html=True)
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
