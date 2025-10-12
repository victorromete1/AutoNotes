# Author: Victor
# Page name: quiz_generator.py
# Page purpose: Quiz generation system for advanced_quiz_system.py
# Date of creation: 2025-10-10
import json
import os
import re
import random
from typing import Dict, Any, List, Optional
from openai import OpenAI
import streamlit as st
# Defines the quiz generator class
class QuizGenerator:
    def __init__(self):
        """Initialize the quiz generator with Anthropic Claude via OpenRouter (no OpenAI fallback)."""
        openrouter_key = st.secrets.get("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY")
        if not openrouter_key:
            st.error("❌ OPENROUTER_API_KEY not found.")
            st.info("🆓 Get one at https://openrouter.ai")
            st.stop()

        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key
        )
        self.model = "anthropic/claude-3-haiku"

    # Generate quiz with AI
    def generate_quiz(self, content: str, quiz_type: str, num_questions: int = 5, difficulty: str = "Medium") -> Dict[str, Any]:
        """Always returns {'title': str, 'questions': [ ... ]}."""
        quiz_type = self._normalize_quiz_type(quiz_type)
        content = self._preprocess_content(content)

        if quiz_type == "mixed":
            return self._generate_mixed_quiz(content, num_questions, difficulty)

        prompt = self._create_prompt(content, quiz_type, num_questions, difficulty)
        raw = self._get_api_response(prompt)
        data = self._parse_response_strict(raw)

        # Final shape & type tagging
        title = data.get("title") or "Study Quiz"
        questions = data.get("questions") or []
        out = {"title": title, "questions": []}
        for q in questions:
            if isinstance(q, dict):
                q["type"] = quiz_type if q.get("type") in (None, "", "mixed") else q["type"]
                out["questions"].append(self._ensure_question_fields(q, quiz_type))
        return out

    # Helper functions
    def _normalize_quiz_type(self, t: str) -> str:
        m = {
            "Multiple Choice Only": "multiple_choice",
            "True/False Only": "true_false",
            "Short Answer Only": "short_answer",
            "Mixed Questions": "mixed"
        }
        return m.get(t, t).lower()
    # Checks if content is too long
    def _preprocess_content(self, content: str) -> str:
        content = re.sub(r'\s+', ' ', content).strip()
        content = content.encode('ascii', 'ignore').decode('ascii')
        if len(content) > 20000:
            content = content[:20000]
            st.warning("⚠️ Content truncated to 20,000 characters.")
        return content
     # Generates prompt based on quiz type
    def _create_prompt(self, content: str, quiz_type: str, num_questions: int, difficulty: str) -> str:
        base = (
            "You are a quiz generator. Output ONLY a single JSON object. "
            "NO markdown, NO code fences, NO comments. The JSON schema is:\n"
            '{ "title": "string", "questions": [ { "question": "string", '
            '"options": ["A) ...","B) ...","C) ...","D) ..."], '
            '"correct_answer": "A|B|C|D or exact text or True/False", '
            '"explanation": "string" } ] }\n'
        )
        if quiz_type == "multiple_choice":
            task = f"Create {num_questions} {difficulty} multiple choice questions from this content. " \
                   f"Each must have options A-D, exactly one correct answer (letter or exact text), and an explanation."
        elif quiz_type == "true_false":
            task = f"Create {num_questions} {difficulty} true/false questions from this content. " \
                   f'Use "True" or "False" for correct_answer and include an explanation.'
        else:  # short_answer
            task = f"Create {num_questions} {difficulty} short answer questions from this content. " \
                   f"Include a clear correct_answer and an explanation."

        return f"{base}\n{task}\nContent:\n{content}"

    def _get_api_response(self, prompt: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Return ONLY valid JSON as specified. No prose."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        return resp.choices[0].message.content or ""

    # Json handling
    def _parse_response_strict(self, response: str) -> Dict[str, Any]:
        """
        Accepts:
          - a proper object with 'questions'
          - a raw array of questions  -> wrap in object
          - a dict of Q1/Q2/...      -> convert to questions list
        Raises on totally invalid.
        """
        text = response.strip()
        text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text, flags=re.IGNORECASE)

        # First try: parse as JSON directly
        obj: Any
        try:
            obj = json.loads(text)
        except Exception:
            # Try to extract a JSON object or array substring
            m = re.search(r'(\{.*\}|\[.*\])', text, flags=re.DOTALL)
            if not m:
                raise ValueError("Model did not return JSON.")
            obj = json.loads(m.group(1))

        # If it's a list, wrap it
        if isinstance(obj, list):
            return {"title": "Study Quiz", "questions": obj}

        if not isinstance(obj, dict):
            raise ValueError("Model returned non-object JSON.")

        if "questions" not in obj or not isinstance(obj.get("questions"), list):
            q_keys = [k for k in obj.keys() if re.match(r'Q\d+', str(k), re.IGNORECASE)]
            if q_keys:
                q_list = [obj[k] for k in sorted(q_keys, key=lambda x: int(re.findall(r'\d+', x)[0]))]
                obj = {"title": obj.get("title", "Study Quiz"), "questions": q_list}

        # Ensure 'questions' exists
        if "questions" not in obj or not isinstance(obj["questions"], list):
            obj["questions"] = []

        return obj

    # Mixed quiz generation
    def _generate_mixed_quiz(self, content: str, num_questions: int, difficulty: str) -> Dict[str, Any]:
        """
        Generate a mixed quiz and ALWAYS return {'title': ..., 'questions': [...] }.
        """
        question_types = [
            ("multiple_choice", 0.5),
            ("true_false", 0.3),
            ("short_answer", 0.2)
        ]

        questions: List[Dict[str, Any]] = []

        for _ in range(num_questions):
            chosen_type = random.choices(
                [t[0] for t in question_types],
                weights=[t[1] for t in question_types],
                k=1
            )[0]

            # Ask for ONE question of the chosen type
            prompt = self._create_prompt(content, chosen_type, 1, difficulty)
            raw = self._get_api_response(prompt)
            data = self._parse_response_strict(raw)
            qlist = data.get("questions", [])
            if qlist:
                q = qlist[0] if isinstance(qlist[0], dict) else {}
                q["type"] = chosen_type
                questions.append(self._ensure_question_fields(q, chosen_type))

        return {"title": "Mixed Quiz", "questions": questions}

    # Ensure question fields & types
    def _ensure_question_fields(self, q: Dict[str, Any], fallback_type: str) -> Dict[str, Any]:
        qtype = (q.get("type") or fallback_type or "").lower()
        if qtype not in ("multiple_choice", "true_false", "short_answer"):
            qtype = "short_answer"
        q["type"] = qtype

        q["question"] = (q.get("question") or "").strip()
        q["explanation"] = q.get("explanation", "")
        if "correct_answer" not in q or q.get("correct_answer") in (None, ""):
            q["correct_answer"] = ""

        if qtype == "multiple_choice":
            opts = q.get("options", [])
            if not isinstance(opts, list) or not opts:
                opts = self._extract_options_from_text(q.get("question", ""))
            q["options"] = opts
            q["correct_answer"] = self._normalize_mc_correct(q.get("correct_answer", ""), opts)
        else:
            q["options"] = q.get("options", [])

        return q

    def _extract_options_from_text(self, text: str) -> List[str]:
        if not text:
            return []
        matches = re.findall(r"(?:^|\s)[A-D]\)\s*([^;|\n]+)", text)
        return [m.strip() for m in matches] if matches else []

    def _normalize_mc_correct(self, correct: Any, options: List[str]) -> str:
        c = str(correct).strip() if correct is not None else ""
        if re.fullmatch(r"[A-Da-d]", c):
            return c.upper()
        for idx, opt in enumerate(options):
            if c.lower() == str(opt).strip().lower():
                return opt
        m = re.match(r"([A-Da-d])\b", c)
        if m:
            return m.group(1).upper()
        return c

    # Grade system used by advanced_quiz_system.py
    def grade_short_answer(self, prompt: str) -> str:
        """
        Ask the same model to judge 'true' / 'false'. Returns 'true' or 'false'.
        """
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Respond only with 'true' or 'false' (lowercase). No punctuation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=3
            )
            ans = (resp.choices[0].message.content or "").strip().lower()
            return "true" if ans.startswith("t") else "false" if ans.startswith("f") else "false"
        except Exception:
            return "false"
