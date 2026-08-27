import streamlit as st
import pandas as pd
import json
import io
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="CM360 - Bulk Event Tag Creation",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# API CONFIG
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/dfatrafficking"
]

API_SERVICE_NAME = "dfareporting"
API_VERSION = "v5"


# ============================================================
# GLOBAL CSS
# ============================================================

st.markdown(
    """
    <style>

    /* --------------------------------------------------------
       GLOBAL
    -------------------------------------------------------- */

    #MainMenu,
    header,
    footer {
        display: none !important;
    }

    section[data-testid="stSidebar"] {
        display: none !important;
    }

    .stApp {
        background: #FFFFFF !important;
        color: #111827 !important;
    }

    .main .block-container {
        padding-top: 0rem !important;
        padding-bottom: 4rem !important;
        max-width: 100% !important;
    }

    /* Remove default Streamlit top spacing */
    [data-testid="stAppViewContainer"] {
        background: #FFFFFF !important;
    }


    /* --------------------------------------------------------
       TOP NAVIGATION
    -------------------------------------------------------- */

    .top-nav {
        height: 66px;
        border-bottom: 1px solid #E5E7EB;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 40px;
        background: #FFFFFF;
        box-sizing: border-box;
    }

    .brand {
        display: flex;
        align-items: center;
        gap: 14px;
        font-size: 16px;
        white-space: nowrap;
    }

    .brand-main {
        font-weight: 700;
        color: #111827;
    }

    .brand-divider {
        color: #D1D5DB;
    }

    .brand-subtitle {
        color: #9CA3AF;
        font-weight: 400;
    }


    /* --------------------------------------------------------
       MAIN CONTENT
    -------------------------------------------------------- */

    .workspace {
        width: 100%;
        max-width: 1120px;
        margin: 0 auto;
        padding-top: 42px;
    }

    .page-title {
        font-size: 28px;
        line-height: 36px;
        font-weight: 700;
        color: #111827;
        margin: 0 0 4px 0;
    }

    .page-subtitle {
        font-size: 14px;
        line-height: 22px;
        color: #9CA3AF;
        margin: 0;
    }


    /* --------------------------------------------------------
       SECTION HEADERS
    -------------------------------------------------------- */

    .section-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-top: 38px;
        margin-bottom: 16px;
    }

    .step-number {
        width: 24px;
        height: 24px;
        min-width: 24px;
        border-radius: 50%;
        background: #2F80ED;
        color: #FFFFFF;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 13px;
        font-weight: 600;
    }

    .section-title {
        font-size: 16px;
        font-weight: 600;
        color: #111827;
        margin: 0;
    }


    /* --------------------------------------------------------
       UPLOAD AREA
    -------------------------------------------------------- */

    .upload-wrapper {
        border: 2px dashed #E5E7EB;
        border-radius: 14px;
        background: #FAFAFA;
        min-height: 350px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        box-sizing: border-box;
        padding: 30px;
    }

    .upload-icon {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        background: #E8F1FF;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 14px;
    }

    .upload-icon svg {
        width: 25px;
        height: 25px;
        stroke: #2F80ED;
    }

    .upload-title {
        font-size: 16px;
        font-weight: 600;
        color: #111827;
        margin-bottom: 8px;
    }

    .upload-or {
        font-size: 13px;
        color: #9CA3AF;
        margin-bottom: 8px;
    }

    .upload-info {
        font-size: 12px;
        color: #A3A3A3;
        margin-top: 8px;
    }


    /* --------------------------------------------------------
       STREAMLIT FILE UPLOADER
    -------------------------------------------------------- */

    div[data-testid="stFileUploader"] {
        width: 100%;
        max-width: 430px;
        margin: 0 auto;
    }

    div[data-testid="stFileUploader"] section {
        border: none !important;
        background: transparent !important;
        padding: 0 !important;
    }

    div[data-testid="stFileUploader"] section > div {
        border: none !important;
        background: transparent !important;
        padding: 0 !important;
    }

    div[data-testid="stFileUploader"] label {
        display: none !important;
    }

    div[data-testid="stFileUploader"] small {
        display: none !important;
    }

    div[data-testid="stFileUploader"] button {
        background: #2F80ED !important;
        color: white !important;
        border: none !important;
        border-radius: 7px !important;
        font-weight: 600 !important;
        padding: 8px 18px !important;
        min-height: 36px !important;
    }

    div[data-testid="stFileUploader"] button:hover {
        background: #2563EB !important;
    }


    /* --------------------------------------------------------
       SAMPLE TEMPLATE BUTTON
    -------------------------------------------------------- */

    div[data-testid="stDownloadButton"] {
        margin-top: 12px;
        display: flex;
        justify-content: center;
    }

    div[data-testid="stDownloadButton"] button {
        background: #FFFFFF !important;
        color: #111827 !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        min-height: 38px !important;
        padding: 7px 18px !important;
    }

    div[data-testid="stDownloadButton"] button:hover {
        background: #F9FAFB !important;
        border-color: #D1D5DB !important;
    }


    /* --------------------------------------------------------
       PREVIEW TABLE
    -------------------------------------------------------- */

    .preview-container {
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        overflow: hidden;
        background: #FFFFFF;
    }

    .preview-footer {
        height: 38px;
        background: #F9FAFB;
        border-top: 1px solid #E5E7EB;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 16px;
        color: #9CA3AF;
        font-size: 12px;
    }


    /* --------------------------------------------------------
       CREATE TAGS BUTTON
    -------------------------------------------------------- */

    .create-button-container {
        display: flex;
        justify-content: center;
        margin-top: 30px;
        margin-bottom: 20px;
    }

    div[data-testid="stButton"] {
        display: flex;
        justify-content: center;
    }

    div[data-testid="stButton"] button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        min-height: 42px !important;
        padding: 0 30px !important;
    }

    div[data-testid="stButton"] button[kind="primary"] {
        background: #2F80ED !important;
        border-color: #2F80ED !important;
        color: white !important;
    }

    div[data-testid="stButton"] button[kind="primary"]:hover {
        background: #2563EB !important;
        border-color: #2563EB !important;
    }


    /* --------------------------------------------------------
       PROFILE SELECTBOX
    -------------------------------------------------------- */

    div[data-testid="stSelectbox"] {
        margin: 0 !important;
    }

    div[data-testid="stSelectbox"] label {
        display: none !important;
    }

    div[data-testid="stSelectbox"] > div > div {
        min-height: 38px !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 8px !important;
        background: #FFFFFF !important;
    }

    div[data-testid="stSelectbox"] svg {
        color: #6B7280 !important;
    }


    /* --------------------------------------------------------
       SIGN OUT
    -------------------------------------------------------- */

    .signout-button button {
        border: 1px solid #E5E7EB !important;
        background: #FFFFFF !important;
        color: #111827 !important;
    }


    /* --------------------------------------------------------
       ALERTS
    -------------------------------------------------------- */

    div[data-testid="stAlert"] {
        border-radius: 8px !important;
    }


    /* --------------------------------------------------------
       RESPONSIVE
    -------------------------------------------------------- */

    @media (max-width: 900px) {

        .top-nav {
            padding: 0 20px;
        }

        .workspace {
            padding-left: 20px;
            padding-right: 20px;
        }

        .brand-subtitle {
            display: none;
        }

        .brand-divider {
            display: none;
        }

    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# AUTHENTICATION
# ============================================================

def render_login_page():

    if "oauth_flow" not in st.session_state:

        try:
            client_config = json.loads(
                st.secrets["client_secrets"]
            )

            flow = InstalledAppFlow.from_client_config(
                client_config,
                SCOPES,
                redirect_uri="urn:ietf:wg:oauth:2.0:oob"
            )

            st.session_state.oauth_flow = flow

            auth_url, _ = flow.authorization_url(
                prompt="consent"
            )

            st.session_state.auth_url = auth_url

        except Exception as e:
            st.error(f"Configuration Error: {e}")
            return

    st.markdown(
        """
        <div style="
            max-width: 1000px;
            margin: 80px auto;
            padding: 40px;
        ">
        """,
        unsafe_allow_html=True
    )

    col_left, col_right = st.columns(
        [1, 1],
        gap="large"
    )

    with col_left:

        st.markdown(
            """
            <div style="padding-top:80px;">
                <h1 style="
                    font-size:32px;
                    color:#111827;
                    margin-bottom:8px;
                ">
                    Welcome Back
                </h1>

                <p style="
                    color:#6B7280;
                    margin-bottom:30px;
                ">
                    Sign in to CM360 Bulk Tag Manager.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <a
                href="{st.session_state.auth_url}"
                target="_blank"
                style="text-decoration:none;"
            >
                <button style="
                    width:100%;
                    background:#FFFFFF;
                    color:#111827;
                    border:1px solid #D1D5DB;
                    padding:12px;
                    border-radius:8px;
                    font-weight:600;
                    cursor:pointer;
                ">
                    Sign in with Google
                </button>
            </a>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<br>", unsafe_allow_html=True)

        auth_code = st.text_input(
            "Authorization Code",
            label_visibility="collapsed",
            placeholder="Paste your authorization code here..."
        )

        if auth_code:

            try:

                st.session_state.oauth_flow.fetch_token(
                    code=auth_code
                )

                st.session_state.creds = (
                    st.session_state.oauth_flow.credentials
                )

                del st.session_state["oauth_flow"]
                del st.session_state["auth_url"]

                st.rerun()

            except Exception:
                st.error(
                    "Invalid or expired code. Please try again."
                )

    with col_right:

        st.markdown(
            """
            <div style="
                height:600px;
                width:100%;
                border-radius:24px;
                background:
                    linear-gradient(
                        135deg,
                        #FFCA01 0%,
                        #FF6500 25%,
                        #FF2000 50%,
                        #EA00AD 75%,
                        #2B0030 100%
                    );
            ">
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# TOP NAVIGATION
# ============================================================

def render_top_nav(profile_dict):

    nav_left, nav_right = st.columns(
        [7, 3],
        vertical_alignment="center"
    )

    with nav_left:

        st.markdown(
            """
            <div class="top-nav" style="
                border:none;
                padding-left:40px;
                justify-content:flex-start;
            ">
                <div class="brand">
                    <span class="brand-main">CM360</span>
                    <span class="brand-divider">·</span>
                    <span class="brand-subtitle">
                        Bulk Event Tag Creation
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with nav_right:

        profile_col, logout_col = st.columns(
            [2.2, 1.2],
            gap="small",
            vertical_alignment="center"
        )

        with profile_col:

            selected_profile_key = st.selectbox(
                "Profile",
                options=list(profile_dict.keys()),
                label_visibility="collapsed"
            )

        with logout_col:

            if st.button(
                "Sign out",
                use_container_width=True
            ):

                if "creds" in st.session_state:
                    del st.session_state["creds"]

                st.rerun()

    return profile_dict[selected_profile_key]


# ============================================================
# SECTION HEADER
# ============================================================

def section_header(number, title):

    st.markdown(
        f"""
        <div class="section-header">
            <div class="step-number">{number}</div>
            <div class="section-title">{title}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# SAMPLE TEMPLATE
# ============================================================

def create_sample_template():

    sample_df = pd.DataFrame(
        [
            {
                "Tag Name": "Example_Pixel",
                "Level": "CAMPAIGN",
                "Parent ID": "12345678",
                "Tag Type": "IMPRESSION_IMAGE_EVENT_TAG",
                "Tag URL": "https://pixel.example.com"
            }
        ]
    )

    buffer = io.BytesIO()

    sample_df.to_csv(
        buffer,
        index=False
    )

    return buffer.getvalue()


# ============================================================
# PREVIEW TABLE
# ============================================================

def render_preview(df):

    section_header(2, "Preview")

    total_rows = len(df)

    # Show maximum 5 rows, matching the mockup
    preview_df = df.head(5).copy()

    # Add status column for preview
    preview_df["Status"] = "Pending"

    # Make the table cleaner
    st.markdown(
        '<div class="preview-container">',
        unsafe_allow_html=True
    )

    st.dataframe(
        preview_df,
        use_container_width=True,
        hide_index=True,
        height=225,
        column_config={
            "Status": st.column_config.TextColumn(
                "STATUS",
                width="small"
            )
        }
    )

    file_name = st.session_state.get(
        "uploaded_file_name",
        "CSV file"
    )

    st.markdown(
        f"""
        <div class="preview-footer">
            <span>
                Showing {min(5, total_rows)} of {total_rows} rows
            </span>

            <span>
                File: {file_name} · {total_rows} records detected
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# ============================================================
# CREATE TAGS
# ============================================================

def create_tags(
    service,
    profile_id,
    df
):

    progress_bar = st.progress(0)

    status_text = st.empty()

    results = []

    success_count = 0
    fail_count = 0

    total_rows = len(df)

    for index, row in df.iterrows():

        tag_name = str(
            row["Tag Name"]
        ).strip()

        level = str(
            row["Level"]
        ).strip().upper()

        parent_id = str(
            row["Parent ID"]
        ).strip()

        payload = {
            "name": tag_name,
            "status": "ENABLED",
            "type": str(
                row["Tag Type"]
            ).strip(),
            "url": str(
                row["Tag URL"]
            ).strip()
        }

        if level == "ADVERTISER":

            payload["advertiserId"] = parent_id

        elif level == "CAMPAIGN":

            payload["campaignId"] = parent_id

        else:

            results.append(
                {
                    "Tag Name": tag_name,
                    "Status": "FAILED",
                    "Details": "Invalid Level"
                }
            )

            fail_count += 1

            progress_bar.progress(
                (index + 1) / total_rows
            )

            continue

        try:

            request = service.eventTags().insert(
                profileId=profile_id,
                body=payload
            )

            request.execute()

            results.append(
                {
                    "Tag Name": tag_name,
                    "Status": "SUCCESS",
                    "Details": "-"
                }
            )

            success_count += 1

        except Exception as e:

            results.append(
                {
                    "Tag Name": tag_name,
                    "Status": "FAILED",
                    "Details": str(e)
                }
            )

            fail_count += 1

        progress_bar.progress(
            (index + 1) / total_rows
        )

        status_text.caption(
            f"Processing: {tag_name}"
        )

    progress_bar.empty()
    status_text.empty()

    return (
        results,
        success_count,
        fail_count
    )


# ============================================================
# MAIN WORKSPACE
# ============================================================

def render_workspace(creds):

    # --------------------------------------------------------
    # Build CM360 service
    # --------------------------------------------------------

    service = build(
        API_SERVICE_NAME,
        API_VERSION,
        credentials=creds
    )

    # --------------------------------------------------------
    # Get profiles
    # --------------------------------------------------------

    try:

        profiles_response = (
            service.userProfiles()
            .list()
            .execute()
        )

        profiles = profiles_response.get(
            "items",
            []
        )

        if not profiles:

            st.error(
                "No active CM360 profiles found for this user."
            )

            st.stop()

        profile_dict = {
            f"{p['userName']} ({p['accountId']})":
                p["profileId"]
            for p in profiles
        }

    except Exception as e:

        st.error(
            f"API Error: {e}"
        )

        st.stop()

    # --------------------------------------------------------
    # Header
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="top-nav">

            <div class="brand">
                <span class="brand-main">CM360</span>
                <span class="brand-divider">·</span>
                <span class="brand-subtitle">
                    Bulk Event Tag Creation
                </span>
            </div>

            <div style="width:420px;"></div>

        </div>
        """,
        unsafe_allow_html=True
    )

    # Place profile/logout over the right side of header
    header_left, header_right = st.columns(
        [8.5, 2],
        vertical_alignment="center"
    )

    with header_right:

        profile_col, logout_col = st.columns(
            [1.6, 1],
            gap="small"
        )

        with profile_col:

            selected_profile_key = st.selectbox(
                "Profile",
                options=list(profile_dict.keys()),
                label_visibility="collapsed"
            )

        with logout_col:

            if st.button(
                "Sign out",
                use_container_width=True
            ):

                del st.session_state["creds"]

                st.rerun()

    profile_id = profile_dict[
        selected_profile_key
    ]

    # --------------------------------------------------------
    # Main workspace
    # --------------------------------------------------------

    st.markdown(
        '<div class="workspace">',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # Page title
    # --------------------------------------------------------

    st.markdown(
        """
        <h1 class="page-title">
            Bulk Event Tag Creation
        </h1>

        <p class="page-subtitle">
            Upload a CSV file to create event tags in bulk.
            Use the sample template to get started.
        </p>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # STEP 1
    # --------------------------------------------------------

    section_header(
        1,
        "Upload Data"
    )

    # Upload area
    st.markdown(
        """
        <div class="upload-wrapper">

            <div class="upload-icon">

                <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                >
                    <path d="M12 16V4"></path>
                    <path d="M8 8l4-4 4 4"></path>
                    <path d="M20 16.5A4.5 4.5 0 0015.5 12h-1"></path>
                    <path d="M4 16.5A4.5 4.5 0 018.5 12h1"></path>
                    <path d="M7 20h10"></path>
                </svg>

            </div>

            <div class="upload-title">
                Drag & drop your CSV file here
            </div>

            <div class="upload-or">
                or
            </div>

        """,
        unsafe_allow_html=True
    )

    uploaded_file = st.file_uploader(
        "Upload CSV",
        type=["csv"],
        label_visibility="collapsed"
    )

    st.markdown(
        """
            <div class="upload-info">
                Maximum file size: 200MB
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # Sample template
    # --------------------------------------------------------

    st.download_button(
        "⇩  Download Sample Template",
        data=create_sample_template(),
        file_name="cm360_template.csv",
        mime="text/csv"
    )

    # --------------------------------------------------------
    # PROCESS UPLOAD
    # --------------------------------------------------------

    if uploaded_file is not None:

        st.session_state[
            "uploaded_file_name"
        ] = uploaded_file.name

        try:

            df = pd.read_csv(
                uploaded_file
            )

            df.columns = (
                df.columns
                .str.strip()
            )

        except Exception as e:

            st.error(
                f"Unable to read CSV file: {e}"
            )

            st.stop()

        # ----------------------------------------------------
        # Validate columns
        # ----------------------------------------------------

        required_cols = {
            "Tag Name",
            "Level",
            "Parent ID",
            "Tag Type",
            "Tag URL"
        }

        missing_cols = (
            required_cols -
            set(df.columns)
        )

        if missing_cols:

            st.error(
                "Missing required columns: "
                + ", ".join(
                    sorted(missing_cols)
                )
            )

        else:

            # ------------------------------------------------
            # STEP 2 - PREVIEW
            # ------------------------------------------------

            render_preview(df)

            # ------------------------------------------------
            # URL validation
            # ------------------------------------------------

            invalid_urls = df[
                ~df["Tag URL"]
                .astype(str)
                .str.startswith(
                    "https://"
                )
            ]

            if not invalid_urls.empty:

                st.warning(
                    f"{len(invalid_urls)} row(s) "
                    "contain non-HTTPS URLs and may fail."
                )

            # ------------------------------------------------
            # CREATE BUTTON
            # ------------------------------------------------

            st.markdown(
                '<div class="create-button-container">',
                unsafe_allow_html=True
            )

            create_clicked = st.button(
                "Create Tags",
                type="primary"
            )

            st.markdown(
                "</div>",
                unsafe_allow_html=True
            )

            # ------------------------------------------------
            # CREATE TAGS
            # ------------------------------------------------

            if create_clicked:

                (
                    results,
                    success_count,
                    fail_count
                ) = create_tags(
                    service,
                    profile_id,
                    df
                )

                st.success(
                    f"Execution complete! "
                    f"{success_count} created, "
                    f"{fail_count} failed."
                )

                # ------------------------------------------------
                # Execution log
                # ------------------------------------------------

                res_df = pd.DataFrame(
                    results
                )

                csv_export = (
                    res_df
                    .to_csv(index=False)
                    .encode("utf-8")
                )

                st.download_button(
                    "Download Execution Log",
                    data=csv_export,
                    file_name="execution_log.csv",
                    mime="text/csv"
                )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# ============================================================
# MAIN ROUTING
# ============================================================

def main():

    if (
        "client_secrets"
        not in st.secrets
    ):

        st.error(
            "Missing 'client_secrets' in "
            "Streamlit secrets configuration."
        )

        st.stop()

    if (
        "creds" not in st.session_state
        or not st.session_state.creds
        or not st.session_state.creds.valid
    ):

        render_login_page()

    else:

        render_workspace(
            st.session_state.creds
        )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
