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
BASE_URL = "https://fa7f-139-5-49-243.ngrok-free.app/v1"  # Replace with your FastAPI URL

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
    """Send a message to the backend and return the structured response."""
    url = f"{BASE_URL}/chat/send_message?message={query}"
    try:
        response = requests.post(url)
        if response.status_code == 200:
            data = response.json()
            content = data.get("content", "")
            if not content:
                return {"summary": "No summary available.", "detailed_analysis": "No detailed analysis available."}
            return parse_backend_response(content)
        else:
            return {"summary": "Error contacting backend.", "detailed_analysis": "No detailed analysis available."}
    except Exception as e:
        return {"summary": f"Error: {str(e)}", "detailed_analysis": "No detailed analysis available."}


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
    
def hr_chat_page():
    st.title("🚀 Profile Query Bot for HR")

    st.markdown(
        """
        <style>
        .message-bubble {
            margin: 10px 0;
            padding: 10px 15px;
            border-radius: 10px;
            max-width: 70%;
            font-size: 16px;
            line-height: 1.5;
        }
        .message-bubble.user {
            background-color: #DCF8C6;
            margin-left: auto;
            text-align: right;
        }
        .message-bubble.assistant {
            background-color: #FFF;
            margin-right: auto;
            text-align: left;
            border: 1px solid #DDD;
        }
        .timestamp {
            font-size: 12px;
            color: gray;
            margin-top: 5px;
        }
        .chat-container {
            max-height: 500px;
            overflow-y: auto;
            padding: 10px;
            background-color: #F5F5F5;
            border: 1px solid #DDD;
            border-radius: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Add custom styles for the chat bubbles
    

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

    # Display chat messages in a styled manner
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for message in st.session_state["messages"]:
        role_class = "user" if message["role"] == "user" else "assistant"
        st.markdown(
            f"""
            <div class="message-bubble {role_class}">
                <div>{message['content']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    # Check if awaiting user ID for profile update or resume upload
    if st.session_state["awaiting_user_id"]:
        user_id_input = st.chat_input("Please enter the user ID for the profile update or resume upload:")
        if user_id_input:
            st.session_state["target_user_id"] = user_id_input
            st.session_state["awaiting_user_id"] = False  # Stop waiting for user_id
            if st.session_state["awaiting_file_upload"]:
                file_upload = st.file_uploader("Please upload the PDF file for the profile update:", type="pdf")
                if file_upload:
                    with st.spinner("Uploading file..."):
                        response = upload_resume(file_upload, st.session_state["target_user_id"])
                        st.session_state["messages"].append({"role": "assistant", "content": response})
                    st.session_state["target_user_id"] = None
                    st.session_state["awaiting_file_upload"] = False
            else:
                st.session_state["awaiting_update_option"] = True
            st.session_state["messages"].append({"role": "user", "content": user_id_input})
            with st.chat_message("user"):
                st.markdown(user_id_input)

    elif st.session_state["awaiting_update_option"]:
        st.markdown("Select the details you want to update:")
        if st.button("Skills details"):
            st.session_state["selected_update_option"] = "skills"
        elif st.button("Certificate details"):
            st.session_state["selected_update_option"] = "certificate"
        elif st.button("Project details"):
            st.session_state["selected_update_option"] = "project"

        if st.session_state["selected_update_option"]:
            st.session_state["awaiting_update_option"] = False

    elif st.session_state["selected_update_option"] == "skills":
        skill_name = st.text_input("Skill Name")
        skill_level = st.selectbox("Skill Level", ["Beginner", "Intermediate", "Advanced"])
        submit_skills = st.button("Submit Skills")
        if submit_skills:
            response = update_skills("skills", st.session_state["target_user_id"], {
                "skill_name": skill_name,
                "skill_level": skill_level
            })
            st.session_state["messages"].append({"role": "assistant", "content": "Skills updated successfully."})
            st.session_state["selected_update_option"] = None

    elif st.session_state["selected_update_option"] == "certificate":
        cert_name = st.text_input("Certification Name")
        cert_date = st.date_input("Certification Date")
        cert_entity = st.text_input("Issuing Entity")
        submit_certificate = st.button("Submit Certificate")
        if submit_certificate:
            response = update_certifications("certificate", st.session_state["target_user_id"], {
                "cert_name": cert_name,
                "cert_date": cert_date,
                "cert_entity": cert_entity
            })
            st.session_state["messages"].append({"role": "assistant", "content": "Certificate updated successfully."})
            st.session_state["selected_update_option"] = None

    elif st.session_state["selected_update_option"] == "project":
        project_name = st.text_input("Project Name")
        project_description = st.text_area("Project Description")
        submit_project = st.button("Submit Project")
        if submit_project:
            response = update_projects("project", st.session_state["target_user_id"], {
                "project_name": project_name,
                "project_description": project_description
            })
            st.session_state["messages"].append({"role": "assistant", "content": "Project updated successfully."})
            st.session_state["selected_update_option"] = None

    else:
        user_input = st.chat_input("Ask a question or type 'update profile' or 'upload resume'...")
        if user_input:
            st.session_state["messages"].append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            if "update profile" in user_input.lower():
                bot_message = "Please provide the user ID for the profile you want to update."
                st.session_state["messages"].append({"role": "assistant", "content": bot_message})
                with st.chat_message("assistant"):
                    st.markdown(bot_message)
                st.session_state["awaiting_user_id"] = True

            elif "upload resume" in user_input.lower():
                bot_message = "Please provide the user ID for the resume you want to upload."
                st.session_state["messages"].append({"role": "assistant", "content": bot_message})
                with st.chat_message("assistant"):
                    st.markdown(bot_message)
                st.session_state["awaiting_user_id"] = True
                st.session_state["awaiting_file_upload"] = True
            else:
                with st.spinner("Processing your query..."):
                    response = send_message(user_input)

                # Display Summary
                    st.markdown("### Summary:")
                    summary = response.get("summary", "No summary available.")
                    st.markdown(summary)

                    # Display Detailed Analysis
                    st.markdown("### Detailed Analysis:")
                    detailed_analysis = response.get("detailed_analysis", "No detailed analysis available.")
                    if isinstance(detailed_analysis, list):
                        for profile in detailed_analysis:
                            st.markdown(f"**Profile ID:** {profile['profile_id']}")
                            st.markdown(f"**Candidate Name:** {profile['candidate_name']}")
                            st.markdown(profile["details"])
                            st.markdown(f"[Download Resume]({profile['resume_url']})")
                            st.markdown("---")
                    else:
                        st.markdown(detailed_analysis)


def parse_backend_response(content):
    """Parse the backend response to extract the summary and detailed analysis."""
    # Extract Summary
    summary_match = re.search(r"\*\*Summary:\*\*(.+?)\n\n", content, re.DOTALL)
    summary = summary_match.group(1).strip() if summary_match else "No summary available."

    # Extract Detailed Analysis
    detailed_analysis_section = re.split(r"\*\*Detailed analysis:\*\*", content, maxsplit=1)
    if len(detailed_analysis_section) > 1:
        detailed_analysis_content = detailed_analysis_section[1].strip()
        profiles = re.findall(r"\* Profile: ([\w\.]+) \((.*?)\)(.+?)(?=\* Profile:|\Z)", detailed_analysis_content, re.DOTALL)
        detailed_analysis = []
        for profile_id, candidate_name, details in profiles:
            resume_url = f"{BASE_URL}/user/download_resume/{profile_id.strip('.pdf')}"
            detailed_analysis.append({
                "profile_id": profile_id,
                "candidate_name": candidate_name.strip(),
                "details": details.strip(),
                "resume_url": resume_url,
            })
    else:
        detailed_analysis = "No detailed analysis available."

    return {"summary": summary, "detailed_analysis": detailed_analysis}

def update_skills(user_id, skill_name, skill_level):
    url = f"{BASE_URL}/v1/skills/update-skills/"
    payload = {"user_id": user_id, "skill_name": skill_name, "skill_level": skill_level}
    return make_api_request(url, payload)

# Helper function for updating certifications
def update_certifications(user_id, cert_name, cert_date, cert_issuer):
    url = f"{BASE_URL}/v1/certifications/update-certifications/"
    payload = {"user_id": user_id, "cert_name": cert_name, "cert_date": str(cert_date), "cert_issuer": cert_issuer}
    return make_api_request(url, payload)

# Helper function for updating projects
def update_projects(user_id, project_name, project_description):
    url = f"{BASE_URL}/v1/projects/update-projects/"
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

if __name__ == "__main__":
    main()
