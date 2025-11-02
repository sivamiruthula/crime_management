import streamlit as st
from db_connection import get_connection, execute_query

def app():
    st.title("📝 COMPLAINT REGISTRATION")

    with st.form("COMPLAINT_FORM"):
        COMPLAINANT_ID = st.text_input("COMPLAINANT ID")
        CRIME_TYPE_ID  = st.text_input("CRIME TYPE ID")
        CASE_TITLE     = st.text_input("CASE TITLE")
        DESCRIPTION    = st.text_area("DESCRIPTION")
        STAFFID        = st.text_input("OFFICER STAFF ID (NCO)")
        SUBMIT = st.form_submit_button("REGISTER CASE")

        if SUBMIT:
            if not all([COMPLAINANT_ID, CRIME_TYPE_ID, CASE_TITLE, DESCRIPTION, STAFFID]):
                st.warning("⚠️ PLEASE FILL IN ALL REQUIRED FIELDS.")
                return

            conn = get_connection()
            if not conn:
                st.error("❌ DATABASE CONNECTION FAILED. PLEASE CHECK YOUR ORACLE CREDENTIALS.")
                return

            try:
                query = """
                    INSERT INTO CASE_TABLE
                    (CASE_ID, COMPLAINANT_ID, CRIME_TYPE_ID, CASE_TITLE,
                     INCIDENT_DATETIME, INCIDENT_LOCATION, DESCRIPTION,
                     NCO_STAFFID, STATUS)
                    VALUES (
                        'C' || TO_CHAR(SYSDATE, 'YYYYMMDDHH24MISS'),
                        :1, :2, :3, SYSTIMESTAMP, 'UNKNOWN', :4, :5, 'REPORTED'
                    )
                """
                execute_query(query, (COMPLAINANT_ID, CRIME_TYPE_ID, CASE_TITLE, DESCRIPTION, STAFFID))
                st.success("✅ CASE REGISTERED SUCCESSFULLY!")

            except Exception as e:
                st.error(f"❌ ERROR REGISTERING CASE: {e}")
