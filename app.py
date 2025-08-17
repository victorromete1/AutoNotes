import calendar
from html import escape
import streamlit as st
import json
from PyPDF2 import PdfReader
import docx
from datetime import datetime, timedelta
from note_generator import NoteGenerator
from flashcard_generator import FlashcardGenerator
from quiz_generator import QuizGenerator
from progress_tracker import ProgressTracker
from pdf_report_generator import PDFReportGenerator
from data_persistence import DataPersistence
from advanced_quiz_system import AdvancedQuizSystem
from utils import sanitize_filename
import base64
from data_import_export import DataImportExport
from datetime import datetime
def next_flashcard(study_cards, correct=False):
    """Move to next flashcard in study session"""
    st.session_state.cards_studied += 1
    if correct:
        st.session_state.cards_correct += 1

    st.session_state.study_index += 1
    st.session_state.show_answer = False

    if st.session_state.study_index >= len(study_cards):
        # Session complete
        accuracy = (st.session_state.cards_correct / st.session_state.cards_studied) * 100

        # Save session
        session = {
            'timestamp': datetime.now().isoformat(),
            'activity_type': 'flashcards',
            'subject': study_cards[0].get('category', 'General'),
            'flashcards_studied': st.session_state.cards_studied,
            'correct_answers': st.session_state.cards_correct,
            'accuracy': accuracy
        }
        st.session_state.study_sessions.append(session)
        auto_save()

        st.success(f"Session complete! Accuracy: {accuracy:.1f}%")

        # Reset
        for key in ['study_index', 'show_answer', 'cards_studied', 'cards_correct']:
            if key in st.session_state:
                del st.session_state[key]

    st.rerun()

# Page configuration
st.set_page_config(
    page_title="AI Study Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize generators
@st.cache_resource
def get_generators():
    return {
        'notes': NoteGenerator(),
        'flashcards': FlashcardGenerator(),
        'quiz': QuizGenerator(),
        'progress': ProgressTracker(),
        'pdf': PDFReportGenerator()
    }

generators = get_generators()
persistence = DataPersistence()
data_io = DataImportExport(persistence) 
advanced_quiz = AdvancedQuizSystem(generators['quiz'])

# Initialize session state
def init_session_state():
    defaults = {
        'notes': [],
        'flashcards': [],
        'study_sessions': [],
        'current_note': "",
        'note_title': "",
        'note_category': "General",
        'page': 'Home'
    }

    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

init_session_state()

# Load saved data
persistence.load_all_data()

# Auto-save function
def auto_save():
    try:
        persistence.auto_save_data()
    except:
        pass

# Navigation sidebar
with st.sidebar:
    st.title("🎓 Study Platform")


    # Navigation
    page = st.selectbox(
        "Navigate:",
        ["🏠 Home", "📝 Notes", "📚 Flashcards", "🧠 Quizzes", "📊 Progress", "📋 Reports","📅 Calendar"],
        key="navigation"
    )
    st.session_state.page = page


    # Quick stats
    st.divider()
    st.subheader("📈 Quick Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Notes", len(st.session_state.notes))
        st.metric("Flashcards", len(st.session_state.flashcards))
    with col2:
        quiz_sessions = [s for s in st.session_state.study_sessions if s.get('activity_type') == 'quiz']
        st.metric("Quizzes", len(quiz_sessions))
        st.metric("Sessions", len(st.session_state.study_sessions))
    data_io.render_sidebar_controls()


# Initialize session state
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

elif st.session_state.page == "📝 Notes":
    st.title("📝 AI Note Generator")

    # Note creation
    st.subheader("✨ Generate New Note")

    col1, col2 = st.columns([2, 1])
    with col1:
        topic = st.text_input("📖 Topic or subject:", placeholder="e.g., Photosynthesis, World War II, Calculus...")

    with col2:
        category = st.text_input("Category:", value="General")

    # File upload option
    st.subheader("📂 Or Upload Text File")
    uploaded_file = st.file_uploader("Upload a text file to generate notes from:", type=['txt', 'md'])

    if st.button("🚀 Generate Notes", type="primary", use_container_width=True):
        content_to_process = ""

        if uploaded_file:
            content_to_process = str(uploaded_file.read(), "utf-8")
            topic = uploaded_file.name.replace('.txt', '').replace('.md', '')
        elif topic.strip():
            content_to_process = topic

        if content_to_process:
            with st.spinner("Generating comprehensive notes..."):
                try:
                    notes_content = generators['notes'].generate_notes(content_to_process)

                    if notes_content:
                        # Save note
                        new_note = {
                            'title': topic,
                            'content': notes_content,
                            'category': category,
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        st.session_state.notes.append(new_note)
                        auto_save()

                        st.success(f"✅ Notes generated successfully for '{topic}'!")

                        # Preview
                        with st.expander("📖 Preview Generated Notes", expanded=True):
                            st.markdown(notes_content)
                    else:
                        st.error("Failed to generate notes. Please try again.")

                except Exception as e:
                    st.error(f"Error: {str(e)}")
        else:
            st.warning("Please enter a topic or upload a file.")

    # Display existing notes
    if st.session_state.notes:
        st.divider()
        st.subheader("📚 Your Notes")

        # Filter options
        categories = list(set([note.get('category', 'General') for note in st.session_state.notes]))
        filter_category = st.selectbox("Filter by category:", ["All"] + categories)

        filtered_notes = st.session_state.notes
        if filter_category != "All":
            filtered_notes = [n for n in filtered_notes if n.get('category') == filter_category]

        for i, note in enumerate(filtered_notes):
            with st.expander(f"📄 {note['title']} ({note.get('category', 'General')})"):
                st.write(f"**Created:** {note['timestamp']}")
                st.markdown(note['content'])

                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("📚 Create Flashcards", key=f"flash_{i}"):
                        with st.spinner("Creating flashcards..."):
                            try:
                                flashcards = generators['flashcards'].generate_flashcards(
                                    note['content'], num_cards=6, difficulty="Medium"
                                )

                                for card in flashcards:
                                    card['category'] = note.get('category', 'General')

                                st.session_state.flashcards.extend(flashcards)
                                auto_save()
                                st.success(f"✅ Created {len(flashcards)} flashcards!")

                                # Log activity
                                session = {
                                    'timestamp': datetime.now().isoformat(),
                                    'activity_type': 'flashcards_created',
                                    'subject': note.get('category', 'General'),
                                    'flashcards_created': len(flashcards),
                                    'duration_minutes': 2
                                }
                                st.session_state.study_sessions.append(session)
                                auto_save()

                            except Exception as e:
                                st.error(f"Error: {str(e)}")

                with col2:
                    st.download_button(
                        "📥 Download",
                        data=note['content'],
                        file_name=f"{sanitize_filename(note['title'])}.txt",
                        mime="text/plain",
                        key=f"download_{i}"
                    )

                with col3:
                    if st.button("🗑️ Delete", key=f"delete_{i}"):
                        st.session_state.notes.remove(note)
                        auto_save()
                        st.rerun()

elif st.session_state.page == "📚 Flashcards":
    st.title("📚 Interactive Flashcards")

    tab1, tab2, tab3 = st.tabs(["📖 Study", "➕ Create", "📂 Manage"])

    with tab1:
        st.subheader("📖 Study Session")
        
        if not st.session_state.flashcards:
            st.info("No flashcards available. Create some first!")
            if st.button("🔄 Refresh"):
                st.rerun()
        else:
            # Category filter
            categories = list(set([card.get('category', 'General') for card in st.session_state.flashcards]))
            selected_category = st.selectbox("Study category:", ["All"] + categories)

            study_cards = st.session_state.flashcards
            if selected_category != "All":
                study_cards = [card for card in study_cards if card.get('category', 'General') == selected_category]

            if study_cards:
                # Initialize study session
                if 'study_index' not in st.session_state:
                    st.session_state.study_index = 0
                    st.session_state.show_answer = False
                    st.session_state.cards_studied = 0
                    st.session_state.cards_correct = 0

                current_card = study_cards[st.session_state.study_index]

                # Progress
                progress = (st.session_state.study_index + 1) / len(study_cards)
                st.progress(progress, text=f"Card {st.session_state.study_index + 1} of {len(study_cards)}")

                # Card display
                st.markdown(f"""
                <div style="border: 2px solid #ddd; border-radius: 10px; padding: 30px; margin: 20px 0; 
                           background-color: #f9f9f9; text-align: center; min-height: 150px;">
                    <h3>{current_card['front']}</h3>
                </div>
                """, unsafe_allow_html=True)

                # Answer section
                if st.session_state.show_answer:
                    st.markdown(f"""
                    <div style="border: 2px solid #4CAF50; border-radius: 10px; padding: 20px; margin: 20px 0; 
                               background-color: #e8f5e8; text-align: center;">
                        <h4>Answer:</h4>
                        <p>{current_card['back']}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown("### How well did you know this?")
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        if st.button("❌ Incorrect", use_container_width=True):
                            next_flashcard(study_cards, correct=False)

                    with col2:
                        if st.button("🤔 Partial", use_container_width=True):
                            next_flashcard(study_cards, correct=True)

                    with col3:
                        if st.button("✅ Correct", use_container_width=True):
                            next_flashcard(study_cards, correct=True)

                else:
                    if st.button("🔍 Show Answer", use_container_width=True):
                        st.session_state.show_answer = True
                        st.rerun()

                # Session stats
                if st.session_state.cards_studied > 0:
                    accuracy = (st.session_state.cards_correct / st.session_state.cards_studied) * 100
                    st.metric("Session Accuracy", f"{accuracy:.1f}%")

    with tab2:
        st.subheader("➕ Create Flashcards")

        method = st.radio(
            "Creation method:",
            ["📝 From Text", "📂 Upload File", "✋ Manual Entry", "📚 From Notes"],
            horizontal=True
        )

        # ---------------- From Text ----------------
        if method == "📝 From Text":
            content = st.text_area("Paste content:", placeholder="Enter study material...", height=150)

            col1, col2, col3 = st.columns(3)
            with col1:
                num_cards = st.slider("Number of cards:", 3, 20, 8)
            with col2:
                difficulty = st.selectbox("Difficulty:", ["Easy", "Medium", "Hard"])
            with col3:
                category = st.text_input("Category:", value="General")

            if st.button("🚀 Generate Flashcards", type="primary"):
                if content.strip():
                    with st.spinner("Creating flashcards..."):
                        try:
                            flashcards = generators['flashcards'].generate_flashcards(
                                content, num_cards=num_cards, difficulty=difficulty
                            )

                            for card in flashcards:
                                card['category'] = category

                            st.session_state.flashcards.extend(flashcards)
                            auto_save()
                            st.success(f"✅ Generated {len(flashcards)} flashcards!")

                            # Log activity
                            session = {
                                'timestamp': datetime.now().isoformat(),
                                'activity_type': 'flashcards_created',
                                'subject': category,
                                'flashcards_created': len(flashcards)
                            }
                            st.session_state.study_sessions.append(session)
                            auto_save()

                            # Preview
                            st.markdown("### Preview:")
                            for i, card in enumerate(flashcards[:3], 1):
                                with st.expander(f"Card {i}"):
                                    st.write(f"**Front:** {card['front']}")
                                    st.write(f"**Back:** {card['back']}")

                            if len(flashcards) > 3:
                                st.info(f"+ {len(flashcards) - 3} more cards created!")

                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                else:
                    st.warning("Please enter content.")

        # ---------------- Manual Entry ----------------
        elif method == "✋ Manual Entry":
            with st.form("manual_flashcard"):
                front = st.text_area("Front (Question):", height=100)
                back = st.text_area("Back (Answer):", height=100)
                category = st.text_input("Category:", value="General")

                if st.form_submit_button("➕ Add Flashcard"):
                    if front.strip() and back.strip():
                        new_card = {
                            'front': front,
                            'back': back,
                            'category': category,
                            'created': datetime.now().isoformat()
                        }
                        st.session_state.flashcards.append(new_card)
                        auto_save()
                        st.success("✅ Flashcard added!")
                    else:
                        st.warning("Please fill in both sides.")

        # ---------------- Upload File ----------------
        elif method == "📂 Upload File":
            uploaded_file = st.file_uploader("Choose a file", type=["txt", "pdf", "docx"])
            if uploaded_file is not None:
                # Text file
                if uploaded_file.type == "text/plain":
                    content = uploaded_file.read().decode("utf-8")
                # PDF file
                elif uploaded_file.type == "application/pdf":
                    from PyPDF2 import PdfReader
                    pdf = PdfReader(uploaded_file)
                    content = ""
                    for page in pdf.pages:
                        content += page.extract_text()
                # Word file
                elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    import docx
                    doc = docx.Document(uploaded_file)
                    content = "\n".join([p.text for p in doc.paragraphs])
                st.text_area("Preview:", value=content[:200] + "...", height=100, disabled=True)

            col1, col2, col3 = st.columns(3)
            with col1:
                num_cards = st.slider("Number of cards:", 3, 20, 8)
            with col2:
                difficulty = st.selectbox("Difficulty:", ["Easy", "Medium", "Hard"])
            with col3:
                category = st.text_input("Category:", value="General")

            if st.button("🚀 Generate Flashcards", type="primary"):
                if content.strip():
                    with st.spinner("Creating flashcards..."):
                        try:
                            flashcards = generators['flashcards'].generate_flashcards(
                                content, num_cards=num_cards, difficulty=difficulty
                            )

                            for card in flashcards:
                                card['category'] = category

                            st.session_state.flashcards.extend(flashcards)
                            auto_save()
                            st.success(f"✅ Generated {len(flashcards)} flashcards!")

                            # Log activity
                            session = {
                                'timestamp': datetime.now().isoformat(),
                                'activity_type': 'flashcards_created',
                                'subject': category,
                                'flashcards_created': len(flashcards)
                            }
                            st.session_state.study_sessions.append(session)
                            auto_save()

                            # Preview
                            st.markdown("### Preview:")
                            for i, card in enumerate(flashcards[:3], 1):
                                with st.expander(f"Card {i}"):
                                    st.write(f"**Front:** {card['front']}")
                                    st.write(f"**Back:** {card['back']}")

                            if len(flashcards) > 3:
                                st.info(f"+ {len(flashcards) - 3} more cards created!")

                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                else:
                    st.warning("Please enter content.")

        # ---------------- From Notes ----------------
        elif method == "📚 From Notes":
            if st.session_state.notes:
                note_titles = [n['title'] for n in st.session_state.notes]
                selected_note = st.selectbox("Select note:", note_titles)
                note_obj = next((n for n in st.session_state.notes if n['title'] == selected_note), None)
                if note_obj:
                    content = note_obj['content']
                    st.text_area("Preview:", value=content[:200] + "...", height=100, disabled=True)

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        num_cards = st.slider("Number of cards:", 3, 20, 8)
                    with col2:
                        difficulty = st.selectbox("Difficulty:", ["Easy", "Medium", "Hard"])
                    with col3:
                        category = st.text_input("Category:", value="General")

                    if st.button("🚀 Generate Flashcards from Note", type="primary"):
                        if content.strip():
                            with st.spinner("Creating flashcards..."):
                                try:
                                    flashcards = generators['flashcards'].generate_flashcards(
                                        content, num_cards=num_cards, difficulty=difficulty
                                    )

                                    for card in flashcards:
                                        card['category'] = category

                                    st.session_state.flashcards.extend(flashcards)
                                    auto_save()
                                    st.success(f"✅ Generated {len(flashcards)} flashcards from note!")

                                    # Log activity
                                    session = {
                                        'timestamp': datetime.now().isoformat(),
                                        'activity_type': 'flashcards_created',
                                        'subject': category,
                                        'flashcards_created': len(flashcards)
                                    }
                                    st.session_state.study_sessions.append(session)
                                    auto_save()

                                    # Preview
                                    st.markdown("### Preview:")
                                    for i, card in enumerate(flashcards[:3], 1):
                                        with st.expander(f"Card {i}"):
                                            st.write(f"**Front:** {card['front']}")
                                            st.write(f"**Back:** {card['back']}")

                                    if len(flashcards) > 3:
                                        st.info(f"+ {len(flashcards) - 3} more cards created!")

                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                        else:
                            st.warning("Note is empty.")
            else:
                st.info("No notes available. Create some first!")


    with tab3:
        st.subheader("📂 Manage Flashcards")

        if st.session_state.flashcards:
            st.write(f"**Total flashcards:** {len(st.session_state.flashcards)}")

            # Export/Clear buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 Export All"):
                    data = generators['flashcards'].save_flashcards_file(
                        st.session_state.flashcards, "export"
                    )
                    st.download_button(
                        "Download",
                        data=data,
                        file_name=f"flashcards_{datetime.now().strftime('%Y%m%d')}.json",
                        mime="application/json"
                    )

            with col2:
                if st.button("🗑️ Clear All"):
                    st.session_state.flashcards = []
                    auto_save()
                    st.success("✅ All flashcards deleted!")
                    st.rerun()

            # Category filter
            categories = list(set([card.get('category', 'General') for card in st.session_state.flashcards]))
            filter_cat = st.selectbox("Filter:", ["All"] + categories)

            filtered = st.session_state.flashcards
            if filter_cat != "All":
                filtered = [c for c in filtered if c.get('category', 'General') == filter_cat]

            # Display cards
            for i, card in enumerate(filtered):
                with st.expander(f"🎴 {card['front'][:50]}..."):
                    st.write(f"**Front:** {card['front']}")
                    st.write(f"**Back:** {card['back']}")
                    st.write(f"**Category:** {card.get('category', 'General')}")

                    if st.button("🗑️ Delete", key=f"del_{i}"):
                        st.session_state.flashcards.remove(card)
                        auto_save()
                        st.rerun()
        else:
            st.info("No flashcards yet. Create some first!")

elif st.session_state.page == "🧠 Quizzes":
    st.title("🧠 Interactive Quiz System")

    tab1, tab2 = st.tabs(["📝 Take Quiz", "📊 History"])

    with tab1:
        # Check if quiz in progress
        if st.session_state.get('quiz_active', False):
            advanced_quiz.display_quiz_interface(st.session_state.get('current_quiz'))
        else:
            st.subheader("📝 Create New Quiz")

        # Initialize content variable
            content = ""

            # First create the form elements
            col1, col2 = st.columns(2)
            with col1:
                source = st.radio("Quiz source:", ["📚 My Notes", "📝 New Content", "📂 Upload file"])
                question_type = st.selectbox(
                    "Question Type:",
                    options=[
                        "Multiple Choice Only",
                        "True/False Only", 
                        "Short Answer Only",
                        "Mixed Questions"
                    ],
                    index=3  # Default to Mixed Questions
                )
            with col2:
                num_questions = st.slider("Questions:", 3, 15, 8)
                difficulty = st.selectbox("Difficulty:", ["Easy", "Medium", "Hard"])

            # Then handle content based on source selection
            if source == "📚 My Notes":
                if st.session_state.notes:
                    note_titles = [n['title'] for n in st.session_state.notes]
                    selected_note = st.selectbox("Select note:", note_titles)
                    note_obj = next((n for n in st.session_state.notes if n['title'] == selected_note), None)
                    if note_obj:
                        content = note_obj['content']
                        st.text_area("Preview:", value=content[:200] + "...", height=100, disabled=True)
                else:
                    st.info("No notes available. Create some first!")

            elif source == "📝 New Content":
                content = st.text_area("Enter content:", height=200, placeholder="Paste study material...")

            elif source == "📂 Upload file":
                uploaded_file = st.file_uploader("Choose a file", type=["txt", "pdf", "docx"])
                if uploaded_file is not None:
                    # Text file
                    if uploaded_file.type == "text/plain":
                        content = uploaded_file.read().decode("utf-8")
                    # PDF file
                    elif uploaded_file.type == "application/pdf":
                        from PyPDF2 import PdfReader
                        pdf = PdfReader(uploaded_file)
                        content = ""
                        for page in pdf.pages:
                            content += page.extract_text()
                    # Word file
                    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                        import docx
                        doc = docx.Document(uploaded_file)
                        content = "\n".join([p.text for p in doc.paragraphs])
                    st.text_area("Preview:", value=content[:200] + "...", height=100, disabled=True)


            if st.button("🚀 Create & Start Quiz", type="primary", use_container_width=True):
                if content.strip():
                    with st.spinner("Creating quiz..."):
                        try:
                            quiz_data = advanced_quiz.create_quiz_from_content(
                                content, num_questions=num_questions, difficulty=difficulty, question_type=question_type
                            )

                            if quiz_data and quiz_data.get('questions'):
                                st.session_state.current_quiz = quiz_data
                                st.session_state.quiz_active = True
                                st.session_state.quiz_question_index = 0
                                st.session_state.quiz_answers = {}
                                st.success("✅ Quiz created! Starting now...")
                                st.rerun()
                            else:
                                st.error("Failed to create quiz. Please try again.")

                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                else:
                    st.warning("Please provide content for the quiz.")
    with tab2:
        st.subheader("📊 Quiz History")

        quiz_sessions = [s for s in st.session_state.study_sessions if s.get('activity_type') == 'quiz']

        if quiz_sessions:
            # Stats (keep existing code)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Quizzes", len(quiz_sessions))
            with col2:
                avg_score = sum(s.get('score', 0) for s in quiz_sessions) / len(quiz_sessions)
                st.metric("Average Score", f"{avg_score:.1f}%")
            with col3:
                best_score = max(s.get('score', 0) for s in quiz_sessions)
                st.metric("Best Score", f"{best_score:.1f}%")

            # History with Retake button
            st.subheader("Recent Results")
            for i, session in enumerate(reversed(quiz_sessions[-10:])):
                timestamp = datetime.fromisoformat(session['timestamp']).strftime("%Y-%m-%d %H:%M")
                score = session.get('score', 0)
                correct = session.get('correct_answers', 0)
                total = session.get('total_questions', 0)

                color = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"

                with st.expander(f"{color} {timestamp} - {score:.1f}% ({correct}/{total})"):
                    st.write(f"**Score:** {score:.1f}%")
                    st.write(f"**Difficulty:** {session.get('difficulty', 'N/A')}")

                    # Add Retake button
                    if st.button("🔄 Retake This Quiz", key=f"retake_{i}"):
                        # Store the original quiz content to recreate it
                        st.session_state.retake_quiz_content = session.get('original_content', '')
                        st.session_state.retake_quiz_config = {
                            'num_questions': session.get('total_questions', 10),
                            'difficulty': session.get('difficulty', 'Medium')
                        }
                        st.session_state.page = "🧠 Quizzes"
                        st.session_state.quiz_active = False  # Force new quiz creation
                        st.rerun()
        else:
            st.info("No quiz history yet. Take your first quiz!")
elif st.session_state.page == "📊 Progress":
    st.title("📊 Learning Analytics")

    if not st.session_state.study_sessions:
        st.info("No study data yet. Start using the platform to see your progress!")
    else:
        # Overall stats
        col1, col2, col3, col4 = st.columns(4)

        total_sessions = len(st.session_state.study_sessions)
        quiz_sessions = [s for s in st.session_state.study_sessions if s.get('activity_type') == 'quiz']
        flashcard_sessions = [s for s in st.session_state.study_sessions if s.get('activity_type') in ['flashcards', 'flashcards_created']]

        with col1:
            st.metric("Total Sessions", total_sessions)
        with col2:
            st.metric("Quizzes Taken", len(quiz_sessions))
        with col3:
            if quiz_sessions:
                avg_quiz_score = sum(s.get('score', 0) for s in quiz_sessions) / len(quiz_sessions)
                st.metric("Avg Quiz Score", f"{avg_quiz_score:.1f}%")
            else:
                st.metric("Avg Quiz Score", "N/A")
        with col4:
            st.metric("Flashcard Sessions", len(flashcard_sessions))

        # Recent activity chart
        st.subheader("📈 Recent Activity")

        # Group sessions by date
        from collections import defaultdict
        daily_activity = defaultdict(int)

        for session in st.session_state.study_sessions:
            date = datetime.fromisoformat(session['timestamp']).strftime('%Y-%m-%d')
            daily_activity[date] += 1

        if daily_activity:
            dates = list(daily_activity.keys())[-7:]  # Last 7 days
            counts = [daily_activity[date] for date in dates]

            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.bar(dates, counts, color='skyblue')
            ax.set_title('Study Sessions (Last 7 Days)')
            ax.set_ylabel('Sessions')
            plt.xticks(rotation=45)
            st.pyplot(fig)

elif st.session_state.page == "📋 Reports":
    st.title("📋 Progress Reports")

    if st.session_state.study_sessions:
        report_type = st.selectbox("Report type:", ["Study Summary", "Quiz Analysis", "Flashcard Report"])

        if st.button("📄 Generate PDF Report", type="primary"):
            with st.spinner("Generating report..."):
                try:
                    valid_sessions = [s for s in st.session_state.study_sessions if isinstance(s, dict)]

                    pdf_data = generators['pdf'].generate_progress_report(
                        valid_sessions,
                        st.session_state.notes,
                        st.session_state.flashcards
                    )

                    st.download_button(
                        "📥 Download Report",
                        data=pdf_data,
                        file_name=f"study_report_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf"
                    )

                except Exception as e:
                    st.error(f"Error generating report: {str(e)}")
    else:
        st.info("No data available for reports. Start studying to generate reports!")
elif st.session_state.page == "📅 Calendar":
    st.title("📅 Calendar & Events")

    # ---- State ----
    if "events" not in st.session_state:
        st.session_state.events = []
    if "calendar_year" not in st.session_state:
        st.session_state.calendar_year = datetime.now().year
    if "calendar_month" not in st.session_state:
        st.session_state.calendar_month = datetime.now().month

    # ---- Add Event ----
    st.subheader("➕ Add Event")
    with st.form("add_event_form"):
        name = st.text_input("Event Title:", placeholder="e.g., Math Test, History Project, Concert")
        date = st.date_input("Date:")
        notes = st.text_area("Details (optional):", placeholder="Extra info…")
        color = st.color_picker("Pick a color:", "#4CAF50")

        if st.form_submit_button("➕ Add"):
            if name.strip():
                st.session_state.events.append({
                    "name": name.strip(),
                    "date": date.isoformat(),
                    "notes": notes.strip(),
                    "color": color,
                    "created": datetime.now().isoformat()
                })
                auto_save()
                st.success(f"✅ Added event — {name.strip()}")
            else:
                st.warning("Please enter a title.")

    st.divider()

    # ---- Month navigation ----
    nav_l, nav_c, nav_r = st.columns([1, 3, 1])
    with nav_l:
        if st.button("‹", key="prev_month"):
            if st.session_state.calendar_month == 1:
                st.session_state.calendar_month = 12
                st.session_state.calendar_year -= 1
            else:
                st.session_state.calendar_month -= 1

    with nav_c:
        month_label = datetime(st.session_state.calendar_year, st.session_state.calendar_month, 1).strftime("%b %Y")
        st.markdown(f"<h3 style='text-align:center;margin:0'>{month_label}</h3>", unsafe_allow_html=True)

    with nav_r:
        if st.button("›", key="next_month"):
            if st.session_state.calendar_month == 12:
                st.session_state.calendar_month = 1
                st.session_state.calendar_year += 1
            else:
                st.session_state.calendar_month += 1

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # ---- Build HTML calendar ----
    cal = calendar.Calendar(firstweekday=0)
    y, m = st.session_state.calendar_year, st.session_state.calendar_month
    month_days = list(cal.itermonthdates(y, m))

    # Pre-index events by date
    events_by_date = {}
    for e in st.session_state.events:
        d = datetime.fromisoformat(e["date"]).date()
        events_by_date.setdefault(d, []).append(e)

    today = datetime.now().date()

    # Weekday headers + grid
    grid_html = """
    <style>
      .cal-wrap { display:grid; grid-template-columns: repeat(7, 1fr); gap:10px; }
      .cal-head   { font-weight:600; text-align:center; padding:8px 0; }
      .cal-cell {
        background:#f9f9f9; border:1px solid #ddd; border-radius:10px;
        min-height:110px; padding:10px; box-sizing:border-box; position:relative;
      }
      .cal-cell.muted { background:#fafafa; color:#bbb; }
      .cal-daynum { position:absolute; top:8px; right:10px; font-weight:600; }
      .cal-today  { box-shadow: 0 0 0 2px #2196F3 inset; }
      .chip {
        display:block; margin-top:4px; border-radius:6px; padding:4px 6px;
        color:white; font-size:12px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
      }
    </style>
    <div class="cal-wrap">
      <div class="cal-head">Mon</div>
      <div class="cal-head">Tue</div>
      <div class="cal-head">Wed</div>
      <div class="cal-head">Thu</div>
      <div class="cal-head">Fri</div>
      <div class="cal-head">Sat</div>
      <div class="cal-head">Sun</div>
    """

    for d in month_days:
        in_month = (d.month == m)
        day_events = events_by_date.get(d, [])
        cls = "cal-cell" + ("" if in_month else " muted")
        if d == today: cls += " cal-today"

        chips_html = ""
        if in_month and day_events:
            for e in day_events[:3]:
                chips_html += f"<div class='chip' style='background:{e['color']}'>{escape(e['name'])}</div>"
            if len(day_events) > 3:
                chips_html += f"<div style='font-size:12px;color:#555'>+{len(day_events)-3} more</div>"

        grid_html += f"""
        <div class="{cls}">
            <div class="cal-daynum">{d.day}</div>
            {chips_html}
        </div>
        """

    grid_html += "</div>"
    st.markdown(grid_html, unsafe_allow_html=True)

    # ---- Daily Reminders (today only) ----
    st.divider()
    st.subheader("📅 Today’s Reminders")
    today_events = events_by_date.get(today, [])
    if today_events:
        for e in today_events:
            st.markdown(f"<span style='color:{e['color']}'>●</span> **{escape(e['name'])}**", unsafe_allow_html=True)
            if e['notes']:
                st.write(f"📝 {e['notes']}")
    else:
        st.info("No events today.")

    # ---- Upcoming Reminders ----
    st.divider()
    st.subheader("⏰ Upcoming")
    upcoming = [
        e for e in st.session_state.events
        if datetime.fromisoformat(e["date"]).date() > today
    ]
    upcoming.sort(key=lambda x: x["date"])
    if upcoming:
        for e in upcoming[:5]:
            date_str = datetime.fromisoformat(e["date"]).strftime("%Y-%m-%d")
            st.markdown(f"<span style='color:{e['color']}'>●</span> **{date_str}** — {escape(e['name'])}", unsafe_allow_html=True)
            if e['notes']:
                st.write(f"📝 {e['notes']}")
    else:
        st.info("No upcoming events.")







# Helper function for flashcard study session


# Auto-save every few minutes
if len(st.session_state.study_sessions) % 5 == 0:
    auto_save()
