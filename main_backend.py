import streamlit as st
import psycopg2
from db_connection import get_connection

# -----------------------------------------------------
# Streamlit App Configuration
# -----------------------------------------------------
st.set_page_config(page_title="Crime Management System", layout="wide")
st.title("🚔 Crime Management System Dashboard")

menu = st.sidebar.selectbox("Select Action", [
    "View Cases",
    "Create Case",
    "Add Complainant",
    "Add Crime Type",
    "View Complainants",
    "View Crime Types",
    "Delete Case",
    "Delete Complainant",
    "Delete Crime Type",
    "🧹 Delete ALL Data"
])



# -----------------------------------------------------
# Database Connection
# -----------------------------------------------------
conn = get_connection()

if not conn:
    st.error("❌ Database connection failed. Please check db_connection.py.")
else:
    cur = conn.cursor()

    # -----------------------------------------------------
    # 1️⃣ View All Cases
    # -----------------------------------------------------
    if menu == "View Cases":
        st.subheader("📋 All Reported Cases")
        try:
            cur.execute("SELECT * FROM case_table ORDER BY created_at DESC;")
            rows = cur.fetchall()
            if rows:
                cols = [desc[0] for desc in cur.description]
                st.dataframe([dict(zip(cols, row)) for row in rows])
            else:
                st.info("No cases found.")
        except Exception as e:
            st.error(f"❌ Error fetching cases: {e}")

    # -----------------------------------------------------
    # 2️⃣ Create New Case
    # -----------------------------------------------------
    elif menu == "Create Case":
        st.subheader("📝 Create a New Case")

        cur.execute("SELECT complainant_id, name FROM complainant ORDER BY complainant_id;")
        complainants = cur.fetchall()
        cur.execute("SELECT crime_type_id, crime_name FROM crime_type ORDER BY crime_type_id;")
        crimes = cur.fetchall()

        complainant_choice = st.selectbox(
            "Select Complainant", 
            options=[f"{cid} - {name}" for cid, name in complainants] if complainants else ["No Complainants Available"]
        )
        crime_choice = st.selectbox(
            "Select Crime Type", 
            options=[f"{cid} - {name}" for cid, name in crimes] if crimes else ["No Crime Types Available"]
        )

        case_title = st.text_input("Case Title")
        description = st.text_area("Description")
        incident_location = st.text_input("Incident Location")
        priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"], index=1)
        created_by = st.text_input("Created By (Staff ID)")

        if st.button("Submit Case"):
            try:
                complainant_id = int(complainant_choice.split(" - ")[0])
                crime_type_id = int(crime_choice.split(" - ")[0])

                cur.execute("""
                    CALL sp_create_case(%s, %s, %s, %s, %s, %s, %s);
                """, (
                    complainant_id, crime_type_id, case_title, 
                    description, incident_location, created_by, priority
                ))
                conn.commit()
                st.success("✅ Case created successfully!")
            except Exception as e:
                conn.rollback()
                st.error(f"❌ Error creating case: {e}")

    # -----------------------------------------------------
    # 3️⃣ Add New Complainant
    # -----------------------------------------------------
    elif menu == "Add Complainant":
        st.subheader("🧑 Add New Complainant")
        name = st.text_input("Full Name")
        age = st.number_input("Age", min_value=1)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        contact_no = st.text_input("Contact Number")
        address = st.text_input("Address")
        occupation = st.text_input("Occupation")
        email = st.text_input("Email Address")
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
                st.error(f"❌ Error adding complainant: {e}")

    # -----------------------------------------------------
    # 4️⃣ Add Crime Type
    # -----------------------------------------------------
    elif menu == "Add Crime Type":
        st.subheader("⚖️ Add New Crime Type")
        crime_name = st.text_input("Crime Name")
        description = st.text_area("Description")
        severity = st.selectbox("Severity Level", ["Low", "Medium", "High", "Critical"], index=1)
        base_penalty = st.number_input("Base Penalty (in years)", min_value=0)
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
                st.error(f"❌ Error creating crime type: {e}")

    # -----------------------------------------------------
    # 5️⃣ View Complainants
    # -----------------------------------------------------
    elif menu == "View Complainants":
        st.subheader("📋 Registered Complainants")
        cur.execute("SELECT complainant_id, name, gender, contact_no, email FROM complainant;")
        rows = cur.fetchall()
        if rows:
            cols = [d[0] for d in cur.description]
            st.dataframe([dict(zip(cols, r)) for r in rows])
        else:
            st.info("No complainants available.")

    # -----------------------------------------------------
    # 6️⃣ View Crime Types
    # -----------------------------------------------------
    
    elif menu == "View Crime Types":
        st.subheader("📋 Existing Crime Types")
        cur.execute("SELECT crime_type_id, crime_name, severity_level, base_penalty_years FROM crime_type;")
        rows = cur.fetchall()
        if rows:
            cols = [d[0] for d in cur.description]
            st.dataframe([dict(zip(cols, r)) for r in rows])
        else:
            st.info("No crime types available.")
            
        # -----------------------------------------------------
    # 7️⃣ Delete Case
    # -----------------------------------------------------
    elif menu == "Delete Case":
        st.subheader("🗑️ Delete Case Record")
        cur.execute("SELECT case_id, case_title FROM case_table ORDER BY created_at DESC;")
        rows = cur.fetchall()
        if rows:
            case_choice = st.selectbox("Select Case to Delete", [f"{r[0]} - {r[1]}" for r in rows])
            if st.button("Delete Selected Case"):
                try:
                    case_id = case_choice.split(" - ")[0]
                    cur.execute("CALL sp_delete_case(%s);", (case_id,))
                    conn.commit()
                    st.success(f"✅ Case {case_id} deleted successfully!")
                except Exception as e:
                    conn.rollback()
                    st.error(f"❌ Error deleting case: {e}")
        else:
            st.info("No cases available to delete.")

    # -----------------------------------------------------
    # 8️⃣ Delete Complainant
    # -----------------------------------------------------
    elif menu == "Delete Complainant":
        st.subheader("🗑️ Delete Complainant Record")
        cur.execute("SELECT complainant_id, name FROM complainant ORDER BY complainant_id;")
        rows = cur.fetchall()
        if rows:
            complainant_choice = st.selectbox("Select Complainant", [f"{r[0]} - {r[1]}" for r in rows])
            if st.button("Delete Selected Complainant"):
                try:
                    complainant_id = int(complainant_choice.split(" - ")[0])
                    cur.execute("CALL sp_delete_complainant(%s);", (complainant_id,))
                    conn.commit()
                    st.success(f"✅ Complainant {complainant_id} deleted successfully!")
                except Exception as e:
                    conn.rollback()
                    st.error(f"❌ Error deleting complainant: {e}")
        else:
            st.info("No complainants available to delete.")

    # -----------------------------------------------------
    # 9️⃣ Delete Crime Type
    # -----------------------------------------------------
    elif menu == "Delete Crime Type":
        st.subheader("🗑️ Delete Crime Type Record")
        cur.execute("SELECT crime_type_id, crime_name FROM crime_type ORDER BY crime_type_id;")
        rows = cur.fetchall()
        if rows:
            crime_choice = st.selectbox("Select Crime Type", [f"{r[0]} - {r[1]}" for r in rows])
            if st.button("Delete Selected Crime Type"):
                try:
                    crime_type_id = int(crime_choice.split(" - ")[0])
                    cur.execute("CALL sp_delete_crime_type(%s);", (crime_type_id,))
                    conn.commit()
                    st.success(f"✅ Crime Type {crime_type_id} deleted successfully!")
                except Exception as e:
                    conn.rollback()
                    st.error(f"❌ Error deleting crime type: {e}")
        else:
            st.info("No crime types available to delete.")

        # -----------------------------------------------------
    # 🧹 Delete ALL Data
    # -----------------------------------------------------
    elif menu == "🧹 Delete ALL Data":
        st.subheader("⚠️ Danger Zone: Delete ALL Data from the Database")

        st.warning(
            "This will permanently delete **ALL** complainants, crimes, cases, evidence, and user data. "
            "Only use this for testing or resetting the system!"
        )

        confirm = st.checkbox("I understand that this action is irreversible.")
        if confirm and st.button("Delete Everything Now 🚨"):
            try:
                cur.execute("CALL sp_delete_all_data();")
                conn.commit()
                st.success("✅ All data deleted successfully. Database reset complete!")
            except Exception as e:
                conn.rollback()
                st.error(f"❌ Error deleting all data: {e}")

    # -----------------------------------------------------
    # 🔒 Confirm before deleting individual records
    # -----------------------------------------------------
    elif menu == "Delete Case":
        st.subheader("🗑️ Delete Case Record")
        cur.execute("SELECT case_id, case_title FROM case_table ORDER BY created_at DESC;")
        rows = cur.fetchall()
        if rows:
            case_choice = st.selectbox("Select Case to Delete", [f"{r[0]} - {r[1]}" for r in rows])
            confirm = st.checkbox("Confirm deletion of this case?")
            if confirm and st.button("Delete Selected Case"):
                try:
                    case_id = case_choice.split(" - ")[0]
                    cur.execute("CALL sp_delete_case(%s);", (case_id,))
                    conn.commit()
                    st.success(f"✅ Case {case_id} deleted successfully!")
                except Exception as e:
                    conn.rollback()
                    st.error(f"❌ Error deleting case: {e}")
        else:
            st.info("No cases available to delete.")



    # -----------------------------------------------------
    # Cleanup
    # -----------------------------------------------------
    cur.close()
    conn.close()
