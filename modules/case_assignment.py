import streamlit as st
from db_connection import get_connection, fetch_data, execute_query

def app():
    st.title("👮 CASE ASSIGNMENT")

    # First, check if tables exist
    from db_connection import check_tables_exist
    if not check_tables_exist():
        st.error("❌ REQUIRED DATABASE TABLES ARE MISSING. Please run the SQL setup script first.")
        return

    # Establish DB connection
    conn = get_connection()
    if not conn:
        st.error("❌ DATABASE CONNECTION FAILED.")
        return

    try:
        # Fetch unassigned cases with better error handling
        cases = fetch_data(
            "SELECT CASE_ID, CASE_TITLE, STATUS FROM CASE_TABLE WHERE STATUS = 'Reported'"
        )

        if not cases:
            st.info("✅ NO UNASSIGNED CASES.")
            return

        # Fetch available CID officers for assignment
        cid_officers = fetch_data(
            "SELECT STAFFID, SURNAME, OTHERNAMES FROM USERLOGIN WHERE ROLE = 'CID' AND IS_ACTIVE = 1"
        )
        
        officer_options = {f"{o['STAFFID']} - {o['SURNAME']}, {o['OTHERNAMES']}": o['STAFFID'] for o in cid_officers}

        for case in cases:
            with st.expander(f"{case['CASE_ID']} - {case['CASE_TITLE']}"):
                if not officer_options:
                    st.warning("No CID officers available for assignment")
                    continue
                    
                selected_officer = st.selectbox(
                    f"ASSIGN CID OFFICER",
                    options=list(officer_options.keys()),
                    key=f"officer_{case['CASE_ID']}"
                )
                
                officer_id = officer_options[selected_officer]
                
                reason = st.text_area(
                    f"ASSIGNMENT REASON",
                    placeholder="Explain why this case is being assigned...",
                    key=f"reason_{case['CASE_ID']}"
                )

                if st.button(f"ASSIGN CASE", key=f"btn_{case['CASE_ID']}"):
                    if not reason.strip():
                        st.warning("Please provide an assignment reason")
                        return

                    try:
                        # Update CASE_TABLE
                        update_success = execute_query(
                            """
                            UPDATE CASE_TABLE
                            SET CID_OFFICER_STAFFID = :1,
                                STATUS = 'Assigned',
                                ASSIGNED_AT = CURRENT_TIMESTAMP,
                                UPDATED_AT = CURRENT_TIMESTAMP
                            WHERE CASE_ID = :2
                            """,
                            (officer_id, case['CASE_ID'])
                        )

                        if update_success:
                            # Insert into CASE_ASSIGNMENT_HISTORY
                            history_success = execute_query(
                                """
                                INSERT INTO CASE_ASSIGNMENT_HISTORY
                                (CASE_ID, ASSIGNED_FROM, ASSIGNED_TO, ASSIGNMENT_REASON, STATUS)
                                VALUES (:1, NULL, :2, :3, 'Active')
                                """,
                                (case['CASE_ID'], officer_id, reason)
                            )

                            if history_success:
                                st.success(f"✅ CASE {case['CASE_ID']} ASSIGNED TO {selected_officer}")
                                st.rerun()  # Refresh the page to show updated list
                            else:
                                st.error("❌ Failed to record assignment history")
                        else:
                            st.error("❌ Failed to update case assignment")

                    except Exception as e:
                        st.error(f"❌ ASSIGNMENT FAILED: {str(e)}")

    except Exception as e:
        st.error(f"❌ ERROR FETCHING CASES: {str(e)}")