import streamlit as st
from streamlit_chat import message  # Importing the streamlit_chat package

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
import regex as re
import requests
import json

# MongoDB connection setup
client = MongoClient("mongodb://localhost:27017/")  # Replace with your MongoDB URL
db = client["default_db_name"]
user_collection = db["users"]

# FastAPI API Base URL
BASE_URL = "https://1517-139-5-49-43.ngrok-free.app/v1"  # Replace with your FastAPI URL

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
    
    # Role options with a placeholder
    roles = ["Please select your role to proceed:", "HR", "Employee", "Manager"]
    selected_role = st.selectbox("Label", roles, index=0)  # Default selection is the placeholder

    if selected_role != "Please select your role to proceed:":
        if st.button("Continue"):
            st.session_state["selected_role"] = selected_role  # Store role in session state
            st.experimental_rerun()  # Refresh to navigate to the chat page
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

def send_message(role, query):
    """
    Sends a message to the API with the specified role and query.
    """
    url = f"{BASE_URL}/chat/send_message"  # Updated API endpoint
    headers = {"Content-Type": "application/json"}  # Specify JSON content type
    payload = {
        "role": role,
        "message": query  # User's query
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raise exception for HTTP errors
        return response.json()  # Return the full JSON response for processing
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to send message: {str(e)}"}





# Function to upload resume to the specified endpoint
def upload_resume(file, user_id):
    url = f"{BASE_URL}/vector/upload_resume/{user_id}"
    st.write(f"Uploading resume to: {url}")  # Debugging output
    
    # Prepare the file payload with application/pdf MIME type
    files = {"file": (file.name, file.getvalue(), "application/pdf")}
    
    try:
        response = requests.post(url, files=files)
        response.raise_for_status()  # Raise an error for unsuccessful responses
        # st.write("Server response:", response.status_code, response.json())  # Debug output
        return response.json().get("message", "Resume uploaded successfully.")
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to upload resume. Error: {str(e)}")
        return f"Failed to upload resume. Error: {str(e)}"


# def format_profiles_with_links(content):
#     """
#     Formats the profiles content to include clickable resume download links.
#     """
#     # BASE_URL = "https://1517-139-5-49-43.ngrok-free.app/v1"  # Replace with your base API URL
#     formatted_content = ""

#     # Split the content into lines
#     lines = content.split("\n")
#     for line in lines:
#         if "Profile:" in line:
#             # Extract the profile ID
#             profile_id = line.split("Profile:")[1].split(".pdf")[0].strip()

#             # Generate the resume download link
#             resume_url = f"{BASE_URL}/user/download_resume/{profile_id}"

#             # Add the download link to the line
#             line += f" [*Download Resume*]({resume_url})"
        
#         # Append the line to the formatted content
#         formatted_content += line + "\n"

#     return formatted_content

def format_profiles_with_links(content, base_url):
    """
    Formats the profiles content to include clickable resume download links and a count of profiles.
    """
    formatted_content = ""
    profile_count = 0

    # Split the content into lines
    lines = content.split("\n")
    for line in lines:
        if "Profile:" in line:
            # Extract the profile ID
            profile_id = line.split("Profile:")[1].split(".pdf")[0].strip()

            # Generate the resume download link
            resume_url = f"{base_url}/user/download_resume/{profile_id}"

            # Add the download link to the line
            line += f" [*Download Resume*]({resume_url})"

            # Increment the profile count
            profile_count += 1

        # Append the line to the formatted content
        formatted_content += line + "\n"

    # Add the profile count summary at the top
    if profile_count > 0:
        formatted_content = f"Here are the {profile_count} profiles for your query:\n\n" + formatted_content

    return formatted_content

import streamlit as st

def hr_chat_page():
    st.title("🚀 Profile Query Bot for HR")

    if "selected_role" not in st.session_state:
        st.warning("Please select your role to proceed.")
        st.stop()

    # Initialize session states
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "awaiting_user_id" not in st.session_state:
        st.session_state["awaiting_user_id"] = False
    if "target_user_id" not in st.session_state:
        st.session_state["target_user_id"] = None
    if "awaiting_file_upload" not in st.session_state:
        st.session_state["awaiting_file_upload"] = False
    if "awaiting_update_option" not in st.session_state:
        st.session_state["awaiting_update_option"] = False
    if "selected_update_option" not in st.session_state:
        st.session_state["selected_update_option"] = None
    if "expanded_messages" not in st.session_state:
        st.session_state["expanded_messages"] = {}

    role = st.session_state["selected_role"]
    st.subheader(f"Role: {role}")

    # Helper function to toggle messages
    def render_collapsible_text(message, message_key, max_length=150):
        if message_key not in st.session_state["expanded_messages"]:
            st.session_state["expanded_messages"][message_key] = False

        if len(message) <= max_length or st.session_state["expanded_messages"][message_key]:
            st.markdown(message, unsafe_allow_html=True)
            if len(message) > max_length:
                if st.button("Show Less", key=f"less_{message_key}"):
                    st.session_state["expanded_messages"][message_key] = False
                    st.experimental_rerun()
        else:
            truncated_message = message[:max_length] + "..."
            st.markdown(truncated_message, unsafe_allow_html=True)
            if st.button("Read More", key=f"more_{message_key}"):
                st.session_state["expanded_messages"][message_key] = True
                st.experimental_rerun()

    # Display chat messages
    for i, message in enumerate(st.session_state["messages"]):
        message_key = f"message_{i}"
        if message["role"] == "user":
            st.markdown(
                f"<div style='text-align: right; margin: 10px;'>"
                f"<div style='display: inline-block; background-color: #DCF8C6; color: #000; padding: 10px; border-radius: 10px; max-width: 70%; word-wrap: break-word;'>",
                unsafe_allow_html=True,
            )
            render_collapsible_text(message["content"], message_key)
            st.markdown("</div></div>", unsafe_allow_html=True)
        else:
            st.markdown(
                f"<div style='text-align: left; margin: 10px;'>"
                f"<div style='display: inline-block; background-color: #FFF; color: #000; padding: 10px; border-radius: 10px; border: 1px solid #CCC; max-width: 70%; word-wrap: break-word;'>",
                unsafe_allow_html=True,
            )
            formatted_content = format_profiles_with_links(message["content"],base_url=BASE_URL)
            render_collapsible_text(formatted_content, message_key)
            st.markdown("</div></div>", unsafe_allow_html=True)

    # Handle "Upload Resume" flow
    if st.session_state["awaiting_user_id"]:
        user_id_input = st.text_input("Please enter the user ID for the action:")
        if user_id_input:
            st.session_state["target_user_id"] = user_id_input
            st.session_state["awaiting_user_id"] = False
            if st.session_state["awaiting_file_upload"]:
                file_upload = st.file_uploader("Upload the PDF file for the user's resume:")
                if file_upload:
                    with st.spinner("Uploading file..."):
                        response = upload_resume(file_upload, user_id_input)
                    st.session_state["messages"].append(
                        {"role": "assistant", "content": "Resume uploaded successfully!"}
                    )
                    st.session_state["awaiting_file_upload"] = False
                    st.experimental_rerun()
            elif st.session_state["awaiting_update_option"]:
                st.session_state["awaiting_update_option"] = True
                st.experimental_rerun()

    # Handle "Update Profile" options
    elif st.session_state["awaiting_update_option"]:
        st.markdown("What would you like to update?")
        if st.button("Skills"):
            st.session_state["selected_update_option"] = "skills"
        elif st.button("Certifications"):
            st.session_state["selected_update_option"] = "certifications"
        elif st.button("Projects"):
            st.session_state["selected_update_option"] = "projects"

        if st.session_state["selected_update_option"]:
            st.session_state["awaiting_update_option"] = False
            st.experimental_rerun()

    # Handle the selected update option
    elif st.session_state["selected_update_option"] == "skills":
        skill_name = st.text_input("Skill Name")
        skill_level = st.selectbox("Skill Level", ["Beginner", "Intermediate", "Advanced"])
        submit_skills = st.button("Submit Skills")
        if submit_skills:
            response = update_skills(
                st.session_state["target_user_id"], {"skill_name": skill_name, "skill_level": skill_level}
            )
            st.session_state["messages"].append({"role": "assistant", "content": "Skills updated successfully!"})
            st.session_state["selected_update_option"] = None
            st.experimental_rerun()

    elif st.session_state["selected_update_option"] == "certifications":
        cert_name = st.text_input("Certification Name")
        cert_date = st.date_input("Certification Date")
        cert_entity = st.text_input("Issuing Entity")
        submit_cert = st.button("Submit Certification")
        if submit_cert:
            response = update_certifications(
                st.session_state["target_user_id"],
                {"cert_name": cert_name, "cert_date": cert_date, "cert_entity": cert_entity},
            )
            st.session_state["messages"].append(
                {"role": "assistant", "content": "Certification updated successfully!"}
            )
            st.session_state["selected_update_option"] = None
            st.experimental_rerun()

    elif st.session_state["selected_update_option"] == "projects":
        project_name = st.text_input("Project Name")
        project_description = st.text_area("Project Description")
        submit_project = st.button("Submit Project")
        if submit_project:
            response = update_projects(
                st.session_state["target_user_id"],
                {"project_name": project_name, "project_description": project_description},
            )
            st.session_state["messages"].append({"role": "assistant", "content": "Project updated successfully!"})
            st.session_state["selected_update_option"] = None
            st.experimental_rerun()

    # General user input handler
    else:
        user_input = st.chat_input("Ask a question or type 'update profile' or 'upload resume'...")
        if user_input:
            st.session_state["messages"].append({"role": "user", "content": user_input})
            with st.spinner("Processing your query..."):
                response = send_message(role, user_input)
                if "error" in response:
                    st.session_state["messages"].append({"role": "assistant", "content": response["error"]})
                else:
                    message_status = response.get("message", "No status available.")
                    content = response.get("content", "No profiles available.")
                    formatted_content = format_profiles_with_links(content,base_url=BASE_URL)
                    response_message = f"*{message_status}*\n\n{formatted_content}"
                    st.session_state["messages"].append({"role": "assistant", "content": response_message})
            st.experimental_rerun()

# def hr_chat_page():
#     st.title("🚀 Profile Query Bot for HR")

#     if "selected_role" not in st.session_state:
#         st.warning("Please select your role to proceed.")
#         st.stop()

#     # Initialize session states
#     if "messages" not in st.session_state:
#         st.session_state["messages"] = []
#     if "awaiting_user_id" not in st.session_state:
#         st.session_state["awaiting_user_id"] = False
#     if "target_user_id" not in st.session_state:
#         st.session_state["target_user_id"] = None
#     if "awaiting_file_upload" not in st.session_state:
#         st.session_state["awaiting_file_upload"] = False
#     if "awaiting_update_option" not in st.session_state:
#         st.session_state["awaiting_update_option"] = False
#     if "selected_update_option" not in st.session_state:
#         st.session_state["selected_update_option"] = None
#     if "expanded_messages" not in st.session_state:
#         st.session_state["expanded_messages"] = {}

#     role = st.session_state["selected_role"]
#     st.subheader(f"Role: {role}")

#     def format_download_links(content):
#         """
#         Replace direct URLs with 'Download Resume' links.
#         """
#         # Replace URLs with the text 'Download Resume'
#         return re.sub(r"https://[\w\-.]+", r"[Download Resume](\g<0>)", content)

#     # Helper function to toggle messages
#     def render_collapsible_text(message, message_key, max_length=150):
#         if message_key not in st.session_state["expanded_messages"]:
#             st.session_state["expanded_messages"][message_key] = False

#         if len(message) <= max_length or st.session_state["expanded_messages"][message_key]:
#             st.markdown(message, unsafe_allow_html=True)
#             if len(message) > max_length:
#                 if st.button("Show Less", key=f"less_{message_key}"):
#                     st.session_state["expanded_messages"][message_key] = False
#                     st.experimental_rerun()
#         else:
#             truncated_message = message[:max_length] + "..."
#             st.markdown(truncated_message, unsafe_allow_html=True)
#             if st.button("Read More", key=f"more_{message_key}"):
#                 st.session_state["expanded_messages"][message_key] = True
#                 st.experimental_rerun()

#     # Display chat messages
#     for i, message in enumerate(st.session_state["messages"]):
#         message_key = f"message_{i}"
#         if message["role"] == "user":
#             st.markdown(
#                 f"<div style='text-align: right; margin: 10px;'>"
#                 f"<div style='display: inline-block; background-color: #DCF8C6; color: #000; padding: 10px; border-radius: 10px; max-width: 70%; word-wrap: break-word;'>",
#                 unsafe_allow_html=True,
#             )
#             render_collapsible_text(message["content"], message_key)
#             st.markdown("</div></div>", unsafe_allow_html=True)
#         else:
#             st.markdown(
#                 f"<div style='text-align: left; margin: 10px;'>"
#                 f"<div style='display: inline-block; background-color: #FFF; color: #000; padding: 10px; border-radius: 10px; border: 1px solid #CCC; max-width: 70%; word-wrap: break-word;'>",
#                 unsafe_allow_html=True,
#             )
#             formatted_content = format_download_links(message["content"])
#             render_collapsible_text(formatted_content, message_key)
#             st.markdown("</div></div>", unsafe_allow_html=True)

#     # Handle "Upload Resume" flow
#     if st.session_state["awaiting_user_id"]:
#         user_id_input = st.text_input("Please enter the user ID for the action:")
#         if user_id_input:
#             st.session_state["target_user_id"] = user_id_input
#             st.session_state["awaiting_user_id"] = False
#             if st.session_state["awaiting_file_upload"]:
#                 file_upload = st.file_uploader("Upload the PDF file for the user's resume:")
#                 if file_upload:
#                     with st.spinner("Uploading file..."):
#                         response = upload_resume(file_upload, user_id_input)
#                     st.session_state["messages"].append(
#                         {"role": "assistant", "content": "Resume uploaded successfully!"}
#                     )
#                     st.session_state["awaiting_file_upload"] = False
#                     st.experimental_rerun()
#             elif st.session_state["awaiting_update_option"]:
#                 st.session_state["awaiting_update_option"] = True
#                 st.experimental_rerun()

#     # Handle "Update Profile" options
#     elif st.session_state["awaiting_update_option"]:
#         st.markdown("What would you like to update?")
#         if st.button("Skills"):
#             st.session_state["selected_update_option"] = "skills"
#         elif st.button("Certifications"):
#             st.session_state["selected_update_option"] = "certifications"
#         elif st.button("Projects"):
#             st.session_state["selected_update_option"] = "projects"

#         if st.session_state["selected_update_option"]:
#             st.session_state["awaiting_update_option"] = False
#             st.experimental_rerun()

#     # Handle the selected update option
#     elif st.session_state["selected_update_option"] == "skills":
#         skill_name = st.text_input("Skill Name")
#         skill_level = st.selectbox("Skill Level", ["Beginner", "Intermediate", "Advanced"])
#         submit_skills = st.button("Submit Skills")
#         if submit_skills:
#             response = update_skills(
#                 st.session_state["target_user_id"], {"skill_name": skill_name, "skill_level": skill_level}
#             )
#             st.session_state["messages"].append({"role": "assistant", "content": "Skills updated successfully!"})
#             st.session_state["selected_update_option"] = None
#             st.experimental_rerun()

#     elif st.session_state["selected_update_option"] == "certifications":
#         cert_name = st.text_input("Certification Name")
#         cert_date = st.date_input("Certification Date")
#         cert_entity = st.text_input("Issuing Entity")
#         submit_cert = st.button("Submit Certification")
#         if submit_cert:
#             response = update_certifications(
#                 st.session_state["target_user_id"],
#                 {"cert_name": cert_name, "cert_date": cert_date, "cert_entity": cert_entity},
#             )
#             st.session_state["messages"].append(
#                 {"role": "assistant", "content": "Certification updated successfully!"}
#             )
#             st.session_state["selected_update_option"] = None
#             st.experimental_rerun()

#     elif st.session_state["selected_update_option"] == "projects":
#         project_name = st.text_input("Project Name")
#         project_description = st.text_area("Project Description")
#         submit_project = st.button("Submit Project")
#         if submit_project:
#             response = update_projects(
#                 st.session_state["target_user_id"],
#                 {"project_name": project_name, "project_description": project_description},
#             )
#             st.session_state["messages"].append({"role": "assistant", "content": "Project updated successfully!"})
#             st.session_state["selected_update_option"] = None
#             st.experimental_rerun()

#     # General user input handler
#     else:
#         user_input = st.chat_input("Ask a question or type 'update profile' or 'upload resume'...")
#         if user_input:
#             st.session_state["messages"].append({"role": "user", "content": user_input})
#             with st.spinner("Processing your query..."):
#                 response = send_message(role, user_input)
#                 if "error" in response:
#                     st.session_state["messages"].append({"role": "assistant", "content": response["error"]})
#                 else:
#                     message_status = response.get("message", "No status available.")
#                     content = response.get("content", "No profiles available.")
#                     formatted_content = format_download_links(content)
#                     response_message = f"*{message_status}*\n\n{formatted_content}"
#                     st.session_state["messages"].append({"role": "assistant", "content": response_message})
#             st.rerun()



            


def render_collapsible_text(text, max_length=150):
    """
    Renders collapsible text with 'Read More' functionality.
    """
    if len(text) <= max_length:
        return text
    else:
        truncated_text = text[:max_length] + "..."
        return (
            f"<span>{truncated_text}</span> "
            f"<button onclick='this.previousElementSibling.style.display=\"none\"; "
            f"this.nextElementSibling.style.display=\"inline\";'>Read More</button>"
            f"<span style='display: none;'>{text} "
            f"<button onclick='this.parentElement.style.display=\"none\"; "
            f"this.parentElement.previousElementSibling.style.display=\"inline\";'>Read Less</button></span>"
        )

# Example CSS
st.markdown(
    """
    <style>
    button {
        background: none!important;
        border: none;
        padding: 0!important;
        color: blue !important;
        text-decoration: underline;
        cursor: pointer;
    }
    button:hover {
        text-decoration: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def update_skills(user_id, skill_name, skill_level):
    url = f"{BASE_URL}/skills/update-skills/"
    payload = {"user_id": user_id, "skill_name": skill_name, "skill_level": skill_level}
    return make_api_request(url, payload)

# Helper function for updating certifications
def update_certifications(user_id, cert_name, cert_date, cert_issuer):
    url = f"{BASE_URL}/certifications/update-certifications/"
    payload = {"user_id": user_id, "cert_name": cert_name, "cert_date": str(cert_date), "cert_issuer": cert_issuer}
    return make_api_request(url, payload)

# Helper function for updating projects
def update_projects(user_id, project_name, project_description):
    url = f"{BASE_URL}/projects/update-projects/"
    payload = {"user_id": user_id, "project_name": project_name, "project_description": project_description}
    return make_api_request(url, payload)

# Generic API request function
def make_api_request(url, payload):
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API Error: {response.status_code}, {response.text}"}
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}



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

if _name_ == "_main_":
    main()