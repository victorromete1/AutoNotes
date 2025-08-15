import json
import re
import random
from openai import OpenAI
import streamlit as st
from typing import Dict

class QuizGenerator:
    def __init__(self):
        """Initialize the quiz generator with Anthropic Claude via OpenRouter."""
        # Get OpenRouter key from Streamlit secrets
        openrouter_key = st.secrets.get("OPENROUTER_API_KEY")

        if not openrouter_key:
            st.error("❌ OPENROUTER_API_KEY not found in Streamlit secrets.")
            st.info("🆓 You can get an OpenRouter API key at https://openrouter.ai")
            st.stop()

        # Always use OpenRouter client
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key
        )
        self.model = "anthropic/claude-3-haiku"
        self.provider = "OpenRouter (Claude 3 Haiku)"

        # Debug: confirm base_url in UI
        st.write(f"✅ Using {self.provider} — base_url: {self.client.base_url}")

    def generate_quiz(self, content, quiz_type, num_questions=5, difficulty="Medium"):
        type_map = {
            "Multiple Choice Only": "multiple_choice",
            "True/False Only": "true_false",
            "Short Answer Only": "short_answer",
            "Mixed Questions": "mixed",
            "multiple_choice": "multiple_choice",
            "true_false": "true_false",
            "short_answer": "short_answer",
            "mixed": "mixed"
        }
        quiz_type = type_map.get(quiz_type, quiz_type)

        if quiz_type == "mixed":
            return self._generate_mixed_quiz(content, num_questions, difficulty)

        prompt = self._create_prompt(content, quiz_type, num_questions, difficulty)
        response = self._get_api_response(prompt)
        quiz_data = self._parse_response(response, quiz_type)
        return quiz_data

    def _generate_mixed_quiz(self, content, num_questions, difficulty):
        question_types = [
            ("multiple_choice", 0.5),
            ("true_false", 0.3),
            ("short_answer", 0.2)
        ]
        mixed_quiz = {}

        for i in range(1, num_questions + 1):
            chosen_type = random.choices(
                [t[0] for t in question_types],
                weights=[t[1] for t in question_types],
                k=1
            )[0]
            quiz_part = self.generate_quiz(content, chosen_type, 1, difficulty) or {}
            for q_key, q_data in quiz_part.items():
                if q_key.startswith('Q'):
                    q_data['type'] = chosen_type
                    mixed_quiz[f"Q{i}"] = q_data
                    break
        return mixed_quiz

    def _create_prompt(self, content: str, quiz_type: str, num_questions: int, difficulty: str) -> str:
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
