import streamlit as st
import sqlite3
import requests
import uuid
from streamlit_option_menu import option_menu

# FastAPI API Base URL
BASE_URL = "https://a157-139-5-49-82.ngrok-free.app/v1"  # Replace with your ngrok URL or local FastAPI URL

# Database connection and setup
conn = sqlite3.connect('user_data.db', check_same_thread=False)
c = conn.cursor()

# Create users table if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS users 
             (username TEXT PRIMARY KEY, password TEXT, user_type TEXT)''')
conn.commit()

# Function to add a user to the database
def add_user(username, password, user_type):
    c.execute('INSERT INTO users (username, password, user_type) VALUES (?, ?, ?)', (username, password, user_type))
    conn.commit()

# Function to check if a user exists
def user_exists(username):
    c.execute('SELECT * FROM users WHERE username=?', (username,))
    return c.fetchone()

# Function to authenticate a user
def authenticate_user(username, password):
    c.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
    return c.fetchone()

# Function to call FastAPI's /send_message endpoint
def send_message(query):
    url = f"{BASE_URL}/chat/send_message?message={query}"
    try:
        response = requests.post(url)
        if response.status_code == 200:
            return response.json().get("content", "No response available.")
        else:
            return f"Error contacting the server: {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"

# Function to upload a file (certification or achievement) to FastAPI
def upload_file(file, employee_name, upload_type):
    if upload_type == "certification":
        url = f"{BASE_URL}/skills/upload_certification/{employee_name}"
    elif upload_type == "achievement":
        url = f"{BASE_URL}/skills/upload_achievements/{employee_name}"
    
    # Send the file to the server
    files = {'file': file}
    response = requests.post(url, files=files)
    
    if response.status_code == 200:
        st.success(f"{upload_type.capitalize()} uploaded successfully for {employee_name}!")
    else:
        st.error(f"Failed to upload {upload_type}. Error: {response.text}")

# Chat app page (for HR)
def hr_chat_page():
    st.title("🚀 Profile Query Bot for HR")

    # Initialize session state for conversation history and conversation_id
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # Chat Interface
    st.subheader("Chat with the Assistant")

    # Display existing chat messages
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input box for user queries
    if user_input := st.chat_input("Ask a question about an employee's profile or anything else..."):
        # Display user message in chat history
        st.session_state["messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Call FastAPI's /send_message API to get results
        with st.chat_message("assistant"):
            with st.spinner("Processing your query..."):
                response = send_message(user_input)

                # Display the response in chat
                st.markdown(f"**Assistant Response:**\n\n{response}")

                # Append assistant response to chat history
                st.session_state["messages"].append({
                    "role": "assistant",
                    "content": f"{response}"
                })

# Streamlit layout
st.set_page_config(page_title="HR Profile Query Bot", layout="wide")

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["role"] = None

# Registration Page
def register_page():
    st.title("Register")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    user_type = st.selectbox("Select your role", ["Employee", "HR", "Manager"])

    if st.button("Register"):
        if user_exists(username):
            st.error("Username already exists. Please choose a different one.")
        else:
            add_user(username, password, user_type)
            st.success("Registration successful! You can now log in.")

# HR Dashboard Page
def hr_page():
    st.title("HR Dashboard")
    st.write("Welcome, HR! You can manage employee profiles and ask for profile-related details.")
    hr_chat_page()  # Redirect HR to chat page

# Sidebar for file upload functionality
def upload_documents_sidebar():
    with st.sidebar:
        st.title("Upload Documents")

        # Ask for employee name
        employee_name = st.text_input("Enter Employee Name", key="employee_name_input")

        # Ensure that employee name is entered before proceeding
        if employee_name:
            st.subheader("Upload Certification")
            cert_file = st.file_uploader("Upload Certification File", type=["pdf", "docx"], key="cert_file")
            
            # Upload certification if file is selected
            if cert_file:
                if st.button("Upload Certification", key="upload_cert_button"):
                    upload_file(cert_file, employee_name, "certification")
            
            st.subheader("Upload Achievement")
            achievement_file = st.file_uploader("Upload Achievement File", type=["pdf", "docx"], key="achievement_file")

            # Upload achievement if file is selected
            if achievement_file:
                if st.button("Upload Achievement", key="upload_achievement_button"):
                    upload_file(achievement_file, employee_name, "achievement")
        else:
            st.warning("Please enter an employee name to proceed with file uploads.")

# Logout function
def logout():
    st.session_state["logged_in"] = False
    st.session_state["role"] = None
    st.experimental_rerun()

# Login Page
def login_page():
    st.title("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user_data = authenticate_user(username, password)
        if user_data:
            st.session_state["logged_in"] = True
            st.session_state["role"] = user_data[2]  # role is stored in the 3rd column in the database
            st.success(f"Logged in as {user_data[2]}")
            st.experimental_rerun()
        else:
            st.error("Invalid credentials. Please try again.")

# Main App Navigation (Login/Registration)
def main():
    if not st.session_state["logged_in"]:
        st.sidebar.title("Navigation")
        choice = st.sidebar.radio("Go to", ["Login", "Register"])

        if choice == "Login":
            login_page()
        else:
            register_page()

    if st.session_state["logged_in"]:
        # Sidebar with logout option after login
        with st.sidebar:
            st.sidebar.title(f"{st.session_state['role']} Menu")
            selected = option_menu(
                menu_title="Menu",
                options=[f"{st.session_state['role']} Home", "Logout"],
                icons=["house", "box-arrow-right"],
                menu_icon="cast",
                default_index=0,
            )

            if selected == "Logout":
                logout()

        # Role-based navigation after login
        if st.session_state["role"] == "HR":
            hr_page()

            upload_documents_sidebar()

        else:
            st.error("Only HR users are allowed in this version.")

# Run the app
if __name__ == "__main__":
    main()
