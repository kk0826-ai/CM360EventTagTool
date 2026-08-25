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

    # --- Dribbble-Style Login CSS ---
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif !important; }
#MainMenu, header, footer {display: none !important;}
section[data-testid="stSidebar"] {display: none !important;}

/* Ambient Mesh Background */
.stApp {
    background: linear-gradient(135deg, #F0F4FF 0%, #F5ECFF 100%) !important;
    color: #0F172A !important;
}

/* The Elevated Login Card */
div[data-testid="column"]:nth-child(2) {
    background-color: #FFFFFF;
    border-radius: 24px;
    padding: 40px;
    box-shadow: 0 24px 48px -12px rgba(0, 0, 0, 0.08);
    border: 1px solid #FFFFFF;
    margin-top: 8vh;
}

/* Google Button Styling */
.google-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    width: 100%;
    background: #FFFFFF;
    color: #334155;
    border: 1px solid #E2E8F0;
    padding: 14px 16px;
    border-radius: 14px;
    font-weight: 600;
    font-size: 1rem;
    text-decoration: none;
    transition: all 0.2s ease;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}
.google-btn:hover {
    background: #F8FAFC;
    border-color: #CBD5E1;
    transform: translateY(-1px);
}

/* Divider */
.divider {
    display: flex;
    align-items: center;
    text-align: center;
    margin: 32px 0 24px 0;
}
.divider::before, .divider::after {
    content: '';
    flex: 1;
    border-bottom: 1px solid #F1F5F9;
}
.divider-text {
    padding: 0 16px;
    color: #94A3B8;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Streamlit Input Overrides */
.stTextInput input {
    background-color: #F8FAFC !important;
    border: 1px solid #E2E8F0 !important;
    color: #0F172A !important;
    border-radius: 14px !important;
    padding: 16px 20px !important;
    font-size: 1rem !important;
    transition: all 0.2s ease;
}
.stTextInput input:focus {
    background-color: #FFFFFF !important;
    border-color: #6366F1 !important;
    box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1) !important;
}
.stTextInput input::placeholder { color: #94A3B8 !important; }
</style>
""", unsafe_allow_html=True)

    # Centered layout using columns
    _, col, _ = st.columns([1, 1.2, 1])
    
    with col:
        # NOTE: HTML flush-left to avoid markdown code block parsing
        st.markdown(f"""
<div style="width: 100%; height: 160px; border-radius: 16px; background: linear-gradient(135deg, #A8C0FF 0%, #3F2B96 100%); margin-bottom: 32px; display: flex; align-items: center; justify-content: center; box-shadow: inset 0 0 0 1px rgba(255,255,255,0.2);">
<div style="background: rgba(255,255,255,0.25); backdrop-filter: blur(12px); padding: 14px; border-radius: 16px; font-size: 32px; box-shadow: 0 8px 16px rgba(0,0,0,0.1); border: 1px solid rgba(255,255,255,0.3); color: white;">⚡</div>
</div>
<h1 style="font-size: 1.8rem; font-weight: 800; color: #0F172A; margin: 0 0 8px 0; letter-spacing: -0.03em; text-align: center;">Welcome back</h1>
<p style="font-size: 1rem; color: #64748B; margin: 0 0 32px 0; text-align: center; font-weight: 500;">Please authorize to manage CM360.</p>
<a href="{auth_url}" target="_blank" class="google-btn">
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M22.56 12.25C22.56 11.47 22.49 10.73 22.36 10H12V14.26H17.92C17.67 15.63 16.89 16.79 15.74 17.56V20.3H19.31C21.4 18.38 22.56 15.57 22.56 12.25Z" fill="#4285F4"/>
<path d="M12 23C14.97 23 17.46 22.02 19.31 20.3L15.74 17.56C14.74 18.23 13.48 18.63 12 18.63C9.13 18.63 6.7 16.69 5.82 14.1H2.15V16.94C3.96 20.53 7.7 23 12 23Z" fill="#34A853"/>
<path d="M5.82 14.1C5.59 13.43 5.46 12.73 5.46 12C5.46 11.27 5.59 10.57 5.82 9.9V7.06H2.15C1.41 8.54 1 10.22 1 12C1 13.78 1.41 15.46 2.15 16.94L5.82 14.1Z" fill="#FBBC05"/>
<path d="M12 5.38C13.62 5.38 15.07 5.94 16.21 7.02L19.38 3.85C17.45 2.05 14.97 1 12 1C7.7 1 3.96 3.47 2.15 7.06L5.82 9.9C6.7 7.31 9.13 5.38 12 5.38Z" fill="#EA4335"/>
</svg>
Sign in with Google
</a>
<div class="divider"><span class="divider-text">Or paste access code</span></div>
""", unsafe_allow_html=True)
        
        auth_code = st.text_input("Auth Code", label_visibility="collapsed", placeholder="Enter authorization code...")
        
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

    # --- Dribbble-Style Workspace CSS ---
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif !important; }
#MainMenu, header, footer {display: none !important;}
section[data-testid="stSidebar"] {display: none !important;}

/* Ultra-clean Workspace Canvas */
.stApp { background-color: #FAFAFA !important; color: #0F172A !important; }

/* Buttons */
.stButton>button {
    border-radius: 12px !important;
    font-weight: 600 !important;
    height: 48px;
    transition: all 0.2s ease;
}
button[kind="primary"] {
    background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%) !important;
    color: #FFFFFF !important;
    border: none !important;
    box-shadow: 0 8px 16px -4px rgba(99, 102, 241, 0.3) !important;
}
button[kind="primary"]:hover {
    box-shadow: 0 12px 20px -4px rgba(99, 102, 241, 0.4) !important;
    transform: translateY(-2px);
}
button[kind="secondary"] {
    background: #FFFFFF !important;
    color: #0F172A !important;
    border: 1px solid #E2E8F0 !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
}
button[kind="secondary"]:hover {
    background: #F8FAFC !important;
    border-color: #CBD5E1 !important;
}

/* File Uploader */
[data-testid="stFileUploadDropzone"] {
    background-color: #FFFFFF !important;
    border: 2px dashed #CBD5E1 !important;
    border-radius: 16px !important;
    padding: 48px !important;
    transition: all 0.2s ease;
}
[data-testid="stFileUploadDropzone"]:hover {
    background-color: #F8FAFC !important;
    border-color: #6366F1 !important;
}

/* Metrics Cards */
div[data-testid="stMetric"] {
    background-color: #FFFFFF;
    border: 1px solid #F1F5F9;
    padding: 24px;
    border-radius: 16px;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);
}
div[data-testid="stMetricLabel"] {
    color: #64748B !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-size: 0.8rem !important;
}
div[data-testid="stMetricValue"] {
    color: #0F172A !important;
    font-weight: 800 !important;
    font-size: 2.5rem !important;
    letter-spacing: -0.02em;
}

/* Selectbox */
.stSelectbox > div > div {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 12px !important;
    color: #0F172A !important;
    height: 48px;
}
</style>
""", unsafe_allow_html=True)

    # Workspace Header Layout
    st.markdown("<br>", unsafe_allow_html=True)
    header_col1, header_col2 = st.columns([3, 1])
    
    with header_col1:
        st.markdown("""
<div style="display: flex; align-items: center; gap: 16px; margin-bottom: 32px;">
<div style="width: 54px; height: 54px; background: linear-gradient(135deg, #A8C0FF 0%, #3F2B96 100%); border-radius: 16px; display: flex; align-items: center; justify-content: center; color: white; font-size: 26px; box-shadow: 0 8px 16px rgba(63,43,150,0.25);">⚡</div>
<div>
<h1 style="margin: 0; font-size: 1.6rem; font-weight: 800; color: #0F172A; letter-spacing: -0.03em;">Workspace Hub</h1>
<p style="margin: 0; font-size: 1rem; color: #64748B; font-weight: 500;">Bulk generate and manage Event Tags</p>
</div>
</div>
""", unsafe_allow_html=True)

    with header_col2:
        selected_profile_key = st.selectbox("Active Profile", options=list(profile_dict.keys()), label_visibility="collapsed")
        profile_id = profile_dict[selected_profile_key]
        if st.button("Sign Out", type="secondary", use_container_width=True):
            del st.session_state['creds']
            st.rerun()

    st.markdown("<hr style='border: none; height: 1px; background-color: #E2E8F0; margin-bottom: 40px;'>", unsafe_allow_html=True)

    # Main Execution Area
    uploaded_file = st.file_uploader("Drop your CSV file here", type=["csv"], label_visibility="collapsed")

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip()
        
        required_cols = {'Tag Name', 'Level', 'Parent ID', 'Tag Type', 'Tag URL'}
        missing_cols = required_cols - set(df.columns)

        if missing_cols:
            st.error(f"❌ Invalid format. Missing columns: `{', '.join(missing_cols)}`")
        else:
            st.markdown("<p style='font-size: 0.8rem; color: #64748B; margin-top: 24px; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;'>Data Preview</p>", unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True, height=200)

            invalid_urls = df[~df['Tag URL'].astype(str).str.startswith('https://')]
            if not invalid_urls.empty:
                st.warning(f"⚠️ Warning: {len(invalid_urls)} row(s) contain non-HTTPS URLs.")

            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("🚀 Execute Event Tags", type="primary"):
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

                st.markdown("<br><p style='font-size: 0.8rem; color: #64748B; margin-bottom: 12px; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;'>Execution Overview</p>", unsafe_allow_html=True)
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
