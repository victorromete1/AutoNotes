# Author: Victor
# Page name: autograder.py
# Page purpose: Autograde system for app.py
# Date of creation: 2025-10-10
import os
import re
import json
import streamlit as st
from openai import OpenAI
# defines the autograder class
class AutoGrader:
    def __init__(self):
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
    # grades text and returns structured feedback
    def grade_text(self, content: str, text_type: str = "essay", extra_notes: str = "") -> dict:
        """
        Grades a piece of writing and returns structured feedback.
        Always returns a dict with keys: score, strengths, weaknesses, suggestions, detailed_feedback.
        """
        content = re.sub(r'\s+', ' ', content).strip()
        if len(content) > 15000:
            content = content[:15000]
            st.warning("⚠️ Input truncated to 15,000 characters.")
        # Ai prompts
        prompt = f"""
        You are an expert writing teacher and grader. Analyze the following {text_type}.
        Consider: clarity, structure, grammar, creativity, vocabulary, engagement, and overall impact.
        Teacher's extra notes: {extra_notes}

        Return ONLY JSON in the format:
        {{
          "score": 0-10,
          "strengths": ["..."],
          "weaknesses": ["..."],
          "suggestions": ["..."],
          "detailed_feedback": "..."
        }}

        Student {text_type}:
        {content}
        """

        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Return ONLY valid JSON as specified. No prose."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )

        raw = resp.choices[0].message.content or "{}"

        try:
            return json.loads(raw)
        except:
            return {
                "score": 0,
                "strengths": [],
                "weaknesses": [],
                "suggestions": [],
                "detailed_feedback": "⚠️ Failed to parse model response."
            }
