import streamlit as st
import pandas as pd
import json
import io
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# --- Page Config ---
st.set_page_config(page_title="CM360 Bulk Event Creator", layout="wide", initial_sidebar_state="collapsed")

# --- API Config ---
SCOPES = ['https://www.googleapis.com/auth/dfatrafficking']
API_SERVICE_NAME = 'dfareporting'
API_VERSION = 'v5'

if "client_secrets" not in st.secrets:
    st.error("⚠️ Missing 'client_secrets' in Streamlit secrets configuration.")
    st.stop()

# --- Minimal CSS ---
st.markdown("""
<style>
#MainMenu, header, footer { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }
.stApp { background-color: #FFFFFF !important; color: #111827 !important; }
.stButton>button, .stDownloadButton>button {
    border-radius: 8px !important;
    font-weight: 500 !important;
}
button[kind="primary"] { background-color: #2563EB !important; color: white !important; }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 1. AUTHENTICATION & LOGIN VIEW (MiQ Split)
# ==========================================
def render_login_page():
    if 'oauth_flow' not in st.session_state:
        try:
            client_config = json.loads(st.secrets["client_secrets"])
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES, redirect_uri='urn:ietf:wg:oauth:2.0:oob')
            st.session_state.oauth_flow = flow
            auth_url, _ = flow.authorization_url(prompt='consent')
            st.session_state.auth_url = auth_url
        except Exception as e:
            st.error(f"Configuration Error: {e}")
            return None

    col_left, col_right = st.columns([1, 1.2], gap="large")
    
    with col_left:
        st.markdown("<br>"*5, unsafe_allow_html=True)
        st.markdown("""
        <h1 style="font-size: 2rem; color: #111827; margin-bottom: 8px;">Welcome Back</h1>
        <p style="color: #4B5563; margin-bottom: 32px;">Sign in to CM360 Bulk Tag Manager.</p>
        """, unsafe_allow_html=True)
        
        st.markdown(f'<a href="{st.session_state.auth_url}" target="_blank" style="text-decoration: none;"><button style="width: 100%; background: #FFFFFF; color: #111827; border: 1px solid #D1D5DB; padding: 12px; border-radius: 8px; font-weight: 600; cursor: pointer; margin-bottom: 16px;">Sign in with Google</button></a>', unsafe_allow_html=True)
        
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

    with col_right:
        st.markdown("""<div style="height: 95vh; width: 100%; border-radius: 24px; margin-top: 12px; background: linear-gradient(135deg, #FFCA01 0%, #FF6500 25%, #FF2000 50%, #EA00AD 75%, #2B0030 100%);"></div>""", unsafe_allow_html=True)


# ==========================================
# 2. MAIN WORKSPACE VIEW (Simple Wireframe Match)
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

    # --- TOP ROW (Profile | Center Header | Sign Out) ---
    head_left, head_center, head_right = st.columns([1.5, 4, 1.5])
    
    with head_left:
        selected_profile_key = st.selectbox("Profile", options=list(profile_dict.keys()), label_visibility="collapsed")
        profile_id = profile_dict[selected_profile_key]
        
    with head_center:
        st.markdown("<h2 style='text-align: center; margin: 0; padding-top: 4px; color: #111827;'>CM360. Bulk event creator</h2>", unsafe_allow_html=True)
        
    with head_right:
        _, btn_col = st.columns([1, 1])
        with btn_col:
            if st.button("Sign out", use_container_width=True):
                del st.session_state['creds']
                st.rerun()

    st.markdown("<hr style='border-top: 1px solid #E5E7EB; margin: 16px 0 32px 0;'>", unsafe_allow_html=True)

    # --- CENTERED CONTENT COLUMN ---
    _, main_col, _ = st.columns([1, 3, 1])
    
    with main_col:
        # --- SECTION 1: UPLOAD DATA ---
        st.markdown("<h3 style='color: #111827; margin-bottom: 16px;'>1. UPLOAD DATA</h3>", unsafe_allow_html=True)
        
        st.markdown("**Drag & drop CSV file or upload CSV file**<br><span style='color: #6B7280; font-size: 0.85rem;'>MAX-200MB</span>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("", type=["csv"], label_visibility="collapsed")
        
        # Download Sample Template
        sample_df = pd.DataFrame([{
            "Tag Name": "Example_Pixel",
            "Level": "CAMPAIGN",
            "Parent ID": "12345678",
            "Tag Type": "IMPRESSION_IMAGE_EVENT_TAG",
            "Tag URL": "https://pixel.example.com"
        }])
        buffer = io.BytesIO()
        sample_df.to_csv(buffer, index=False)
        st.download_button("Download Sample Template", data=buffer.getvalue(), file_name="cm360_template.csv", mime="text/csv")


        # --- SECTION 2: PREVIEW (Hidden until upload) ---
        if uploaded_file is not None:
            st.markdown("<hr style='border-top: 1px solid #E5E7EB; margin: 40px 0;'>", unsafe_allow_html=True)
            st.markdown("<h3 style='color: #111827; margin-bottom: 16px;'>2. Preview</h3>", unsafe_allow_html=True)
            
            df = pd.read_csv(uploaded_file)
            df.columns = df.columns.str.strip()
            
            required_cols = {'Tag Name', 'Level', 'Parent ID', 'Tag Type', 'Tag URL'}
            missing_cols = required_cols - set(df.columns)

            if missing_cols:
                st.error(f"❌ Missing required columns: `{', '.join(missing_cols)}`")
            else:
                st.dataframe(df, use_container_width=True, height=250)

                invalid_urls = df[~df['Tag URL'].astype(str).str.startswith('https://')]
                if not invalid_urls.empty:
                    st.warning(f"⚠️ {len(invalid_urls)} row(s) contain non-HTTPS URLs and will fail.")

                st.markdown("<br>", unsafe_allow_html=True)
                
                # Execute Action
                if st.button("Create Tags", type="primary", use_container_width=True):
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
                            results.append({"Tag Name": tag_name, "Status": "FAILED", "Details": "Invalid Level"})
                            fail_count += 1
                            continue

                        try:
                            req = service.eventTags().insert(profileId=profile_id, body=payload)
                            req.execute()
                            results.append({"Tag Name": tag_name, "Status": "SUCCESS", "Details": "-"})
                            success_count += 1
                        except Exception as e:
                            results.append({"Tag Name": tag_name, "Status": "FAILED", "Details": str(e)})
                            fail_count += 1

                        progress_bar.progress((index + 1) / len(df))
                        status_text.caption(f"Processing: {tag_name}")

                    st.success(f"Execution complete! {success_count} created, {fail_count} failed.")

                    res_df = pd.DataFrame(results)
                    csv_export = res_df.to_csv(index=False).encode('utf-8')
                    st.download_button("Download Execution Log", data=csv_export, file_name="execution_log.csv", mime="text/csv")


# ==========================================
# MAIN ROUTING
# ==========================================
def main():
    if 'creds' not in st.session_state or not st.session_state.creds or not st.session_state.creds.valid:
        render_login_page()
    else:
        render_workspace(st.session_state.creds)

if __name__ == "__main__":
    main()
