import streamlit as st
from db_connection import get_connection, fetch_data, execute_query

def app():
    st.title("✅ CASE CLOSURE")

    # Create Oracle DB connection
    conn = get_connection()
    if not conn:
        st.error("❌ FAILED TO CONNECT TO ORACLE DATABASE.")
        return

    # Fetch cases under investigation
    under_review = fetch_data(
        "SELECT CASE_ID, CASE_TITLE FROM CASE_TABLE WHERE STATUS = 'Closed'"
    )

    if not under_review:
        st.info("NO CASES READY FOR CLOSURE.")
        return

    for c in under_review:
        with st.expander(f"{c['CASE_ID']} - {c['CASE_TITLE']}"):
            notes = st.text_area(
                f"CLOSURE NOTES FOR CASE {c['CASE_ID']}",
                key=f"notes_{c['CASE_ID']}"
            )

            if st.button(f"CLOSE CASE {c['CASE_ID']}", key=f"close_{c['CASE_ID']}"):
                try:
                    # Update CASE_TABLE status and closure time
                    execute_query(
                        """
                        UPDATE CASE_TABLE
                        SET STATUS = 'CLOSED',
                            CLOSED_AT = SYSTIMESTAMP
                        WHERE CASE_ID = :1
                        """,
                        (c['CASE_ID'],)
                    )

                    st.success(f"✅ CASE {c['CASE_ID']} CLOSED SUCCESSFULLY.")

                except Exception as e:
                    st.error(f"❌ FAILED TO CLOSE CASE {c['CASE_ID']}: {e}")
