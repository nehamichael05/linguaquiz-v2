from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import anthropic
import os
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

class QuizRequest(BaseModel):
    language: str
    level: str
    count: int = 5

@app.get("/")
def root():
    return {"status": "LinguaQuiz backend is running"}

@app.post("/generate-quiz")
def generate_quiz(request: QuizRequest):
    prompt = f"""Generate {request.count} language learning quiz questions for {request.language} at {request.level} level.

Return ONLY a raw JSON array. No markdown. No backticks. No explanation. Just the array.

Example format:
[{{"type":"translate","question":"How do you say Hello in Spanish?","options":["Hola","Adios","Gracias","Por favor"],"correct":0,"explanation":"Hola means Hello in Spanish"}}]

Rules:
- Exactly 4 options per question
- correct is the index (0, 1, 2, or 3) of the right answer
- Mix these types: translate, reverse, fill, meaning
- beginner = basic greetings/numbers, intermediate = common phrases, advanced = grammar

Return ONLY the JSON array starting with [ and ending with ]"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()

    # Clean markdown if present
    if "```" in raw:
        raw = raw.replace("```json", "").replace("```", "").strip()

    # Extract JSON array
    start = raw.find("[")
    end = raw.rfind("]")
    if start != -1 and end != -1:
        raw = raw[start:end+1]

    try:
        questions = json.loads(raw)
        return {"questions": questions, "language": request.language, "level": request.level}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parse error: {str(e)}")
