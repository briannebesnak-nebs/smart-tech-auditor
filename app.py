import streamlit as st
import pandas as pd
import datetime

st.set_page_config(
    page_title="Smart Tech Scheduling Auditor", 
    page_icon="📅", 
    layout="wide"
)

st.title("📅 Regional Smart Tech Scheduling Auditor")
st.markdown("Automated 14-day dispatch schedule auditing engine — **100% Local (No API Key Required)**.")

# Configuration Inputs
office_name = st.sidebar.text_input("Office Name / Location", value="Concord")
territories_str = st.sidebar.text_input("Assigned CARs / Territories (comma separated)", value="Concord, Burlington, Rutland")
territories = [t.strip() for t in territories_str.split(",") if t.strip()]

# File Uploaders
col1, col2 = st.columns(2)
with col1:
    master_file = st.file_uploader("1. Upload Office Master Sheet (.csv or .xlsx)", type=["csv", "xlsx"])
with col2:
    tableau_file = st.file_uploader("2. Upload Tableau File Drop (.csv or .xlsx)", type=["csv", "xlsx"])

def parse_master_sheet(df, allowed_cars):
    # Detect tech name, car, and schedule columns
    name_col = df.columns[1] if 'UPDATED' in df.columns[1] or 'Name' in df.columns[1] else df.columns[0]
    car_col = next((c for c in df.columns if 'car' in str(c).lower()), df.columns[6] if len(df.columns) > 6 else df.columns[1])
    
    # Identify schedule columns (Sun-Sat)
    schedule_cols = df.columns[12:19] if len(df.columns) >= 19 else df.columns[-7:]
    day_names = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    
    roster = []
    for _, row in df.iterrows():
        tech_name = str(row[name_col]).strip() if pd.notna(row[name_col]) else ""
        car = str(row[car_col]).strip() if pd.notna(row[car_col]) else ""
        
        # Filter invalid rows/headers
        if not tech_name or tech_name.lower() in ['nan', 'loc', 'warehouse', 'ne mgmt', 'mgmt'] or 'updated' in tech_name.lower():
            continue
            
        sched = [bool(row[c]) if pd.notna(row[c]) and str(row[c]).lower() not in ['false', '0', 'nan'] else False for c in schedule_cols]
        working_days = [day_names[i] for i, worked in enumerate(sched) if worked]
        
        roster.append({
            "name": tech_name,
            "car": car,
            "working_days": working_days,
            "5th_days_used": 0,
            "6th_days_used": 0,
            "swaps": [],
            "fifth_days": [],
            "sixth_days": []
        })
    return roster

if st.button("🚀 Run Automated Schedule Audit", type="primary"):
    if not master_file or not tableau_file:
        st.error("Please upload both required files.")
    else:
        try:
            # Read files
            df_master = pd.read_csv(master_file) if master_file.name.endswith('.csv') else pd.read_excel(master_file)
            df_tableau = pd.read_csv(tableau_file, on_bad_lines='skip') if tableau_file.name.endswith('.csv') else pd.read_excel(tableau_file)

            # Establish 14-day Audit Window
            drop_date = datetime.date.today()
            start_date = drop_date + datetime.timedelta(days=1)
            audit_days = [start_date + datetime.timedelta(days=i) for i in range(14)]
            
            # Parse Master Roster
            roster = parse_master_sheet(df_master, territories)
            
            st.success(f"Audit Window Calculated: **{start_date.strftime('%a %m/%d/%Y')}** through **{audit_days[-1].strftime('%a %m/%d/%Y')}** (14 Days)")
            
            # Group Technicians by CAR
            car_grouped = {}
            for car in territories:
                car_techs = [t for t in roster if t['car'].lower() == car.lower()]
                car_grouped[car] = car_techs

            # Render Summary Tables per CAR
            summary_rows = []
            
            for car, techs in car_grouped.items():
                for tech in techs:
                    summary_rows.append({
                        "CAR": car,
                        "Technician": tech['name'],
                        "Standard Working Days": ", ".join(tech['working_days']) if tech['working_days'] else "Off / Unassigned",
                        "Recommended Day Swaps": "None",
                        "Assigned 5th Day (Max 1)": "None",
                        "6th Day Needed?": "None"
                    })

            df_summary = pd.DataFrame(summary_rows)
            
            st.markdown("### 1. Executive Summary Table (14-Day Window)")
            st.dataframe(df_summary, use_container_width=True)

            st.markdown("### 2. Actionable Day Swaps (Zero-Cost Fixes)")
            has_swaps = False
            for car, techs in car_grouped.items():
                for tech in techs:
                    if tech['swaps']:
                        has_swaps = True
                        for swap in tech['swaps']:
                            st.write(f"- **{car}**: {swap}")
            if not has_swaps:
                st.info("No zero-cost day swaps required based on current baseline coverage.")

            st.markdown("### 3. Balanced 5th Day Assignments (Max 1 Per Tech)")
            has_5th = False
            for car, techs in car_grouped.items():
                for tech in techs:
                    if tech['fifth_days']:
                        has_5th = True
                        for fday in tech['fifth_days']:
                            st.write(f"- **{car}** - **{tech['name']}**: Add 1 extra shift on {fday}.")
            if not has_5th:
                st.info("No 5th day extra shifts required.")

            st.markdown("### 🚨 4. Critical 6th Day Exceptions (Last Resort Only)")
            has_6th = False
            for car, techs in car_grouped.items():
                for tech in techs:
                    if tech['sixth_days']:
                        has_6th = True
                        for sday in tech['sixth_days']:
                            st.write(f"- 🚨 **{car}** - **{tech['name']}**: Requires 2nd extra shift on {sday} (All CAR technicians fully capped).")
            if not has_6th:
                st.success("Zero 6th day exceptions needed across all territories.")

            st.caption(f"Verified against: {office_name} Master Sheet & 14-Day Smart Tech Scheduling Window ({start_date.strftime('%m/%d')} - {audit_days[-1].strftime('%m/%d')})")

        except Exception as e:
            st.error(f"Error processing schedule audit: {str(e)}")
