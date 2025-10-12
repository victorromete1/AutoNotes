# Author: Victor
# Page name: flashcard_generator.py
# Page purpose: Flashcard generation system for app.py
# Date of creation: 2025-10-10
import json
import os
from openai import OpenAI
import streamlit as st
from datetime import datetime

class FlashcardGenerator:
    def __init__(self):
        """Initialize the flashcard generator with DeepSeek via OpenRouter (no OpenAI fallback)."""
        
        # Get OpenRouter API key from Streamlit secrets or environment
        openrouter_key = st.secrets.get("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY")
        
        if not openrouter_key:
            st.error("⚠️ No OpenRouter API key found. Please set OPENROUTER_API_KEY.")
            st.stop()
        
        # Always use OpenRouter client
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key
        )
        self.model = "deepseek/deepseek-chat"

    #Generate flashcards witrh ai
    def generate_flashcards(self, content, num_cards=10, difficulty="Medium"):
        """Generate flashcards from given content."""
        try:
            prompt = f"""
            Create {num_cards} high-quality flashcards from the following content.
            Difficulty level: {difficulty}
            
            Content:
            {content}
            
            Return ONLY a valid JSON array with this exact structure:
            [
                {{
                    "front": "Question or term",
                    "back": "Answer or definition",
                    "category": "Subject area",
                    "difficulty": "{difficulty}"
                }}
            ]
            
            Make sure each flashcard:
            - Tests important concepts
            - Has clear, concise questions
            - Provides complete answers
            - Covers different aspects of the material
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert educator creating effective study flashcards. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            flashcards_text = response.choices[0].message.content.strip()
            
            # Clean up the response to ensure valid JSON
            if flashcards_text.startswith("```json"):
                flashcards_text = flashcards_text[7:]
            if flashcards_text.endswith("```"):
                flashcards_text = flashcards_text[:-3]
            
            flashcards = json.loads(flashcards_text)
            
            # Add metadata
            for card in flashcards:
                card["created"] = datetime.now().isoformat()
                card["id"] = f"card_{datetime.now().timestamp()}_{len(card['front'])}"
            
            return flashcards
            
        except json.JSONDecodeError as e:
            st.error(f"Error parsing flashcards: {e}")
            return []
        except Exception as e:
            st.error(f"Error generating flashcards: {e}")
            return []
    #Save flashcards (not used)
    def save_flashcards_file(self, flashcards, filename):
        """Save flashcards to a .flashcard file."""
        data = {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "flashcards": flashcards,
            "total_cards": len(flashcards)
        }
        
        return json.dumps(data, indent=2)
    #Load flashcards (not used)
    def load_flashcards_file(self, file_content):
        """Load flashcards from a .flashcard file."""
        try:
            data = json.loads(file_content)
            return data.get("flashcards", [])
        except json.JSONDecodeError:
            st.error("Invalid flashcard file format")
            return []
