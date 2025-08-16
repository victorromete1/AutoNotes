import json
import base64
import streamlit as st
from github import Github
from cryptography.fernet import Fernet
from datetime import datetime

# --- Config ---
KEY = st.secrets["encryption"]["fernet_key"].encode()
fernet = Fernet(KEY)
GITHUB_TOKEN = st.secrets["github"]["token"]
GITHUB_REPO = st.secrets["github"]["repo"]  # Format: "username/repo"

def get_github_filepath(username: str) -> str:
    """Returns path like 'user_data/victor.json' in your GitHub repo"""
    return f"user_data/{username.lower()}.json"

def github_save_user_data(username: str, data: dict):
    """Saves encrypted user data to GitHub"""
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        file_path = get_github_filepath(username)
        
        # Encrypt and prepare data
        encrypted = fernet.encrypt(json.dumps(data).encode())
        content = base64.b64encode(encrypted).decode()
        
        # Check if file exists
        try:
            file = repo.get_contents(file_path)
            repo.update_file(
                path=file_path,
                message=f"Update user data for {username}",
                content=content,
                sha=file.sha
            )
        except:
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
    except Exception as e:
        st.error(f"GitHub load failed: {str(e)}")
        return None

# --- User Management ---
def register_user(username: str, password: str) -> bool:
    """Creates new user file in GitHub's user_data/ folder"""
    if github_load_user_data(username) is not None:
        return False  # User exists
    
    return github_save_user_data(username, {
        "password": fernet.encrypt(password.encode()).decode(),
        "notes": [],
        "flashcards": [],
        "study_sessions": [],
        "created_at": datetime.now().isoformat()
    })

def login_user(username: str, password: str) -> bool:
    """Authenticates and loads user data from GitHub"""
    user_data = github_load_user_data(username)
    if not user_data:
        return False
        
    try:
        # Verify password
        stored_pass = fernet.decrypt(user_data["password"].encode()).decode()
        if stored_pass != password:
            return False
            
        # Load into session
        st.session_state.update({
            "logged_in": True,
            "username": username,
            "notes": user_data.get("notes", []),
            "flashcards": user_data.get("flashcards", []),
            "study_sessions": user_data.get("study_sessions", [])
        })
        return True
    except:
        return False

def save_current_user():
    """Auto-saves session data to GitHub"""
    if not st.session_state.get("logged_in"):
        return
        
    github_save_user_data(st.session_state["username"], {
        "password": fernet.encrypt("dummy").decode(),  # Password not stored in session
        "notes": st.session_state.get("notes", []),
        "flashcards": st.session_state.get("flashcards", []),
        "study_sessions": st.session_state.get("study_sessions", []),
        "updated_at": datetime.now().isoformat()
    })
