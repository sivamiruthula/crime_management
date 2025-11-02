import streamlit as st
from db_connection import get_connection

st.set_page_config(page_title="Crime Management System", layout="wide")

st.title("🚔 Crime Management System Dashboard")

menu = st.sidebar.selectbox("Select Action", [
    "View Cases",
    "Create Case",
    "Add Complainant",
    "Add Crime Type"
])

conn = get_connection()

if not conn:
    st.error("Database connection failed.")
else:
    cur = conn.cursor()

    if menu == "View Cases":
        st.subheader("📋 All Cases")
        try:
            cur.execute("SELECT * FROM case_table ORDER BY created_at DESC;")
            rows = cur.fetchall()
            if rows:
                cols = [desc[0] for desc in cur.description]
                st.dataframe([dict(zip(cols, row)) for row in rows])
            else:
                st.info("No cases found.")
        except Exception as e:
            st.error(f"Error fetching cases: {e}")

    elif menu == "Create Case":
        st.subheader("📝 Create New Case")
        complainant_id = st.number_input("Complainant ID", min_value=1)
        crime_type_id = st.number_input("Crime Type ID", min_value=1)
        case_title = st.text_input("Case Title")
        description = st.text_area("Description")
        incident_location = st.text_input("Incident Location")
        created_by = st.text_input("Created By (Staff ID)")

        if st.button("Submit Case"):
            try:
                cur.execute("""
                    CALL sp_create_case(%s, %s, %s, %s, %s, %s);
                """, (complainant_id, crime_type_id, case_title, description, incident_location, created_by))
                conn.commit()
                st.success("✅ Case created successfully!")
            except Exception as e:
                conn.rollback()
                st.error(f"❌ Error creating case: {e}")

    elif menu == "Add Complainant":
        st.subheader("🧑 Add New Complainant")
        name = st.text_input("Name")
        age = st.number_input("Age", min_value=1)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        contact_no = st.text_input("Contact No")
        address = st.text_input("Address")
        occupation = st.text_input("Occupation")
        email = st.text_input("Email")
        registered_by = st.text_input("Registered By (Staff ID)")

        if st.button("Add Complainant"):
            try:
                cur.execute("""
                    CALL sp_create_complainant(%s,%s,%s,%s,%s,%s,%s,%s);
                """, (name, age, gender, contact_no, address, occupation, email, registered_by))
                conn.commit()
                st.success("✅ Complainant added successfully!")
            except Exception as e:
                conn.rollback()
                st.error(f"❌ Error: {e}")

    elif menu == "Add Crime Type":
        st.subheader("⚖️ Add Crime Type")
        crime_name = st.text_input("Crime Name")
        description = st.text_area("Description")
        severity = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"])
        base_penalty = st.number_input("Base Penalty (years)", min_value=0)
        admin = st.text_input("Admin ID")

        if st.button("Create Crime Type"):
            try:
                cur.execute("""
                    CALL sp_create_crime_type(%s,%s,%s,%s,%s);
                """, (crime_name, description, severity, base_penalty, admin))
                conn.commit()
                st.success("✅ Crime type created successfully!")
            except Exception as e:
                conn.rollback()
                st.error(f"❌ Error: {e}")

    cur.close()
    conn.close()
