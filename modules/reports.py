import streamlit as st
import pandas as pd
from db_connection import get_connection, fetch_data
from utils.charts import plot_status_chart

def app():
    st.title("📊 CASE REPORTS & ANALYTICS")

    # Create Oracle connection
    conn = get_connection()
    if not conn:
        st.error("❌ DATABASE CONNECTION FAILED.")
        return

    try:
        # Fetch report data from CASE_TABLE
        query = "SELECT * FROM CASE_TABLE"
        rows = fetch_data(query)

        if not rows:
            st.info("NO CASE RECORDS FOUND IN THE DATABASE.")
            return

        # Convert fetched data into DataFrame
        df = pd.DataFrame(rows)
        st.subheader("📂 CASE TABLE DATA")
        st.dataframe(df, use_container_width=True)

        # Show case status chart (only if STATUS column exists)
        if "STATUS" in df.columns:
            st.subheader("📈 CASE STATUS DISTRIBUTION")
            plot_status_chart(df)
        else:
            st.warning("⚠️ 'STATUS' COLUMN NOT FOUND — CANNOT PLOT STATUS CHART.")

        st.success("✅ REPORT LOADED SUCCESSFULLY.")

    except Exception as e:
        st.error(f"❌ FAILED TO LOAD REPORT: {e}")
