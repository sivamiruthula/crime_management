<<<<<<< HEAD
import streamlit as st
from db_connection import get_connection

st.title("🧩 Run Backend Procedure – Create Case")

complainant_id = st.number_input("Complainant ID", value=1, step=1)
crime_type_id = st.number_input("Crime Type ID", value=1, step=1)
case_title = st.text_input("Case Title", "Theft at Market")
description = st.text_area("Description", "Reported stolen items at local market.")
incident_location = st.text_input("Incident Location", "Vellore Market")
created_by = st.text_input("Created By (staff ID)", "NCO001")

if st.button("Create Case"):
    conn = get_connection()
    if conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                CALL sp_create_case(%s, %s, %s, %s, %s, %s);
            """, (complainant_id, crime_type_id, case_title, description, incident_location, created_by))
            conn.commit()
            st.success("✅ Case created successfully!")
        except Exception as e:
            conn.rollback()
            st.error(f"❌ Error: {e}")
        finally:
            cur.close()
            conn.close()
=======
import streamlit as st
from db_connection import get_connection

st.title("🧩 Run Backend Procedure – Create Case")

complainant_id = st.number_input("Complainant ID", value=1, step=1)
crime_type_id = st.number_input("Crime Type ID", value=1, step=1)
case_title = st.text_input("Case Title", "Theft at Market")
description = st.text_area("Description", "Reported stolen items at local market.")
incident_location = st.text_input("Incident Location", "Vellore Market")
created_by = st.text_input("Created By (staff ID)", "NCO001")

if st.button("Create Case"):
    conn = get_connection()
    if conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                CALL sp_create_case(%s, %s, %s, %s, %s, %s);
            """, (complainant_id, crime_type_id, case_title, description, incident_location, created_by))
            conn.commit()
            st.success("✅ Case created successfully!")
        except Exception as e:
            conn.rollback()
            st.error(f"❌ Error: {e}")
        finally:
            cur.close()
            conn.close()
>>>>>>> 5033e5e9 (Fixed indentation and added serial number in complainant view)
