# user_data.py - Complete Case-Insensitive Solution (No DB Changes)
import hashlib
from datetime import datetime
from typing import Tuple, Optional, Dict, List
import streamlit as st
from supabase import create_client

# Initialize Supabase
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---- Core Functions ----
def hash_password(password: str) -> str:
    """SHA-256 hashing for passwords"""
    return hashlib.sha256(password.encode()).hexdigest()

def _find_user_by_username(username: str) -> Optional[Dict]:
    """Case-insensitive user lookup (helper function)"""
    users = supabase.table("users").select("*").execute().data
    return next((u for u in users if u["username"].lower() == username.lower()), None)

# ---- Authentication ----
def register_user(username: str, password: str) -> Tuple[bool, str]:
    """Register with original casing but case-insensitive checks"""
    if len(username) < 4:
        return False, "Username must be 4+ characters"
    
    existing_user = _find_user_by_username(username)
    if existing_user:
        return False, f"Username '{existing_user['username']}' already exists (case-insensitive)"
    
    try:
        supabase.table("users").insert({
            "username": username,  # Store with original case
            "password": hash_password(password),
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        return True, "Registration successful!"
    except Exception as e:
        return False, f"Registration failed: {str(e)}"

def authenticate(username: str, password: str) -> Tuple[bool, str, Optional[str]]:
    """Login with any username casing, returns (success, message, actual_username)"""
    user = _find_user_by_username(username)
    if not user:
        return False, "User not found", None
    
    if user["password"] == hash_password(password):
        return True, "Login successful", user["username"]  # Return actual username casing
    return False, "Incorrect password", None

# ---- User Management ----
def update_password(username: str, new_password: str) -> Tuple[bool, str]:
    """Case-insensitive password update"""
    user = _find_user_by_username(username)
    if not user:
        return False, "User not found"
    
    try:
        supabase.table("users").update({"password": hash_password(new_password)}) \
             .eq("username", user["username"]).execute()
        return True, "Password updated"
    except Exception as e:
        return False, f"Update failed: {str(e)}"

def delete_user(username: str) -> Tuple[bool, str]:
    """Case-insensitive account deletion"""
    user = _find_user_by_username(username)
    if not user:
        return False, "User not found"
    
    try:
        # Delete all user data first
        supabase.table("user_data").delete().eq("username", user["username"]).execute()
        supabase.table("users").delete().eq("username", user["username"]).execute()
        return True, "Account deleted"
    except Exception as e:
        return False, f"Deletion failed: {str(e)}"

# ---- Data Handling ----
def save_user_data(username: str, data_type: str, data: List[Dict]) -> Tuple[bool, str]:
    """Save notes/flashcards/etc with case-insensitive lookup"""
    user = _find_user_by_username(username)
    if not user:
        return False, "User not found"
    
    try:
        # First clear existing data
        supabase.table(data_type).delete().eq("username", user["username"]).execute()
        
        # Insert new data with timestamp
        records = [{**item, "username": user["username"], 
                   "updated_at": datetime.utcnow().isoformat()} 
                  for item in data]
        
        supabase.table(data_type).insert(records).execute()
        return True, "Data saved successfully"
    except Exception as e:
        return False, f"Save error: {str(e)}"

def load_user_data(username: str, data_type: str) -> Tuple[bool, List[Dict]]:
    """Load user data with case-insensitive lookup"""
    user = _find_user_by_username(username)
    if not user:
        return False, []
    
    try:
        data = supabase.table(data_type) \
                     .select("*") \
                     .eq("username", user["username"]) \
                     .execute().data
        return True, data
    except Exception as e:
        return False, []

# ---- Admin Tools ----
def admin_get_all_users() -> List[Dict]:
    """Get all users (admin only)"""
    return supabase.table("users").select("username, created_at").execute().data

def admin_impersonate(username: str) -> Tuple[bool, str, Optional[Dict]]:
    """Admin login-as (returns actual user data)"""
    user = _find_user_by_username(username)
    if not user:
        return False, "User not found", None
    return True, "Impersonation successful", user
