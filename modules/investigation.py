import streamlit as st
from db_connection import get_connection, fetch_data, execute_query

def app():
    st.title("🔍 INVESTIGATION PROGRESS")

    # Open a database connection
    conn = get_connection()
    if not conn:
        st.error("❌ COULD NOT CONNECT TO ORACLE DATABASE.")
        return

    # Fetch all currently assigned cases
    active_cases = fetch_data(
        "SELECT CASE_ID, CASE_TITLE FROM CASE_TABLE WHERE STATUS = 'Under Investigation'"
    )

    if not active_cases:
        st.info("NO ACTIVE CASES UNDER INVESTIGATION.")
        return

    for case in active_cases:
        with st.expander(f"{case['CASE_ID']} - {case['CASE_TITLE']}"):
            officer_id = st.text_input(
                f"CID OFFICER STAFF ID FOR {case['CASE_ID']}",
                key=f"officer_{case['CASE_ID']}"
            )
            itype = st.selectbox(
                f"INVESTIGATION TYPE FOR {case['CASE_ID']}",
                ["INITIAL", "FOLLOW-UP", "EVIDENCE COLLECTION", "INTERVIEW", "FINAL REPORT"],
                key=f"type_{case['CASE_ID']}"
            )
            note = st.text_area(
                f"INVESTIGATION NOTE FOR {case['CASE_ID']}",
                key=f"note_{case['CASE_ID']}"
            )

            if st.button(f"SUBMIT REPORT FOR {case['CASE_ID']}", key=f"submit_{case['CASE_ID']}"):
                if not officer_id or not note.strip():
                    st.warning("⚠️ PLEASE PROVIDE OFFICER ID AND INVESTIGATION NOTE.")
                    continue
                try:
                    execute_query(
                        """
                        INSERT INTO INVESTIGATION (
                            CASE_ID,
                            CID_OFFICER_STAFFID,
                            INVESTIGATION_TYPE,
                            INVESTIGATION_NOTE,
                            INVESTIGATION_DATE
                        ) VALUES (:1, :2, :3, :4, SYSTIMESTAMP)
                        """,
                        (case['CASE_ID'], officer_id, itype, note)
                    )
                    st.success(f"✅ INVESTIGATION NOTE ADDED FOR {case['CASE_ID']}")
                except Exception as e:
                    st.error(f"❌ FAILED TO INSERT INVESTIGATION NOTE: {e}")
