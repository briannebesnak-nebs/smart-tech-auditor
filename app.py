import streamlit as st
import pandas as pd
import datetime
import google.generativeai as genai

# Streamlit Page Setup
st.set_page_config(
    page_title="Smart Tech Scheduling Auditor",
    page_icon="📅",
    layout="wide"
)

st.title("📅 Regional Smart Tech Scheduling Auditor")
st.markdown("Upload your office's Master Sheet and daily Tableau drop file to generate an optimized 14-day scheduling audit.")

# Sidebar Controls
st.sidebar.header("⚙️ Settings & Configuration")

# API Key handling (either entered in UI or retrieved from Streamlit secrets)
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password", help="Get a free API key at aistudio.google.com")
if not api_key and "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]

office_name = st.sidebar.text_input("Office Name / Location", value="Concord")
territories = st.sidebar.text_input("Assigned CARs / Territories (comma separated)", value="Concord, Burlington, Rutland")

st.sidebar.markdown("---")
st.sidebar.info("💡 **Free Deployment Tip:** Store the Gemini API Key in Streamlit Secrets so users don't have to enter it manually.")

# Main Interface File Uploaders
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Office Master Sheet")
    master_file = st.file_uploader("Upload static roster & baseline schedule (.csv or .xlsx)", type=["csv", "xlsx"], key="master")

with col2:
    st.subheader("2. Tableau File Drop")
    tableau_file = st.file_uploader("Upload daily Smart Tech Scheduling export (.csv or .xlsx)", type=["csv", "xlsx"], key="tableau")

# Process Files on Button Click
if st.button("🚀 Run 14-Day Schedule Audit", type="primary"):
    if not api_key:
        st.error("Please enter a valid Gemini API Key in the sidebar.")
    elif not master_file or not tableau_file:
        st.error("Please upload both the Office Master Sheet and the Tableau File Drop.")
    else:
        try:
            with st.spinner("Analyzing schedule targets, calculating 14-day audit window, and balancing shifts..."):
                # Configure Gemini API
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-1.5-flash")

                # Read data preview for prompt context
                if master_file.name.endswith('.csv'):
                    df_master = pd.read_csv(master_file)
                else:
                    df_master = pd.read_excel(master_file)

                if tableau_file.name.endswith('.csv'):
                    df_tableau = pd.read_csv(tableau_file)
                else:
                    df_tableau = pd.read_excel(tableau_file)

                drop_date = datetime.date.today().strftime("%Y-%m-%d")

                # Construct Audit Prompt
                prompt = f"""
You are an expert Dispatch and Scheduling Auditor for the {office_name} office.
Your job is to compare the staffing recommendations in the provided Tableau Smart Tech Scheduling File against the static {office_name} Master Sheet.

Date Context:
- File Drop Date: {drop_date}
- Audit Scope: Evaluate EXACTLY 14 consecutive calendar days starting the day AFTER {drop_date}.
- Ignore all date columns before the Start Date or beyond the 14-day window.

Assigned Territories / CARs: {territories}

Data Files Provided:
1. Master Sheet Data ({office_name}):
{df_master.to_string()}

2. Tableau Smart Tech Scheduling Data Drop:
{df_tableau.to_string()}

Auditing Logic & Optimization Hierarchy:
1. Identify Daily Deficits & Surpluses for each day in the 14-day window per CAR.
2. Priority 1 (Day Swaps): Swap scheduled working days for existing techs within their schedule (zero extra cost).
3. Priority 2 (Single 5th Day Cap): Assign maximum ONE 5th day per technician across the entire 14 days. Balance across roster.
4. Priority 3 (6th Days - Absolute Last Resort): Only flag if all techs in that CAR are already capped at a 5th day.

Output Format Required:
Return a clean, well-formatted Markdown response containing:
1. Executive Summary Table (Columns: CAR | Technician | Recommended Day Swaps | Assigned 5th Day (Max 1) | 6th Day Needed?)
2. Actionable Day Swaps (Zero-Cost Fixes)
3. Balanced 5th Day Assignments
4. Critical 6th Day Exceptions (Last Resort Only)
"""

                # Query Gemini API
                response = model.generate_content(prompt)

                st.success("Audit Complete!")
                st.markdown("---")
                st.markdown(response.text)

                # Download button for the generated report
                st.download_button(
                    label="📥 Download Audit Report (.txt)",
                    data=response.text,
                    file_name=f"{office_name}_Schedule_Audit_{drop_date}.txt",
                    mime="text/plain"
                )

        except Exception as e:
            st.error(f"An error occurred during processing: {str(e)}")
