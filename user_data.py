import json
import base64
import streamlit as st
from github import Github
from github.GithubException import UnknownObjectException
from cryptography.fernet import Fernet
from datetime import datetime

# --- Config ---
KEY = st.secrets["encryption"]["fernet_key"].encode()
fernet = Fernet(KEY)
GITHUB_TOKEN = st.secrets["github"]["token"]
GITHUB_REPO = st.secrets["github"]["repo"]  # Format: "username/repo"

def get_github_filepath(username: str) -> str:
    """Return path like 'userdata/victor.json'"""
    return f"userdata/{username.lower()}.json"

# --- GitHub Storage ---
def github_save_user_data(username: str, data: dict) -> bool:
    """Encrypts and saves user data to GitHub"""
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        file_path = get_github_filepath(username)

        # Encrypt dict
        encrypted = fernet.encrypt(json.dumps(data).encode())
        content = base64.b64encode(encrypted).decode()

        # Save or update file
        try:
            file = repo.get_contents(file_path)
            repo.update_file(
                path=file_path,
                message=f"Update user data for {username}",
                content=content,
                sha=file.sha
            )
        except UnknownObjectException:
            repo.create_file(
                path=file_path,
                message=f"Create user data for {username}",
                content=content
            )
        return True
    except Exception as e:
        st.error(f"GitHub save failed: {str(e)}")
        return False

def github_load_user_data(username: str) -> dict:
    """Loads and decrypts user data from GitHub"""
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        file_path = get_github_filepath(username)

        file = repo.get_contents(file_path)
        encrypted = base64.b64decode(file.content)
        return json.loads(fernet.decrypt(encrypted).decode())
    except UnknownObjectException:
        return None
    except Exception as e:
        st.error(f"GitHub load failed: {str(e)}")
        return None

# --- User Management ---
def register_user(username: str, password: str) -> bool:
    """Create new user file in userdata/"""
    if not username or not password:
        st.error("Username and password cannot be empty")
        return False

    if github_load_user_data(username) is not None:
        st.error("Username already exists")
        return False

    user_data = {
        "password": password,   # plain here, whole file encrypted later
        "notes": [],
        "flashcards": [],
        "study_sessions": [],
        "created_at": datetime.now().isoformat()
    }

    if github_save_user_data(username, user_data):
        st.success(f"Account '{username}' created successfully!")
        return True
    else:
        st.error("Failed to create account")
        return False

def login_user(username: str, password: str) -> bool:
    """Authenticate user"""
    user_data = github_load_user_data(username)
    if not user_data:
        st.error("User not found")
        return False

    if user_data["password"] != password:
        st.error("Incorrect password")
        return False

    st.session_state.update({
        "logged_in": True,
        "username": username,
        "notes": user_data.get("notes", []),
        "flashcards": user_data.get("flashcards", []),
        "study_sessions": user_data.get("study_sessions", [])
    })
    return True

def save_current_user():
    """Auto-save session to GitHub"""
    if not st.session_state.get("logged_in"):
        return

    user_data = github_load_user_data(st.session_state["username"])
    if not user_data:
        st.error("Failed to load user data for saving")
        return

    updated_data = {
        "password": user_data["password"],
        "notes": st.session_state.get("notes", []),
        "flashcards": st.session_state.get("flashcards", []),
        "study_sessions": st.session_state.get("study_sessions", []),
        "updated_at": datetime.now().isoformat()
    }

    github_save_user_data(st.session_state["username"], updated_data)

def logout_user():
    """Save & clear session"""
    if st.session_state.get("logged_in"):
        save_current_user()
        st.session_state.update({
            "logged_in": False,
            "username": "",
            "notes": [],
            "flashcards": [],
            "study_sessions": []
        })
