import streamlit as st
import pandas as pd
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

st.set_page_config(page_title="CM360 Bulk Event Tags", layout="wide")
st.title("Campaign Manager 360: Bulk Event Tag Creator")

# --- Configuration ---
SCOPES = ['https://www.googleapis.com/auth/dfareporting']
API_SERVICE_NAME = 'dfareporting'
API_VERSION = 'v4' 

# --- Authentication Logic (Adapted from your DV360 tool) ---
def get_creds():
    # 1. Check if token already exists in the user's session
    if 'creds' in st.session_state and st.session_state.creds and st.session_state.creds.valid:
        return st.session_state.creds

    # 2. Start the Manual Copy-Paste Flow
    try:
        # Assuming you pasted the Desktop App JSON directly into Streamlit Secrets
        # e.g., using a variable named `client_secrets`
        client_config = json.loads(st.secrets["client_secrets"])
        flow = InstalledAppFlow.from_client_config(
            client_config, 
            SCOPES, 
            redirect_uri='urn:ietf:wg:oauth:2.0:oob'
        )
    except Exception as e:
        st.error(f"Failed to load secrets. Make sure your secrets are configured. Error: {e}")
        return None

    # Generate the authorization URL
    auth_url, _ = flow.authorization_url(prompt='consent')
    st.info("Please log in with your Google account to access Campaign Manager 360.")
    st.markdown(f"### [🔗 Click here to get your Authorization Code]({auth_url})", unsafe_allow_html=True)
    
    # Text input for the user to paste the code
    auth_code = st.text_input("Paste the authorization code you received here:", type="password")
    
    if auth_code:
        try:
            # Exchange the pasted code for a token
            flow.fetch_token(code=auth_code)
            creds = flow.credentials
            
            # Save the valid credentials into session state
            st.session_state.creds = creds
            st.success("Authentication successful!")
            st.rerun() # Refresh the page to show the main tool
            
        except Exception as e:
            st.error(f"Error fetching token (the code might be expired or invalid): {e}")
            
    return None

# --- Main Application Logic ---
creds = get_creds()

if creds:
    service = build(API_SERVICE_NAME, API_VERSION, credentials=creds)
    
    col1, col2 = st.columns([0.9, 0.1])
    col1.success("Authenticated Successfully with CM360")
    if col2.button("Log Out"):
        del st.session_state['creds']
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
                    results.append({"Tag Name": row['Tag Name'], "Status": f"Failed: {e}", "ID": None})
                    
                # Update visual progress
                progress_bar.progress((index + 1) / len(df))
                status_text.text(f"Processed {index + 1} of {len(df)} tags...")
                
            # Step D: Display Results
            st.success("Bulk upload complete!")
            results_df = pd.DataFrame(results)
            st.dataframe(results_df)
            
            csv_export = results_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download QA Results", data=csv_export, file_name="event_tag_results.csv", mime="text/csv")
