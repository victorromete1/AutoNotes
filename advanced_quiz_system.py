# advanced_quiz_system.py
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st


class AdvancedQuizSystem:
    def __init__(self, quiz_generator):
        """
        Orchestrates quiz creation and grading using a provided QuizGenerator.
        Expects quiz_generator to expose: generate_quiz(content, quiz_type, num_questions, difficulty) -> dict
        """
        self.quiz_generator = quiz_generator

    # -----------------------------
    # Public: Create quiz from content
    # -----------------------------
    def create_quiz_from_content(self, content: str, num_questions: int = 10,
                                 difficulty: str = "Medium", question_type: str = "Mixed Questions") -> Optional[Dict[str, Any]]:
        """Create a quiz from provided content with specified question types (UI label safe)."""
        try:
            # Map UI-friendly labels to internal quiz_type values for QuizGenerator
            question_type_map = {
                "Multiple Choice Only": "multiple_choice",
                "True/False Only": "true_false",
                "Short Answer Only": "short_answer",
                "Mixed Questions": "mixed"
            }
            quiz_type_internal = question_type_map.get(question_type, "multiple_choice")

            # Generate quiz from content with correct type
            quiz_data = self.quiz_generator.generate_quiz(
                content=content,
                num_questions=num_questions,
                difficulty=difficulty,
                quiz_type=quiz_type_internal
            )

            if not quiz_data or not isinstance(quiz_data, dict):
                st.error("Failed to create quiz: empty or invalid data returned from generator.")
                return None

            # Normalize/repair questions to guarantee required fields exist
            normalized = self._normalize_questions(quiz_data, fallback_type=quiz_type_internal)

            # Build formatted quiz payload that the UI expects
            formatted_quiz = {
                "title": normalized.get("title", "Study Quiz"),
                "description": normalized.get("description", "Test your knowledge"),
                "questions": [],
                "metadata": {
                    "created": datetime.now().isoformat(),
                    "difficulty": difficulty,
                    "total_questions": len(normalized.get("questions", [])),
                    "original_content": content,
                    "question_type": question_type
                }
            }

            for i, q in enumerate(normalized.get("questions", [])):
                # Ensure consistent schema for the app
                formatted_quiz["questions"].append({
                    "id": i + 1,
                    "question": q.get("question", "").strip(),
                    "type": q.get("type", quiz_type_internal),
                    "options": q.get("options", []),
                    "correct_answer": q.get("correct_answer", ""),
                    "explanation": q.get("explanation", ""),
                    "points": q.get("points", 1)
                })

            if not formatted_quiz["questions"]:
                st.error("Failed to create quiz: no questions after normalization.")
                return None

            return formatted_quiz

        except json.JSONDecodeError as e:
            st.error(f"Error parsing quiz (JSON): {str(e)}")
            return None
        except Exception as e:
            st.error(f"Error creating quiz: {str(e)}")
            return None

    # -----------------------------
    # Public: Grade a submission
    # -----------------------------
    def grade_submission(self, quiz: Dict[str, Any], user_answers: Dict[int, Any]) -> Dict[str, Any]:
        """
        Grade user answers. user_answers is a dict: {question_id: user_answer}
        For MC: user_answer should match option (e.g., 'A'/'B' or the text) — we compare smartly.
        For TF: user_answer can be 'True'/'False'/bool.
        For SA: string similarity fallback (simple contains-insensitive).
        """
        total = 0
        correct = 0
        details: List[Dict[str, Any]] = []

        questions = quiz.get("questions", [])
        for q in questions:
            qid = q.get("id")
            if qid is None:
                continue
            total += 1

            qtype = (q.get("type") or "").lower()
            correct_answer = (q.get("correct_answer") or "").strip()
            explanation = q.get("explanation", "")
            user_ans = user_answers.get(qid, None)

            is_correct = False
            normalized_user = self._coerce_answer_for_type(user_ans, qtype)
            normalized_correct = self._coerce_answer_for_type(correct_answer, qtype)

            if qtype == "multiple_choice":
                # Compare by option key (A/B/C/D) or by text case-insensitively
                is_correct = self._compare_mc_answer(normalized_user, normalized_correct, q)
            elif qtype == "true_false":
                # Normalize to 'true' or 'false'
                is_correct = str(normalized_user).lower() == str(normalized_correct).lower()
            else:
                # short_answer (or unknown): simple case-insensitive containment or exact match
                if isinstance(normalized_user, str) and isinstance(normalized_correct, str):
                    u = normalized_user.strip().lower()
                    c = normalized_correct.strip().lower()
                    is_correct = (u == c) or (c in u) or (u in c)

            if is_correct:
                correct += 1

            details.append({
                "question_id": qid,
                "question": q.get("question", ""),
                "type": qtype,
                "user_answer": user_ans,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "explanation": explanation,
                "points_awarded": 1 if is_correct else 0
            })

        return {
            "score": correct,
            "total": total,
            "percent": (correct / total * 100.0) if total else 0.0,
            "details": details,
            "graded_at": datetime.now().isoformat()
        }

    # -----------------------------
    # Internal: Normalization & Cleaning
    # -----------------------------
    def _normalize_questions(self, quiz_data: Dict[str, Any], fallback_type: str) -> Dict[str, Any]:
        """
        Ensure 'questions' is a list of dicts with required keys.
        Guarantees 'correct_answer' exists (maps sample_answer/key_points → correct_answer).
        Adds 'type' to each question if missing.
        """
        data = dict(quiz_data)
        questions = data.get("questions", [])
        if not isinstance(questions, list):
            # Try to recover if the model returned raw text JSON that needs cleaning
            raw = json.dumps(quiz_data) if not isinstance(quiz_data, str) else quiz_data
            cleaned = self._clean_model_json(raw)
            try:
                candidate = json.loads(cleaned)
                questions = candidate.get("questions", [])
                data.update(candidate)
            except Exception:
                # Show debug to help diagnose
                with st.expander("Debug: Unable to parse questions list", expanded=False):
                    st.markdown("**Raw (repr):**")
                    st.code(repr(raw))
                    st.markdown("**Cleaned (repr):**")
                    st.code(repr(cleaned))
                # Force empty list to avoid crashes
                questions = []

        normalized_questions: List[Dict[str, Any]] = []
        for q in questions:
            if not isinstance(q, dict):
                # If LLM returned a string, try to parse it as a question dict
                if isinstance(q, str):
                    q_try = self._try_parse_question_dict(q)
                    if q_try is not None:
                        q = q_try
                    else:
                        continue
                else:
                    continue

            # Key normalization
            if "correct_answer" not in q or not q.get("correct_answer"):
                # Map alternate keys commonly returned by models
                for alt in ("sample_answer", "expected_answer", "answer", "key_points", "model_answer"):
                    if q.get(alt):
                        q["correct_answer"] = q.get(alt)
                        break
                # As a last resort, if TF question has no correct_answer but looks boolean in explanation
                if not q.get("correct_answer") and (q.get("type", fallback_type).lower() == "true_false"):
                    inferred = self._infer_true_false_from_text(q.get("explanation", "")) or ""
                    q["correct_answer"] = inferred

            # Ensure 'type'
            qtype = (q.get("type") or fallback_type or "").lower()
            if qtype not in ("multiple_choice", "true_false", "short_answer", "mixed"):
                qtype = fallback_type or "multiple_choice"
            q["type"] = qtype

            # Ensure fields exist
            q["question"] = (q.get("question") or "").strip()
            q["explanation"] = q.get("explanation", "")
            if qtype == "multiple_choice":
                opts = q.get("options", [])
                if not isinstance(opts, list) or not opts:
                    # Try to extract options from text if present
                    opts = self._extract_options_from_text(q.get("question", ""))
                q["options"] = opts

                # Normalize MC correct to option key (A/B/C/...) if possible
                if q.get("correct_answer"):
                    q["correct_answer"] = self._normalize_mc_correct(q["correct_answer"], opts)

            # Final guarantee: 'correct_answer' must exist as a string
            if "correct_answer" not in q or q["correct_answer"] is None:
                q["correct_answer"] = ""

            # Coerce non-strings to strings for storage
            if not isinstance(q["correct_answer"], (str, int, float, bool)):
                q["correct_answer"] = str(q["correct_answer"])
            q["correct_answer"] = str(q["correct_answer"])

            normalized_questions.append(q)

        data["questions"] = normalized_questions
        return data

    def _clean_model_json(self, text: str) -> str:
        """
        Clean common LLM JSON issues that cause:
            Error parsing quiz: Invalid \\escape: line X column Y (char Z)
        Steps:
        - Strip code fences and leading/trailing whitespace
        - Replace smart quotes with regular quotes
        - Remove unescaped control characters
        - Escape stray backslashes that are not valid JSON escapes
        - Remove trailing commas
        """
        if not isinstance(text, str):
            try:
                text = json.dumps(text)
            except Exception:
                text = str(text)

        # Remove triple backtick code fences (```json ... ```)
        text = re.sub(r"^\s*```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
        text = re.sub(r"\s*```\s*$", "", text, flags=re.IGNORECASE)

        # Replace smart quotes
        text = text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")

        # Remove unescaped control chars (except \n, \t which are valid when properly escaped)
        # First, ensure bare newlines are escaped inside quotes by a conservative approach later
        # Here, just strip ASCII control chars outside typical JSON escapes
        text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", " ", text)

        # Escape stray backslashes not forming a valid JSON escape (\", \\, \/, \b, \f, \n, \r, \t, \uXXXX)
        text = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', text)

        # Remove trailing commas in objects and arrays: {...,} or [ ... ,]
        text = re.sub(r",\s*([}\]])", r"\1", text)

        return text

    def _try_parse_question_dict(self, qtext: str) -> Optional[Dict[str, Any]]:
        """Try to parse a single question represented as a JSON string."""
        if not isinstance(qtext, str):
            return None
        cleaned = self._clean_model_json(qtext)
        try:
            obj = json.loads(cleaned)
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None

    # -----------------------------
    # Internal: Helpers
    # -----------------------------
    def _infer_true_false_from_text(self, text: str) -> Optional[str]:
        """Heuristic: pull 'True'/'False' from explanation text if clearly stated."""
        if not text or not isinstance(text, str):
            return None
        m = re.search(r"\b(true|false)\b", text, flags=re.IGNORECASE)
        return m.group(1).capitalize() if m else None

    def _extract_options_from_text(self, text: str) -> List[str]:
        """
        Try to extract MC options from inline text like:
        '... A) foo; B) bar; C) baz; D) qux ...'
        """
        if not text:
            return []
        matches = re.findall(r"(?:^|\s)[A-D]\)\s*([^;|\n]+)", text)
        return [m.strip() for m in matches] if matches else []

    def _normalize_mc_correct(self, correct: Any, options: List[str]) -> str:
        """
        Normalize MC correct answer to either 'A'/'B'/... or the exact option text if that’s what you store.
        If correct looks like the text of an option, keep it as-is. If it looks like 'A', return 'A'.
        """
        if correct is None:
            return ""
        c = str(correct).strip()

        # If it's already a single-letter option key
        if re.fullmatch(r"[A-Z]", c, flags=re.IGNORECASE):
            return c.upper()

        # If it matches an option text, keep text
        for idx, opt in enumerate(options):
            if c.lower() == str(opt).strip().lower():
                return opt  # return canonical option text

        # If it starts with something like "A)" or "Option A"
        m = re.match(r"([A-Da-d])\b", c)
        if m:
            return m.group(1).upper()

        return c

    def _coerce_answer_for_type(self, ans: Any, qtype: str) -> Any:
        """Normalize user/correct answers by type for reliable comparisons."""
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
        """
        Compare MC answers robustly:
        - If correct is 'A'..'D', accept user 'A'..'D' or matching option text.
        - If correct is text, accept that text or its corresponding letter if options align.
        """
        options = [str(o).strip() for o in q.get("options", [])]
        if not options:
            # Fallback to simple string compare
            return str(user_ans).strip().lower() == str(correct_ans).strip().lower()

        # Build letter map
        letters = [chr(ord('A') + i) for i in range(len(options))]
        letter_to_text = dict(zip(letters, options))

        u = str(user_ans).strip()
        c = str(correct_ans).strip()

        # If correct is a letter
        if c.upper() in letter_to_text:
            # Accept user letter or user text equal to that option
            if u.upper() == c.upper():
                return True
            return u.lower() == letter_to_text[c.upper()].lower()

        # If correct is text: accept exact text or corresponding letter if uniquely matches
        if c:
            if u.lower() == c.lower():
                return True
            # Find letter whose text equals c
            for L, txt in letter_to_text.items():
                if txt.lower() == c.lower():
                    return u.upper() == L
        return False
