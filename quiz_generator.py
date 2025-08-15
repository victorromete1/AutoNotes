import json
import os
import re
from openai import OpenAI
import streamlit as st
from datetime import datetime
from typing import Optional, Dict, List, Union

class QuizGenerator:
    def __init__(self):
        """Initialize with configurable API clients."""
        self.client = self._initialize_client()
        self.model = self._select_model()
        
    def _initialize_client(self) -> OpenAI:
        """Initialize the appropriate API client with fallback logic."""
        try:
            # Try OpenRouter first
            if "OPENROUTER_API_KEY" in st.secrets:
                return OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=st.secrets["OPENROUTER_API_KEY"]
                )
            
            # Fallback to OpenAI
            if "OPENAI_API_KEY" in st.secrets:
                return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            
            # Final fallback to environment variables
            if os.getenv("OPENAI_API_KEY"):
                return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            raise ValueError("No valid API keys found")
            
        except Exception as e:
            st.error(f"API initialization failed: {str(e)}")
            st.stop()

    def _select_model(self) -> str:
        """Select the appropriate model based on available credentials."""
        if "OPENROUTER_API_KEY" in st.secrets:
            return "anthropic/claude-3-haiku"  # More reliable than deepseek
        return "gpt-4-turbo"  # Default to OpenAI's best model

    def generate_quiz(
        self,
        content: str,
        quiz_type: str = "multiple_choice",
        num_questions: int = 5,
        difficulty: str = "Medium"
    ) -> Optional[Dict]:
        """Generate a quiz from content with robust error handling."""
        if not content.strip():
            st.error("Content cannot be empty")
            return None

        try:
            # Clean and preprocess content
            content = self._preprocess_content(content)
            
            # Handle mixed quiz type
            if quiz_type == "mixed":
                return self._generate_mixed_quiz(content, num_questions, difficulty)
            
            # Generate the appropriate prompt
            prompt = self._create_prompt(content, quiz_type, num_questions, difficulty)
            
            # Get API response with retry logic
            response = self._get_api_response(prompt)
            
            # Parse and validate the response
            quiz_data = self._parse_response(response, quiz_type)
            
            # Add metadata
            quiz_data.update({
                "quiz_id": f"quiz_{datetime.now().timestamp()}",
                "created": datetime.now().isoformat(),
                "type": quiz_type,
                "difficulty": difficulty,
                "source_content": content[:1000] + "..." if len(content) > 1000 else content
            })
            
            return quiz_data

        except Exception as e:
            st.error(f"Quiz generation failed: {str(e)}")
            st.error(f"Problematic content: {content[:200]}...")
            return None

    def _generate_mixed_quiz(
        self,
        content: str,
        num_questions: int,
        difficulty: str
    ) -> Dict:
        """Generate a quiz with mixed question types."""
        # Calculate distribution of question types
        mc_count = max(1, num_questions // 2)
        tf_count = max(1, num_questions // 3)
        sa_count = num_questions - mc_count - tf_count
        
        # Generate each type
        mc_quiz = self.generate_quiz(content, "multiple_choice", mc_count, difficulty)
        tf_quiz = self.generate_quiz(content, "true_false", tf_count, difficulty)
        sa_quiz = self.generate_quiz(content, "short_answer", sa_count, difficulty)
        
        # Combine results
        combined = {
            "title": f"Mixed Quiz ({difficulty} Difficulty)",
            "questions": [],
            "type": "mixed",
            "difficulty": difficulty,
            "quiz_id": f"quiz_{datetime.now().timestamp()}",
            "created": datetime.now().isoformat()
        }
        
        if mc_quiz and mc_quiz.get("questions"):
            for q in mc_quiz["questions"]:
                q["type"] = "multiple_choice"
                combined["questions"].append(q)
        
        if tf_quiz and tf_quiz.get("questions"):
            for q in tf_quiz["questions"]:
                q["type"] = "true_false"
                combined["questions"].append(q)
                
        if sa_quiz and sa_quiz.get("questions"):
            for q in sa_quiz["questions"]:
                q["type"] = "short_answer"
                combined["questions"].append(q)
        
        # Shuffle questions
        if len(combined["questions"]) > 1:
            import random
            random.shuffle(combined["questions"])
            
        return combined

    def _preprocess_content(self, content: str) -> str:
        """Clean and normalize input content."""
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content).strip()
        
        # Remove problematic characters
        content = content.encode('ascii', 'ignore').decode('ascii')
        
        # Truncate very long content
        if len(content) > 20000:
            content = content[:20000]
            st.warning("Content was truncated to 20,000 characters")
            
        return content

    def _create_prompt(
        self,
        content: str,
        quiz_type: str,
        num_questions: int,
        difficulty: str
    ) -> str:
        """Create a tailored prompt based on quiz type."""
        prompt_templates = {
            "multiple_choice": """
            Create {num_questions} {difficulty} difficulty multiple choice questions from this content.
            Each question must have 4 options (A-D) with exactly one correct answer.
            Format response as JSON with: title, questions (list of dicts with question, options, correct_answer, explanation)
            Content: {content}
            """,
            "true_false": """
            Create {num_questions} {difficulty} difficulty true/false statements from this content.
            Format response as JSON with: title, questions (list of dicts with question, correct_answer, explanation)
            Content: {content}
            """,
            "short_answer": """
            Create {num_questions} {difficulty} difficulty short answer questions from this content.
            Format response as JSON with: title, questions (list of dicts with question, sample_answer, key_points)
            Content: {content}
            """
        }
        
        base_prompt = prompt_templates.get(
            quiz_type,
            prompt_templates["multiple_choice"]
        ).format(
            num_questions=num_questions,
            difficulty=difficulty,
            content=content
        )
        
        return f"""
        {base_prompt}
        
        Important:
        - Return ONLY valid JSON
        - Don't include markdown formatting
        - Ensure all questions relate directly to the content
        - For multiple choice, make incorrect answers plausible
        - Include 'type' field for each question matching '{quiz_type}'
        """

    def _get_api_response(self, prompt: str, max_retries: int = 3) -> str:
        """Get API response with retry logic."""
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a quiz generation expert. Always return valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000,
                    response_format={"type": "json_object"}
                )
                return response.choices[0].message.content
                
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                st.warning(f"Retry {attempt + 1} for quiz generation...")

    def _parse_response(self, response: str, quiz_type: str) -> Dict:
        """Parse and validate the API response."""
        try:
            # Clean the response
            response = response.strip()
            response = re.sub(r'^```json\s*|\s*```$', '', response)  # Remove markdown wrappers
            
            # Parse JSON
            quiz_data = json.loads(response)
            
            # Validate structure
            if not isinstance(quiz_data, dict):
                raise ValueError("Response is not a JSON object")
                
            if "questions" not in quiz_data or not isinstance(quiz_data["questions"], list):
                raise ValueError("Missing or invalid questions array")
                
            # Add type to each question
            for question in quiz_data["questions"]:
                question["type"] = quiz_type
                
            return quiz_data
            
        except json.JSONDecodeError as e:
            st.error(f"Failed to parse JSON response: {str(e)}")
            st.error(f"Response content: {response[:500]}...")
            raise ValueError("Invalid JSON response from API")
