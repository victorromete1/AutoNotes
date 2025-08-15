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
        """Generate a quiz with randomly mixed question types.
        
        Args:
            content: The content to generate questions from
            num_questions: Total number of questions to generate
            difficulty: Difficulty level ('Easy', 'Medium', 'Hard')
            
        Returns:
            dict: Dictionary of mixed questions with keys like 'Q1', 'Q2', etc.
        """
        # Define possible question types and their weights
        question_types = [
            ("multiple_choice", 0.5),   # 50% chance
            ("true_false", 0.3),       # 30% chance  
            ("short_answer", 0.2)      # 20% chance
        ]
        
        mixed_quiz = {}
        
        for i in range(1, num_questions + 1):
            # Weighted random selection of question type
            chosen_type = random.choices(
                [t[0] for t in question_types],
                weights=[t[1] for t in question_types],
                k=1
            )[0]
            
            # Generate single question of chosen type
            quiz_part = self.generate_quiz(content, chosen_type, 1, difficulty) or {}
            
            # Extract the question data (should only be one question)
            for q_key, q_data in quiz_part.items():
                if q_key.startswith('Q'):  # Only process question entries
                    # Ensure question has type field
                    q_data['type'] = chosen_type
                    mixed_quiz[f"Q{i}"] = q_data
                    break
        
        return mixed_quiz

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

