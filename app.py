import streamlit as st
import json
from datetime import datetime
from note_generator import NoteGenerator
from utils import export_notes_as_text, sanitize_filename

# Configure page
st.set_page_config(
    page_title="AI Study Notes Generator",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize note generator
@st.cache_resource
def get_note_generator():
    return NoteGenerator()

note_gen = get_note_generator()

# Initialize session state
if 'notes' not in st.session_state:
    st.session_state.notes = []

if 'current_note' not in st.session_state:
    st.session_state.current_note = ""

if 'note_title' not in st.session_state:
    st.session_state.note_title = ""

if 'note_category' not in st.session_state:
    st.session_state.note_category = "General"

# Main title
st.title("📝 AI Study Notes Generator")
st.markdown("Generate comprehensive study notes with the power of AI")

# Sidebar for note management
with st.sidebar:
    st.header("📚 Note Management")
    
    # Categories
    categories = list(set([note.get('category', 'General') for note in st.session_state.notes]))
    if not categories:
        categories = ['General']
    
    selected_category = st.selectbox(
        "Filter by Category",
        ["All"] + sorted(categories)
    )
    
    st.divider()
    
    # Display saved notes
    st.subheader("Saved Notes")
    
    # Filter notes by category
    filtered_notes = st.session_state.notes
    if selected_category != "All":
        filtered_notes = [note for note in st.session_state.notes if note.get('category', 'General') == selected_category]
    
    if filtered_notes:
        for i, note in enumerate(filtered_notes):
            with st.expander(f"{note['title'][:30]}..." if len(note['title']) > 30 else note['title']):
                st.write(f"**Category:** {note.get('category', 'General')}")
                st.write(f"**Created:** {note['timestamp']}")
                st.write(f"**Content:** {note['content'][:100]}..." if len(note['content']) > 100 else note['content'])
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Load", key=f"load_{i}"):
                        st.session_state.current_note = note['content']
                        st.session_state.note_title = note['title']
                        st.session_state.note_category = note.get('category', 'General')
                        st.rerun()
                
                with col2:
                    if st.button("Delete", key=f"delete_{i}"):
                        # Find the note in the original list and remove it
                        for j, original_note in enumerate(st.session_state.notes):
                            if (original_note['title'] == note['title'] and 
                                original_note['timestamp'] == note['timestamp']):
                                st.session_state.notes.pop(j)
                                break
                        st.rerun()
    else:
        st.info("No notes saved yet")
    
    st.divider()
    
    # Export all notes
    if st.session_state.notes:
        if st.button("📥 Export All Notes"):
            exported_content = export_notes_as_text(st.session_state.notes)
            st.download_button(
                label="Download Notes",
                data=exported_content,
                file_name=f"study_notes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.header("🤖 AI Note Generation")
    
    # Input methods
    input_method = st.radio(
        "Choose input method:",
        ["Topic/Subject", "Text Content", "Questions/Prompts"]
    )
    
    user_input = ""
    
    if input_method == "Topic/Subject":
        user_input = st.text_input(
            "Enter a topic or subject:",
            placeholder="e.g., Photosynthesis, World War II, Calculus derivatives..."
        )
        
        # Additional options for topic-based generation
        note_type = st.selectbox(
            "Note type:",
            ["Summary", "Detailed Explanation", "Key Points", "Study Guide", "Definitions"]
        )
        
        detail_level = st.select_slider(
            "Detail level:",
            options=["Basic", "Intermediate", "Advanced"]
        )
        
    elif input_method == "Text Content":
        user_input = st.text_area(
            "Paste text content to summarize:",
            placeholder="Paste your lecture notes, textbook content, or any text you want to summarize...",
            height=150
        )
        
        note_type = st.selectbox(
            "Processing type:",
            ["Summarize", "Extract Key Points", "Create Study Questions", "Organize Content"]
        )
        
    else:  # Questions/Prompts
        user_input = st.text_area(
            "Enter your questions or prompts:",
            placeholder="e.g., Explain the causes of climate change, What are the main themes in Romeo and Juliet?",
            height=100
        )
        note_type = "Answer Questions"
    
    # Generate button
    if st.button("🚀 Generate Notes", type="primary"):
        if user_input.strip():
            with st.spinner("Generating your notes... This may take a moment."):
                try:
                    generated_notes = note_gen.generate_notes(
                        user_input, 
                        note_type=note_type,
                        detail_level=detail_level if input_method == "Topic/Subject" else "Intermediate"
                    )
                    st.session_state.current_note = generated_notes
                    st.success("Notes generated successfully!")
                except Exception as e:
                    st.error(f"Error generating notes: {str(e)}")
                    st.info("Please check your OpenAI API key and try again.")
        else:
            st.warning("Please enter some content to generate notes from.")

with col2:
    st.header("✏️ Note Editor")
    
    # Note metadata
    col2_1, col2_2 = st.columns(2)
    
    with col2_1:
        st.session_state.note_title = st.text_input(
            "Note Title:",
            value=st.session_state.note_title,
            placeholder="Enter a title for your note..."
        )
    
    with col2_2:
        categories_list = ["General", "Math", "Science", "History", "Literature", "Languages", "Arts", "Other"]
        current_categories = list(set([note.get('category', 'General') for note in st.session_state.notes]))
        all_categories = sorted(list(set(categories_list + current_categories)))
        
        st.session_state.note_category = st.selectbox(
            "Category:",
            all_categories,
            index=all_categories.index(st.session_state.note_category) if st.session_state.note_category in all_categories else 0
        )
    
    # Note content editor
    st.session_state.current_note = st.text_area(
        "Edit your notes:",
        value=st.session_state.current_note,
        height=400,
        placeholder="Generated notes will appear here, or you can write your own notes manually..."
    )
    
    # Action buttons
    col2_a, col2_b, col2_c = st.columns(3)
    
    with col2_a:
        if st.button("💾 Save Note"):
            if st.session_state.current_note.strip() and st.session_state.note_title.strip():
                new_note = {
                    'title': st.session_state.note_title,
                    'content': st.session_state.current_note,
                    'category': st.session_state.note_category,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.session_state.notes.append(new_note)
                st.success("Note saved successfully!")
            else:
                st.warning("Please enter both a title and content for your note.")
    
    with col2_b:
        if st.button("🗑️ Clear"):
            st.session_state.current_note = ""
            st.session_state.note_title = ""
            st.rerun()
    
    with col2_c:
        if st.session_state.current_note.strip():
            st.download_button(
                label="📥 Export Note",
                data=st.session_state.current_note,
                file_name=f"{sanitize_filename(st.session_state.note_title or 'note')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )

# Footer with instructions
st.divider()
with st.expander("ℹ️ How to Use This App"):
    st.markdown("""
    **Getting Started:**
    1. **Choose Input Method**: Select between Topic/Subject, Text Content, or Questions/Prompts
    2. **Enter Your Content**: Provide the topic, text, or questions you want notes for
    3. **Generate Notes**: Click the "Generate Notes" button to create AI-powered study notes
    4. **Edit & Organize**: Use the note editor to modify content and add titles/categories
    5. **Save & Export**: Save notes for later use or export them as text files
    
    **Tips:**
    - Be specific with your topics for better results
    - Use the category system to organize different subjects
    - The detail level affects how comprehensive your generated notes will be
    - You can manually edit any generated content before saving
    
    **API Key Setup:**
    - Make sure your OpenAI API key is set in the environment variables
    - The app uses GPT-4o for the best note generation quality
    """)

# Display current stats
if st.session_state.notes:
    st.info(f"📊 You have {len(st.session_state.notes)} saved notes across {len(set([note.get('category', 'General') for note in st.session_state.notes]))} categories")
