import json
import streamlit as st
from cryptography.fernet import Fernet

DATA_FILE = "data.json"

# --- Load Fernet key from Streamlit secrets ---
KEY = st.secrets["encryption"]["fernet_key"].encode()
fernet = Fernet(KEY)

# --- Encryption helpers ---
def encrypt_data(data: dict) -> bytes:
    """Encrypt a Python dict and return bytes"""
    return fernet.encrypt(json.dumps(data).encode())

def decrypt_data(encrypted_data: bytes) -> dict:
    """Decrypt bytes and return Python dict"""
    return json.loads(fernet.decrypt(encrypted_data))

# --- User management ---
def load_all_users() -> dict:
    """Load all users from encrypted data file"""
    try:
        with open(DATA_FILE, "rb") as f:
            encrypted = f.read()
        return decrypt_data(encrypted)
    except FileNotFoundError:
        return {}
    except:
        st.error("Could not decrypt user data. Wrong key or corrupted file.")
        return {}

def save_all_users(users: dict):
    """Save all users to encrypted data file"""
    encrypted = encrypt_data(users)
    with open(DATA_FILE, "wb") as f:
        f.write(encrypted)

def register_user(username: str, password: str) -> bool:
    users = load_all_users()
    if username in users:
        return False
    users[username] = {
        "password": password,
        "notes": [],
        "flashcards": [],
        "study_sessions": []
    }
    save_all_users(users)
    return True

def login_user(username: str, password: str) -> bool:
    users = load_all_users()
    if username in users and users[username]["password"] == password:
        st.session_state.username = username
        st.session_state.logged_in = True
        # Load user data into session
        st.session_state.notes = users[username]["notes"]
        st.session_state.flashcards = users[username]["flashcards"]
        st.session_state.study_sessions = users[username]["study_sessions"]
        return True
    return False

def save_user_data():
    """Save current user's session data back to encrypted file"""
    if not st.session_state.get("logged_in", False):
        return
    users = load_all_users()
    username = st.session_state.username
    users[username] = {
        "password": users[username]["password"],
        "notes": st.session_state.get("notes", []),
        "flashcards": st.session_state.get("flashcards", []),
        "study_sessions": st.session_state.get("study_sessions", [])
    }
    save_all_users(users)
