import os
import subprocess

def start_backend():
    """
    Launch Streamlit backend for the Crime Management System.
    """
    print("🚀 Starting Crime Management System Backend...")

    # Activate your Python environment if needed
    venv_path = r"D:\Crime-Management-System-main\frontend_env\Scripts\activate"
    project_path = r"D:\Crime-Management-System-main"

    # Run Streamlit backend
    command = f'cmd /k "cd /d {project_path} && call {venv_path} && streamlit run main_backend.py"'
    subprocess.Popen(command, shell=True)

    print("✅ Backend is running! Visit http://localhost:8501 in your browser.")

if __name__ == "__main__":
    start_backend()
