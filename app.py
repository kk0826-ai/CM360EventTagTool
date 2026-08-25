import streamlit as st
import pandas as pd
import json
import io
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# --- Page Config ---
st.set_page_config(
    page_title="CM360 Bulk Event Tag Tool",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- API Config ---
SCOPES = ['https://www.googleapis.com/auth/dfatrafficking']
API_SERVICE_NAME = 'dfareporting'
API_VERSION = 'v5'

if "client_secrets" not in st.secrets:
    st.error("⚠️ Missing 'client_secrets' in Streamlit secrets configuration.")
    st.stop()

# --- Custom Modern UI Engine (Video Validator Inspired) ---
st.markdown("""
    <style>
    /* Global Reset & Typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: #0B0F17;
        color: #F1F5F9;
    }

    /* Top Glassmorphic Hero Banner */
    .hero-container {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 28px 32px;
        margin-bottom: 24px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5);
    }
    
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #60A5FA 0%, #A78BFA 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 6px;
        letter-spacing: -0.02em;
    }
    
    .hero-subtitle {
        color: #94A3B8;
        font-size: 1.05rem;
        font-weight: 400;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0F172A !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Tabs Override (Video Validator Pill Navigation) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: transparent;
        border-bottom: 1px solid #1E293B;
        padding-bottom: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 42px;
        background: #1E293B;
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 10px !important;
        color: #94A3B8 !important;
        font-weight: 600;
        font-size: 0.9rem;
        padding: 0 24px;
        transition: all 0.2s ease-in-out;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background: #334155;
        color: #F8FAFC !important;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
        color: #FFFFFF !important;
        border-color: #60A5FA !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35);
    }

    /* Card Containers */
    .content-card {
        background: #1E293B;
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }

    /* Modern Metric Cards */
    div[data-testid="stMetric"] {
        background: linear-gradient(180deg, #1E293B 0%, #0F172A 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }

    div[data-testid="stMetricLabel"] {
        color: #94A3B8 !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    div[data-testid="stMetricValue"] {
        color: #F8FAFC !important;
        font-size: 1.8rem !important;
        font-weight: 800 !important;
    }

    /* Primary Action Buttons */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%);
        border: 1px solid #60A5FA;
        border-radius: 10px;
        color: #FFFFFF;
        font-weight: 600;
        font-size: 1rem;
        padding: 12px 28px;
        transition: all 0.2s ease;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4);
    }

    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.6);
        background: linear-gradient(135deg, #60A5FA 0%, #2563EB 100%);
    }

    /* Secondary Download Buttons */
    .stDownloadButton > button {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 10px;
        color: #38BDF8;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    .stDownloadButton > button:hover {
        background: #334155;
        color: #F8FAFC;
        border-color: #38BDF8;
    }

    /* Custom Badges */
    .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
        background: rgba(56, 189, 248, 0.1);
        color: #38BDF8;
        border: 1px solid rgba(56, 189, 248, 0.2);
    }
    </style>
""", unsafe_allow_html=True)

# --- Authentication Logic ---
def get_creds():
    if 'creds' in st.session_state and st.session_state.creds and st.session_state.creds.valid:
        return st.session_state.creds

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
            st.error(f"Failed to load client configuration: {e}")
            return None

    flow = st.session_state.oauth_flow
    auth_url = st.session_state.auth_url

    st.markdown("""
        <div class="hero-container">
            <div class="hero-title">⚡ CM360 Tool Authorization</div>
            <div class="hero-subtitle">Authenticate your Google Account to manage Campaign Manager 360 Event Tags</div>
        </div>
    """, unsafe_allow_html=True)

    st.info("Follow the two simple steps below to authorize your session.")
    
    col_a, col_b = st.columns([0.5, 0.5])
    with col_a:
        st.markdown(f"""
            <div class="content-card">
                <h4>Step 1: Get Access Code</h4>
                <p style="color: #94A3B8;">Click below to open Google authorization in a new tab.</p>
                <a href="{auth_url}" target="_blank" style="text-decoration: none;">
                    <button style="width: 100%; background: #2563EB; color: white; border: none; padding: 10px; border-radius: 8px; font-weight: 600; cursor: pointer;">
                        🔗 Launch Google Login
                    </button>
                </a>
            </div>
        """, unsafe_allow_html=True)

    with col_b:
        st.markdown("<div class='content-card'><h4>Step 2: Submit Token</h4>", unsafe_allow_html=True)
        auth_code = st.text_input("Paste authorization code here:", type="password", label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)
    
    if auth_code:
        try:
            flow.fetch_token(code=auth_code)
            creds = flow.credentials
            st.session_state.creds = creds
            
            del st.session_state['oauth_flow']
            del st.session_state['auth_url']
            
            st.success("Authorization successful! Loading environment...")
            st.rerun()
        except Exception as e:
            st.error(f"Error fetching token: {e}")
            if 'oauth_flow' in st.session_state:
                del st.session_state['oauth_flow']
                del st.session_state['auth_url']
            
    return None

# --- Main App Execution ---
creds = get_creds()

if creds:
    service = build(API_SERVICE_NAME, API_VERSION, credentials=creds)

    # --- Sidebar Setup ---
    with st.sidebar:
        st.markdown("<h3 style='color: #F8FAFC; margin-bottom: 20px;'>⚙️ Environment Settings</h3>", unsafe_allow_html=True)
        
        try:
            profiles_response = service.userProfiles().list().execute()
            profiles = profiles_response.get('items', [])
            
            if not profiles:
                st.error("No active CM360 profiles found for this user.")
                st.stop()
                
            profile_dict = {f"{p['userName']} (ID: {p['accountId']})": p['profileId'] for p in profiles}
            selected_profile_key = st.selectbox("Active User Profile", options=list(profile_dict.keys()))
            profile_id = profile_dict[selected_profile_key]
            
            st.markdown(f"<div style='margin-top: 10px;'><span class='badge'>Profile ID: {profile_id}</span></div>", unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Error retrieving user profiles: {e}")
            st.stop()
            
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.divider()
        if st.button("🔴 Terminate Session", use_container_width=True):
            del st.session_state['creds']
            st.rerun()

    # --- Main Hero Section ---
    st.markdown("""
        <div class="hero-container">
            <div class="hero-title">CM360 Bulk Event Tag Engine</div>
            <div class="hero-subtitle">Programmatically generate, validate, and apply tracking tags across Advertisers and Campaigns</div>
        </div>
    """, unsafe_allow_html=True)

    # --- Navigation Tabs ---
    tab_create, tab_template, tab_docs = st.tabs(["🚀 Bulk Execution", "📋 Sample Template", "📖 API Specifications"])

    # ---------------------------------------------------------
    # TAB 1: BULK EXECUTION ENGINE
    # ---------------------------------------------------------
    with tab_create:
        uploaded_file = st.file_uploader("Upload CSV Spreadsheet", type=["csv"], help="Upload CSV formatted according to the spec.")

        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            df.columns = df.columns.str.strip()
            
            required_cols = {'Tag Name', 'Level', 'Parent ID', 'Tag Type', 'Tag URL'}
            missing_cols = required_cols - set(df.columns)

            if missing_cols:
                st.error(f"❌ Missing required columns: `{', '.join(missing_cols)}`")
            else:
                st.markdown("<h4 style='color: #F8FAFC;'>Parsed Input Preview</h4>", unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True)

                invalid_urls = df[~df['Tag URL'].astype(str).str.startswith('https://')]
                if not invalid_urls.empty:
                    st.warning(f"⚠️ Warning: {len(invalid_urls)} row(s) contain non-HTTPS URLs which will trigger CM360 validation errors.")

                st.markdown("<br>", unsafe_allow_html=True)

                if st.button("🚀 Run Bulk Event Creation", type="primary"):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    results = []
                    
                    success_count = 0
                    fail_count = 0

                    for index, row in df.iterrows():
                        tag_name = str(row['Tag Name']).strip()
                        level = str(row['Level']).strip().upper()
                        parent_id = str(row['Parent ID']).strip()
                        tag_type = str(row['Tag Type']).strip()
                        tag_url = str(row['Tag URL']).strip()

                        tag_payload = {
                            "name": tag_name,
                            "status": "ENABLED", 
                            "type": tag_type,
                            "url": tag_url
                        }
                        
                        if level == 'ADVERTISER':
                            tag_payload["advertiserId"] = parent_id
                        elif level == 'CAMPAIGN':
                            tag_payload["campaignId"] = parent_id
                        else:
                            results.append({
                                "Row": index + 1,
                                "Tag Name": tag_name, 
                                "Status": "FAILED", 
                                "Details": "Invalid Level (Must be ADVERTISER or CAMPAIGN)", 
                                "Generated ID": None
                            })
                            fail_count += 1
                            continue

                        try:
                            request = service.eventTags().insert(profileId=profile_id, body=tag_payload)
                            response = request.execute()
                            results.append({
                                "Row": index + 1,
                                "Tag Name": tag_name, 
                                "Status": "SUCCESS", 
                                "Details": "Created Successfully", 
                                "Generated ID": response.get('id')
                            })
                            success_count += 1
                        except Exception as e:
                            results.append({
                                "Row": index + 1,
                                "Tag Name": tag_name, 
                                "Status": "FAILED", 
                                "Details": str(e), 
                                "Generated ID": None
                            })
                            fail_count += 1

                        progress = (index + 1) / len(df)
                        progress_bar.progress(progress)
                        status_text.text(f"Processing row {index + 1} of {len(df)}: {tag_name}")

                    st.markdown("<br><h4 style='color: #F8FAFC;'>Execution Summary</h4>", unsafe_allow_html=True)
                    col_m1, col_m2, col_m3 = st.columns(3)
                    col_m1.metric("Total Executed", len(df))
                    col_m2.metric("Successful", success_count)
                    col_m3.metric("Failed", fail_count)

                    results_df = pd.DataFrame(results)
                    st.dataframe(results_df, use_container_width=True)

                    csv_export = results_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "📥 Download Execution Audit Log", 
                        data=csv_export, 
                        file_name="cm360_event_tag_audit_log.csv", 
                        mime="text/csv"
                    )

    # ---------------------------------------------------------
    # TAB 2: TEMPLATE GENERATOR
    # ---------------------------------------------------------
    with tab_template:
        st.markdown("<h4 style='color: #F8FAFC;'>Download Starter CSV</h4>", unsafe_allow_html=True)
        st.write("Use this sample file structure to prepare your bulk uploads.")

        sample_data = pd.DataFrame([
            {
                "Tag Name": "IAS_Impability_JS_Q3",
                "Level": "ADVERTISER",
                "Parent ID": "12345678",
                "Tag Type": "IMPRESSION_JAVASCRIPT_EVENT_TAG",
                "Tag URL": "https://pixel.adsafeprotected.com/jload?anId=9999"
            },
            {
                "Tag Name": "DV_Click_Tracker",
                "Level": "CAMPAIGN",
                "Parent ID": "87654321",
                "Tag Type": "CLICK_THROUGH_EVENT_TAG",
                "Tag URL": "https://tm.doubleverify.com/visit?id=123"
            },
            {
                "Tag Name": "Moat_Standard_Image_Pixel",
                "Level": "CAMPAIGN",
                "Parent ID": "87654321",
                "Tag Type": "IMPRESSION_IMAGE_EVENT_TAG",
                "Tag URL": "https://z.moatads.com/pixel.gif?m=1"
            }
        ])

        st.dataframe(sample_data, use_container_width=True)

        buffer = io.BytesIO()
        sample_data.to_csv(buffer, index=False)
        st.download_button(
            label="📥 Download Template CSV",
            data=buffer.getvalue(),
            file_name="cm360_event_tags_template.csv",
            mime="text/csv"
        )

    # ---------------------------------------------------------
    # TAB 3: FIELD SPECIFICATIONS
    # ---------------------------------------------------------
    with tab_docs:
        st.markdown("<h4 style='color: #F8FAFC;'>Field Mapping Specifications</h4>", unsafe_allow_html=True)
        
        st.markdown("""
        | Field Name | Scope | API Requirement & Formatting |
        | :--- | :--- | :--- |
        | `Tag Name` | Required | Free text identifier for the tag in CM360 |
        | `Level` | Required | Must be strictly set to **`ADVERTISER`** or **`CAMPAIGN`** |
        | `Parent ID` | Required | Numeric ID corresponding to the chosen Level |
        | `Tag Type` | Required | Must match one of: `IMPRESSION_JAVASCRIPT_EVENT_TAG`, `IMPRESSION_IMAGE_EVENT_TAG`, `CLICK_THROUGH_EVENT_TAG` |
        | `Tag URL` | Required | Third-party endpoint URL. Must start with **`https://`** |
        """)
