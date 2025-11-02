import streamlit as st
import tempfile
from filemanager import insert_evidence_file
from db_connection import get_connection, fetch_data

def app():
    st.title("🧾 EVIDENCE UPLOAD PORTAL")

    # Create a database connection
    conn = get_connection()
    if not conn:
        st.error("❌ DATABASE CONNECTION FAILED.")
        return
    
    # Fetch all open (non-closed) cases
    cases = fetch_data("SELECT CASE_ID, CASE_TITLE FROM CASE_TABLE WHERE STATUS != 'Closed'")

    if not cases:
        st.info("NO OPEN CASES AVAILABLE.")
        return

    case_options = {f"{c['CASE_ID']} - {c['CASE_TITLE']}": c['CASE_ID'] for c in cases}
    selected_case = st.selectbox("SELECT CASE", list(case_options.keys()))

    evidence_type = st.selectbox(
        "EVIDENCE TYPE",
        ["PHYSICAL", "DIGITAL", "DOCUMENT", "BIOLOGICAL", "PHOTOGRAPHIC", "VIDEO", "AUDIO", "OTHER"]
    )

    uploaded_by = st.text_input("OFFICER STAFF ID (UPLOADER)")
    description = st.text_area("DESCRIPTION OF EVIDENCE")

    uploaded_file = st.file_uploader(
        "UPLOAD EVIDENCE FILE",
        type=["jpg", "png", "pdf", "mp4", "wav", "txt", "docx"]
    )

    if uploaded_file and st.button("SUBMIT EVIDENCE"):
        try:
            # Save file temporarily for Oracle BLOB upload
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(uploaded_file.getbuffer())
                temp_path = tmp.name

            # Call file upload function
            insert_evidence_file(
                connection=conn,
                evidence_id=None,  # Auto-generated in DB if applicable
                filename=uploaded_file.name,
                file_type=uploaded_file.type,
                uploaded_by=uploaded_by,
                description=description,
                file_path=temp_path
            )

            st.success(f"✅ '{uploaded_file.name}' UPLOADED SUCCESSFULLY FOR {selected_case}!")

        except Exception as e:
            st.error(f"❌ UPLOAD FAILED: {e}")
