# app.py
import json
from typing import Dict, Any, List

import streamlit as st

from quiz_generator import QuizGenerator
from advanced_quiz_system import AdvancedQuizSystem


# ==============================
# App State Helpers
# ==============================
def _init_state() -> None:
    if "quiz" not in st.session_state:
        st.session_state.quiz = None
    if "answers" not in st.session_state:
        st.session_state.answers = {}
    if "phase" not in st.session_state:
        st.session_state.phase = "setup"  # setup -> quiz -> results
    if "debug_raw" not in st.session_state:
        st.session_state.debug_raw = ""
    if "debug_cleaned" not in st.session_state:
        st.session_state.debug_cleaned = ""


def _reset_all() -> None:
    st.session_state.quiz = None
    st.session_state.answers = {}
    st.session_state.phase = "setup"
    st.session_state.debug_raw = ""
    st.session_state.debug_cleaned = ""


# ==============================
# Content Loading
# ==============================
def _read_uploaded_text(upload) -> str:
    """
    Read text from an uploaded file. Supports .txt/.md/.json to avoid extra deps.
    If non-text (e.g., PDF) is provided, we warn and return empty string.
    """
    if upload is None:
        return ""
    filename = upload.name.lower()
    try:
        if filename.endswith(".txt") or filename.endswith(".md"):
            return upload.read().decode("utf-8", errors="ignore")
        if filename.endswith(".json"):
            raw = upload.read().decode("utf-8", errors="ignore")
            # If it's a JSON array/object with a 'content' field, use that; else return raw JSON.
            try:
                obj = json.loads(raw)
                if isinstance(obj, dict) and "content" in obj:
                    return str(obj.get("content", ""))
                return raw
            except Exception:
                return raw
        # Fallback for unsupported types
        st.warning("Unsupported file type here (try .txt, .md, or .json). Skipping file.")
        return ""
    except Exception as e:
        st.error(f"Could not read uploaded file: {e}")
        return ""


# ==============================
# UI Render Helpers
# ==============================
def _render_header(generator: QuizGenerator) -> None:
    st.title("📚 Study Quiz Builder")
    st.caption("Generate and take quizzes from your notes/content.")

    with st.sidebar:
        st.subheader("⚙️ Settings")
        st.write(f"Model in use: **{generator.model}**")

        st.markdown("---")
        st.caption("Debug")
        st.checkbox("Show debug panels", key="show_debug", value=False)


def _render_setup(advanced_system: AdvancedQuizSystem) -> None:
    st.subheader("1) Provide content")
    col1, col2 = st.columns([1, 1])

    with col1:
        text_content = st.text_area(
            "Paste content here",
            height=240,
            placeholder="Paste your study notes, textbook excerpt, or key points..."
        )

    with col2:
        upload = st.file_uploader(
            "…or upload a text file (.txt, .md, .json)",
            type=["txt", "md", "json"],
            accept_multiple_files=False
        )
        file_text = _read_uploaded_text(upload) if upload else ""

        if file_text and not text_content:
            st.info("Loaded content from uploaded file.")
            text_content = file_text
        elif file_text and text_content:
            st.info("Both text and file provided. The pasted text will be used.")

    st.subheader("2) Configure quiz")
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        num_questions = st.slider("Number of questions", 3, 25, 10, 1)
    with c2:
        difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"], index=1)
    with c3:
        question_type = st.selectbox(
            "Question type",
            ["Mixed Questions", "Multiple Choice Only", "True/False Only", "Short Answer Only"],
            index=0
        )

    st.markdown("---")
    create = st.button("🚀 Create & Start Quiz", type="primary", use_container_width=True)

    if create:
        content = (text_content or "").strip()
        if not content:
            st.error("Please provide some content first (paste text or upload a file).")
            return

        with st.spinner("Generating your quiz…"):
            quiz = advanced_system.create_quiz_from_content(
                content=content,
                num_questions=num_questions,
                difficulty=difficulty,
                question_type=question_type
            )
        if not quiz:
            st.error("Failed to create quiz. Check the debug panel below if enabled.")
            if st.session_state.get("show_debug"):
                with st.expander("Debug: Quiz generator output", expanded=False):
                    if st.session_state.debug_raw:
                        st.markdown("**Raw model output (repr):**")
                        st.code(repr(st.session_state.debug_raw))
                    if st.session_state.debug_cleaned:
                        st.markdown("**Cleaned model JSON (repr):**")
                        st.code(repr(st.session_state.debug_cleaned))
            return

        st.session_state.quiz = quiz
        st.session_state.answers = {}
        st.session_state.phase = "quiz"
        st.success("Quiz created! Scroll down to start answering.")


def _letter_for_index(i: int) -> str:
    return chr(ord("A") + i)


def _render_quiz() -> None:
    quiz = st.session_state.quiz or {}
    title = quiz.get("title", "Your Quiz")
    desc = quiz.get("description", "Answer the questions below.")
    meta = quiz.get("metadata", {})

    st.header(f"📝 {title}")
    st.caption(desc)
    with st.expander("Quiz details", expanded=False):
        st.write({
            "difficulty": meta.get("difficulty"),
            "question_type": meta.get("question_type"),
            "created": meta.get("created"),
            "total_questions": meta.get("total_questions")
        })

    st.markdown("---")
    questions: List[Dict[str, Any]] = quiz.get("questions", [])
    for q in questions:
        qid = q.get("id")
        qtext = q.get("question", "")
        qtype = (q.get("type") or "").lower()
        options = q.get("options", []) or []

        if qid is None:
            continue

        st.subheader(f"Q{qid}. {qtext}")

        # Initialize stored answer if missing
        if qid not in st.session_state.answers:
            st.session_state.answers[qid] = None

        if qtype == "multiple_choice":
            # Show lettered options (A, B, C, ...)
            labelled = [f"{_letter_for_index(i)}. {opt}" for i, opt in enumerate(options)]
            choice = st.radio(
                f"Choose one:",
                options=labelled if labelled else ["(No options provided)"],
                index=0 if st.session_state.answers[qid] is None else labelled.index(
                    st.session_state.answers[qid]
                ) if st.session_state.answers[qid] in labelled else 0,
                key=f"q_{qid}_mc"
            )
            # Store the letter (A/B/C/...), which our grader accepts (or the text if no options)
            if options:
                letter = choice.split(".", 1)[0].strip()
                st.session_state.answers[qid] = letter
            else:
                st.session_state.answers[qid] = choice

        elif qtype == "true_false":
            tf = st.radio(
                "Select True or False:",
                options=["True", "False"],
                index=0 if st.session_state.answers[qid] in (None, "True") else 1,
                key=f"q_{qid}_tf"
            )
            st.session_state.answers[qid] = tf

        else:
            # short_answer (or unknown)
            ans = st.text_input(
                "Your answer:",
                value=st.session_state.answers[qid] or "",
                key=f"q_{qid}_sa"
            )
            st.session_state.answers[qid] = ans

        st.markdown("---")

    colA, colB = st.columns([1, 1])
    with colA:
        submit = st.button("✅ Submit Answers", type="primary", use_container_width=True)
    with colB:
        cancel = st.button("↩️ Start Over", use_container_width=True)

    if cancel:
        _reset_all()
        st.experimental_rerun()

    if submit:
        st.session_state.phase = "results"


def _render_results(advanced_system: AdvancedQuizSystem) -> None:
    quiz = st.session_state.quiz or {}
    answers = st.session_state.answers or {}
    if not quiz:
        st.warning("No quiz available to grade. Please create one first.")
        return

    with st.spinner("Grading…"):
        result = advanced_system.grade_submission(quiz, answers)

    st.header("📊 Results")
    st.subheader(f"Score: {result['score']} / {result['total']}  ({result['percent']:.1f}%)")

    with st.expander("See detailed feedback", expanded=True):
        for row in result["details"]:
            st.markdown(f"**Q{row['question_id']}.** {row['question']}")
            st.write(f"**Your answer:** {row['user_answer']}")
            st.write(f"**Correct answer:** {row['correct_answer']}")
            st.write(f"**Result:** {'✅ Correct' if row['is_correct'] else '❌ Incorrect'}")
            if row.get("explanation"):
                st.caption(row["explanation"])
            st.markdown("---")

    col1, col2 = st.columns([1, 1])
    with col1:
        again = st.button("🆕 Create Another Quiz", use_container_width=True)
    with col2:
        retry = st.button("🔁 Retake This Quiz", use_container_width=True)

    if again:
        _reset_all()
        st.experimental_rerun()

    if retry:
        # Keep same quiz; clear answers; go back to quiz phase
        st.session_state.answers = {}
        st.session_state.phase = "quiz"
        st.experimental_rerun()


# ==============================
# Main
# ==============================
def main() -> None:
    st.set_page_config(page_title="Study Quiz Builder", page_icon="🧠", layout="wide")
    _init_state()

    # Construct services
    generator = QuizGenerator()
    advanced_system = AdvancedQuizSystem(generator)

    _render_header(generator)

    # Optional: Surface debug info from the normalization layer, if any
    if st.session_state.get("show_debug"):
        with st.expander("Internal Debug (if available)", expanded=False):
            # The advanced system will set debug panels via session_state if you wire it up.
            # Leaving hooks here so nothing breaks if you had them before.
            if st.session_state.debug_raw:
                st.markdown("**Raw model output (repr):**")
                st.code(repr(st.session_state.debug_raw))
            if st.session_state.debug_cleaned:
                st.markdown("**Cleaned model JSON (repr):**")
                st.code(repr(st.session_state.debug_cleaned))

    phase = st.session_state.phase
    if phase == "setup":
        _render_setup(advanced_system)
    elif phase == "quiz":
        _render_quiz()
    else:
        _render_results(advanced_system)


if __name__ == "__main__":
    main()
