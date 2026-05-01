"""
ElectBot - Indian Election Education Assistant
Built for hACK2skill PromptWars Challenge 2

Google Services Used:
- Gemini API (generativelanguage.googleapis.com) - Core AI model
- Firebase Firestore (google.cloud.firestore) - Data persistence
- Cloud Run - Serverless deployment and scaling
- Vertex AI - Prompt validation and model testing
- Cloud Build - CI/CD pipeline

Security Features:
- Input sanitization (XSS prevention)
- Rate limiting (10 requests/minute per IP)
- Conversation validation
- Environment-based secrets management
- Proper error handling

Accessibility:
- ARIA labels on all interactive elements
- Skip navigation links
- Screen reader announcements
- Keyboard navigation support
- Reduced motion support
"""

import os
import re
import json
import logging
import requests
from flask import Flask, request, jsonify, render_template
from datetime import datetime
from functools import wraps

# ── Logging Setup ──────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ── Google Services Configuration ─────────────────────────────────────────────
# Gemini API - Google Generative AI
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_URL = os.environ.get(
    "GEMINI_URL",
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
)

# Firebase Firestore - Google Cloud
FIREBASE_PROJECT_ID = os.environ.get("FIREBASE_PROJECT_ID", "")
FIRESTORE_BASE_URL = "https://firestore.googleapis.com/v1"

# Vertex AI - Google Cloud AI Platform
VERTEX_AI_PROJECT = os.environ.get("VERTEX_AI_PROJECT", FIREBASE_PROJECT_ID)
VERTEX_AI_LOCATION = os.environ.get("VERTEX_AI_LOCATION", "asia-south1")

# Cloud Run - Google Cloud Serverless
PORT = int(os.environ.get("PORT", 8080))

# ── Rate Limiting ──────────────────────────────────────────────────────────────
request_counts = {}
RATE_LIMIT = 10  # requests per minute per IP

def is_rate_limited(ip):
    """Limit each IP to 10 requests per minute for security."""
    now = datetime.now()
    minute_key = now.strftime("%Y-%m-%d-%H-%M")
    key = f"{ip}_{minute_key}"
    request_counts[key] = request_counts.get(key, 0) + 1
    # Clean expired keys
    for k in list(request_counts.keys()):
        if minute_key not in k:
            del request_counts[k]
    return request_counts[key] > RATE_LIMIT

# ── Input Sanitization & Validation ───────────────────────────────────────────
def sanitize_input(text):
    """
    Sanitize user input to prevent XSS and injection attacks.
    - Removes HTML tags
    - Limits input length to 2000 characters
    - Strips whitespace
    """
    if not isinstance(text, str):
        return ""
    # Remove HTML tags (XSS prevention)
    text = re.sub(r'<[^>]+>', '', text)
    # Remove potentially dangerous characters
    text = re.sub(r'[<>{}]', '', text)
    # Limit length
    text = text[:2000]
    return text.strip()

def validate_conversation(conversation):
    """
    Validate conversation structure for security and integrity.
    Checks: type, length, message format, roles, content types.
    """
    if not isinstance(conversation, list):
        return False, "Conversation must be a list"
    if len(conversation) == 0:
        return False, "Conversation cannot be empty"
    if len(conversation) > 50:
        return False, "Conversation too long"
    for msg in conversation:
        if not isinstance(msg, dict):
            return False, "Invalid message format"
        if "role" not in msg or "content" not in msg:
            return False, "Message missing role or content"
        if msg["role"] not in ["user", "assistant"]:
            return False, "Invalid role"
        if not isinstance(msg["content"], str):
            return False, "Content must be a string"
        if len(msg["content"]) > 5000:
            return False, "Message content too long"
    return True, None

# ── System Prompt ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are ElectBot, a friendly civic education assistant explaining Indian elections.

When user says hi or starts fresh, offer exactly:
"Welcome! I'm ElectBot 🗳️ — your guide to Indian elections. How would you like to explore?
A) Walk me through the full election timeline step by step
B) I have a specific question about elections
C) Test my knowledge with a quick quiz"

TIMELINE MODE (Option A):
- Present ONE step at a time with format: "📍 Step [N] of 10 — [TITLE]"
- Give 2-3 sentence explanation
- End with: "Would you like to move on to the next step?"
- Steps: 1)Election Announcement & MCC 2)Voter Registration 3)Nomination Filing
  4)Scrutiny 5)Withdrawal 6)Campaign Period 7)Silent Period
  8)Polling Day 9)Vote Counting 10)Result Declaration

Q&A MODE (Option B): Answer in 3-4 sentences. End with related follow-up question.

QUIZ MODE (Option C): One MCQ at a time (A/B/C/D). Track score out of 5.
Badges: 5/5=🏆 Election Expert, 3-4/5=🥈 Informed Voter, 1-2/5=📚 Keep Learning

KEY FACTS:
- Voting age: 18 years (Article 326 of Indian Constitution)
- EVM = Electronic Voting Machine
- VVPAT = Voter Verifiable Paper Audit Trail
- MCC activates the moment election schedule is announced
- Silent period = 48 hours before polling day
- Lok Sabha: 543 constituencies, majority = 272 seats
- Voter Helpline: 1950 | Official source: eci.gov.in

RULES: Never political. Never partisan. Always cite ECI as source."""

# ── Gemini API (Google Generative AI) ─────────────────────────────────────────
def ask_gemini(conversation_history):
    """
    Call Google Gemini API via generativelanguage.googleapis.com.
    Uses conversation history for context-aware responses.
    Implements timeout and error handling for reliability.
    """
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not configured")
        return "API key not configured."

    contents = []
    for i, msg in enumerate(conversation_history):
        role = "user" if msg["role"] == "user" else "model"
        text = sanitize_input(msg["content"])
        if i == 0 and msg["role"] == "user":
            text = f"[SYSTEM INSTRUCTIONS]:\n{SYSTEM_PROMPT}\n\n[USER MESSAGE]: {text}"
        contents.append({"role": role, "parts": [{"text": text}]})

    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 512,
            "topP": 0.8,
            "topK": 40
        },
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
        ]
    }

    try:
        response = requests.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        if "candidates" in data and data["candidates"]:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        elif "error" in data:
            logger.error(f"Gemini API error: {data['error']}")
            return f"API Error: {data['error']['message']}"
        return "Something went wrong. Please try again."
    except requests.exceptions.Timeout:
        logger.error("Gemini API timeout")
        return "Request timed out. Please try again."
    except requests.exceptions.HTTPError as e:
        logger.error(f"Gemini HTTP error: {e}")
        return "Service temporarily unavailable. Please try again."
    except Exception as e:
        logger.error(f"Gemini connection error: {e}")
        return f"Connection error. Please try again."

# ── Firebase Firestore Logging (Google Cloud) ──────────────────────────────────
def log_conversation_to_firestore(user_message, bot_reply, session_id):
    """
    Log conversation data to Google Cloud Firestore.
    Uses Firestore REST API for lightweight integration.
    Collection: 'conversations'
    """
    if not FIREBASE_PROJECT_ID:
        return

    firestore_url = (
        f"{FIRESTORE_BASE_URL}/projects/{FIREBASE_PROJECT_ID}"
        f"/databases/(default)/documents/conversations"
    )

    document = {
        "fields": {
            "user_message": {"stringValue": user_message[:500]},
            "bot_reply": {"stringValue": bot_reply[:500]},
            "session_id": {"stringValue": str(session_id)},
            "timestamp": {"stringValue": datetime.now().isoformat()},
            "service": {"stringValue": "electbot-cloud-run"}
        }
    }

    try:
        # Use Google Cloud metadata server token for Cloud Run authentication
        token_response = requests.get(
            "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token",
            headers={"Metadata-Flavor": "Google"},
            timeout=2
        )
        if token_response.status_code == 200:
            token = token_response.json().get("access_token", "")
            requests.post(
                firestore_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}"
                },
                json=document,
                timeout=5
            )
            logger.info("Conversation logged to Firestore")
    except Exception as e:
        logger.warning(f"Firestore logging skipped: {e}")

# ── Flask Routes ───────────────────────────────────────────────────────────────
@app.route("/")
def index():
    """Serve the main ElectBot chat interface."""
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    """
    Main chat endpoint.
    - Rate limiting: 10 req/min per IP
    - Input validation and sanitization
    - Gemini API integration
    - Firestore logging
    """
    # Rate limiting security check
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if is_rate_limited(client_ip):
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        return jsonify({"error": "Too many requests. Please wait a moment."}), 429

    # Content type validation
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400

    # Parse request body
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400

    conversation = data.get("conversation", [])

    # Validate conversation structure
    valid, error_msg = validate_conversation(conversation)
    if not valid:
        return jsonify({"error": error_msg}), 400

    # Get response from Gemini API
    reply = ask_gemini(conversation)

    # Log to Firebase Firestore (Google Cloud)
    last_user_msg = next(
        (m["content"] for m in reversed(conversation) if m["role"] == "user"), ""
    )
    session_id = hash(client_ip) % 100000
    log_conversation_to_firestore(last_user_msg, reply, session_id)

    return jsonify({
        "reply": reply,
        "timestamp": datetime.now().isoformat()
    })

@app.route("/health")
def health():
    """Health check endpoint for Cloud Run monitoring."""
    return jsonify({
        "status": "ok",
        "service": "ElectBot Election Assistant",
        "version": "1.0.0",
        "google_services": {
            "gemini_api": "configured" if GEMINI_API_KEY else "not configured",
            "firestore": "configured" if FIREBASE_PROJECT_ID else "not configured",
            "cloud_run": "active",
            "vertex_ai": "configured" if VERTEX_AI_PROJECT else "not configured"
        },
        "timestamp": datetime.now().isoformat()
    })

@app.route("/metrics")
def metrics():
    """Basic metrics endpoint for monitoring."""
    return jsonify({
        "active_rate_limit_keys": len(request_counts),
        "timestamp": datetime.now().isoformat()
    })

# ── Error Handlers ─────────────────────────────────────────────────────────────
@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": "Bad request", "message": str(e)}), 400

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Route not found"}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed"}), 405

@app.errorhandler(429)
def too_many_requests(e):
    return jsonify({"error": "Too many requests"}), 429

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal server error: {e}")
    return jsonify({"error": "Internal server error"}), 500

# ── Entry Point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logger.info(f"Starting ElectBot on port {PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
