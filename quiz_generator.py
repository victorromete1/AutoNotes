import json
import os
import re
import random
from openai import OpenAI
import streamlit as st
from datetime import datetime
from typing import Optional, Dict

class QuizGenerator:
    def __init__(self):
        """Initialize API client."""
        self.client = self._initialize_client()
        self.model = self._select_model()

    def _initialize_client(self) -> OpenAI:
        """Set up API client from secrets or environment."""
        try:
            if "OPENROUTER_API_KEY" in st.secrets:
                return OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=st.secrets["OPENROUTER_API_KEY"]
                )
            if "OPENAI_API_KEY" in st.secrets:
                return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            if os.getenv("OPENAI_API_KEY"):
                return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            raise ValueError("❌ No API key found for quiz generation.")
        except Exception as e:
            st.error(f"API initialization failed: {e}")
            st.stop()

    def _select_model(self) -> str:
        """Pick best available model."""
        if "OPENROUTER_API_KEY" in st.secrets:
            return "anthropic/claude-3-haiku"
        return "gpt-4-turbo"

    def generate_quiz(
        self,
        content: str,
        quiz_type: str,
        num_questions: int = 5,
        difficulty: str = "Medium"
    ) -> Optional[Dict]:
        """Generate quiz questions from content."""
        if not content.strip():
            st.error("❌ No content provided for quiz.")
            return None

        try:
            content = self._preprocess_content(content)

            if quiz_type == "mixed":
                return self._generate_mixed_quiz(content, num_questions, difficulty)

            prompt = self._create_prompt(content, quiz_type, num_questions, difficulty)
            response = self._get_api_response(prompt)
            quiz_data = self._parse_response(response, quiz_type)

            quiz_data.update({
                "quiz_id": f"quiz_{datetime.now().timestamp()}",
                "created": datetime.now().isoformat(),
                "type": quiz_type,
                "difficulty": difficulty,
                "source_content": content[:1000] + "..." if len(content) > 1000 else content
            })
            return quiz_data

        except Exception as e:
            st.error(f"Quiz generation failed: {e}")
            return None

    def _generate_mixed_quiz(self, content: str, num_questions: int, difficulty: str) -> Dict:
        """Generate mixed-type quiz."""
        mc_count = max(1, num_questions // 2)
        tf_count = max(1, num_questions // 3)
        sa_count = num_questions - mc_count - tf_count

        mc_quiz = self.generate_quiz(content, "multiple_choice", mc_count, difficulty) or {}
        tf_quiz = self.generate_quiz(content, "true_false", tf_count, difficulty) or {}
        sa_quiz = self.generate_quiz(content, "short_answer", sa_count, difficulty) or {}

        combined = {
            "title": f"Mixed Quiz ({difficulty})",
            "questions": [],
            "type": "mixed",
            "difficulty": difficulty,
            "quiz_id": f"quiz_{datetime.now().timestamp()}",
            "created": datetime.now().isoformat()
        }

        for quiz, qtype in [(mc_quiz, "multiple_choice"), (tf_quiz, "true_false"), (sa_quiz, "short_answer")]:
            if quiz.get("questions"):
                for q in quiz["questions"]:
                    q["type"] = qtype
                    combined["questions"].append(q)

        random.shuffle(combined["questions"])
        return combined

    def _preprocess_content(self, content: str) -> str:
        """Clean and trim content."""
        content = re.sub(r'\s+', ' ', content).strip()
        content = content.encode('ascii', 'ignore').decode('ascii')
        if len(content) > 20000:
            content = content[:20000]
            st.warning("⚠️ Content truncated to 20,000 characters.")
        return content

    def _create_prompt(self, content: str, quiz_type: str, num_questions: int, difficulty: str) -> str:
        """Prompt template."""
        templates = {
            "multiple_choice": f"""
            Create {num_questions} {difficulty} difficulty multiple choice questions from this content.
            Each must have options A-D, exactly one correct answer, and an explanation.
            Return ONLY valid JSON: {{ "title": "", "questions": [ {{ "question": "", "options": [], "correct_answer": "", "explanation": "" }} ] }}
            Content: {content}
            """,
            "true_false": f"""
            Create {num_questions} {difficulty} difficulty true/false questions from this content.
            Return ONLY valid JSON: {{ "title": "", "questions": [ {{ "question": "", "correct_answer": "True/False", "explanation": "" }} ] }}
            Content: {content}
            """,
            "short_answer": f"""
            Create {num_questions} {difficulty} difficulty short answer questions from this content.
            Return ONLY valid JSON: {{ "title": "", "questions": [ {{ "question": "", "correct_answer": "", "explanation": "" }} ] }}
            Content: {content}
            """
        }
        return templates[quiz_type]

    def _get_api_response(self, prompt: str) -> str:
        """Call LLM API."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a quiz generator. Output valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content

    def _parse_response(self, response: str, quiz_type: str) -> Dict:
        """Ensure JSON is valid."""
        try:
            cleaned = re.sub(r'^```json\s*|\s*```$', '', response.strip())
            quiz_data = json.loads(cleaned)
            if "questions" not in quiz_data or not isinstance(quiz_data["questions"], list):
                raise ValueError("Invalid questions array in quiz data.")
            for q in quiz_data["questions"]:
                q["type"] = quiz_type
            return quiz_data
        except Exception as e:
            st.error(f"❌ JSON parse error: {e}")
            st.text_area("Raw API output:", response, height=300)
            raise
    def grade_short_answer(self, prompt: str) -> str:
        """
        Uses the quiz generator's LLM to check short answer correctness.
        Returns 'true' or 'false'.
        """
        # If you already have a method to talk to your model (e.g., self.model_api_call),
        # reuse it here:
        try:
            response = self.model_api_call(prompt)  # Replace with your actual call
            return str(response).strip().lower()
        except Exception as e:
            return "false"

