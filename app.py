import streamlit as st
import pandas as pd
import json
import io
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# --- Page Setup ---
st.set_page_config(page_title="CM360 Bulk Event Tag Creation", layout="wide", initial_sidebar_state="collapsed")

# --- API Configuration ---
SCOPES = ['https://www.googleapis.com/auth/dfatrafficking']
API_SERVICE_NAME = 'dfareporting'
API_VERSION = 'v5'

if "client_secrets" not in st.secrets:
    st.error("⚠️ Missing 'client_secrets' in Streamlit secrets configuration.")
    st.stop()

# --- Essential Minimalist Styling ---
st.markdown("""
<style>
/* Global Clean Reset */
#MainMenu, header, footer { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }

.stApp {
    background-color: #FAFAFA !important;
    color: #0F172A !important;
}

/* Base Buttons */
.stButton>button, .stDownloadButton>button {
    border-radius: 6px !important;
    font-weight: 500 !important;
    height: 42px;
}

button[kind="primary"] {
    background-color: #2563EB !important;
    color: #FFFFFF !important;
    border: none !important;
}
button[kind="primary"]:hover {
    background-color: #1D4ED8 !important;
}

button[kind="secondary"], .stDownloadButton>button {
    background-color: #FFFFFF !important;
    color: #334155 !important;
    border: 1px solid #CBD5E1 !important;
}
button[kind="secondary"]:hover, .stDownloadButton>button:hover {
    background-color: #F1F5F9 !important;
}

/* File Uploader Container */
[data-testid="stFileUploadDropzone"] {
    background-color: #FFFFFF !important;
    border: 1px dashed #CBD5E1 !important;
    border-radius: 8px !important;
    padding: 40px !important;
}

/* Table Card */
[data-testid="stDataFrame"] {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
}

/* Step Badges */
.step-number {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    background-color: #2563EB;
    color: #FFFFFF;
    border-radius: 50%;
    font-size: 13px;
    font-weight: 600;
    margin-right: 8px;
}
</style>
""", unsafe_allow_html=True)


# ==========================================
# 1. AUTHENTICATION (Split Screen with MiQ Colors)
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

    col_left, col_right = st.columns([1, 1.2], gap="large")
    
    with col_left:
        st.write("") 
        st.write("") 
        st.write("") 
        st.write("") 
        
        st.markdown(f"""
<div style="padding-top: 40px;">
<h1 style="font-size: 1.8rem; font-weight: 700; color: #0F172A; margin-bottom: 8px;">Welcome Back</h1>
<p style="font-size: 0.95rem; color: #64748B; margin-bottom: 28px;">Sign in to CM360 Bulk Tag Manager.</p>

<a href="{auth_url}" target="_blank" style="text-decoration: none;">
<button style="display: flex; align-items: center; justify-content: center; gap: 10px; width: 100%; background: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1; padding: 12px; border-radius: 8px; font-weight: 600; cursor: pointer; margin-bottom: 16px;">
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
        
        auth_code = st.text_input("Authorization Code", label_visibility="collapsed", placeholder="Paste authorization code here...")
        
        if auth_code:
            try:
                st.session_state.oauth_flow.fetch_token(code=auth_code)
                st.session_state.creds = st.session_state.oauth_flow.credentials
                del st.session_state['oauth_flow']
                del st.session_state['auth_url']
                st.rerun()
            except Exception as e:
                st.error("Invalid authorization code. Please try again.")

    with col_right:
        st.markdown("""
<div style="height: 90vh; width: 100%; border-radius: 16px; margin-top: 12px; background: linear-gradient(135deg, #FFCA01 0%, #FF6500 25%, #FF2000 50%, #EA00AD 75%, #2B0030 100%);">
</div>
""", unsafe_allow_html=True)


# ==========================================
# 2. MAIN WORKSPACE (Simple Vertical Layout)
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

    # Top Header Bar
    h_left, h_right1, h_right2 = st.columns([5, 2, 1])
    with h_left:
        st.markdown("""
        <div style="padding-top: 8px;">
            <strong style="font-size: 1.1rem; color: #0F172A;">CM360</strong>
            <span style="color: #94A3B8; margin: 0 6px;">·</span>
            <span style="color: #64748B;">Bulk Event Tag Creation</span>
        </div>
        """, unsafe_allow_html=True)
    with h_right1:
        selected_profile_key = st.selectbox("Profile", options=list(profile_dict.keys()), label_visibility="collapsed")
        profile_id = profile_dict[selected_profile_key]
    with h_right2:
        if st.button("Sign out", type="secondary", use_container_width=True):
            del st.session_state['creds']
            st.rerun()

    st.markdown("<hr style='border: none; border-top: 1px solid #E2E8F0; margin: 12px 0 32px 0;'>", unsafe_allow_html=True)

    # Main Center Column
    _, main_col, _ = st.columns([1, 4, 1])

    with main_col:
        st.markdown("""
        <h2 style="font-size: 1.6rem; font-weight: 700; color: #0F172A; margin-bottom: 6px;">Bulk Event Tag Creation</h2>
        <p style="color: #64748B; margin-bottom: 28px;">Upload a CSV file to create event tags in bulk. Use the sample template to get started.</p>
        """, unsafe_allow_html=True)

        # STEP 1: UPLOAD DATA
        st.markdown("""
        <div style="font-size: 1.1rem; font-weight: 600; color: #0F172A; margin-bottom: 12px;">
            <span class="step-number">1</span> Upload Data
        </div>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader("Upload CSV File", type=["csv"], label_visibility="collapsed")

        # Download Sample Template Button
        sample_df = pd.DataFrame([{
            "Tag Name": "Example_Impression_Tag",
            "Level": "CAMPAIGN",
            "Parent ID": "12345678",
            "Tag Type": "IMPRESSION_IMAGE_EVENT_TAG",
            "Tag URL": "https://pixel.example.com"
        }])
        buffer = io.BytesIO()
        sample_df.to_csv(buffer, index=False)
        
        st.markdown("<div style='margin-top: 12px;'></div>", unsafe_allow_html=True)
        st.download_button(
            "📥 Download Sample Template", 
            data=buffer.getvalue(), 
            file_name="cm360_event_tags_template.csv", 
            mime="text/csv"
        )

        # STEP 2: PREVIEW & EXECUTE (Conditional on upload)
        if uploaded_file is not None:
            st.markdown("<hr style='border: none; border-top: 1px solid #E2E8F0; margin: 40px 0 28px 0;'>", unsafe_allow_html=True)
            st.markdown("""
            <div style="font-size: 1.1rem; font-weight: 600; color: #0F172A; margin-bottom: 16px;">
                <span class="step-number">2</span> Preview Data
            </div>
            """, unsafe_allow_html=True)

            df = pd.read_csv(uploaded_file)
            df.columns = df.columns.str.strip()
            
            required_cols = {'Tag Name', 'Level', 'Parent ID', 'Tag Type', 'Tag URL'}
            missing_cols = required_cols - set(df.columns)

            if missing_cols:
                st.error(f"❌ Missing required CSV columns: `{', '.join(missing_cols)}`")
            else:
                st.dataframe(df, use_container_width=True, height=280)

                invalid_urls = df[~df['Tag URL'].astype(str).str.startswith('https://')]
                if not invalid_urls.empty:
                    st.warning(f"⚠️ {len(invalid_urls)} row(s) contain URLs that do not start with `https://` and will fail.")

                st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
                
                # Execute Action
                if st.button("Create Tags", type="primary"):
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
                            results.append({"Tag Name": tag_name, "Status": "SUCCESS", "Details": "Created", "ID": res.get('id')})
                            success_count += 1
                        except Exception as e:
                            results.append({"Tag Name": tag_name, "Status": "FAILED", "Details": str(e), "ID": None})
                            fail_count += 1

                        progress_bar.progress((index + 1) / len(df))
                        status_text.caption(f"Processing row {index + 1} of {len(df)}: {tag_name}")

                    st.success(f"Execution complete! {success_count} created, {fail_count} failed.")

                    res_df = pd.DataFrame(results)
                    st.dataframe(res_df, use_container_width=True)

                    csv_export = res_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "📥 Download Audit Log", 
                        data=csv_export, 
                        file_name="cm360_creation_log.csv", 
                        mime="text/csv", 
                        type="secondary"
                    )


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
