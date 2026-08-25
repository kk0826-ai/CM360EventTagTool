import streamlit as st
import pandas as pd
import json
import io
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# --- Page Setup ---
st.set_page_config(
    page_title="CM360 Bulk Event Tag Tool",
    page_icon="🏷️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Configuration ---
SCOPES = ['https://www.googleapis.com/auth/dfatrafficking']
API_SERVICE_NAME = 'dfareporting'
API_VERSION = 'v5'

# Load secrets
if "client_secrets" not in st.secrets:
    st.error("⚠️ Missing secrets configuration! Please check your Streamlit App Settings.")
    st.stop()

# --- Custom Styling for Classic Enterprise UI ---
st.markdown("""
    <style>
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #64748B;
        margin-bottom: 2rem;
    }
    .stMetric {
        background-color: #F8FAFC;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #E2E8F0;
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
            st.error(f"Failed to initialize authentication flow: {e}")
            return None

    flow = st.session_state.oauth_flow
    auth_url = st.session_state.auth_url

    st.markdown("<div class='main-header'>🔐 CM360 Authentication</div>", unsafe_allow_html=True)
    st.info("Log in with your Google account authorized for Campaign Manager 360.")
    st.markdown(f"#### 1. [Click here to get your Authorization Code]({auth_url})", unsafe_allow_html=True)
    
    auth_code = st.text_input("#### 2. Paste your Authorization Code below:", type="password")
    
    if auth_code:
        try:
            flow.fetch_token(code=auth_code)
            creds = flow.credentials
            st.session_state.creds = creds
            
            # Clean session state
            del st.session_state['oauth_flow']
            del st.session_state['auth_url']
            
            st.success("Authentication successful!")
            st.rerun()
        except Exception as e:
            st.error(f"Error fetching token: {e}")
            if 'oauth_flow' in st.session_state:
                del st.session_state['oauth_flow']
                del st.session_state['auth_url']
            
    return None

# --- Main App Controller ---
creds = get_creds()

if creds:
    service = build(API_SERVICE_NAME, API_VERSION, credentials=creds)

    # --- Sidebar Setup ---
    with st.sidebar:
        st.image("https://www.gstatic.com/images/branding/product/2x/campaign_manager_64dp.png", width=50)
        st.title("CM360 Settings")
        
        # Profile Selector
        try:
            profiles_response = service.userProfiles().list().execute()
            profiles = profiles_response.get('items', [])
            
            if not profiles:
                st.error("No active CM360 profiles found for this account.")
                st.stop()
                
            profile_dict = {f"{p['userName']} (ID: {p['accountId']})": p['profileId'] for p in profiles}
            selected_profile_key = st.selectbox("Active Profile", options=list(profile_dict.keys()))
            profile_id = profile_dict[selected_profile_key]
            
            st.caption(f"**Profile ID:** `{profile_id}`")
            
        except Exception as e:
            st.error(f"Error fetching user profiles: {e}")
            st.stop()
            
        st.divider()
        if st.button("🔴 Log Out", use_container_width=True):
            del st.session_state['creds']
            st.rerun()

    # --- Header Banner ---
    st.markdown("<div class='main-header'>Campaign Manager 360: Event Tag Manager</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Bulk create impression & click event tags across Advertisers and Campaigns</div>", unsafe_allow_html=True)

    # --- Tabs Navigation ---
    tab_create, tab_template, tab_docs = st.tabs(["🚀 Bulk Tag Creator", "📋 Download CSV Template", "📖 Field Documentation"])

    # ---------------------------------------------------------
    # TAB 1: BULK CREATOR
    # ---------------------------------------------------------
    with tab_create:
        uploaded_file = st.file_uploader("Upload CSV File", type=["csv"], help="Upload your structured event tags CSV.")

        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            
            # Sanitize column names
            df.columns = df.columns.str.strip()
            
            required_cols = {'Tag Name', 'Level', 'Parent ID', 'Tag Type', 'Tag URL'}
            missing_cols = required_cols - set(df.columns)

            if missing_cols:
                st.error(f"⚠️ Missing required columns in CSV: `{', '.join(missing_cols)}`")
            else:
                st.subheader("Data Preview")
                st.dataframe(df, use_container_width=True)

                # Pre-flight Validation Warning
                invalid_urls = df[~df['Tag URL'].astype(str).str.startswith('https://')]
                if not invalid_urls.empty:
                    st.warning(f"⚠️ Found {len(invalid_urls)} row(s) where 'Tag URL' does not start with `https://`. These will fail during creation.")

                st.divider()

                if st.button("🚀 Execute Bulk Tag Creation", type="primary"):
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
                                "Status": "Failed", 
                                "Error Details": "Invalid Level (Must be ADVERTISER or CAMPAIGN)", 
                                "Tag ID": None
                            })
                            fail_count += 1
                            continue

                        # Make API Call
                        try:
                            request = service.eventTags().insert(profileId=profile_id, body=tag_payload)
                            response = request.execute()
                            results.append({
                                "Row": index + 1,
                                "Tag Name": tag_name, 
                                "Status": "Success", 
                                "Error Details": "None", 
                                "Tag ID": response.get('id')
                            })
                            success_count += 1
                        except Exception as e:
                            results.append({
                                "Row": index + 1,
                                "Tag Name": tag_name, 
                                "Status": "Failed", 
                                "Error Details": str(e), 
                                "Tag ID": None
                            })
                            fail_count += 1

                        # Update UI Progress
                        progress = (index + 1) / len(df)
                        progress_bar.progress(progress)
                        status_text.text(f"Processing row {index + 1} of {len(df)}: {tag_name}")

                    # Execution Summary Dashboard
                    st.subheader("Creation Summary")
                    col_m1, col_m2, col_m3 = st.columns(3)
                    col_m1.metric("Total Rows", len(df))
                    col_m2.metric("Successfully Created", success_count)
                    col_m3.metric("Failed", fail_count)

                    results_df = pd.DataFrame(results)
                    st.dataframe(results_df, use_container_width=True)

                    # Export Log
                    csv_export = results_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "📥 Download Execution Log (CSV)", 
                        data=csv_export, 
                        file_name="cm360_event_tag_log.csv", 
                        mime="text/csv"
                    )

    # ---------------------------------------------------------
    # TAB 2: SAMPLE CSV TEMPLATE
    # ---------------------------------------------------------
    with tab_template:
        st.subheader("Generate Sample Template")
        st.write("Use this pre-formatted CSV template to populate your event tag data.")

        sample_data = pd.DataFrame([
            {
                "Tag Name": "IAS_Impression_JavaScript_Tag",
                "Level": "ADVERTISER",
                "Parent ID": "12345678",
                "Tag Type": "IMPRESSION_JAVASCRIPT_EVENT_TAG",
                "Tag URL": "https://pixel.adsafeprotected.com/jload?anId=9999"
            },
            {
                "Tag Name": "DoubleVerify_Click_Tracker",
                "Level": "CAMPAIGN",
                "Parent ID": "87654321",
                "Tag Type": "CLICK_THROUGH_EVENT_TAG",
                "Tag URL": "https://tm.doubleverify.com/visit?id=123"
            },
            {
                "Tag Name": "Moat_Impression_Image_Tag",
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
            label="📥 Download Sample CSV Template",
            data=buffer.getvalue(),
            file_name="cm360_event_tags_template.csv",
            mime="text/csv"
        )

    # ---------------------------------------------------------
    # TAB 3: DOCUMENTATION
    # ---------------------------------------------------------
    with tab_docs:
        st.subheader("Field Specifications & Rules")
        
        st.markdown("""
        | Field | Description | Allowed Values / Formatting |
        | :--- | :--- | :--- |
        | **Tag Name** | Descriptive name for the tag | Any text (e.g., `IAS_Viewability_Q3`) |
        | **Level** | Scope of the event tag | `ADVERTISER` or `CAMPAIGN` |
        | **Parent ID** | CM360 ID where tag will be attached | Numeric ID (Advertiser ID or Campaign ID) |
        | **Tag Type** | Format/Type of event tag | `IMPRESSION_JAVASCRIPT_EVENT_TAG`<br>`IMPRESSION_IMAGE_EVENT_TAG`<br>`CLICK_THROUGH_EVENT_TAG` |
        | **Tag URL** | Third-party pixel URL | Must start with **`https://`** |
        """)
