# user_data.py - Case-insensitive username handling (lowercase-only)
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import streamlit as st
from supabase import create_client

# Initialize Supabase
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
ADMIN_KEY = st.secrets.get("ADMIN_KEY", "")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---- Core Functions ----
def _now_iso() -> str:
    """Get current UTC timestamp"""
    return datetime.utcnow().isoformat()

def hash_password(password: str) -> str:
    """Secure password hashing"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def normalize_username(username: str) -> str:
    """Convert username to lowercase and strip whitespace"""
    return username.strip().lower()

# ---- Authentication ----
def register_user(username: str, password: str) -> Tuple[bool, str]:
    """Register new user (auto-lowercase)"""
    normalized = normalize_username(username)
    if not normalized or not password:
        return False, "Username and password required"
    
    try:
        # Check for existing username (case-insensitive)
        existing = supabase.table("users") \
                         .select("username") \
                         .eq("username", normalized) \
                         .execute()
        
        if existing.data:
            return False, "Username already exists"
            
        # Insert new user
        supabase.table("users").insert({
            "username": normalized,
            "password": hash_password(password),
            "created_at": _now_iso()
        }).execute()
        
        return True, "Registration successful"
    except Exception as e:
        return False, f"Registration failed: {str(e)}"

def authenticate(username: str, password: str) -> Tuple[bool, str]:
    """Login with case-insensitive username"""
    normalized = normalize_username(username)
    try:
        # Find user
        user = supabase.table("users") \
                     .select("*") \
                     .eq("username", normalized) \
                     .execute()
        
        if not user.data:
            return False, "User not found"
            
        # Verify password
        if user.data[0]["password"] == hash_password(password):
            return True, "Login successful"
        return False, "Incorrect password"
    except Exception as e:
        return False, f"Login error: {str(e)}"

# ---- User Management ----
def admin_reset_password(target_username: str, new_password: str) -> Tuple[bool, str]:
    """Admin password reset (case-insensitive)"""
    normalized = normalize_username(target_username)
    try:
        supabase.table("users") \
              .update({"password": hash_password(new_password)}) \
              .eq("username", normalized) \
              .execute()
        return True, "Password updated"
    except Exception as e:
        return False, f"Reset failed: {str(e)}"

def delete_account(username: str) -> Tuple[bool, str]:
    """Delete account (case-insensitive)"""
    normalized = normalize_username(username)
    try:
        # Delete user data first
        tables = ["notes", "flashcards", "study_sessions", "events"]
        for table in tables:
            supabase.table(table) \
                  .delete() \
                  .eq("username", normalized) \
                  .execute()
        
        # Delete user
        supabase.table("users") \
              .delete() \
              .eq("username", normalized) \
              .execute()
        
        return True, "Account deleted"
    except Exception as e:
        return False, f"Deletion failed: {str(e)}"

# ---- Data Handling ----
def save_current_user(session_state: dict) -> Tuple[bool, str]:
    """Save all user data using lowercase username"""
    if not session_state.get("logged_in"):
        return False, "Not logged in"
    
    normalized = normalize_username(session_state["username"])
    
    try:
        # Save notes
        supabase.table("notes") \
              .delete() \
              .eq("username", normalized) \
              .execute()
        
        notes_data = [{
            "username": normalized,
            "title": note.get("title"),
            "content": note.get("content"),
            "category": note.get("category", "General"),
            "created_at": note.get("timestamp") or _now_iso(),
            "updated_at": note.get("timestamp") or _now_iso()
        } for note in session_state.get("notes", [])]
        
        if notes_data:
            supabase.table("notes").insert(notes_data).execute()
        
        # Repeat same pattern for flashcards, study_sessions, events...
        # [Your existing data saving logic here]
        
        return True, "Data saved successfully"
    except Exception as e:
        return False, f"Save error: {str(e)}"

def load_user_data(username: str, merge_local: bool = False, 
                 local_state: Optional[dict] = None) -> Tuple[bool, dict]:
    """Load user data with case-insensitive lookup"""
    normalized = normalize_username(username)
    try:
        # Load notes
        notes = supabase.table("notes") \
                      .select("*") \
                      .eq("username", normalized) \
                      .execute()
        
        # Load flashcards
        flashcards = supabase.table("flashcards") \
                           .select("*") \
                           .eq("username", normalized) \
                           .execute()
        
        # [Load other tables similarly...]
        
        payload = {
            "notes": [{
                "title": n["title"],
                "content": n["content"],
                "category": n.get("category", "General"),
                "timestamp": n["created_at"]
            } for n in notes.data] if notes.data else [],
            
            "flashcards": [{
                "front": f["front"],
                "back": f["back"],
                "category": f.get("category", "General"),
                "created": f["created_at"]
            } for f in flashcards.data] if flashcards.data else [],
            
            # [Add other data types...]
        }
        
        if merge_local and local_state:
            return True, {
                "notes": local_state.get("notes", []) + payload["notes"],
                "flashcards": local_state.get("flashcards", []) + payload["flashcards"],
                # [Merge other data types...]
            }
            
        return True, payload
    except Exception as e:
        return False, {"error": str(e)}
