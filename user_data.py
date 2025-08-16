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
```# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "notes" not in st.session_state:
    st.session_state.notes = []
if "flashcards" not in st.session_state:
    st.session_state.flashcards = []
if "study_sessions" not in st.session_state:
    st.session_state.study_sessions = []

# Auto-save for logged-in users
if st.session_state.get("logged_in"):
    save_current_user()  # Now pushes to GitHub automatically

# --- Home Page ---
# --- Home Page / User Account Section ---
if st.session_state.page == "🏠 Home":
    st.title("🎓 Welcome!")

    st.markdown("""
    Unlock your full learning potential with an intelligent, all-in-one study platform powered by AI.  
    Whether you're preparing for exams, mastering a subject, or building long-term knowledge, this tool adapts to the way **you** learn best.  
    """)

    # --- Login/Register Section ---
    st.markdown("---")
    st.subheader("🔐 User Account (Optional)")
    st.info("You **do not need to log in** to use this app, but logging in allows your notes, flashcards, and quizzes to be saved across devices.")

    if not st.session_state.logged_in:
        login_tab, register_tab = st.tabs(["Login", "Register"])

        # --- Login Tab ---
        with login_tab:
            with st.form("login_form"):
                st.subheader("Login")
                username = st.text_input("Username", key="login_user")
                password = st.text_input("Password", type="password", key="login_pass")
                if st.form_submit_button("Login"):
                    success = login_user(username, password)
                    if success:
                        st.success(f"Welcome back, {username}!")
                        st.rerun()
                    else:
                        st.error(
                            "Login failed. Possible causes:\n"
                            "- Incorrect username or password\n"
                            "- Fernet key mismatch with saved account\n"
                            "- User file missing in GitHub repo"
                        )

        # --- Register Tab ---
        with register_tab:
            with st.form("register_form"):
                st.subheader("Register")
                new_user = st.text_input("Choose Username", key="reg_user")
                new_pass = st.text_input("Choose Password", type="password", key="reg_pass")
                confirm_pass = st.text_input("Confirm Password", type="password", key="reg_pass_confirm")

                if st.form_submit_button("Register"):
                    if new_pass != confirm_pass:
                        st.error("Passwords don't match!")
                    else:
                        success = register_user(new_user, new_pass)
                        if success:
                            st.success("Account created! Please log in.")
                            st.rerun()
                        else:
                            st.error(
                                "Registration failed. Possible causes:\n"
                                "- Username already exists\n"
                                "- GitHub save failed\n"
                                "- Fernet key issue"
                            )
    else:
        # --- Logged-in view ---
        st.success(f"Logged in as {st.session_state.username}")
        if st.button("Logout"):
            logout_user()  # Saves session to GitHub + clears session
            st.rerun()

    st.markdown("---")

    # --- Features Section ---
    st.markdown("""
    ### 🚀 Key Features:
    - **📝 Smart Notes**: Instantly generate clear, structured notes from any topic  
    - **🎴 Flashcards**: Create interactive flashcards to reinforce your memory  
    - **❓ Adaptive Quizzes**: Test your knowledge with personalized, AI-driven quizzes  
    - **📊 Progress Tracking**: Monitor your growth with detailed insights & analytics  
    - **📑 Reports**: Export beautifully formatted PDF reports of your learning journey  

    ### 💡 Quick Start Guide:
    1. **Create Notes** → Enter a topic you're studying and let AI generate study notes  
    2. **Build Flashcards** → Turn your notes into bite-sized flashcards for revision  
    3. **Test Yourself** → Take adaptive quizzes with instant feedback  
    4. **Track Progress** → Watch your performance improve over time  
    """)

    # --- Recent Activity ---
    if st.session_state.get("study_sessions"):
        st.subheader("📅 Recent Activity")
        recent_sessions = sorted(
            st.session_state.study_sessions, 
            key=lambda x: x.get('timestamp', ''), reverse=True
        )[:5]

        for session in recent_sessions:
            timestamp = datetime.fromisoformat(session['timestamp']).strftime("%Y-%m-%d %H:%M")
            activity = session.get('activity_type', 'Unknown')

            if activity == 'quiz':
                score = session.get('score', 0)
                st.write(f"🧠 {timestamp} - Quiz completed: {score:.1f}%")
            elif activity == 'flashcards':
                count = session.get('flashcards_studied', 0)
                st.write(f"📚 {timestamp} - Studied {count} flashcards")
            elif activity == 'flashcards_created':
                count = session.get('flashcards_created', 0)
                st.write(f"➕ {timestamp} - Created {count} flashcards")
```
