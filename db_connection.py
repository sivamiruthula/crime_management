import psycopg2
import streamlit as st

# --- PostgreSQL Connection Configuration ---
DB_USER = "postgres"         # your PostgreSQL username
DB_PASSWORD = "1"  # replace with your PostgreSQL password
DB_NAME = "crime_db"         # name of the database you created
DB_HOST = "localhost"
DB_PORT = "5432"

# --- 1️⃣ Persistent Connection via Streamlit Session ---
def get_connection():
    """Return a persistent PostgreSQL connection stored in Streamlit session."""
    if "db_conn" in st.session_state:
        try:
            # test the connection
            with st.session_state.db_conn.cursor() as cur:
                cur.execute("SELECT 1;")
            return st.session_state.db_conn
        except Exception:
            st.session_state.db_conn = None

    try:
        conn = psycopg2.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME
        )
        st.session_state.db_conn = conn
        st.toast("✅ Connected to PostgreSQL Database.")
        return conn
    except Exception as e:
        st.error(f"❌ Database connection failed: {e}")
        st.session_state.db_conn = None
        return None


# --- 2️⃣ Safe Query Executor ---
def execute_query(query, params=None):
    conn = get_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            conn.commit()
        return True
    except Exception as e:
        st.error(f"❌ Query execution error: {e}")
        conn.rollback()
        return False


# --- 3️⃣ Fetch Data ---
def fetch_data(query, params=None):
    conn = get_connection()
    if not conn:
        return []
    try:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            cols = [desc[0] for desc in cur.description]
            rows = [dict(zip(cols, row)) for row in cur.fetchall()]
        return rows
    except Exception as e:
        st.error(f"❌ Data fetch error: {e}")
        return []


# --- 4️⃣ Check tables exist ---
def check_tables_exist():
    """Check if required tables exist and are accessible"""
    conn = get_connection()
    if not conn:
        return False

    try:
        query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name IN (
            'case_table', 'complainant', 'crime_type', 'userlogin',
            'investigation', 'case_assignment_history', 'evidence',
            'suspect', 'witness', 'evidence_file'
          );
        """
        existing_tables = fetch_data(query)
        st.write("📋 **Existing Tables:**")
        for table in existing_tables:
            st.write(f"✅ {table['table_name']}")

        required = ['case_table', 'complainant', 'crime_type', 'userlogin']
        missing = [t for t in required if not any(e['table_name'] == t for e in existing_tables)]

        if missing:
            st.error(f"❌ Missing required tables: {', '.join(missing)}")
            return False
        return True
    except Exception as e:
        st.error(f"❌ Error checking tables: {e}")
        return False


# --- 5️⃣ Streamlit entrypoint ---
if __name__ == "__main__":
    st.title("🚓 Crime Management System - PostgreSQL Connectivity Test")

    connected = get_connection()
    if connected:
        st.success("✅ Connected to PostgreSQL Database!")
        if check_tables_exist():
            st.success("✅ All required tables exist!")
        else:
            st.warning("⚠️ Some required tables are missing.")
    else:
        st.error("❌ Could not connect to database.")
