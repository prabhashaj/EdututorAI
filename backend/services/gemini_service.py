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
Create {num_questions} multiple choice questions about '{topic}' at difficulty level {difficulty}/5.

CRITICAL: Follow this EXACT format for each question. Do not deviate from this format:

Question 1:
What is the capital of France?
A) London
B) Berlin
C) Paris
D) Madrid
ANSWER: C
EXPLANATION: Paris is the capital and largest city of France.

Question 2:
Which planet is closest to the Sun?
A) Venus
B) Mercury
C) Earth
D) Mars
ANSWER: B
EXPLANATION: Mercury is the smallest planet and the one closest to the Sun in our solar system.

Now generate {num_questions} questions about '{topic}' following this EXACT format:
- Start each question with "Question X:" where X is the number
- Write the question on the next line
- List exactly 4 options (A, B, C, D)
- Include "ANSWER: " followed by the correct letter
- Include "EXPLANATION: " followed by a brief explanation
- Leave a blank line between questions

Topic: {topic}
Difficulty: {difficulty}/5
Number of questions: {num_questions}

Begin:
"""

    @staticmethod
    def parse_quiz_output(output_text: str) -> list[dict]:
        import re
        questions = []
        
        try:
            # Split by "Question X:" pattern
            question_blocks = re.split(r'Question \d+:', output_text, flags=re.IGNORECASE)
            
            for block in question_blocks[1:]:  # Skip the first empty block
                if not block.strip():
                    continue
                
                lines = [line.strip() for line in block.strip().split('\n') if line.strip()]
                if len(lines) < 6:  # Need at least question + 4 options + answer
                    continue
                
                # Extract question text (first non-empty line)
                question_text = lines[0]
                
                # Extract options
                options = []
                option_texts = []
                answer_line_idx = -1
                
                for i, line in enumerate(lines[1:], 1):
                    # Check for options A), B), C), D)
                    option_match = re.match(r'^([A-D])\)\s*(.+)$', line, re.IGNORECASE)
                    if option_match:
                        letter = option_match.group(1).upper()
                        text = option_match.group(2).strip()
                        options.append(letter)
                        option_texts.append(text)
                    elif line.startswith('ANSWER:'):
                        answer_line_idx = i
                        break
                
                # Ensure we have exactly 4 options
                if len(options) != 4 or len(option_texts) != 4:
                    continue
                
                # Extract correct answer
                correct_answer = None
                explanation = ""
                
                if answer_line_idx > 0:
                    answer_line = lines[answer_line_idx]
                    answer_match = re.search(r'ANSWER:\s*([A-D])', answer_line, re.IGNORECASE)
                    if answer_match:
                        correct_answer = answer_match.group(1).upper()
                    
                    # Extract explanation
                    for line in lines[answer_line_idx + 1:]:
                        if line.startswith('EXPLANATION:'):
                            explanation = line[12:].strip()  # Remove "EXPLANATION:"
                        elif explanation and not line.startswith('Question'):
                            explanation += " " + line
                        else:
                            break
                
                # Validate and add question
                if (question_text and 
                    len(option_texts) == 4 and 
                    correct_answer and 
                    correct_answer in ['A', 'B', 'C', 'D']):
                    
                    questions.append({
                        'question': question_text,
                        'options': option_texts,  # Just the text, not the letters
                        'correct_answer': correct_answer,
                        'explanation': explanation if explanation else f"The correct answer is {correct_answer}."
                    })
            
            # If no questions were parsed, create a fallback
            if not questions:
                questions = [
                    {
                        'question': 'What is a key concept in the topic we are studying?',
                        'options': ['Concept A', 'Concept B', 'Concept C', 'Concept D'],
                        'correct_answer': 'A',
                        'explanation': 'This is a basic question about the topic.'
                    }
                ]
            
            return questions
            
        except Exception as e:
            print(f"Error parsing quiz output: {e}")
            # Return fallback questions
            return [
                {
                    'question': 'What is an important aspect of this subject?',
                    'options': ['Option A', 'Option B', 'Option C', 'Option D'],
                    'correct_answer': 'A',
                    'explanation': 'This is a fallback question due to parsing error.'
                }
            ]
