# THIS FILE IS NOT IN USE, JUST FOR DEBUGGING PURPOSES
import json
import streamlit as st
from datetime import datetime

class DataImportExport:
    def __init__(self, persistence):
        self.persistence = persistence

    def export_all_data(self):
        data = {
            'notes': st.session_state.get('notes', []),
            'flashcards': st.session_state.get('flashcards', []),
            'study_sessions': st.session_state.get('study_sessions', []),
            'export_date': datetime.now().isoformat(),
            'version': '2.0'
        }
        return json.dumps(data, indent=2)

    def import_all_data(self, uploaded_file):
        try:
            data = json.load(uploaded_file)
            if not isinstance(data, dict):
                st.error("Invalid data format")
                return False
            self.persistence.clear_all_data()
            if 'notes' in data and isinstance(data['notes'], list):
                st.session_state.notes = data['notes']
            if 'flashcards' in data and isinstance(data['flashcards'], list):
                st.session_state.flashcards = data['flashcards']
            if 'study_sessions' in data and isinstance(data['study_sessions'], list):
                st.session_state.study_sessions = data['study_sessions']
            st.success("Data imported successfully!")
            return True
        except json.JSONDecodeError:
            st.error("Invalid JSON file")
            return False
        except Exception as e:
            st.error(f"Error importing data: {str(e)}")
            return False

    def render_sidebar_controls(self):
        with st.sidebar:
            st.divider()
            st.subheader("🔁 Data Transfer")
            export_data = self.export_all_data()
            st.download_button(
                label="📤 Export All Data",
                data=export_data,
                file_name=f"study_platform_backup_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                help="Download all your notes, flashcards, and quiz history"
            )
            uploaded_file = st.file_uploader(
                "📥 Import Data",
                type=['json'],
                accept_multiple_files=False,
                help="Upload a previously exported JSON file to restore your data"
            )
            if uploaded_file:
                if st.button("⚠️ Confirm Import (Overwrites Current Data)"):
                    if self.import_all_data(uploaded_file):
                        st.rerun()
            st.divider()
            st.subheader("🛑 Danger Zone")
            if st.button("🗑️ Delete All Data"):
                st.session_state.confirm_delete_all = True
            if st.session_state.get("confirm_delete_all", False):
                st.warning("This will permanently delete **all notes, flashcards, and history**!")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("⚠️ Confirm Delete Everything"):
                        self.persistence.clear_all_data()
                        st.session_state.confirm_delete_all = False
                        st.success("✅ All data deleted!")
                        st.rerun()
                with col2:
                    if st.button("❌ Cancel"):
                        st.session_state.confirm_delete_all = False
