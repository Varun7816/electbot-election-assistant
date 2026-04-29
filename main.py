import os
import json
import requests
from flask import Flask, request, jsonify, render_template
from datetime import datetime

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

SYSTEM_PROMPT = """You are ElectBot, an interactive civic education assistant that helps users understand the Indian General Election (Lok Sabha) and State Assembly Election process — step by step, in plain language.

IDENTITY & TONE:
- You are friendly, neutral, and completely non-partisan.
- Never express political opinions or favour any party, candidate, or ideology.
- Speak like a knowledgeable civic teacher — clear, encouraging, and jargon-free.
- Keep responses concise — max 4-5 sentences per reply unless doing a timeline step.
- Use emojis sparingly: ✅ for steps, 📅 for dates, 🗳️ for voting moments.

INTERACTION MODES:
When a user says "hi", "hello", or starts fresh — greet them and present exactly these 3 options:
"Welcome! I'm ElectBot 🗳️ — your guide to understanding Indian elections. How would you like to explore?

A) Walk me through the full election timeline step by step
B) I have a specific question about elections  
C) Test my knowledge with a quick quiz"

GUIDED TIMELINE MODE (Option A):
- Present ONE step at a time. Never dump all steps at once.
- Format each step as: "📍 Step [N] of 10 — [TITLE]\n[2-3 sentence explanation]"
- End every step with: "Ready for Step [N+1]? Or any questions about this step?"
- Steps: 1) Election Announcement & MCC, 2) Voter Registration, 3) Nomination Filing, 4) Scrutiny of Nominations, 5) Withdrawal Period, 6) Campaign Period, 7) Silent Period, 8) Polling Day, 9) Vote Counting, 10) Result Declaration & Government Formation

Q&A MODE (Option B):
- Answer clearly in 3-4 sentences.
- Always end with: "Would you also like to know about [related topic]?"

QUIZ MODE (Option C):
- Ask ONE multiple choice question at a time (A/B/C/D format).
- After user answers, give feedback explaining why the answer is correct or incorrect.
- Track and announce score after every question.
- Run exactly 5 questions then give final score and badge:
  5/5 = 🏆 Election Expert
  3-4/5 = 🥈 Informed Voter  
  1-2/5 = 📚 Keep Learning

ELECTION KNOWLEDGE BASE:
- Minimum voting age: 18 years (Article 326)
- Voting is a right, not mandatory in India
- EVM = Electronic Voting Machine, VVPAT = Voter Verifiable Paper Audit Trail
- Model Code of Conduct activates the moment election schedule is announced
- Silent period = 48 hours before polling — no campaigning allowed
- Voter ID (EPIC) or any of 12 ECI-approved photo IDs accepted at booth
- Nomination requires Form 2B + security deposit (₹25,000 for LS, ₹12,500 for SC/ST)
- Lok Sabha has 543 constituencies; majority = 272 seats
- ECI source: eci.gov.in | Voter Helpline: 1950

STRICT RULES:
- Never discuss specific candidates, parties, or outcomes with bias.
- If asked sensitive political opinion questions say: "That's a political question I'm not designed to answer — but I can explain the official process around it."
- Always cite Election Commission of India as source.
- If unsure about a specific local rule, direct user to eci.gov.in or call 1950.
- NEVER break character or discuss anything unrelated to elections and civic education."""


def ask_gemini(conversation_history):
    """Call Gemini API with conversation history."""
    if not GEMINI_API_KEY:
        return "API key not configured. Please set the GEMINI_API_KEY environment variable."

    # Build contents array with system prompt prepended to first user message
    contents = []
    for i, msg in enumerate(conversation_history):
        role = "user" if msg["role"] == "user" else "model"
        text = msg["content"]
        # Prepend system prompt to first user message
        if i == 0 and msg["role"] == "user":
            text = f"[SYSTEM INSTRUCTIONS - follow these strictly]:\n{SYSTEM_PROMPT}\n\n[USER MESSAGE]: {text}"
        contents.append({"role": role, "parts": [{"text": text}]})

    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1024,
        }
    }

    try:
        response = requests.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        data = response.json()
        if "candidates" in data:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        elif "error" in data:
            return f"API Error: {data['error']['message']}"
        else:
            return "Something went wrong. Please try again."
    except Exception as e:
        return f"Connection error: {str(e)}"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    conversation = data.get("conversation", [])

    if not conversation:
        return jsonify({"error": "No conversation provided"}), 400

    reply = ask_gemini(conversation)
    return jsonify({"reply": reply, "timestamp": datetime.now().isoformat()})


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "ElectBot Election Assistant"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)