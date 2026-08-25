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

    _, col, _ = st.columns([1, 1.2, 1])
    
    with col:
        # EVERY line of HTML must have ZERO leading spaces to bypass the Markdown parser
        st.markdown(f"""
<div class="login-container">
<div class="login-card">
<div class="login-header">
<div class="login-logo">⚡</div>
<div class="login-title">Sign in to CM360</div>
<div class="login-subtitle">Connect your Google account to continue</div>
</div>
<div class="step-box">
<div class="step-num">1</div>
<div class="step-text">Generate Google Auth Code</div>
</div>
<a href="{auth_url}" target="_blank" style="text-decoration: none;">
<button style="width: 100%; background: #FFFFFF; color: #18181B; border: 1px solid #E4E4E7; padding: 10px; border-radius: 8px; font-weight: 500; cursor: pointer; font-family: Inter, sans-serif; box-shadow: 0 1px 2px rgba(0,0,0,0.05); margin-bottom: 24px;">
Open Google Login Tab ↗
</button>
</a>
<div class="step-box">
<div class="step-num">2</div>
<div class="step-text">Paste Code to Authenticate</div>
</div>
""", unsafe_allow_html=True)
        
        auth_code = st.text_input("Auth Code", label_visibility="collapsed", placeholder="Enter the code here...")
        
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
        
        st.markdown("""
</div>
</div>
""", unsafe_allow_html=True)
