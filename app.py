import streamlit as st
import pandas as pd
import json
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# --- 1. Configuration ---
SCOPES = ['https://www.googleapis.com/auth/dfareporting']
API_SERVICE_NAME = 'dfareporting'
API_VERSION = 'v4' 

st.set_page_config(page_title="CM360 Bulk Event Tags", layout="wide")
st.title("Campaign Manager 360: Bulk Event Tag Creator")

# Load the secret from Streamlit Cloud
if "client_secrets" not in st.secrets:
    st.error("Missing secrets! Please make sure the 'client_secrets' block is configured in your Streamlit App Settings.")
    st.stop()

# Parse the JSON string from secrets
client_config = json.loads(st.secrets["client_secrets"])
# Extract the redirect URI dynamically
REDIRECT_URI = client_config["web"]["redirect_uris"][0] 

# --- 2. Web Authentication Flow ---
def authenticate():
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

    # 1. Check if token already exists in the user's session
    if 'creds_token' in st.session_state:
        creds = Credentials.from_authorized_user_info(st.session_state['creds_token'], SCOPES)
        if creds.valid:
            return build(API_SERVICE_NAME, API_VERSION, credentials=creds)

    # 2. Check if the URL contains the auth code (user just logged in)
    if 'code' in st.query_params:
        auth_code = st.query_params['code']
        try:
            # Try to exchange the code for a token
            flow.fetch_token(code=auth_code)
            creds = flow.credentials
            
            # Save token to session and clear the URL so it looks clean
            st.session_state['creds_token'] = json.loads(creds.to_json())
            st.query_params.clear()
            st.rerun()
            
        except Exception as e:
            # If the code was already used or expired, clear the URL and stop gracefully
            st.query_params.clear()
            st.warning("Login session expired or the page was refreshed. Please click Login again.")
            st.stop()

    # 3. If neither, present the login button
    auth_url, _ = flow.authorization_url(prompt='consent')
    st.info("Please log in with your Google account to access Campaign Manager 360.")
    st.link_button("Login with Google", auth_url, type="primary")
    st.stop() # Halts the rest of the app until they log in

# --- 3. Main Application ---
service = authenticate()

if service:
    # Top bar showing login success and logout button
    col1, col2 = st.columns([0.9, 0.1])
    col1.success("Authenticated Successfully")
    if col2.button("Log Out"):
        del st.session_state['creds_token']
        st.rerun()

    st.divider()

    # Step A: Select CM360 Profile
    try:
        profiles_response = service.userProfiles().list().execute()
        profiles = profiles_response.get('items', [])
        
        if not profiles:
            st.error("No CM360 profiles found for your account.")
            st.stop()
            
        profile_dict = {f"{p['userName']} (Account ID: {p['accountId']})": p['profileId'] for p in profiles}
        selected_profile_key = st.selectbox("Select your CM360 Profile", options=list(profile_dict.keys()))
        profile_id = profile_dict[selected_profile_key]
        
    except Exception as e:
        st.error(f"Error fetching profiles: {e}")
        st.stop()

    st.divider()

    # Step B: Upload CSV File
    st.subheader("Upload your Event Tags")
    st.markdown("Ensure your CSV has these exact columns: **Tag Name, Level, Parent ID, Tag Type, Tag URL**")
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write("Data Preview:")
        st.dataframe(df.head())
        
        # Step C: Execution Engine
        if st.button("Create Tags in CM360", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            results = []
            
            for index, row in df.iterrows():
                tag_payload = {
                    "name": str(row['Tag Name']),
                    "status": "ENABLED", 
                    "type": str(row['Tag Type']).strip(),
                    "url": str(row['Tag URL']).strip()
                }
                
                level = str(row['Level']).strip().upper()
                
                if level == 'ADVERTISER':
                    tag_payload["advertiserId"] = str(row['Parent ID'])
                elif level == 'CAMPAIGN':
                    tag_payload["campaignId"] = str(row['Parent ID'])
                else:
                    results.append({"Tag Name": row['Tag Name'], "Status": "Failed: Invalid Level (Must be ADVERTISER or CAMPAIGN)", "ID": None})
                    continue
                    
                # Call the CM360 API
                try:
                    request = service.eventTags().insert(profileId=profile_id, body=tag_payload)
                    response = request.execute()
                    results.append({"Tag Name": row['Tag Name'], "Status": "Success", "ID": response['id']})
                    
                except Exception as e:
                    # Catch API errors (e.g. invalid URL format, non-whitelisted domain, wrong parent ID)
                    results.append({"Tag Name": row['Tag Name'], "Status": f"Failed: {e}", "ID": None})
                    
                # Update visual progress
                progress_bar.progress((index + 1) / len(df))
                status_text.text(f"Processed {index + 1} of {len(df)} tags...")
                
            # Step D: Display Results
            st.success("Bulk upload complete!")
            results_df = pd.DataFrame(results)
            st.dataframe(results_df)
            
            # Allow users to download the success/fail log
            csv_export = results_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download QA Results", data=csv_export, file_name="event_tag_results.csv", mime="text/csv")
