import streamlit as st
import pandas as pd
import json
import io
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# --- Page Config (Must be first) ---
st.set_page_config(page_title="CM360 Tag Manager", layout="wide", initial_sidebar_state="collapsed")

# --- API Config ---
SCOPES = ['https://www.googleapis.com/auth/dfatrafficking']
API_SERVICE_NAME = 'dfareporting'
API_VERSION = 'v5'

if "client_secrets" not in st.secrets:
    st.error("⚠️ Missing 'client_secrets' in Streamlit secrets configuration.")
    st.stop()

# --- CSS Injection (Zero indentation to bypass markdown parsing) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif !important; }
#MainMenu, header, footer {display: none !important;}
section[data-testid="stSidebar"] {display: none !important;}

/* Clean App Background */
.stApp { background-color: #FFFFFF !important; color: #0F172A !important; }

/* Buttons */
.stButton>button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    height: 48px;
    transition: all 0.2s ease;
}
button[kind="primary"] {
    background: #0F172A !important;
    color: #FFFFFF !important;
    border: none !important;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1) !important;
}
button[kind="primary"]:hover {
    background: #334155 !important;
    transform: translateY(-1px);
}
button[kind="secondary"] {
    background: #FFFFFF !important;
    color: #0F172A !important;
    border: 1px solid #E2E8F0 !important;
}
button[kind="secondary"]:hover {
    background: #F8FAFC !important;
    border-color: #CBD5E1 !important;
}

/* Inputs & File Uploader */
.stTextInput input {
    background-color: #F8FAFC !important;
    border: 1px solid #E2E8F0 !important;
    color: #0F172A !important;
    border-radius: 8px !important;
    padding: 12px 16px !important;
    height: 48px !important;
}
.stTextInput input:focus {
    background-color: #FFFFFF !important;
    border-color: #0F172A !important;
    box-shadow: 0 0 0 1px #0F172A !important;
}
[data-testid="stFileUploadDropzone"] {
    background-color: #F8FAFC !important;
    border: 1px dashed #CBD5E1 !important;
    border-radius: 12px !important;
    padding: 32px !important;
}

/* Dataframes */
[data-testid="stDataFrame"] {
    border: 1px solid #E2E8F0;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)


# ==========================================
# 1. AUTHENTICATION & LOGIN VIEW (SPLIT SCREEN)
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

    # Create the two-column split layout
    col_left, col_right = st.columns([1, 1.2], gap="large")
    
    with col_left:
        st.write("") 
        st.write("") 
        st.write("") 
        st.write("") 
        st.write("") 
        st.write("") 
        
        # 100% Flush left HTML for the clean login UI
        st.markdown(f"""
<div>
<h1 style="font-size: 2rem; font-weight: 700; color: #0F172A; margin: 0 0 8px 0; letter-spacing: -0.02em;">Welcome Back</h1>
<p style="font-size: 1rem; color: #64748B; margin: 0 0 32px 0;">Sign in to CM360 Bulk Tag Manager.</p>

<a href="{auth_url}" target="_blank" style="text-decoration: none;">
<button style="display: flex; align-items: center; justify-content: center; gap: 10px; width: 100%; background: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1; padding: 12px; border-radius: 8px; font-weight: 600; cursor: pointer; box-shadow: 0 1px 2px rgba(0,0,0,0.05); margin-bottom: 16px;">
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M22.56 12.25C22.56 11.47 22.49 10.73 22.36 10H12V14.26H17.92C17.67 15.63 16.89 16.79 15.74 17.56V20.3H19.31C21.4 18.38 22.56 15.57 22.56 12.25Z" fill="#4285F4"/>
<path d="M12 23C14.97 23 17.46 22.02 19.31 20.3L15.74 17.56C14.74 18.23 13.48 18.63 12 18.63C9.13 18.63 6.7 16.69 5.82 14.1H2.15V16.94C3.96 20.53 7.7 23 12 23Z" fill="#34A853"/>
<path d="M5.82 14.1C5.59 13.43 5.46 12.73 5.46 12C5.46 11.27 5.59 10.57 5.82 9.9V7.06H2.15C1.41 8.54 1 10.22 1 12C1 13.78 1.41 15.46 2.15 16.94L5.82 14.1Z" fill="#FBBC05"/>
<path d="M12 5.38C13.62 5.38 15.07 5.94 16.21 7.02L19.38 3.85C17.45 2.05 14.97 1 12 1C7.7 1 3.96 3.47 2.15 7.06L5.82 9.9C6.7 7.31 9.13 5.38 12 5.38Z" fill="#EA4335"/>
</svg>
Sign in with Google
</button>
</a>
</div>
""", unsafe_allow_html=True)
        
        # Input Field placed immediately below the button
        auth_code = st.text_input("Authorization Code", label_visibility="collapsed", placeholder="Paste your authorization code here...")
        
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

    with col_right:
        # Beautiful MiQ Brand Gradient covering the right side
        st.markdown("""
<div style="height: 95vh; width: 100%; border-radius: 24px; margin-top: 12px; background: linear-gradient(135deg, #FFCA01 0%, #FF6500 25%, #FF2000 50%, #EA00AD 75%, #2B0030 100%); box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);">
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

    # --- Workspace Header ---
    st.markdown("<br>", unsafe_allow_html=True)
    header_col1, header_col2 = st.columns([3, 1])
    
    with header_col1:
        st.markdown("""
<div>
<h1 style="margin: 0; font-size: 1.5rem; font-weight: 700; color: #0F172A;">Bulk Event Tags</h1>
<p style="margin: 0; font-size: 0.95rem; color: #64748B;">Upload, preview, and generate pixels across campaigns.</p>
</div>
""", unsafe_allow_html=True)

    with header_col2:
        selected_profile_key = st.selectbox("Active Profile", options=list(profile_dict.keys()), label_visibility="collapsed")
        profile_id = profile_dict[selected_profile_key]
        if st.button("Sign Out", type="secondary", use_container_width=True):
            del st.session_state['creds']
            st.rerun()

    st.markdown("<hr style='border: none; height: 1px; background-color: #E2E8F0; margin: 32px 0;'>", unsafe_allow_html=True)

    # --- Left/Right Workspace Layout ---
    work_left, work_right = st.columns([1, 1.5], gap="large")

    with work_left:
        st.markdown("<h3 style='font-size: 1.1rem; color: #0F172A; margin-bottom: 16px;'>1. Upload Data</h3>", unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader("Drop your CSV file here", type=["csv"], label_visibility="collapsed")
        
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("Need the CSV Template?"):
            st.write("Your CSV must contain exactly these 5 columns.")
            sample_df = pd.DataFrame([{
                "Tag Name": "Example_Pixel",
                "Level": "CAMPAIGN",
                "Parent ID": "123456",
                "Tag Type": "IMPRESSION_IMAGE_EVENT_TAG",
                "Tag URL": "https://pixel.example.com"
            }])
            st.dataframe(sample_df, hide_index=True)
            buffer = io.BytesIO()
            sample_df.to_csv(buffer, index=False)
            st.download_button("Download Template", data=buffer.getvalue(), file_name="template.csv", mime="text/csv", type="secondary")

    with work_right:
        st.markdown("<h3 style='font-size: 1.1rem; color: #0F172A; margin-bottom: 16px;'>2. Preview & Execute</h3>", unsafe_allow_html=True)
        
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            df.columns = df.columns.str.strip()
            
            required_cols = {'Tag Name', 'Level', 'Parent ID', 'Tag Type', 'Tag URL'}
            missing_cols = required_cols - set(df.columns)

            if missing_cols:
                st.error(f"❌ Invalid format. Missing columns: `{', '.join(missing_cols)}`")
            else:
                st.dataframe(df, use_container_width=True, height=250)

                invalid_urls = df[~df['Tag URL'].astype(str).str.startswith('https://')]
                if not invalid_urls.empty:
                    st.warning(f"⚠️ {len(invalid_urls)} row(s) contain non-HTTPS URLs and will fail.")

                st.markdown("<br>", unsafe_allow_html=True)
                
                # Execution Trigger
                if st.button("🚀 Push Tags to CM360", type="primary"):
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
                    st.success(f"Execution complete! {success_count} tags created, {fail_count} failed.")

                    res_df = pd.DataFrame(results)
                    st.dataframe(res_df, use_container_width=True)

                    csv_export = res_df.to_csv(index=False).encode('utf-8')
                    st.download_button("Download Execution Log", data=csv_export, file_name="tag_log.csv", mime="text/csv", type="secondary")
        else:
            st.info("Upload a CSV file on the left to preview your data and execute the creation process.")


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
