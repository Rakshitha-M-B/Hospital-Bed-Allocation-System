import streamlit as st
import sqlite3
import pandas as pd

# --- DATABASE CONFIGURATION ---
DB_NAME = "hospital.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    return conn

def initialize_database():
    """Creates tables and triggers for automation and logging."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Create Main Tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS beds (
            bed_id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            is_occupied INTEGER DEFAULT 0
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            ailment TEXT NOT NULL,
            bed_id INTEGER UNIQUE,
            FOREIGN KEY (bed_id) REFERENCES beds (bed_id)
        )
    ''')
    
    # 2. Create Logs Table (Audit Trail)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            details TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # --- TRIGGERS (Automation & Logging) ---

    # Trigger 1: Auto-Occupy bed when patient added
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS update_bed_occupied
        AFTER INSERT ON patients
        BEGIN
            UPDATE beds SET is_occupied = 1 WHERE bed_id = NEW.bed_id;
        END;
    ''')

    # Trigger 2: Auto-Release bed when patient discharged
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS update_bed_available
        AFTER DELETE ON patients
        BEGIN
            UPDATE beds SET is_occupied = 0 WHERE bed_id = OLD.bed_id;
        END;
    ''')

    # Trigger 3: LOG ADMISSION (New)
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS log_admission_trigger
        AFTER INSERT ON patients
        BEGIN
            INSERT INTO logs (action, details) 
            VALUES ('ADMISSION', 'Patient ' || NEW.name || ' admitted to Bed ID ' || NEW.bed_id);
        END;
    ''')

    # Trigger 4: LOG DISCHARGE (New)
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS log_discharge_trigger
        AFTER DELETE ON patients
        BEGIN
            INSERT INTO logs (action, details) 
            VALUES ('DISCHARGE', 'Patient ' || OLD.name || ' discharged from Bed ID ' || OLD.bed_id);
        END;
    ''')

    # Seed Data (Create 5 beds if empty)
    cursor.execute('SELECT count(*) FROM beds')
    if cursor.fetchone()[0] == 0:
        beds = [('ICU',), ('General Ward',), ('General Ward',), ('Private Room',), ('ICU',)]
        cursor.executemany('INSERT INTO beds (type) VALUES (?)', beds)
    
    conn.commit()
    conn.close()

# Initialize DB
initialize_database()

# --- STREAMLIT UI ---

st.set_page_config(page_title="Hospital System", page_icon="🏥", layout="wide")
st.title("🏥 Hospital Bed Allocation System")

# Tabs layout
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Admit Patient", 
    "View Allocations", 
    "Discharge", 
    "Bed Inventory", 
    "Activity Logs"
])

# --- TAB 1: ADMIT PATIENT (Create) ---
with tab1:
    st.header("Admit New Patient")
    
    conn = get_db_connection()
    df_beds = pd.read_sql("SELECT bed_id, type FROM beds WHERE is_occupied = 0", conn)
    conn.close()

    if df_beds.empty:
        st.error("⚠️ No beds available! Please discharge a patient first.")
    else:
        with st.form("admit_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Patient Name")
            with col2:
                ailment = st.text_input("Ailment / Diagnosis")
            
            bed_options = df_beds.apply(lambda x: f"Bed {x['bed_id']} - {x['type']}", axis=1)
            selected_bed_str = st.selectbox("Select Available Bed", bed_options)
            
            submitted = st.form_submit_button("Allocate Bed")
            
            if submitted and name and ailment:
                selected_bed_id = int(selected_bed_str.split()[1])
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    # Trigger 'log_admission_trigger' runs automatically here
                    cursor.execute("INSERT INTO patients (name, ailment, bed_id) VALUES (?, ?, ?)", 
                                   (name, ailment, selected_bed_id))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Patient {name} admitted.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# --- TAB 2: VIEW ALLOCATIONS (Read + Join) ---
with tab2:
    st.header("Current Patient Allocations")
    conn = get_db_connection()
    query = '''
        SELECT p.patient_id, p.name, p.ailment, b.bed_id, b.type
        FROM patients p
        JOIN beds b ON p.bed_id = b.bed_id
    '''
    df_allocations = pd.read_sql(query, conn)
    conn.close()
    
    if df_allocations.empty:
        st.info("No patients currently admitted.")
    else:
        st.dataframe(df_allocations, use_container_width=True)

# --- TAB 3: DISCHARGE (Delete) ---
with tab3:
    st.header("Discharge Patient")
    
    conn = get_db_connection()
    df_patients = pd.read_sql("SELECT patient_id, name FROM patients", conn)
    conn.close()
    
    if df_patients.empty:
        st.info("No patients to discharge.")
    else:
        patient_options = df_patients.apply(lambda x: f"{x['patient_id']} - {x['name']}", axis=1)
        selected_patient_str = st.selectbox("Select Patient to Discharge", patient_options)
        
        if st.button("Discharge Patient"):
            patient_id = int(selected_patient_str.split()[0])
            conn = get_db_connection()
            cursor = conn.cursor()
            # Trigger 'log_discharge_trigger' runs automatically here
            cursor.execute("DELETE FROM patients WHERE patient_id = ?", (patient_id,))
            conn.commit()
            conn.close()
            st.success(f"Patient discharged.")
            st.rerun()

# --- TAB 4: BED INVENTORY ---
with tab4:
    st.header("Bed Inventory")
    conn = get_db_connection()
    df_inventory = pd.read_sql("SELECT * FROM beds", conn)
    conn.close()
    
    def highlight_occupied(val):
        return f'background-color: {"#ffcccc" if val == 1 else "#ccffcc"}'

    st.dataframe(df_inventory.style.applymap(highlight_occupied, subset=['is_occupied']), use_container_width=True)

# --- TAB 5: ACTIVITY LOGS (New) ---
with tab5:
    st.header("System Logs")
    st.caption("History of all admissions and discharges (Recorded via Triggers).")
    
    conn = get_db_connection()
    # Order by newest first
    df_logs = pd.read_sql("SELECT log_id, timestamp, action, details FROM logs ORDER BY timestamp DESC", conn)
    conn.close()
    
    if df_logs.empty:
        st.info("No activity recorded yet.")
    else:
        st.dataframe(df_logs, use_container_width=True)