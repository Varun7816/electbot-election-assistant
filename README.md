# ElectBot — Indian Election Education Assistant

> Built for **hACK2skill PromptWars Challenge 2**

An AI-powered chatbot that helps Indian citizens understand the complete Lok Sabha election process — interactively, step by step, with WhatsApp-style tap options.

## Live Demo
https://electbot-election-assistant-git-754321216116.asia-south2.run.app

## GitHub
https://github.com/Varun7816/electbot-election-assistant

---

## Features
- 📍 10-step Lok Sabha election timeline (one step at a time)
- 💬 Q&A mode — ask any election question
- 🧠 5-question quiz with score tracking and badge system
- 👆 WhatsApp-style tap options — no typing needed
- ♿ Fully accessible (ARIA labels, keyboard navigation, screen reader support)

---

## Google Services Used

| Service | Purpose | Integration |
|---------|---------|-------------|
| **Gemini API** (generativelanguage.googleapis.com) | Core AI — powers all conversations, quiz, timeline | REST API via `requests` |
| **Firebase Firestore** (google.cloud.firestore) | Logs chat conversations for analytics | Firestore REST API + Cloud Run metadata token |
| **Cloud Run** | Serverless deployment, auto-scaling | Dockerfile deployment |
| **Vertex AI** | Prompt validation and model behaviour testing | Vertex AI Studio |
| **Cloud Build** | CI/CD pipeline — auto-deploy on GitHub push | Build triggers |
| **Anti Gravity** | App scaffolding and initial code generation | Prompt-based generation |

---

## Architecture

```
User Browser
     │
     ▼
Cloud Run (Flask App)
     │
     ├── GET  /          → Serve chat UI (index.html)
     ├── POST /chat      → Call Gemini API → Log to Firestore
     ├── GET  /health    → Health check (Google services status)
     └── GET  /metrics   → Usage metrics
     │
     ├── Gemini API (generativelanguage.googleapis.com)
     │   └── gemini-2.5-flash model
     │
     └── Firebase Firestore
         └── conversations collection
```

---

## Security Features
- ✅ Input sanitization (XSS prevention via regex)
- ✅ Rate limiting (10 requests/minute per IP)
- ✅ Conversation structure validation
- ✅ Content length limits (2000 chars)
- ✅ Role validation (only user/assistant allowed)
- ✅ API keys stored in Cloud Run environment variables
- ✅ No secrets in codebase or GitHub
- ✅ Safety settings on Gemini API calls
- ✅ Proper HTTP error handlers (400, 404, 405, 429, 500)

---

## Accessibility Features
- ✅ Skip navigation link for keyboard users
- ✅ ARIA labels on all interactive elements
- ✅ `role="main"`, `role="banner"`, `role="contentinfo"` landmarks
- ✅ `aria-live="polite"` for screen reader announcements
- ✅ `aria-hidden="true"` on decorative elements
- ✅ Focus management on option buttons
- ✅ `prefers-reduced-motion` media query
- ✅ Keyboard navigable (Tab, Enter support)
- ✅ High contrast saffron/navy color scheme
- ✅ `<label>` element for textarea

---

## Running Tests

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest test_main.py -v

# Run specific test class
pytest test_main.py::TestSanitizeInput -v
pytest test_main.py::TestValidateConversation -v
pytest test_main.py::TestRoutes -v
```

### Test Coverage
- `TestSanitizeInput` — 11 tests (XSS prevention, input handling)
- `TestValidateConversation` — 13 tests (security, data integrity)
- `TestRoutes` — 16 tests (Cloud Run route compatibility)
- **Total: 40 tests**

---

## Project Structure

```
electbot-election-assistant/
├── main.py              # Flask app + Gemini + Firestore integration
├── test_main.py         # 40 pytest tests
├── pytest.ini           # Test configuration
├── requirements.txt     # Python dependencies
├── Dockerfile           # Cloud Run container config
├── README.md            # This file
├── .gitignore           # Protects secrets
└── templates/
    └── index.html       # Chat UI with ARIA accessibility
```

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google AI Studio API key | ✅ Yes |
| `GEMINI_URL` | Gemini model endpoint | No (has default) |
| `FIREBASE_PROJECT_ID` | Firebase project ID | No |
| `PORT` | Server port | No (default: 8080) |

---

## Prompt Evolution

| Version | Changes | Who Designed |
|---------|---------|-------------|
| V1 | Generic "answer election questions" | Human |
| V2 | Added A/B/C interaction modes | Human + Gemini |
| V3 | Added neutrality guardrails | Human |
| V4 | Shortened prompt + structured knowledge base | Human + Gemini |

**Gemini handled:** Quiz flow logic, follow-up question suggestions
**Human designed:** Neutrality rules, election knowledge base, deployment architecture

---

## Deployment

```bash
# Deploy to Cloud Run
gcloud run deploy electbot-election-assistant-git \
  --source . \
  --region asia-south2 \
  --set-env-vars GEMINI_API_KEY=your_key_here \
  --allow-unauthenticated \
  --project your-project-id
```
