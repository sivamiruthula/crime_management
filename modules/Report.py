import streamlit as st
from streamlit.components.v1 import html
import sys
import os

def app():
    # add backend project /src to path
    sys.path.append(os.path.abspath("./crime_analytics_project/src"))

    from visualizer import CrimeVisualizer



    # PAGE SETTINGS
    st.set_page_config(
        page_title="Crime Analytics Reports",
        layout="wide"
    )

    st.title("📊 Crime Analytics Reports & Insights")

    # Initialize visualizer once
    viz = CrimeVisualizer()
    viz.load_data()

    # -------------------------------------------------------
    # SAFE FILE READER (avoid errors if user hasn't generated)
    # -------------------------------------------------------
    def safe_read(file_path):
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            st.warning(f"⚠️ Missing file: {file_path}")
            return None

    # -------------------------------------------------------
    # FIRST TAB: MAPS
    # -------------------------------------------------------
    tab1, tab2, tab3, tab4 = st.tabs(
        ["🗺️ Hotspot Maps", "📌 Cluster Map", "📈 Temporal Charts", "📑 Summary & Dashboard"]
    )

    with tab1:
        st.header("Crime Hotspot Heatmap")

        heatmap_html_path = "crime_analytics_project/outputs/maps/crime_hotspot_heatmap.html"

        # If map doesn't exist, generate once
        if not os.path.exists(heatmap_html_path):
            viz.create_hotspot_heatmap()

        heat_html = safe_read(heatmap_html_path)
        if heat_html:
            html(heat_html, height=600)

    with tab2:
        st.header("Crime Cluster Visualization")

        clustermap_html_path = "crime_analytics_project/outputs/maps/crime_clusters_map.html"

        if not os.path.exists(clustermap_html_path):
            viz.create_cluster_map()

        cluster_html = safe_read(clustermap_html_path)
        if cluster_html:
            html(cluster_html, height=600)

    with tab3:
        st.header("Temporal Analysis Charts")

        chart_path = "crime_analytics_project/outputs/charts/temporal_analysis.png"


        if not os.path.exists(chart_path):
            viz.create_temporal_analysis_charts()

        if os.path.exists(chart_path):
            st.image(chart_path, caption="Temporal Crime Trends", use_container_width=True)


    with tab4:
        st.header("Interactive Plotly Dashboard")

        dashboard_path = "crime_analytics_project/outputs/reports/interactive_dashboard.html"


        if not os.path.exists(dashboard_path):
            viz.create_interactive_dashboard()

        dashboard_html = safe_read(dashboard_path)
        if dashboard_html:
            html(dashboard_html, height=800)

        st.divider()
        st.header("📌 Summary Statistics")

        summary_path = "crime_analytics_project/outputs/reports/summary_statistics.txt"


        if not os.path.exists(summary_path):
            viz.generate_summary_statistics()

        if os.path.exists(summary_path):
            with open(summary_path, "r") as f:
                st.text(f.read())

    st.success("✅ Reports loaded successfully!")
