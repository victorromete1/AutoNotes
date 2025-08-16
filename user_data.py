import json
import base64
import streamlit as st
from github import Github
from github.GithubException import UnknownObjectException
from cryptography.fernet import Fernet, InvalidToken
from datetime import datetime

KEY = st.secrets["encryption"]["fernet_key"].encode()
fernet = Fernet(KEY)
GITHUB_TOKEN = st.secrets["github"]["token"]
GITHUB_REPO = st.secrets["github"]["repo"]  # "username/repo"

def get_github_filepath(username: str) -> str:
    return f"userdata/{username.lower()}.json"

def github_load_user_data(username: str) -> dict | None:
    """Loads and decrypts user data from GitHub with clear diagnostics."""
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        file_path = get_github_filepath(username)
        st.write(f"Looking for file in repo: {GITHUB_REPO}/{file_path}")  # DEBUG

        file = repo.get_contents(file_path)  # raises UnknownObjectException if not found
        try:
            encrypted = base64.b64decode(file.content)
        except Exception as e:
            st.error(f"Base64 decode failed: {e}")
            return None

        try:
            decrypted = fernet.decrypt(encrypted)  # raises InvalidToken on key mismatch
        except InvalidToken:
            st.error("Decryption failed: Fernet key does not match the one used to encrypt this file.")
            return None

        try:
            return json.loads(decrypted.decode())
        except Exception as e:
            st.error(f"JSON parse failed after decryption: {e}")
            return None

    except UnknownObjectException:
        st.error("User account not found. Please register first.")
        return None
    except Exception as e:
        st.error(f"GitHub load failed: {e}")
        return None

def github_save_user_data(username: str, data: dict) -> bool:
    """Encrypt and save (create or update) per-user JSON."""
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        file_path = get_github_filepath(username)

        encrypted = fernet.encrypt(json.dumps(data).encode())
        content = base64.b64encode(encrypted).decode()

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
        st.error(f"GitHub save failed: {e}")
        return False

def register_user(username: str, password: str) -> bool:
    username = username.lower()  # normalize so 'Victo' == 'victo'
    if not username or not password:
        st.error("Username and password cannot be empty")
        return False
    if github_load_user_data(username) is not None:
        st.error("Username already exists")
        return False

    data = {
        "password": password,     # stored inside encrypted JSON; not double-encrypted
        "notes": [],
        "flashcards": [],
        "study_sessions": [],
        "created_at": datetime.now().isoformat()
    }
    if github_save_user_data(username, data):
        st.success(f"Account '{username}' created successfully!")
        return True
    st.error("Failed to create account")
    return False

def login_user(username: str, password: str) -> bool:
    username = username.lower()
    user_data = github_load_user_data(username)
    if not user_data:
        return False
    if user_data.get("password") != password:
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
