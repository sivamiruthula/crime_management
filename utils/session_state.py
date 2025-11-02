import streamlit as st

def init_session_state():
    if 'user' not in st.session_state:
        st.session_state['user'] = None
