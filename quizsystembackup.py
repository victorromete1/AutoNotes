# Author: Victor
# Page name: advanced_quiz_system.py
# Page purpose: Advanced Quiz System generator for app.py
# Date of creation: 2025-10-10
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import streamlit as st

class AdvancedQuizSystem:
    def __init__(self, quiz_generator):
        self.quiz_generator = quiz_generator
    #Create a quiz from provided content with specified question types
    def create_quiz_from_content(self, content: str, num_questions: int = 10,
                               difficulty: str = "Medium", question_type: str = "Mixed Questions") -> Optional[Dict[str, Any]]:
        try:
            # Map labels
            question_type_map = {
                "Multiple Choice Only": "multiple_choice",
                "True/False Only": "true_false",
                "Short Answer Only": "short_answer",
                "Mixed Questions": "mixed"
            }
            quiz_type_internal = question_type_map.get(question_type, "multiple_choice")

            # Generate quiz
            quiz_data = self.quiz_generator.generate_quiz(
                content=content,
                num_questions=num_questions,
                difficulty=difficulty,
                quiz_type=quiz_type_internal
            )

            if not quiz_data or not isinstance(quiz_data, dict):
                st.error("Failed to generate quiz: invalid data returned")
                return None

            # Normalize questions
            normalized = self._normalize_questions(quiz_data, fallback_type=quiz_type_internal)

            # Build formatted quiz
            formatted_quiz = {
                'title': normalized.get('title', 'Study Quiz'),
                'description': normalized.get('description', 'Test your knowledge'),
                'questions': [],
                'metadata': {
                    'created': datetime.now().isoformat(),
                    'difficulty': difficulty,
                    'total_questions': len(normalized.get('questions', [])),
                    'original_content': content,
                    'question_type': question_type
                }
            }

            # Format questions with all required fields
            for i, q in enumerate(normalized.get('questions', [])):
                formatted_quiz['questions'].append({
                    'id': i + 1,
                    'question': q.get('question', '').strip(),
                    'type': q.get('type', quiz_type_internal),
                    'options': q.get('options', []),
                    'correct_answer': str(q.get('correct_answer', '')),
                    'explanation': q.get('explanation', ''),
                    'points': q.get('points', 1)
                })

            return formatted_quiz

        except Exception as e:
            st.error(f"Error creating quiz: {str(e)}")
            return None
    # Displays the quiz interface
    def display_quiz_interface(self, quiz_data):
        """Display the interactive quiz interface (app.py compatible)"""
        if not quiz_data:
            st.error("No quiz data available")
            return

        # Initialize quiz state if not exists
        if 'quiz_state' not in st.session_state:
            st.session_state.quiz_state = {
                'current_question': 0,
                'answers': {}, 
                'started': True,
                'completed': False,
                'start_time': datetime.now()
            }

        total = len(quiz_data['questions'])
        current = st.session_state.quiz_state['current_question']

        # Quiz header
        st.header(f"📝 {quiz_data['title']}")
        st.caption(f"Question Type: {quiz_data['metadata']['question_type']} | Difficulty: {quiz_data['metadata']['difficulty']}")
        st.write(quiz_data['description'])

        # Progress
        if st.session_state.quiz_state['completed']:
            progress = 1.0
            status = "Quiz completed!"
        else:
            progress = (current) / total if total else 0.0
            status = f"Question {current + 1} of {total}"

        st.progress(progress)
        st.write(status)

        # Display current question or results
        if not st.session_state.quiz_state['completed']:
            self._display_question(quiz_data['questions'][current], current)
            self._display_navigation(quiz_data, total, current)
        else:
            self._display_quiz_results(quiz_data)
    # Displays quiz history with retake functionality
    def display_quiz_history(self):
        """Display quiz history with retake functionality"""
        quiz_sessions = [s for s in st.session_state.get('study_sessions', []) 
                        if s.get('activity_type') == 'quiz']

        if not quiz_sessions:
            st.info("No quiz history yet. Complete your first quiz to see results!")
            return

        st.header("📚 Quiz History")

        # Stats summary
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Quizzes", len(quiz_sessions))
        avg_score = sum(s['score'] for s in quiz_sessions) / len(quiz_sessions)
        col2.metric("Average Score", f"{avg_score:.1f}%")
        best_score = max(s['score'] for s in quiz_sessions)
        col3.metric("Best Score", f"{best_score:.1f}%")

        # Filter options
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_difficulty = st.selectbox("Filter by difficulty:", ["All"] + sorted(list(set(s['difficulty'] for s in quiz_sessions))))
        with col2:
            filter_type = st.selectbox("Filter by type:", ["All"] + sorted(list(set(s.get('question_type', 'Mixed Questions') for s in quiz_sessions))))
        with col3:
            sort_by = st.selectbox("Sort by:", ["Date (Newest)", "Date (Oldest)", "Score (Highest)", "Score (Lowest)"])

        # Apply filters and sorting
        filtered_sessions = self._filter_and_sort_sessions(quiz_sessions, filter_difficulty, filter_type, sort_by)

        # Display sessions
        st.subheader("Quiz Attempts")
        for i, session in enumerate(filtered_sessions):
            with st.expander(f"{session['title']} - {session['score']:.1f}% - {session['timestamp'][:10]}"):
                col1, col2 = st.columns([3,1])
                with col1:
                    st.write(f"📅 Date: {session['timestamp'][:10]}")
                    st.write(f"🔢 Score: {session['score']:.1f}% ({session['correct_answers']}/{session['total_questions']})")
                    st.write(f"📊 Difficulty: {session['difficulty']}")
                    st.write(f"❓ Type: {session.get('question_type', 'Mixed Questions')}")
                    st.write(f"⏱️ Time: {session.get('time_taken', 'N/A')}")

                with col2:
                    if st.button("🔄 Retake This Quiz", key=f"retake_{i}"):
                        st.session_state.retake_quiz = {
                            'content': session['original_content'],
                            'num_questions': session['total_questions'],
                            'difficulty': session['difficulty'],
                            'question_type': session.get('question_type', 'Mixed Questions')
                        }
                        st.session_state.page = "🧠 Quizzes"
                        st.session_state.quiz_active = False
                        st.rerun()

    # -----------------------------
    # Grading and Results
    # -----------------------------
    # Grades the whole quiz
    def grade_submission(self, quiz: Dict[str, Any], user_answers: Dict[int, Any]) -> Dict[str, Any]:
        """Grade user answers with improved robustness"""
        total = 0
        correct = 0
        details = []

        for q in quiz.get('questions', []):
            qid = q.get('id')
            if qid is None:
                continue

            total += 1
            result = self._grade_question(q, user_answers.get(qid))
            if result['is_correct']:
                correct += 1
            details.append(result)

        return {
            'score': correct,
            'total': total,
            'percent': (correct / total * 100) if total else 0,
            'details': details,
            'graded_at': datetime.now().isoformat()
        }
    # Displays the quiz results
    def _display_quiz_results(self, quiz_data):
        """Display comprehensive quiz results (app.py compatible)"""
        st.header("🎉 Quiz Complete!")
        st.subheader(f"Quiz Type: {quiz_data['metadata']['question_type']}")

        # Grade the quiz 
        grading_result = self.grade_submission(
            quiz_data,
            st.session_state.quiz_state['answers']
        )

        # Convert to flat results for display
        results = []
        question_types = {}
        for detail in grading_result['details']:
            q_type = detail['type']
            if q_type not in question_types:
                question_types[q_type] = {'correct': 0, 'total': 0}
            question_types[q_type]['total'] += 1
            if detail['is_correct']:
                question_types[q_type]['correct'] += 1

            results.append({
                'question_number': detail.get('question_id', 0),
                'question': detail['question'],
                'user_answer': detail['user_answer'],
                'correct_answer': detail['correct_answer'],
                'is_correct': detail['is_correct'],
                'explanation': detail['explanation'],
                'type': q_type
            })

        time_taken = datetime.now() - st.session_state.quiz_state['start_time']

        # Display score summary
        col1, col2, col3 = st.columns(3)
        col1.metric("Score", f"{grading_result['percent']:.1f}%")
        col2.metric("Correct", f"{grading_result['score']}/{grading_result['total']}")
        col3.metric("Time Taken", f"{time_taken.seconds//60}m {time_taken.seconds%60}s")

        # Performance insights
        self._display_performance_analysis(grading_result['percent'], question_types, results)

        # Per-question insights dropdowns 
        st.subheader("🔎 Question Insights")
        for d in results:
            q_label = f"Q{d['question_number']}: {d['question'][:80]}{'...' if len(d['question'])>80 else ''}"
            with st.expander(q_label):
                if isinstance(d['user_answer'], dict):
                    st.markdown(f"**Your answer:** {d['user_answer']['letter']}")
                else:
                    st.markdown(f"**Your answer:** {d['user_answer']}")
                st.markdown(f"**Correct answer:** {d['correct_answer']}")
                st.markdown(f"**Result:** {'✅ Correct' if d['is_correct'] else '❌ Incorrect'}")
                if d.get('explanation'):
                    st.caption(f"💡 {d['explanation']}")

        # Save results
        self._save_quiz_results(quiz_data, results, grading_result['percent'], time_taken)

        # Navigation
        col1, col2 = st.columns(2)
        if col1.button("🔄 Retake Quiz", type="primary"):
            self._reset_quiz_state()
            st.session_state.retake_quiz = {
                'content': quiz_data['metadata']['original_content'],
                'num_questions': quiz_data['metadata']['total_questions'],
                'difficulty': quiz_data['metadata']['difficulty'],
                'question_type': quiz_data['metadata']['question_type']
            }
            st.rerun()

        if col2.button("⬅️ Back to Quiz Setup"):
            self._reset_quiz_state()
            st.session_state.quiz_active = False
            st.rerun()

    # -----------------------------
    # Helper Methods 
    # -----------------------------
    # Displays each question
    def _display_question(self, question, index):
        """Display a single question """
        st.subheader(f"Question {index + 1}")
        st.markdown(f"**Type:** {question['type'].replace('_', ' ').title()}")
        st.write(question['question'])

        qid = question.get('id', index + 1)
        key = f"q_{qid}"

        help_text = "Open the insights dropdown on the results page to review your answer vs correct answer."

        if question['type'] == 'multiple_choice':
            options = question.get('options', [])
            selected = st.radio("Select answer:", options, key=key, index=None, help=help_text)
            if selected is not None and selected != "":
                st.session_state.quiz_state['answers'][qid] = {
                    'answer': selected,
                    'letter': self._extract_answer_letter(selected)
                }

        elif question['type'] == 'true_false':
            selected = st.radio("Select answer:", ["True", "False"], key=key, index=None, help=help_text)
            if selected is not None and selected != "":
                st.session_state.quiz_state['answers'][qid] = selected

        elif question['type'] in ['short_answer', 'fill_blank']:
            default_val = ""
            if qid in st.session_state.quiz_state['answers'] and isinstance(st.session_state.quiz_state['answers'][qid], str):
                default_val = st.session_state.quiz_state['answers'][qid]
            answer = st.text_input("Your answer:", value=default_val, key=key, help=help_text, placeholder="Type your answer here")
            if answer is not None:
                st.session_state.quiz_state['answers'][qid] = answer
        else:
            # Fallback to short answer if an unknown type slips through
            answer = st.text_input("Your answer:", key=key, help=help_text, placeholder="Type your answer here")
            if answer is not None:
                st.session_state.quiz_state['answers'][qid] = answer

        if qid in st.session_state.quiz_state['answers']:
            st.info("🔵 Answered")
    #Navigation buttons, eg previous next etc.
    def _display_navigation(self, quiz_data, total, current):
        col1, col2, col3 = st.columns([1,1,1])

        with col1:
            if current > 0 and st.button("← Previous"):
                st.session_state.quiz_state['current_question'] -= 1
                st.rerun()

        with col2:
            if current < total - 1 and st.button("Next →"):
                # require current question answered before moving on
                current_qid = quiz_data['questions'][current]['id']
                if current_qid in st.session_state.quiz_state['answers']:
                    st.session_state.quiz_state['current_question'] += 1
                    st.rerun()
                else:
                    st.warning("Please answer the question first")

        with col3:
            if current == total - 1 and st.button("🏁 Finish Quiz"):
                current_qid = quiz_data['questions'][current]['id']
                if current_qid in st.session_state.quiz_state['answers']:
                    st.session_state.quiz_state['completed'] = True
                    st.rerun()
                else:
                    st.warning("Please answer the question first")
    # Displays how good you did
    def _display_performance_analysis(self, score, question_types, results):
        """Display detailed performance analysis (app.py compatible)"""
        if score >= 90:
            st.success("🌟 Outstanding performance! You've mastered this material.")
        elif score >= 80:
            st.info("👍 Strong performance! You understand most concepts well.")
        elif score >= 70:
            st.warning("📚 Good effort. Review these areas to improve:")
        else:
            st.error("💪 Needs improvement. Focus on these fundamentals:")

        # Performance by question type
        st.subheader("By Question Type")
        for q_type, stats in question_types.items():
            type_name = q_type.replace('_', ' ').title()
            accuracy = (stats['correct'] / stats['total']) * 100 if stats['total'] else 0

            if accuracy >= 80:
                st.success(f"• {type_name}: {accuracy:.1f}% accuracy")
            elif accuracy >= 60:
                st.info(f"• {type_name}: {accuracy:.1f}% accuracy")
            else:
                st.error(f"• {type_name}: {accuracy:.1f}% accuracy")

        # Specific recommendations
        incorrect = [r for r in results if not r['is_correct']]
        if incorrect:
            st.subheader("🔍 Focus Areas")
            st.write("You missed these concepts:")
            for i, r in enumerate(incorrect[:5]):
                st.write(f"- {r['question'][:100]}...")

        # Study recommendations
        st.subheader("📚 Study Tips")
        if score >= 90:
            st.write("- Challenge yourself with more advanced material")
            st.write("- Help others learn these concepts")
        elif score >= 70:
            st.write("- Review your incorrect answers")
            st.write("- Create flashcards for key concepts")
        else:
            st.write("- Review the foundational concepts")
            st.write("- Practice with similar quizzes")
            st.write("- Study in shorter, more frequent sessions")
    # Saves the quiz results ot the database or session state
    def _save_quiz_results(self, quiz_data, results, score, time_taken):
        """Save quiz results to session state (app.py compatible)"""
        quiz_result = {
            'timestamp': datetime.now().isoformat(),
            'title': quiz_data['title'],
            'score': score,
            'correct_answers': sum(1 for r in results if r['is_correct']),
            'total_questions': len(results),
            'difficulty': quiz_data['metadata']['difficulty'],
            'question_type': quiz_data['metadata'].get('question_type', 'Mixed Questions'),
            'activity_type': 'quiz',
            'original_content': quiz_data['metadata']['original_content'],
            'detailed_results': results,
            'time_taken': f"{time_taken.seconds//60}m {time_taken.seconds%60}s"
        }

        if 'study_sessions' not in st.session_state:
            st.session_state.study_sessions = []
        st.session_state.study_sessions.append(quiz_result)
    # Resets the quiz state for a new quiz
    def _reset_quiz_state(self):
        """Reset quiz state (app.py compatible)"""
        if 'quiz_state' in st.session_state:
            del st.session_state.quiz_state
        if 'retake_quiz' in st.session_state:
            del st.session_state.retake_quiz
    # Filters and sorts quiz sessions based on user selection
    def _extract_answer_letter(self, answer):
        """Extract letter from multiple choice answer (app.py compatible)"""
        match = re.match(r'^([A-Za-z])[\)\.]?\s*', str(answer).strip())
        return match.group(1).upper() if match else ""
    # cleans ai generated stuff
    def _normalize_questions(self, quiz_data: Dict[str, Any], fallback_type: str) -> Dict[str, Any]:
        """Enhanced question normalization from new version"""
        data = dict(quiz_data)
        questions = data.get("questions", [])
        
        if not isinstance(questions, list):
            raw = json.dumps(quiz_data) if not isinstance(quiz_data, str) else quiz_data
            cleaned = self._clean_model_json(raw)
            try:
                candidate = json.loads(cleaned)
                questions = candidate.get("questions", [])
                data.update(candidate)
            except Exception:
                questions = []

        normalized_questions = []
        for q in questions:
            if not isinstance(q, dict):
                if isinstance(q, str):
                    q = self._try_parse_question_dict(q) or {}
                else:
                    continue

            # Ensure required fields
            q = self._ensure_question_fields(q, fallback_type)
            normalized_questions.append(q)

        # Deduplicate questions by text
        seen = set()
        unique_questions = []
        for q in normalized_questions:
            if q["question"] not in seen:
                unique_questions.append(q)
                seen.add(q["question"])

        data["questions"] = unique_questions
        return data

    # Ensure all feilds exist
    def _ensure_question_fields(self, q: Dict[str, Any], fallback_type: str) -> Dict[str, Any]:
        """Ensure all required question fields exist with proper values"""
        # Determine question type
        qtype = (q.get("type") or fallback_type or "").lower()
        if qtype not in ("multiple_choice", "true_false", "short_answer", "mixed"):
            # Anything unknown becomes short answer so a text box appears
            qtype = "short_answer"
        if qtype == "mixed":
            if isinstance(q.get("options"), list) and q.get("options"):
                qtype = "multiple_choice"
            elif isinstance(q.get("correct_answer"), str) and q.get("correct_answer").strip().lower() in ("true", "false"):
                qtype = "true_false"
            else:
                qtype = "short_answer"
        q["type"] = qtype

        # Ensure correct answer exists
        if "correct_answer" not in q or not q.get("correct_answer"):
            for alt in ("sample_answer", "expected_answer", "answer", "key_points"):
                if q.get(alt):
                    q["correct_answer"] = q[alt]
                    break
            if not q.get("correct_answer") and qtype == "true_false":
                inferred = self._infer_true_false_from_text(q.get("explanation", "")) or ""
                q["correct_answer"] = inferred

        # Clean fields
        q["question"] = (q.get("question") or "").strip()
        q["explanation"] = q.get("explanation", "")
        q["correct_answer"] = str(q.get("correct_answer", ""))

        # Handle question type specifics
        if qtype == "true_false":
            ans = q["correct_answer"].strip().lower()
            if ans in ["a) true", "true", "t", "yes", "1"]:
                q["correct_answer"] = "True"
            elif ans in ["b) false", "false", "f", "no", "0"]:
                q["correct_answer"] = "False"

        if qtype == "multiple_choice":
            opts = q.get("options", [])
            if not isinstance(opts, list) or not opts:
                opts = self._extract_options_from_text(q.get("question", ""))
            q["options"] = opts
            q["correct_answer"] = self._normalize_mc_correct(q["correct_answer"], opts)

        return q
    # Grades questions
    def _grade_question(self, question: Dict[str, Any], user_answer: Any) -> Dict[str, Any]:
        """Grade a single question with improved robustness"""
        qtype = (question.get("type") or "").lower()
        correct_answer = str(question.get("correct_answer", "")).strip()
        explanation = question.get("explanation", "")
        
        is_correct = False
        normalized_user = self._coerce_answer_for_type(user_answer, qtype)
        normalized_correct = self._coerce_answer_for_type(correct_answer, qtype)

        if qtype == "multiple_choice":
            is_correct = self._compare_mc_answer(normalized_user, normalized_correct, question)
        elif qtype == "true_false":
            is_correct = str(normalized_user).lower() == str(normalized_correct).lower()
        else:  # short_answer or unknown
            if isinstance(normalized_user, str) and isinstance(normalized_correct, str):
                u = normalized_user.strip().lower()
                c = normalized_correct.strip().lower()
                # First, quick fuzzy check
                if (u == c) or (c in u) or (u in c):
                    is_correct = True
                else:
                    # Use AI to judge correctness more flexibly (best-effort)
                    is_correct = self._ai_check_short_answer(
                        question.get("question", ""),
                        correct_answer,
                        user_answer
                    )

        return {
            "question_id": question.get("id", 0),
            "question": question.get("question", ""),
            "type": qtype,
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "explanation": explanation,
            "points_awarded": 1 if is_correct else 0
        }

    # -----------------------------
    # Utility Methods
    # -----------------------------

    def _clean_model_json(self, text: str) -> str:
        """Clean common LLM JSON issues (robust to code fences)"""
        if not isinstance(text, str):
            try:
                text = json.dumps(text)
            except Exception:
                text = str(text)

        s = text.strip()
        # Remove json / fences at start and end
        s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.IGNORECASE)
        s = re.sub(r"```\s*$", "", s, flags=re.IGNORECASE)
        # Normalize quotes and control 
        s = s.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
        s = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", " ", s)
        # Fix stray backslashes
        s = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', s)
        # Remove trailing commas
        s = re.sub(r",\s*([}\]])", r"\1", s)
        return s

    def _try_parse_question_dict(self, qtext: str) -> Optional[Dict[str, Any]]:
        """Try to parse a single question represented as a JSON string"""
        if not isinstance(qtext, str):
            return None
        cleaned = self._clean_model_json(qtext)
        try:
            obj = json.loads(cleaned)
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None
    #  pull True/False from text
    def _infer_true_false_from_text(self, text: str) -> Optional[str]:
        if not text or not isinstance(text, str):
            return None
        m = re.search(r"\b(true|false)\b", text, flags=re.IGNORECASE)
        return m.group(1).capitalize() if m else None
    # Extracts multiple choice options form the text
    def _extract_options_from_text(self, text: str) -> List[str]:
        """Extract MC options from text"""
        if not text:
            return []
        matches = re.findall(r"(?:^|\s)[A-D]\)\s*([^;|\n]+)", text)
        return [m.strip() for m in matches] if matches else []

    def _normalize_mc_correct(self, correct: Any, options: List[str]) -> str:
        """Normalize MC correct answer to option key or text"""
        if correct is None:
            return ""
        c = str(correct).strip()

        # If a single letter was provided
        if re.fullmatch(r"[A-Z]", c, flags=re.IGNORECASE):
            return c.upper()

        # If exact option text was provided
        for idx, opt in enumerate(options):
            if c.lower() == str(opt).strip().lower():
                return opt

        
        m = re.match(r"([A-Da-d])\b", c)
        if m:
            return m.group(1).upper()

        return c

    def _coerce_answer_for_type(self, ans: Any, qtype: str) -> Any:
        """Normalize answers by type"""
        if qtype == "true_false":
            if isinstance(ans, bool):
                return "True" if ans else "False"
            if isinstance(ans, str):
                s = ans.strip().lower()
                if s in ("true", "t", "yes", "y", "1"):
                    return "True"
                if s in ("false", "f", "no", "n", "0"):
                    return "False"
        if isinstance(ans, str):
            return ans.strip()
        return ans

    def _compare_mc_answer(self, user_ans: Any, correct_ans: Any, q: Dict[str, Any]) -> bool:
        """Robust MC answer comparison"""
        options = [str(o).strip() for o in q.get("options", [])]
        if not options:
            return str(user_ans).strip().lower() == str(correct_ans).strip().lower()

        letters = [chr(ord('A') + i) for i in range(len(options))]
        letter_to_text = dict(zip(letters, options))

        # Pull stored values
        if isinstance(user_ans, dict) and 'answer' in user_ans:
            u = str(user_ans['answer']).strip()
        else:
            u = str(user_ans).strip()
        c = str(correct_ans).strip()

        # If correct is a letter (A/B/C/D)
        if c.upper() in letter_to_text:
            if u.upper() == c.upper():
                return True
            return u.lower() == letter_to_text[c.upper()].lower()

        # If correct is exact text
        if c:
            if u.lower() == c.lower():
                return True
            # If user picked a letter that corresponds to the correct text
            for L, txt in letter_to_text.items():
                if txt.lower() == c.lower():
                    return u.upper() == L
        return False

    def _filter_and_sort_sessions(self, sessions, filter_difficulty, filter_type, sort_by):
        """Filter and sort quiz sessions"""
        filtered = sessions
        if filter_difficulty != "All":
            filtered = [s for s in filtered if s['difficulty'] == filter_difficulty]
        if filter_type != "All":
            filtered = [s for s in filtered if s.get('question_type', 'Mixed Questions') == filter_type]

        reverse = True
        if sort_by == "Date (Newest)":
            key = lambda x: x['timestamp']
        elif sort_by == "Date (Oldest)":
            key = lambda x: x['timestamp']
            reverse = False
        elif sort_by == "Score (Highest)":
            key = lambda x: x['score']
        else:  
            key = lambda x: x['score']
            reverse = False

        return sorted(filtered, key=key, reverse=reverse)

    # -----------------------------
    # AI-assisted short answer grading
    # -----------------------------

    def _ai_check_short_answer(self, question_text: str, correct_answer: str, user_answer: Union[str, Any]) -> bool:
        try:
            if hasattr(self.quiz_generator, 'grade_short_answer') and callable(getattr(self.quiz_generator, 'grade_short_answer')):
                prompt = (
                    "You are grading a short answer question.\n"
                    f"Question: {question_text}\n"
                    f"Correct Answer: {correct_answer}\n"
                    f"Student's Answer: {user_answer}\n"
                    "Respond only with 'true' if the student's answer is correct, or 'false' if it is incorrect."
                )
                result = self.quiz_generator.grade_short_answer(prompt)
                return str(result).strip().lower().startswith('t')
            else:
                return False
        except Exception as e:
            st.warning(f"AI short answer check failed: {e}")
            return False
