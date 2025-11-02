import streamlit as st
from streamlit_option_menu import option_menu
from modules import (
    complaint_registration,
    case_assignment,
    investigation,
    case_closure,
    reports,
    evidence_upload,
    Report
)
import utils.session_state as session_state

st.set_page_config(page_title="Crime Record Management System", layout="wide")
session_state.init_session_state()

with st.sidebar:
    selected = option_menu(
        "CRIME RECORD SYSTEM",
        ["Complaint Registration", "Case Assignment", "Investigation", "Case Closure", "Reports", "Evidence Upload","Report"],  # 👈 added
        icons=["pencil", "person-badge", "search", "check2-circle", "bar-chart", "upload","file-earmark"],
        menu_icon="shield-lock",
        default_index=0,
    )

if selected == "Complaint Registration":
    complaint_registration.app()
elif selected == "Case Assignment":
    case_assignment.app()
elif selected == "Investigation":
    investigation.app()
elif selected == "Case Closure":
    case_closure.app()
elif selected == "Reports":
    reports.app()
elif selected=="Evidence Upload":
    evidence_upload.app()
elif selected == "Report":
    Report.app()
