import streamlit as st
import pandas as pd
import json
import io
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# --- Page Config (Must be first) ---
st.set_page_config(page_title="CM360 Tag Manager", layout="wide", initial_sidebar_state="expanded")

# --- API Config ---
SCOPES = ['https://www.googleapis.com/auth/dfatrafficking']
API_SERVICE_NAME = 'dfareporting'
API_VERSION = 'v5'

if "client_secrets" not in st.secrets:
    st.error("⚠️ Missing 'client_secrets' in Streamlit secrets configuration.")
    st.stop()

# ==========================================
# 1. AUTHENTICATION & LOGIN VIEW (MiQ Style)
# ==========================================
def render_login_page():
    # Hide the sidebar entirely on the login page
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {display: none !important;}
        .stApp { background-color: #FFFFFF !important; color: #0F172A !important; }
        </style>
    """, unsafe_allow_html=True)

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
        st.markdown("<br>"*6, unsafe_allow_html=True)
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
        st.markdown("""
        <div style="height: 95vh; width: 100%; border-radius: 24px; margin-top: 12px; background: linear-gradient(135deg, #FFCA01 0%, #FF6500 25%, #FF2000 50%, #EA00AD 75%, #2B0030 100%); box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);">
        </div>
        """, unsafe_allow_html=True)


# ==========================================
# 2. MAIN SAAS WORKSPACE VIEW (NEW UI)
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

    # --- Workspace CSS Engine ---
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif !important; }
    #MainMenu, header, footer {display: none !important;}
    
    /* Global App Background */
    .stApp { background-color: #F8FAFC !important; color: #0F172A !important; }

    /* --- SIDEBAR STYLING --- */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0;
        min-width: 260px !important;
        max-width: 260px !important;
    }
    
    /* Push profile to the bottom of sidebar */
    .sidebar-profile-box {
        background: #F8FAFC;
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #E2E8F0;
        margin-top: 40vh; /* Pushes to bottom visually */
    }

    /* Override Selectbox & Logout Button in Sidebar */
    .stSelectbox > div > div {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
    }
    .stButton>button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease;
    }
    
    /* --- MAIN CONTENT CARDS --- */
    /* Target the file uploader container to look like Card 1 */
    [data-testid="stFileUploader"] {
        background: #FFFFFF;
        padding: 24px;
        border-radius: 16px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
        margin-bottom: 24px;
    }
    [data-testid="stFileUploadDropzone"] {
        background-color: #FFFFFF !important;
        border: 2px dashed #CBD5E1 !important;
        border-radius: 12px !important;
        padding: 32px !important;
    }
    
    /* Primary execute button styling */
    button[kind="primary"] {
        background: #2563EB !important;
        color: #FFFFFF !important;
        border: none !important;
        height: 48px;
    }
    button[kind="primary"]:hover { background: #1D4ED8 !important; }
    
    /* Target Dataframe container to look like a card */
    [data-testid="stDataFrame"] {
        background: #FFFFFF;
        padding: 16px;
        border-radius: 16px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    
    /* Custom Headers */
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }
    .card-title {
        display: flex;
        align-items: center;
        gap: 12px;
        font-weight: 700;
        color: #0F172A;
        font-size: 1.05rem;
    }
    .step-circle {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.85rem;
        font-weight: 700;
    }
    .step-blue { background: #2563EB; color: white; }
    .step-gray { background: #E2E8F0; color: #64748B; }
    .step-subtext {
        font-size: 0.75rem;
        color: #94A3B8;
        font-weight: 700;
        letter-spacing: 0.05em;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- Sidebar Construction ---
    with st.sidebar:
        # Navigation Mockup
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 40px; margin-top: 10px;">
            <div style="background: #2563EB; color: white; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: bold;">P</div>
            <span style="font-weight: 700; font-size: 1.2rem; color: #0F172A;">PixelGen</span>
        </div>
        <p style="font-size: 0.75rem; font-weight: 700; color: #94A3B8; letter-spacing: 0.05em; margin-bottom: 12px;">CORE ENGINE</p>
        <div style="color: #64748B; font-weight: 500; font-size: 0.95rem; padding: 10px 12px; margin-bottom: 4px;">Overview</div>
        <div style="color: #2563EB; font-weight: 600; font-size: 0.95rem; padding: 10px 12px; background: #EFF6FF; border-radius: 8px; margin-bottom: 4px;">Bulk Event Tags</div>
        <div style="color: #64748B; font-weight: 500; font-size: 0.95rem; padding: 10px 12px; margin-bottom: 4px;">Run History</div>
        """, unsafe_allow_html=True)

        # Bottom Profile & Logout block
        st.markdown('<div class="sidebar-profile-box">', unsafe_allow_html=True)
        st.markdown('<p style="font-size: 0.85rem; font-weight: 600; color: #0F172A; margin: 0 0 8px 0;">Active Profile</p>', unsafe_allow_html=True)
        selected_profile_key = st.selectbox("Profile", options=list(profile_dict.keys()), label_visibility="collapsed")
        profile_id = profile_dict[selected_profile_key]
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Sign Out", use_container_width=True):
            del st.session_state['creds']
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


    # --- Main Header ---
    st.markdown("""
    <div style="margin-top: 10px; margin-bottom: 32px;">
        <h1 style="font-size: 1.5rem; font-weight: 700; color: #0F172A; margin: 0 0 4px 0;">Bulk Event Tags</h1>
        <p style="font-size: 0.95rem; color: #64748B; margin: 0;">Upload, preview, and generate pixels across campaigns.</p>
    </div>
    """, unsafe_allow_html=True)

    # --- Two Column Layout (Bento Box Style) ---
    work_left, work_right = st.columns([1, 1.5], gap="large")

    with work_left:
        # 1. UPLOAD CARD 
        st.markdown("""
        <div class="card-header">
            <div class="card-title"><div class="step-circle step-blue">1</div> Upload Data</div>
            <div class="step-subtext">STEP 1 OF 2</div>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader("Upload CSV", type=["csv"], label_visibility="collapsed")
        
        # Download Template Expander
        with st.expander("📄 Download CSV Template"):
            st.write("Ensure your headers match exactly.")
            sample_df = pd.DataFrame([{"Tag Name": "Example", "Level": "CAMPAIGN", "Parent ID": "123", "Tag Type": "IMPRESSION_IMAGE_EVENT_TAG", "Tag URL": "https://url.com"}])
            buffer = io.BytesIO()
            sample_df.to_csv(buffer, index=False)
            st.download_button("Download Now", data=buffer.getvalue(), file_name="template.csv", mime="text/csv")

        # 2. RECENT ACTIVITY CARD (HTML Mockup)
        st.markdown("""
        <div style="background: #FFFFFF; border-radius: 16px; border: 1px solid #E2E8F0; padding: 24px; margin-top: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
            <div style="display: flex; justify-content: space-between; margin-bottom: 24px;">
                <h3 style="margin: 0; font-size: 1.05rem; font-weight: 700; color: #0F172A;">Recent Activity</h3>
                <span style="color: #2563EB; font-size: 0.85rem; font-weight: 600; cursor: pointer;">View All</span>
            </div>
            
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;">
                <div style="display: flex; gap: 12px; align-items: center;">
                    <div style="width: 32px; height: 32px; border-radius: 50%; background: #DCFCE7; color: #16A34A; display: flex; align-items: center; justify-content: center; font-weight: bold;">✓</div>
                    <div>
                        <p style="margin: 0; font-weight: 700; font-size: 0.9rem; color: #0F172A;">events_batch_sept.csv</p>
                        <p style="margin: 0; font-size: 0.8rem; color: #64748B;">Completed 12 mins ago</p>
                    </div>
                </div>
                <div style="background: #DCFCE7; color: #16A34A; font-size: 0.7rem; font-weight: 700; padding: 4px 8px; border-radius: 6px;">SUCCESS</div>
            </div>

            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; gap: 12px; align-items: center;">
                    <div style="width: 32px; height: 32px; border-radius: 50%; background: #FEE2E2; color: #DC2626; display: flex; align-items: center; justify-content: center; font-weight: bold;">✕</div>
                    <div>
                        <p style="margin: 0; font-weight: 700; font-size: 0.9rem; color: #0F172A;">raw_pixels_dump.csv</p>
                        <p style="margin: 0; font-size: 0.8rem; color: #64748B;">Failed 2 hrs ago</p>
                    </div>
                </div>
                <div style="background: #FEE2E2; color: #DC2626; font-size: 0.7rem; font-weight: 700; padding: 4px 8px; border-radius: 6px;">ERROR</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


    with work_right:
        # 3. PREVIEW & EXECUTE CARD
        st.markdown("""
        <div class="card-header" style="margin-bottom: 10px;">
            <div class="card-title"><div class="step-circle step-gray">2</div> Preview & Execute</div>
        </div>
        """, unsafe_allow_html=True)
        
        # EMPTY STATE
        if not uploaded_file:
            st.markdown("""
            <div style="background: #FFFFFF; border-radius: 16px; border: 1px solid #E2E8F0; padding: 80px 40px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                <div style="width: 80px; height: 80px; background: #F1F5F9; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 24px auto;">
                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#64748B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="8" y1="6" x2="21" y2="6"></line>
                        <line x1="8" y1="12" x2="21" y2="12"></line>
                        <line x1="8" y1="18" x2="21" y2="18"></line>
                        <line x1="3" y1="6" x2="3.01" y2="6"></line>
                        <line x1="3" y1="12" x2="3.01" y2="12"></line>
                        <line x1="3" y1="18" x2="3.01" y2="18"></line>
                    </svg>
                </div>
                <h2 style="font-size: 1.25rem; font-weight: 700; color: #0F172A; margin: 0 0 8px 0;">Ready to preview your data</h2>
                <p style="font-size: 0.95rem; color: #64748B; max-width: 400px; margin: 0 auto;">Upload a CSV file on the left to preview your records, map headers, and execute the creation process.</p>
            </div>
            """, unsafe_allow_html=True)
        
        # FILLED STATE
        else:
            df = pd.read_csv(uploaded_file)
            df.columns = df.columns.str.strip()
            
            required_cols = {'Tag Name', 'Level', 'Parent ID', 'Tag Type', 'Tag URL'}
            missing_cols = required_cols - set(df.columns)

            if missing_cols:
                st.error(f"❌ Invalid format. Missing columns: `{', '.join(missing_cols)}`")
            else:
                st.dataframe(df, use_container_width=True, height=400)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Align the execute button to the right like the mockup
                _, btn_col = st.columns([2, 1])
                with btn_col:
                    if st.button("Start Tagging Process", type="primary", use_container_width=True):
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

                        st.success(f"Execution complete! {success_count} tags created, {fail_count} failed.")

                        res_df = pd.DataFrame(results)
                        csv_export = res_df.to_csv(index=False).encode('utf-8')
                        st.download_button("Download Execution Log", data=csv_export, file_name="tag_log.csv", mime="text/csv")


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
