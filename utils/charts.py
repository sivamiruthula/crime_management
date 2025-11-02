import streamlit as st
import matplotlib.pyplot as plt

def plot_status_chart(df):
    if 'STATUS' not in df.columns:
        st.warning("Status column missing from data.")
        return

    status_counts = df['STATUS'].value_counts()
    fig, ax = plt.subplots()
    ax.bar(status_counts.index, status_counts.values)
    ax.set_xlabel("Status")
    ax.set_ylabel("Number of Cases")
    ax.set_title("Case Status Distribution")
    st.pyplot(fig)
