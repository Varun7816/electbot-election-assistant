import os
import json
import requests
from flask import Flask, request, jsonify, render_template
from datetime import datetime

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent"

SYSTEM_PROMPT = """You are ElectBot, a friendly 
civic education assistant explaining Indian elections.

When user says hi, offer 3 options:
A) Step-by-step election timeline
B) Ask a question  
C) Take a quiz

For timeline: explain one step at a time, 
ask before moving to next step.
For quiz: one question at a time, track score out of 5.
Always be neutral, never political.
Source: eci.gov.in | Helpline: 1950"""


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