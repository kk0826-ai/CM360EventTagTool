import streamlit as st
import pandas as pd
import json
import io
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="CM360 - Bulk Event Tag Creation",
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

st.markdown("""
<style>

/* ============================================================
   HIDE STREAMLIT DEFAULT UI
   ============================================================ */

#MainMenu {
    visibility: hidden;
}

header {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

section[data-testid="stSidebar"] {
    display: none !important;
}

.stApp {
    background-color: #FFFFFF !important;
}


/* ============================================================
   REMOVE DEFAULT TOP PADDING
   ============================================================ */

.block-container {
    padding-top: 0rem !important;
    padding-bottom: 3rem !important;
}


/* ============================================================
   TOP NAVIGATION
   ============================================================ */

.top-header {
    width: 100%;
    height: 66px;
    border-bottom: 1px solid #E5E7EB;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 40px;
    box-sizing: border-box;
    background: #FFFFFF;
}

.top-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 15px;
}

.top-brand-main {
    font-weight: 700;
    color: #111827;
}

.top-brand-separator {
    color: #D1D5DB;
}

.top-brand-sub {
    color: #9CA3AF;
    font-weight: 400;
}


/* ============================================================
   HEADER WIDGETS
   ============================================================ */

.header-widget {
    margin-top: -58px;
    margin-bottom: 0px;
}

.header-widget div[data-testid="stSelectbox"] {
    margin: 0 !important;
}

.header-widget div[data-testid="stSelectbox"] label {
    display: none !important;
}

.header-widget div[data-baseweb="select"] {
    min-height: 34px !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 8px !important;
    background: #FFFFFF !important;
}

.header-widget button {
    min-height: 34px !important;
    height: 34px !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 8px !important;
    background: #FFFFFF !important;
    color: #111827 !important;
    font-size: 13px !important;
}


/* ============================================================
   MAIN CONTENT
   ============================================================ */

.main-content {
    width: 100%;
    max-width: 830px;
    margin: 0 auto;
    padding-top: 42px;
}


/* ============================================================
   PAGE TITLE
   ============================================================ */

.page-title {
    font-size: 27px;
    line-height: 34px;
    font-weight: 700;
    color: #111827;
    margin: 0 0 4px 0;
}

.page-description {
    font-size: 14px;
    line-height: 22px;
    color: #9CA3AF;
    margin: 0;
}


/* ============================================================
   SECTION HEADER
   ============================================================ */

.section-header {
    display: flex;
    align-items: center;
    gap: 11px;
    margin-top: 38px;
    margin-bottom: 16px;
}

.section-number {
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

.section-name {
    font-size: 16px;
    font-weight: 600;
    color: #111827;
}


/* ============================================================
   UPLOAD BOX
   ============================================================ */

.upload-box {
    border: 2px dashed #E5E7EB;
    border-radius: 14px;
    background: #FAFAFA;
    min-height: 350px;
    width: 100%;
    box-sizing: border-box;

    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;

    text-align: center;
}

.upload-icon {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: #E7F0FF;

    display: flex;
    align-items: center;
    justify-content: center;

    margin-bottom: 14px;
}

.upload-icon svg {
    width: 24px;
    height: 24px;
    stroke: #2F80ED;
}

.upload-title {
    font-size: 16px;
    font-weight: 600;
    color: #111827;
    margin-bottom: 7px;
}

.upload-or {
    font-size: 13px;
    color: #9CA3AF;
    margin-bottom: 4px;
}

.upload-limit {
    font-size: 12px;
    color: #A3A3A3;
    margin-top: 5px;
}


/* ============================================================
   FILE UPLOADER
   ============================================================ */

div[data-testid="stFileUploader"] {
    width: 100%;
}

div[data-testid="stFileUploader"] label {
    display: none !important;
}

div[data-testid="stFileUploader"] section {
    border: none !important;
    padding: 0 !important;
    background: transparent !important;
}

div[data-testid="stFileUploader"] section > div {
    border: none !important;
    padding: 0 !important;
    background: transparent !important;
}

div[data-testid="stFileUploader"] small {
    display: none !important;
}

div[data-testid="stFileUploader"] button {
    background: #2F80ED !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 7px !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    padding: 8px 18px !important;
}

div[data-testid="stFileUploader"] button:hover {
    background: #2563EB !important;
}


/* ============================================================
   SAMPLE TEMPLATE
   ============================================================ */

.sample-template {
    margin-top: 10px;
}

.sample-template button {
    border: 1px solid #E5E7EB !important;
    background: #FFFFFF !important;
    color: #111827 !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}


/* ============================================================
   PREVIEW
   ============================================================ */

.preview-box {
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    overflow: hidden;
    background: #FFFFFF;
}


/* ============================================================
   DATAFRAME
   ============================================================ */

div[data-testid="stDataFrame"] {
    border: none !important;
}

div[data-testid="stDataFrame"] iframe {
    border: none !important;
}


/* ============================================================
   PREVIEW FOOTER
   ============================================================ */

.preview-footer {
    height: 38px;
    background: #F9FAFB;
    border-top: 1px solid #E5E7EB;

    display: flex;
    align-items: center;
    justify-content: space-between;

    padding: 0 15px;

    font-size: 12px;
    color: #9CA3AF;
}


/* ============================================================
   CREATE BUTTON
   ============================================================ */

.create-area {
    display: flex;
    justify-content: center;
    margin-top: 23px;
}

.create-area button {
    min-width: 143px !important;
    min-height: 43px !important;

    background: #2F80ED !important;
    border: 1px solid #2F80ED !important;

    color: #FFFFFF !important;

    border-radius: 8px !important;

    font-size: 14px !important;
    font-weight: 600 !important;
}

.create-area button:hover {
    background: #2563EB !important;
    border-color: #2563EB !important;
}


/* ============================================================
   ALERTS
   ============================================================ */

div[data-testid="stAlert"] {
    border-radius: 8px !important;
}


/* ============================================================
   MOBILE
   ============================================================ */

@media (max-width: 900px) {

    .top-header {
        padding: 0 20px;
    }

    .top-brand-sub,
    .top-brand-separator {
        display: none;
    }

    .main-content {
        padding-left: 20px;
        padding-right: 20px;
    }

}

</style>
""", unsafe_allow_html=True)


# ============================================================
# LOGIN PAGE
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

            st.error(
                f"Configuration Error: {e}"
            )

            return

    col_left, col_right = st.columns(
        [1, 1.2],
        gap="large"
    )

    with col_left:

        st.markdown(
            "<br><br><br><br>",
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <h1 style="
                font-size:2rem;
                color:#111827;
                margin-bottom:8px;
            ">
                Welcome Back
            </h1>

            <p style="
                color:#4B5563;
                margin-bottom:32px;
            ">
                Sign in to CM360 Bulk Tag Manager.
            </p>
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
                height:95vh;
                width:100%;
                border-radius:24px;
                margin-top:12px;

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


# ============================================================
# TOP HEADER
# ============================================================

def render_header(profile_dict):

    # Header visual
    st.markdown(
        """
        <div class="top-header">

            <div class="top-brand">

                <span class="top-brand-main">
                    CM360
                </span>

                <span class="top-brand-separator">
                    ·
                </span>

                <span class="top-brand-sub">
                    Bulk Event Tag Creation
                </span>

            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    # Widgets positioned below/within header area
    st.markdown(
        '<div class="header-widget">',
        unsafe_allow_html=True
    )

    spacer_left, profile_col, logout_col = st.columns(
        [8.2, 1.6, 1.0],
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

            if "creds" in st.session_state:
                del st.session_state["creds"]

            st.rerun()

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )

    return profile_dict[selected_profile_key]


# ============================================================
# SECTION HEADER
# ============================================================

def render_section_header(number, title):

    st.markdown(
        f"""
        <div class="section-header">

            <div class="section-number">
                {number}
            </div>

            <div class="section-name">
                {title}
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# SAMPLE TEMPLATE
# ============================================================

def get_sample_template():

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
# CREATE TAGS
# ============================================================

def process_create_tags(
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

        # ----------------------------------------------------
        # Parent
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # API request
        # ----------------------------------------------------

        try:

            req = service.eventTags().insert(
                profileId=profile_id,
                body=payload
            )

            req.execute()

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
    # Get CM360 profiles
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

    profile_id = render_header(
        profile_dict
    )

    # --------------------------------------------------------
    # Main content wrapper
    # --------------------------------------------------------

    st.markdown(
        '<div class="main-content">',
        unsafe_allow_html=True
    )

    # ========================================================
    # PAGE TITLE
    # ========================================================

    st.markdown(
        """
        <div class="page-title">
            Bulk Event Tag Creation
        </div>

        <div class="page-description">
            Upload a CSV file to create event tags in bulk.
            Use the sample template to get started.
        </div>
        """,
        unsafe_allow_html=True
    )

    # ========================================================
    # STEP 1
    # ========================================================

    render_section_header(
        1,
        "Upload Data"
    )

    # --------------------------------------------------------
    # Upload box
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="upload-box">

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
                    <path d="M20 16.5A4.5 4.5 0 0015.5 12"></path>
                    <path d="M4 16.5A4.5 4.5 0 018.5 12"></path>
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

    # --------------------------------------------------------
    # IMPORTANT:
    # File uploader is outside the HTML div.
    # This avoids Streamlit DOM/layout issues.
    # --------------------------------------------------------

    uploaded_file = st.file_uploader(
        "Upload CSV",
        type=["csv"],
        label_visibility="collapsed"
    )

    st.markdown(
        """
            <div class="upload-limit">
                Maximum file size: 200MB
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # Sample template
    # --------------------------------------------------------

    st.markdown(
        '<div class="sample-template">',
        unsafe_allow_html=True
    )

    st.download_button(
        "⇩  Download Sample Template",
        data=get_sample_template(),
        file_name="cm360_template.csv",
        mime="text/csv"
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )

    # ========================================================
    # CSV PROCESSING
    # ========================================================

    if uploaded_file is not None:

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

            st.markdown(
                "</div>",
                unsafe_allow_html=True
            )

            return

        # ----------------------------------------------------
        # Required columns
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

            # =================================================
            # STEP 2
            # =================================================

            render_section_header(
                2,
                "Preview"
            )

            total_rows = len(df)

            # ------------------------------------------------
            # Prepare preview
            # ------------------------------------------------

            preview_df = df.head(5).copy()

            preview_df["Status"] = "Pending"

            # ------------------------------------------------
            # Preview container
            # ------------------------------------------------

            st.markdown(
                '<div class="preview-box">',
                unsafe_allow_html=True
            )

            st.dataframe(
                preview_df,
                use_container_width=True,
                hide_index=True,
                height=235
            )

            file_name = uploaded_file.name

            st.markdown(
                f"""
                <div class="preview-footer">

                    <span>
                        Showing {min(5, total_rows)}
                        of {total_rows} rows
                    </span>

                    <span>
                        File: {file_name}
                        · {total_rows} records detected
                    </span>

                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown(
                "</div>",
                unsafe_allow_html=True
            )

            # =================================================
            # URL VALIDATION
            # =================================================

            invalid_urls = df[
                ~df["Tag URL"]
                .astype(str)
                .str.startswith("https://")
            ]

            if not invalid_urls.empty:

                st.warning(
                    f"{len(invalid_urls)} row(s) contain "
                    "non-HTTPS URLs and may fail."
                )

            # =================================================
            # CREATE TAGS
            # =================================================

            st.markdown(
                '<div class="create-area">',
                unsafe_allow_html=True
            )

            create_tags_clicked = st.button(
                "Create Tags",
                type="primary"
            )

            st.markdown(
                "</div>",
                unsafe_allow_html=True
            )

            # =================================================
            # EXECUTION
            # =================================================

            if create_tags_clicked:

                (
                    results,
                    success_count,
                    fail_count
                ) = process_create_tags(
                    service,
                    profile_id,
                    df
                )

                # ------------------------------------------------
                # Result message
                # ------------------------------------------------

                if fail_count == 0:

                    st.success(
                        f"Execution complete! "
                        f"{success_count} tags created successfully."
                    )

                elif success_count == 0:

                    st.error(
                        f"Execution complete. "
                        f"{fail_count} tags failed."
                    )

                else:

                    st.warning(
                        f"Execution complete! "
                        f"{success_count} created, "
                        f"{fail_count} failed."
                    )

                # ------------------------------------------------
                # Execution log
                # ------------------------------------------------

                result_df = pd.DataFrame(
                    results
                )

                csv_export = (
                    result_df
                    .to_csv(index=False)
                    .encode("utf-8")
                )

                st.download_button(
                    "Download Execution Log",
                    data=csv_export,
                    file_name="execution_log.csv",
                    mime="text/csv"
                )

    # --------------------------------------------------------
    # Close main wrapper
    # --------------------------------------------------------

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# ============================================================
# MAIN ROUTING
# ============================================================

def main():

    # --------------------------------------------------------
    # Check secrets
    # --------------------------------------------------------

    if "client_secrets" not in st.secrets:

        st.error(
            "⚠️ Missing 'client_secrets' in "
            "Streamlit secrets configuration."
        )

        st.stop()

    # --------------------------------------------------------
    # Authentication
    # --------------------------------------------------------

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
