import os
import pandas as pd
import streamlit as st

# Core system parameters
DATABASE_FILE = "grades_database.csv"
REQUIRED_COLUMNS = ["id", "class", "subject", "period", "semester", "grade"]

def initialize_database():
    """Configures a starter database schema with mock profiles if no file exists."""
    if not os.path.exists(DATABASE_FILE):
        df = pd.DataFrame(columns=REQUIRED_COLUMNS)
        df.loc[len(df)] = ["STU1001", "Grade_11A", "Mathematics", "Quarter_1", "Semester_1", "92"]
        df.loc[len(df)] = ["STU1001", "Grade_11A", "English_Lit", "Quarter_1", "Semester_1", "88"]
        df.loc[len(df)] = ["STU1001", "Grade_11A", "Mathematics", "Quarter_2", "Semester_1", "96"]
        df.loc[len(df)] = ["STU1001", "Grade_11A", "English_Lit", "Quarter_2", "Semester_1", "90"]
        df.loc[len(df)] = ["STU1001", "Grade_11A", "Mathematics", "Quarter_3", "Semester_2", "85"]
        df.loc[len(df)] = ["STU1002", "Grade_11B", "Mathematics", "Quarter_1", "Semester_1", "79"]
        df.to_csv(DATABASE_FILE, index=False)

initialize_database()

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Automated Student Grading Engine", page_icon="🏫", layout="wide")
st.title("🏫 Automated Student Grading & Evaluation Engine")

# Maintain session state variables
if "student_authenticated" not in st.session_state:
    st.session_state.student_authenticated = False
if "student_id" not in st.session_state:
    st.session_state.student_id = ""
if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

tab1, tab2 = st.tabs(["🎓 Student Report Card Portal", "🛠️ Registrar & System Admin Management"])

# ==========================================
# TAB 1: STUDENT PORTAL
# ==========================================
with tab1:
    st.subheader("Student Report Card Access")
    st.markdown("Sign in using your unique Student ID string token to display term averages and download report cards.")
    
    # Login Row
    col1, col2 = st.columns([3, 1])
    with col1:
        student_id_input = st.text_input("Student ID Token", value=st.session_state.student_id, placeholder="e.g., STU1001").strip()
    with col2:
        st.write("##") # alignment spacer
        if st.button("🔑 Access Portal Dashboard", use_container_width=True):
            if not student_id_input:
                st.warning("⚠️ Student ID cannot be empty.")
                st.session_state.student_authenticated = False
            elif not os.path.exists(DATABASE_FILE):
                st.error("❌ No database found. Contact Admin.")
                st.session_state.student_authenticated = False
            else:
                df = pd.read_csv(DATABASE_FILE)
                valid_ids = df['id'].astype(str).unique()
                if student_id_input in valid_ids:
                    st.session_state.student_authenticated = True
                    st.session_state.student_id = student_id_input
                    st.success(f"✅ Welcome Back Student: {student_id_input}")
                else:
                    st.error("❌ Student ID not found in current logs.")
                    st.session_state.student_authenticated = False

    # Main Student Panel Content Area
    if st.session_state.student_authenticated:
        st.markdown("---")
        df = pd.read_csv(DATABASE_FILE)
        student_rows = df[df['id'].astype(str) == st.session_state.student_id].copy()
        student_rows['grade'] = pd.to_numeric(student_rows['grade'], errors='coerce')
        
        # --- Metrics Summaries ---
        st.markdown("### 📊 Academic Standing Overview")
        yearly_avg = student_rows['grade'].mean()
        
        m_col1, m_col2 = st.columns(2)
        m_col1.metric(label="Overall Yearly Average Grade", value=f"{yearly_avg:.2f}%")
        
        with m_col2:
            st.markdown("**Semester Breakdown:**")
            for sem in sorted(student_rows['semester'].unique()):
                sem_avg = student_rows[student_rows['semester'] == sem]['grade'].mean()
                st.markdown(f"* **{str(sem).replace('_', ' ')}:** {sem_avg:.2f}%")
        
        # --- Interactive Data Filters ---
        st.markdown("### 🔍 Filter Specific Views & Export")
        semesters = ["All Semesters"] + sorted(student_rows['semester'].dropna().astype(str).unique().tolist())
        periods = ["All Periods"] + sorted(student_rows['period'].dropna().astype(str).unique().tolist())
        
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            selected_semester = st.selectbox("Filter Semester", options=semesters)
        with f_col2:
            selected_period = st.selectbox("Filter Grading Term", options=periods)
            
        # Apply Filters
        filtered_df = student_rows.copy()
        if selected_semester != "All Semesters":
            filtered_df = filtered_df[filtered_df['semester'].astype(str) == selected_semester]
        if selected_period != "All Periods":
            filtered_df = filtered_df[filtered_df['period'].astype(str) == selected_period]
            
        if filtered_df.empty:
            st.warning("### ⚠️ No Records Match criteria.")
        else:
            # Display localized snapshot calculations
            contextual_avg = filtered_df['grade'].mean()
            st.info(f"💡 Selected View Scope Average (**{selected_semester} / {selected_period}**): **{contextual_avg:.2f}%**")
            
            # Display target filtered dataframe table
            st.dataframe(filtered_df, use_container_width=True)
            
            # Generate export data framework structures
            export_df = filtered_df.copy()
            export_df['grade'] = export_df['grade'].map(lambda x: f"{x:.1f}" if pd.notnull(x) else "")
            
            summary_row = {
                "id": "SUMMARY", "class": "-", "subject": "Filtered Average Score", 
                "period": "-", "semester": "-", "grade": f"{contextual_avg:.2f}%"
            }
            export_df = pd.concat([export_df, pd.DataFrame([summary_row])], ignore_index=True)
            
            # Streaming download pipeline object block
            csv_data = export_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Structured CSV Report Card",
                data=csv_data,
                file_name=f"report_card_{st.session_state.student_id}.csv",
                mime="text/csv",
                use_container_width=True
            )

# ==========================================
# TAB 2: ADMIN UTILITIES
# ==========================================
with tab2:
    st.subheader("Registrar Login")
    
    # Credentials Panel
    a_col1, a_col2 = st.columns(2)
    with a_col1:
        admin_user = st.text_input("Admin Security User", placeholder="admin")
    with a_col2:
        admin_pass = st.text_input("Admin Cryptographic Key Pass", type="password", placeholder="•••••••••")
        
    if st.button("🔓 Authenticate System Access"):
        if admin_user == "admin" and admin_pass == "password123":
            st.session_state.admin_authenticated = True
            st.success("✅ Admin Authentication Successful. Live database loaded below.")
        else:
            st.session_state.admin_authenticated = False
            st.error("❌ Invalid Admin Username or Password.")
            
    # Protected Administrative Workspace
    if st.session_state.admin_authenticated:
        st.markdown("---")
        st.subheader("📂 Bulk Append System Ledger Database records (.CSV format only)")
        
        uploaded_file = st.file_uploader("Upload Structured Records File", type=["csv"])
        
        if uploaded_file is not None:
            if st.button("⚡ Synchronize System Schemas & Merge Databases"):
                try:
                    uploaded_df = pd.read_csv(uploaded_file)
                    uploaded_df.columns = [c.strip().lower() for c in uploaded_df.columns]
                    
                    missing = [col for col in REQUIRED_COLUMNS if col not in uploaded_df.columns]
                    if missing:
                        st.error(f"❌ Upload Rejected. Missing required columns: {', '.join(missing)}")
                    else:
                        final_df = uploaded_df[REQUIRED_COLUMNS]
                        if os.path.exists(DATABASE_FILE):
                            existing_df = pd.read_csv(DATABASE_FILE)
                            combined_df = pd.concat([existing_df, final_df], ignore_index=True).drop_duplicates()
                            combined_df.to_csv(DATABASE_FILE, index=False)
                        else:
                            final_df.to_csv(DATABASE_FILE, index=False)
                        st.success(f"🎉 Success! Merged {len(final_df)} records into the system database.")
                except Exception as e:
                    st.error(f"❌ Engine failure parsing file: {str(e)}")
                    
        # Always render the live filesystem contents
        st.markdown("### Live Operational Filesystem View")
        if os.path.exists(DATABASE_FILE):
            live_df = pd.read_csv(DATABASE_FILE)
            st.dataframe(live_df, use_container_width=True)
