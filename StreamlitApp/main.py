

from fastapi import UploadFile
import streamlit as st
from pymongo import MongoClient
import bcrypt
import uuid
from datetime import datetime
from streamlit_option_menu import option_menu
import requests
from file_chat_input import file_chat_input
from streamlit_float import float_init

# MongoDB connection setup
client = MongoClient("mongodb://localhost:27017/")  # Replace with your MongoDB URL
db = client["default_db_name"]
user_collection = db["users"]

# FastAPI API Base URL
BASE_URL = "https://9815-139-5-49-243.ngrok-free.app/v1"  # Replace with your FastAPI URL

# Initialize session state variables
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "role" not in st.session_state:
    st.session_state["role"] = None
if "selected_role" not in st.session_state:
    st.session_state["selected_role"] = None
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None

# Utility functions for authentication and data storage
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def add_user_to_mongo(user_id, username, password, user_type, email):
    hashed_password = hash_password(password)
    user_data = {
        "user_id": user_id,
        "username": username,
        "password": hashed_password,
        "user_type": user_type,
        "email": email,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    try:
        user_collection.insert_one(user_data)
        return True
    except:
        return False

def user_exists(username):
    return user_collection.find_one({"username": username}) is not None

def authenticate_user(username, password):
    user = user_collection.find_one({"username": username})
    if user and verify_password(password, user["password"]):
        return user
    return None

# Streamlit layout and pages
def role_selection_page():
    st.title("Select Your Role")
    
    # Adding "Please select your role to proceed" as a placeholder without a default selection
    roles = ["Please select your role to proceed:", "HR", "Employee", "Manager"]
    selected_role = st.selectbox("Label", roles, index=0)  # Default selection set to the placeholder
    
    if selected_role != "Please select your role to proceed:":
        if st.button("Continue"):
            st.session_state["selected_role"] = selected_role
            st.rerun()
    else:
        st.warning("Please select your role to proceed.")

def register_page():
    st.title("Register")
    user_id = st.number_input("User ID", min_value=1000000, max_value=9999999)
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    email = st.text_input("Email")
    user_type = st.session_state.get("selected_role", "Employee")

    if st.button("Register"):
        if user_exists(username):
            st.error("Username already exists. Please choose a different one.")
        else:
            if add_user_to_mongo(user_id, username, password, user_type, email):
                st.success("Registration successful! You can now log in.")
            else:
                st.error("Registration failed. Please try again.")

def login_page():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user_data = authenticate_user(username, password)
        if user_data:
            st.session_state["logged_in"] = True
            st.session_state["role"] = user_data["user_type"]
            st.session_state["user_id"] = user_data["user_id"]
            st.success(f"Logged in as {user_data['user_type']}")
            st.rerun()
        else:
            st.error("Invalid credentials. Please try again.")

def send_message(query):
    url = f"{BASE_URL}/chat/send_message?message={query}"
    response = requests.post(url)
    if response.status_code == 200:
        return response.json().get("content", "No response available.")
    else:
        return f"Error contacting the server: {response.status_code}"


# Function to upload resume to the specified endpoint
def upload_resume(file, user_id):
    url = f"{BASE_URL}/vector/upload_resume/{user_id}"
    st.write(f"Uploading resume to: {url}")  # Debugging output
    
    # Prepare the file payload with application/pdf MIME type
    files = {"file": (file.name, file.getvalue(), "application/pdf")}
    
    try:
        response = requests.post(url, files=files)
        response.raise_for_status()  # Raise an error for unsuccessful responses
        st.write("Server response:", response.status_code, response.json())  # Debug output
        return response.json().get("message", "Resume uploaded successfully.")
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to upload resume. Error: {str(e)}")
        return f"Failed to upload resume. Error: {str(e)}"

# Main function for the HR chat page
# def hr_chat_page():
#     st.title("🚀 Profile Query Bot for HR")

#     # Initialize session state for messages and tracking
#     if "messages" not in st.session_state:
#         st.session_state["messages"] = []
#     if "awaiting_user_id" not in st.session_state:
#         st.session_state["awaiting_user_id"] = False
#     if "target_user_id" not in st.session_state:
#         st.session_state["target_user_id"] = None
#     if "awaiting_file_upload" not in st.session_state:
#         st.session_state["awaiting_file_upload"] = False

#     # Display chat messages
#     for message in st.session_state["messages"]:
#         with st.chat_message(message["role"]):
#             st.markdown(message["content"])

#     # Check if awaiting user ID for profile update/upload resume
#     if st.session_state["awaiting_user_id"]:
#         # Ask for user ID input
#         user_id_input = st.chat_input("Please enter the user ID for the profile update:")
#         if user_id_input:
#             st.session_state["target_user_id"] = user_id_input
#             st.session_state["awaiting_user_id"] = False  # Stop waiting for user_id
#             st.session_state["awaiting_file_upload"] = True  # Now await file upload
#             st.session_state["messages"].append({"role": "user", "content": user_id_input})
            
#             with st.chat_message("user"):
#                 st.markdown(user_id_input)
            
#     # Check if awaiting file upload after receiving user ID
#     if st.session_state["awaiting_file_upload"]:
#         # Display file uploader
#         file_upload = st.file_uploader("Please upload the PDF file for the profile update:")
#         if file_upload:
#             # Process file upload with the provided user ID
#             with st.spinner("Uploading file..."):
#                 response = upload_resume(file_upload, st.session_state["target_user_id"])
#                 # st.markdown(f"**Upload Response:** {response}")
#                 # st.session_state["messages"].append({"role": "assistant", "content": response})
#             # Reset file upload and target_user_id after upload
#             st.session_state["target_user_id"] = None
#             st.session_state["awaiting_file_upload"] = False

#     # Standard chat input for questions or commands
#     else:
#         user_input = st.chat_input("Ask a question or type 'update profile' to update a user's profile...")
#         if user_input:
#             st.session_state["messages"].append({"role": "user", "content": user_input})
            
#             with st.chat_message("user"):
#                 st.markdown(user_input)

#             if "update profile" in user_input.lower() or "upload resume" in user_input.lower():
#                 # Bot asks for user ID when 'update profile' or 'upload resume' is mentioned
#                 bot_message = "Please provide the user ID for the profile you want to update."
#                 st.session_state["messages"].append({"role": "assistant", "content": bot_message})
                
#                 with st.chat_message("assistant"):
#                     st.markdown(bot_message)
                
#                 st.session_state["awaiting_user_id"] = True  # Set flag to wait for user_id input
            
#             else:
#                 # Handle regular queries via assistant API
#                 with st.chat_message("assistant"):
#                     with st.spinner("Processing your query..."):
#                         response = send_message(user_input)
#                         st.markdown(f"**Assistant Response:**\n\n{response}")
#                         st.session_state["messages"].append({"role": "assistant", "content": response})

def hr_chat_page():
    st.title("🚀 Profile Query Bot for HR")

    # Initialize session state for messages and tracking
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "awaiting_user_id" not in st.session_state:
        st.session_state["awaiting_user_id"] = False
    if "target_user_id" not in st.session_state:
        st.session_state["target_user_id"] = None
    if "awaiting_update_option" not in st.session_state:
        st.session_state["awaiting_update_option"] = False
    if "selected_update_option" not in st.session_state:
        st.session_state["selected_update_option"] = None
    if "awaiting_file_upload" not in st.session_state:
        st.session_state["awaiting_file_upload"] = False

    # Display chat messages
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Check if awaiting user ID for profile update or resume upload
    if st.session_state["awaiting_user_id"]:
        # Ask for user ID input
        user_id_input = st.chat_input("Please enter the user ID for the profile update or resume upload:")
        if user_id_input:
            st.session_state["target_user_id"] = user_id_input
            st.session_state["awaiting_user_id"] = False  # Stop waiting for user_id
            if st.session_state["awaiting_file_upload"]:
                # Display file uploader for resume upload
                file_upload = st.file_uploader("Please upload the PDF file for the profile update:", type="pdf")
                if file_upload:
                    # Process file upload with the provided user ID
                    with st.spinner("Uploading file..."):
                        response = upload_resume(file_upload, st.session_state["target_user_id"])
                        st.session_state["messages"].append({"role": "assistant", "content": response})
                    # Reset target_user_id after upload
                    st.session_state["target_user_id"] = None
                    st.session_state["awaiting_file_upload"] = False
            else:
                # Otherwise, show options for updating profile details
                st.session_state["awaiting_update_option"] = True  # Now await update option
            st.session_state["messages"].append({"role": "user", "content": user_id_input})
            
            with st.chat_message("user"):
                st.markdown(user_id_input)

    # Check if awaiting update option selection
    elif st.session_state["awaiting_update_option"]:
        st.markdown("Select the details you want to update:")
        if st.button("Skills details"):
            st.session_state["selected_update_option"] = "skills"
        elif st.button("Certificate details"):
            st.session_state["selected_update_option"] = "certificate"
        elif st.button("Project details"):
            st.session_state["selected_update_option"] = "project"

        if st.session_state["selected_update_option"]:
            st.session_state["awaiting_update_option"] = False  # Stop waiting for update option

    # Show respective form based on selected update option
    elif st.session_state["selected_update_option"] == "skills":
        # Display skills update form
        skill_name = st.text_input("Skill Name")
        skill_level = st.selectbox("Skill Level", ["Beginner", "Intermediate", "Advanced"])
        submit_skills = st.button("Submit Skills")
        if submit_skills:
            # Process and save skills data
            response = save_data("skills", st.session_state["target_user_id"], {
                "skill_name": skill_name,
                "skill_level": skill_level
            })
            st.write(f"Response: {response}")
            st.session_state["messages"].append({"role": "assistant", "content": "Skills updated successfully."})
            st.session_state["selected_update_option"] = None

    elif st.session_state["selected_update_option"] == "certificate":
        # Display certificate update form
        cert_name = st.text_input("Certification Name")
        cert_date = st.date_input("Certification Date")
        cert_entity = st.text_input("Issuing Entity")
        submit_certificate = st.button("Submit Certificate")
        if submit_certificate:
            # Process and save certificate data
            response = save_data("certificate", st.session_state["target_user_id"], {
                "cert_name": cert_name,
                "cert_date": cert_date,
                "cert_entity": cert_entity
            })
            st.write(f"Response: {response}")
            st.session_state["messages"].append({"role": "assistant", "content": "Certificate updated successfully."})
            st.session_state["selected_update_option"] = None

    elif st.session_state["selected_update_option"] == "project":
        # Display project update form
        project_name = st.text_input("Project Name")
        project_description = st.text_area("Project Description")
        submit_project = st.button("Submit Project")
        if submit_project:
            # Process and save project data
            response = save_data("project", st.session_state["target_user_id"], {
                "project_name": project_name,
                "project_description": project_description
            })
            st.write(f"Response: {response}")
            st.session_state["messages"].append({"role": "assistant", "content": "Project updated successfully."})
            st.session_state["selected_update_option"] = None

    # Standard chat input for other questions or commands
    else:
        user_input = st.chat_input("Ask a question or type 'update profile' or 'upload resume' to update a user's profile or upload their resume...")
        if user_input:
            st.session_state["messages"].append({"role": "user", "content": user_input})
            
            with st.chat_message("user"):
                st.markdown(user_input)

            if "update profile" in user_input.lower():
                # Bot asks for user ID when 'update profile' is mentioned
                bot_message = "Please provide the user ID for the profile you want to update."
                st.session_state["messages"].append({"role": "assistant", "content": bot_message})
                
                with st.chat_message("assistant"):
                    st.markdown(bot_message)
                
                st.session_state["awaiting_user_id"] = True  # Set flag to wait for user_id input

            elif "upload resume" in user_input.lower():
                # Bot asks for user ID when 'upload resume' is mentioned
                bot_message = "Please provide the user ID for the resume you want to upload."
                st.session_state["messages"].append({"role": "assistant", "content": bot_message})
                
                with st.chat_message("assistant"):
                    st.markdown(bot_message)
                
                st.session_state["awaiting_user_id"] = True  # Set flag to wait for user_id input
                st.session_state["awaiting_file_upload"] = True  # Set flag for file upload flow

            else:
                # Handle regular queries via assistant API
                with st.chat_message("assistant"):
                    with st.spinner("Processing your query..."):
                        response = send_message(user_input)
                        st.markdown(f"**Assistant Response:**\n\n{response}")
                        st.session_state["messages"].append({"role": "assistant", "content": response})

# Function to save data based on type
def save_data(data_type, user_id, data):
    # Implement the logic to save data (skills, certificate, project) to the backend
    # Mocked response for now
    return f"{data_type.capitalize()} details for user {user_id} saved successfully."





def hr_page():
    st.title("HR Dashboard")
    st.write("Welcome, HR! You can manage employee profiles and ask for profile-related details.")
    hr_chat_page()

# Logout function
def logout():
    st.session_state["logged_in"] = False
    st.session_state["role"] = None
    st.rerun()

# Main navigation
def main():
    if "selected_role" not in st.session_state or st.session_state["selected_role"] is None:
        role_selection_page()
    else:
        if not st.session_state["logged_in"]:
            st.sidebar.title("Navigation")
            choice = st.sidebar.radio("Go to", ["Login", "Register"])
            if choice == "Login":
                login_page()
            else:
                register_page()
        if st.session_state["logged_in"]:
            with st.sidebar:
                st.sidebar.title(f"{st.session_state['role']} Menu")
                selected = option_menu("Menu", [f"{st.session_state['role']} Home", "Logout"], icons=["house", "box-arrow-right"], menu_icon="cast", default_index=0)
                if selected == "Logout":
                    logout()
            if st.session_state["role"] == "HR":
                hr_page()
            else:
                st.error("Only HR users are allowed in this version.")

if __name__ == "__main__":
    main()
