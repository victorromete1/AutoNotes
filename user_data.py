# Author: Victor
# Page name: user_data.py
# Page purpose: User data management for app.py
# Date of creation: 2025-10-10
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

# Core functions
def _now_iso() -> str:
    """Get current UTC timestamp"""
    return datetime.utcnow().isoformat()
# Password hasher
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()
# convert username to lowercase
def normalize_username(username: str) -> str:
    return username.strip().lower()

def admin_delete_account(target_username: str) -> Tuple[bool, str]:
    normalized = normalize_username(target_username)
    try:
        # Check if user exists
        user_check = supabase.table("users").select("username").eq("username", normalized).execute()
        if not user_check.data:
            return False, "User does not exist"

        # Delete all user data first
        tables = ["notes", "flashcards", "study_sessions", "events"]
        for table in tables:
            supabase.table(table).delete().eq("username", normalized).execute()

        # Delete the user
        supabase.table("users").delete().eq("username", normalized).execute()

        return True, "User account and data deleted successfully"
    except Exception as e:
        return False, f"Deletion failed: {str(e)}"

# Authentication functions
def register_user(username: str, password: str) -> Tuple[bool, str]:
    """Register new user (auto-lowercase)"""
    normalized = normalize_username(username)
    if not normalized or not password:
        return False, "Username and password required"
    
    try:
        # Check for existing username
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

def admin_reset_password(target_username: str, new_password: str) -> Tuple[bool, str]:
    normalized = normalize_username(target_username)
    try:
        # Check if user exists first
        user_check = supabase.table("users").select("username").eq("username", normalized).execute()
        if not user_check.data:
            return False, "User does not exist"

        # Proceed to update password
        supabase.table("users").update({"password": hash_password(new_password)}).eq("username", normalized).execute()
        return True, "Password updated successfully"
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

# Data handling functions
def save_current_user(session_state: dict) -> Tuple[bool, str]:
    if not session_state.get("logged_in"):
        return False, "Not logged in"
    
    normalized = normalize_username(session_state["username"])
    
    try:
        # NOTES
        supabase.table("notes").delete().eq("username", normalized).execute()
        notes_to_insert = []
        for n in session_state.get("notes", []):
            notes_to_insert.append({
                "username": normalized,
                "title": n.get("title"),
                "content": n.get("content"),
                "category": n.get("category", "General"),
                "created_at": n.get("timestamp") or _now_iso(),
                "updated_at": n.get("timestamp") or _now_iso()
            })
        if notes_to_insert:
            supabase.table("notes").insert(notes_to_insert).execute()

        # FLASHCARDS
        supabase.table("flashcards").delete().eq("username", normalized).execute()
        fcs = []
        for c in session_state.get("flashcards", []):
            fcs.append({
                "username": normalized,
                "front": c.get("front"),
                "back": c.get("back"),
                "category": c.get("category", "General"),
                "created_at": c.get("created") or _now_iso()
            })
        if fcs:
            supabase.table("flashcards").insert(fcs).execute()

        # STUDY SESSIONS
        supabase.table("study_sessions").delete().eq("username", normalized).execute()
        ss = []
        for s in session_state.get("study_sessions", []):
            ss.append({
                "username": normalized,
                "timestamp": s.get("timestamp") or _now_iso(),
                "activity_type": s.get("activity_type"),
                "data": s
            })
        if ss:
            supabase.table("study_sessions").insert(ss).execute()

        # EVENTS
        supabase.table("events").delete().eq("username", normalized).execute()
        events = []
        for e in session_state.get("events", []):
            events.append({
                "username": normalized,
                "name": e.get("name"),      
                "date": e.get("date"),     
                "notes": e.get("notes"),
                "color": e.get("color"),
                "created_at": e.get("created") or _now_iso()
            })
        if events:
            supabase.table("events").insert(events).execute()

        return True, "Data saved successfully"
    except Exception as e:
        return False, f"Save error: {str(e)}"

def change_password(username, new_password):
    """Changes the password for a given user."""
    try:
        # Hash the new password for secure storage
        hashed_password = hash_password(new_password)
        
        # Update the user's record in the 'users' table
        supabase.table("users").update({
            "password": hashed_password
        }).eq("username", username.lower()).execute()
        
        return True, "Password updated successfully."
    except Exception as e:
        # Return the error message if the update fails
        return False, str(e)

def delete_account(username):
    """Deletes a user's account and all their data."""
    try:
        # Delete the user's row from the 'users' table
        supabase.from_("users").delete().eq("username", username.lower()).execute()
        
        return True, "Account deleted successfully."
    except Exception as e:
        # Return the error message if the deletion fails
        return False, str(e)



def load_user_data(username: str, merge_local: bool = False, 
                 local_state: Optional[dict] = None) -> Tuple[bool, dict]:
    """Load user data with case-insensitive lookup"""
    normalized = normalize_username(username)
    try:
        # NOTES
        r = supabase.table("notes").select("*").eq("username", normalized).execute()
        notes = []
        if r.data:
            for row in r.data:
                notes.append({
                    "title": row.get("title"),
                    "content": row.get("content"),
                    "category": row.get("category"),
                    "timestamp": row.get("created_at")
                })

        # FLASHCARDS
        r = supabase.table("flashcards").select("*").eq("username", normalized).execute()
        flashcards = []
        if r.data:
            for row in r.data:
                flashcards.append({
                    "front": row.get("front"),
                    "back": row.get("back"),
                    "category": row.get("category"),
                    "created": row.get("created_at")
                })

        # STUDY SESSIONS
        r = supabase.table("study_sessions").select("*").eq("username", normalized).execute()
        study_sessions = []
        if r.data:
            for row in r.data:
                study_sessions.append(row.get("data") or {"timestamp": row.get("timestamp"), "activity_type": row.get("activity_type")})

        # EVENTS
        r = supabase.table("events").select("*").eq("username", normalized).execute()
        events = []
        if r.data:
            for row in r.data:
                events.append({
                    "name": row.get("name"),      # Check if your app uses 'name' or 'title'
                    "date": row.get("date"),       # Check if your app uses 'date' or 'start'/'end'
                    "notes": row.get("notes"),
                    "color": row.get("color"),
                    "created": row.get("created_at")
                })

        payload = {
            "notes": notes,
            "flashcards": flashcards,
            "study_sessions": study_sessions,
            "events": events  
        }

        if merge_local and local_state:
            merged = {
                "notes": local_state.get("notes", []) + payload["notes"],
                "flashcards": local_state.get("flashcards", []) + payload["flashcards"],
                "study_sessions": local_state.get("study_sessions", []) + payload["study_sessions"],
                "events": local_state.get("events", []) + payload["events"] # <-- NOW MERGES EVENTS!
            }
            return True, merged
            
        return True, payload
    except Exception as e:
        return False, {"error": str(e)}
def export_user_data(username: str) -> Tuple[bool, str, dict]:
    """Export all user data as JSON"""
    normalized = normalize_username(username)
    try:
        # Get all user data
        user_data = {}
        
        # NOTES
        r = supabase.table("notes").select("*").eq("username", normalized).execute()
        user_data["notes"] = r.data if r.data else []
        
        # FLASHCARDS
        r = supabase.table("flashcards").select("*").eq("username", normalized).execute()
        user_data["flashcards"] = r.data if r.data else []
        
        # STUDY SESSIONS
        r = supabase.table("study_sessions").select("*").eq("username", normalized).execute()
        user_data["study_sessions"] = r.data if r.data else []
        
        # EVENTS
        r = supabase.table("events").select("*").eq("username", normalized).execute()
        user_data["events"] = r.data if r.data else []
        
        # USER INFO
        r = supabase.table("users").select("username, created_at").eq("username", normalized).execute()
        user_data["user_info"] = r.data[0] if r.data else {}
        
        # Add export metadata
        user_data["export_metadata"] = {
            "exported_at": _now_iso(),
            "username": normalized,
            "data_types": ["notes", "flashcards", "study_sessions", "events", "user_info"],
            "total_items": len(user_data["notes"]) + len(user_data["flashcards"]) + 
                          len(user_data["study_sessions"]) + len(user_data["events"])
        }
        
        return True, "Export successful", user_data
        
    except Exception as e:
        return False, f"Export failed: {str(e)}", {}
