import streamlit as st
import pandas as pd
import datetime

st.set_page_config(
    page_title="Smart Tech Audit Prompt Builder", 
    page_icon="📋", 
    layout="wide"
)

st.title("📋 Smart Tech Scheduling Prompt Builder")
st.markdown("Upload your office files below to generate a pre-formatted audit prompt ready for Gemini.")

# Office and Territory Inputs
col_info1, col_info2 = st.columns(2)
with col_info1:
    office_name = st.text_input("Office Name / Location", value="Concord")
with col_info2:
    territories = st.text_input("Assigned CARs / Territories", value="Concord, Burlington, Rutland")

# File Uploaders
col1, col2 = st.columns(2)
with col1:
    master_file = st.file_uploader("1. Upload Office Master Sheet (.csv or .xlsx)", type=["csv", "xlsx"])
with col2:
    tableau_file = st.file_uploader("2. Upload Tableau File Drop (.csv or .xlsx)", type=["csv", "xlsx"])

# Generate Button
if st.button("🚀 Generate Audit Prompt", type="primary"):
    if not master_file or not tableau_file:
        st.error("Please upload both the Master Sheet and the Tableau File Drop.")
    else:
        try:
            # Parse Master Sheet
            if master_file.name.endswith('.csv'):
                df_master = pd.read_csv(master_file)
            else:
                df_master = pd.read_excel(master_file)

            # Parse Tableau File
            if tableau_file.name.endswith('.csv'):
                df_tableau = pd.read_csv(tableau_file)
            else:
                df_tableau = pd.read_excel(tableau_file)

            drop_date = datetime.date.today().strftime("%Y-%m-%d")

            # Build Full Prompt String
            full_prompt = f"""Role:
You are an expert Dispatch and Scheduling Auditor for the {office_name} office.
Your job is to compare the staffing recommendations in the provided Tableau Smart Tech Scheduling File against the static {office_name} Master Sheet.

Time Horizon & Audit Window Rules:
- File Drop Date: {drop_date}
- Start Date: Begin analysis on the calendar day after the file is dropped.
- Audit Scope (2-Week Window): Evaluate EXACTLY 14 consecutive calendar days starting from the Start Date.
- Filter Rule: Ignore all date columns in the dropped file before the Start Date or beyond the 14-day window.

Assigned Territories / CARs: {territories}

Data Files Provided:

1. Master Sheet Data ({office_name}):
{df_master.to_csv(index=False)}

2. Tableau Smart Tech Scheduling Data Drop:
{df_tableau.to_csv(index=False)}

Auditing Logic & Optimization Hierarchy:
Identify Daily Deficits & Surpluses for each day in the 14-day window per CAR.

Priority 1 (Day Swaps): First attempt to fix deficits by swapping scheduled working days for existing techs within their schedule (zero-cost fix).
Priority 2 (Single 5th Day Cap): Assign maximum ONE 5th day per technician across the entire 14-day window. Rotate and balance across roster.
Priority 3 (6th Days - Absolute Last Resort): Only suggest a 6th day if ALL techs in that CAR are already capped at a 5th day and deficit still exists.

Output Format Required:
1. Executive Summary Table (Columns: CAR | Technician | Recommended Day Swaps | Assigned 5th Day (Max 1) | 6th Day Needed?)
2. Actionable Day Swaps (Zero-Cost Fixes)
3. Balanced 5th Day Assignments (Max 1 Per Tech)
4. Critical 6th Day Exceptions (Last Resort Only)
"""

            st.success("Prompt Generated Successfully!")
            st.subheader("Copy the text box below and paste it directly into Gemini:")
            st.code(full_prompt, language="text")

        except Exception as e:
            st.error(f"Error reading files: {str(e)}")
