# backend/services/gemini_service.py
import requests
import os
from typing import List, Dict

class GeminiService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

    def generate_quiz(self, topic: str, difficulty: int, num_questions: int) -> str:
        prompt = self.build_prompt(topic, difficulty, num_questions)
        headers = {"Content-Type": "application/json"}
        params = {"key": self.api_key}
        data = {
            "contents": [{
                "role": "user",
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 2048
            }
        }
        response = requests.post(self.api_url, headers=headers, params=params, json=data)
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]

    @staticmethod
    def build_prompt(topic: str, difficulty: int, num_questions: int) -> str:
        return f"""
You are an expert quiz generator. Strictly follow the format below for each question. Do not add any extra text or commentary.

Generate {num_questions} multiple choice questions about the topic: '{topic}' at difficulty level {difficulty} (1=easy, 5=hard).

Format for each question:
Q<number>: <question text>
A) <option 1>
B) <option 2>
C) <option 3>
D) <option 4>
ANSWER: <correct letter>
EXPLANATION: <brief explanation>

Repeat this format for all {num_questions} questions. Do not include answers in the options. Do not add any extra text before or after the questions.
"""

    @staticmethod
    def parse_quiz_output(output_text: str) -> list[dict]:
        import re
        questions = []
        question_blocks = re.split(r'\s*Q\d+:\s*', output_text)
        for block in question_blocks:
            if not block.strip():
                continue
            lines = block.strip().split('\n')
            if not lines:
                continue
            question_text = ""
            options_dict = {}
            correct_answer = None
            explanation = ""
            state = "question"
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if state == "question":
                    if re.match(r'[A-D]\)', line):
                        state = "options"
                    else:
                        question_text += line + "\n"
                        continue
                if state == "options":
                    option_match = re.match(r'([A-D])\)\s*(.*)', line)
                    if option_match:
                        letter = option_match.group(1)
                        text = option_match.group(2).strip()
                        if letter not in options_dict:
                            options_dict[letter] = text
                    elif line.startswith("ANSWER:"):
                        state = "answer"
                    else:
                        continue
                if state == "answer":
                    if line.startswith("ANSWER:"):
                        answer_match = re.search(r'ANSWER:\s*([A-D])', line)
                        if answer_match:
                            correct_answer = answer_match.group(1)
                            state = "explanation"
                        else:
                            continue
                if state == "explanation":
                    if line.startswith("EXPLANATION:"):
                        explanation += line[len("EXPLANATION:"):].strip()
                    elif explanation:
                        explanation += "\n" + line
            if question_text.strip() and len(options_dict) == 4 and correct_answer:
                options_list = [f"{letter}) {options_dict[letter]}" for letter in sorted(options_dict.keys())]
                questions.append({
                    'question': question_text.strip(),
                    'options': options_list,
                    'correct_answer': correct_answer,
                    'explanation': explanation.strip()
                })
        return questions
