# 📧 Email Triage OpenEnv

> A real-world AI agent environment for email classification, prioritization, escalation, and reply drafting.

[![OpenEnv](https://img.shields.io/badge/OpenEnv-compatible-blue)](https://openenv.dev)
[![HF Spaces](https://img.shields.io/badge/🤗-Hugging%20Face%20Space-yellow)](https://huggingface.co/spaces)
[![Python](https://img.shields.io/badge/python-3.11-blue)](https://python.org)

---

## 🌍 Environment Description

**Email Triage** simulates a real-world business inbox management task — one of the most common and economically valuable workflows in modern operations. Support teams, operations staff, and customer success managers spend significant time triaging emails: identifying what they're about, how urgent they are, whether to escalate, and what to reply.

This environment trains and evaluates agents on the **full triage pipeline**:

1. **Category classification** — Is this a billing issue? A technical bug? Spam?
2. **Priority assessment** — How urgently does this need a response?
3. **Escalation decision** — Should a human manager handle this?
4. **Reply drafting** — Generate a professional, contextually appropriate reply

The environment features **15 carefully crafted emails** spanning real business scenarios: overcharge disputes, production outages, GDPR requests, security vulnerability disclosures, legal threats, and more. Emails range from obvious (clear spam, clear critical outage) to deeply nuanced (ambiguous tone, missing context, multi-turn threads).

---

## 🗂 Project Structure

```
email-triage-env/
├── app.py              # FastAPI HTTP server (OpenEnv API)
├── inference.py        # Baseline inference script (required)
├── openenv.yaml        # Environment metadata & spec
├── requirements.txt
├── Dockerfile
├── env/
│   ├── __init__.py
│   ├── environment.py  # EmailTriageEnv core class
│   ├── models.py       # Pydantic typed models
│   ├── graders.py      # Task graders (deterministic, 0.0–1.0)
│   └── data.py         # Email dataset with ground-truth labels
└── README.md
```

---

## 🔍 Observation Space

Each step provides an `Observation` object:

| Field | Type | Description |
|-------|------|-------------|
| `email_id` | `str` | Unique email identifier |
| `subject` | `str` | Email subject line |
| `body` | `str` | Full email body text |
| `sender` | `str` | Sender email address |
| `timestamp` | `str` | ISO 8601 timestamp |
| `thread_history` | `list[str]` | Prior messages in thread (oldest first) |
| `inbox_metadata.total_emails` | `int` | Total emails in this task batch |
| `inbox_metadata.current_index` | `int` | Index of current email (0-based) |
| `inbox_metadata.processed` | `int` | Emails processed so far |
| `task_id` | `str` | Active task identifier |
| `done` | `bool` | Whether the episode is complete |

---

## ⚡ Action Space

The agent submits an `Action` object per email:

| Field | Type | Options | Description |
|-------|------|---------|-------------|
| `category` | `str` | `billing`, `technical`, `general`, `spam`, `urgent` | Email category |
| `priority` | `str` | `low`, `medium`, `high`, `critical` | Response urgency |
| `escalate` | `bool` | `true` / `false` | Whether to escalate to human agent |
| `reply_draft` | `str\|null` | Any text | Draft reply (required for task_hard) |

---

## 🎯 Tasks

### Task 1 — Email Classification (`task_easy`)
**Difficulty: Easy** | 5 emails | Max 10 steps

The agent must correctly categorize each email. Emails are unambiguous with clear signals.

**Scoring:** `0.70 × category_correct + 0.30 × escalation_correct`

**Expected baseline (GPT-4o-mini):** ~0.82

---

### Task 2 — Priority + Classification (`task_medium`)
**Difficulty: Medium** | 5 emails | Max 15 steps

Emails have nuanced signals (multi-turn threads, implicit urgency, cross-domain cues). The agent must correctly classify AND assign priority.

**Scoring:** `0.40 × category + 0.40 × priority + 0.20 × escalation`

Priority uses **partial credit**: off-by-1 level = 0.5, off-by-2+ = 0.0

**Expected baseline (GPT-4o-mini):** ~0.65

---

### Task 3 — Full Triage with Reply (`task_hard`)
**Difficulty: Hard** | 5 emails | Max 20 steps

Ambiguous, sensitive, and high-stakes emails (legal threats, GDPR requests, whistleblowers, deceased account access, security disclosures). Full triage required including a professional reply draft.

**Scoring:** `0.25 × category + 0.25 × priority + 0.20 × escalation + 0.30 × reply_quality`

Reply quality is scored by semantic keyword matching against expected reply components.

**Expected baseline (GPT-4o-mini):** ~0.55

---

## 🎁 Reward Function

Rewards are **dense** — provided at every step, not just episode end:

- **Partial credit** for priority (off-by-one ladder)
- **Keyword-weighted** reply quality (proportional to matched expected components)
- **Minor penalties** for unnecessary replies to spam emails
- **Length bonus** for reply drafts that show sufficient detail (capped at +0.1)

This ensures agents receive learning signal throughout the trajectory, not just at the end.

---

## 🚀 Setup & Usage

### Local Development

```bash
# 1. Clone and install
git clone <repo>
cd email-triage-env
pip install -r requirements.txt

# 2. Start the server
python app.py
# Server runs at http://localhost:7860

# 3. Test the API
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "task_easy"}'
```

### Docker

```bash
docker build -t email-triage-env .
docker run -p 7860:7860 \
  -e HF_TOKEN=your_key \
  -e MODEL_NAME=gpt-4o-mini \
  -e API_BASE_URL=https://api.openai.com/v1 \
  email-triage-env
```

### Run Baseline Inference

```bash
export HF_TOKEN=your_openai_api_key
export MODEL_NAME=gpt-4o-mini
export API_BASE_URL=https://api.openai.com/v1

python inference.py
```

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/tasks` | List all tasks |
| `POST` | `/reset` | Reset environment, returns first observation |
| `POST` | `/step` | Submit action, returns observation + reward |
| `GET` | `/state` | Current internal state |
| `GET` | `/score` | Current episode score |

### Example: Full Episode

```python
import requests

BASE = "http://localhost:7860"

# Reset
obs = requests.post(f"{BASE}/reset", json={"task_id": "task_hard"}).json()

while not obs["done"]:
    action = {
        "category": "technical",
        "priority": "high",
        "escalate": True,
        "reply_draft": "Thank you for reaching out. We are escalating this immediately..."
    }
    result = requests.post(f"{BASE}/step", json=action).json()
    print(f"Reward: {result['reward']['value']}")
    obs = result["observation"]
```

---

## 📊 Baseline Scores

Scores from running `inference.py` with `gpt-4o-mini`:

| Task | Score | Notes |
|------|-------|-------|
| `task_easy` | 0.82 | High accuracy on clear-cut emails |
| `task_medium` | 0.65 | Struggles with priority nuance |
| `task_hard` | 0.55 | Reply quality and edge cases challenge model |
| **Overall** | **0.67** | |

---

## 🧪 OpenEnv Validation

```bash
openenv validate .
```

Validates: `openenv.yaml` schema, typed models, `step()/reset()/state()` endpoints, Dockerfile.

---

## 🔑 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_BASE_URL` | LLM API base URL | `https://api.openai.com/v1` |
| `MODEL_NAME` | Model identifier | `gpt-4o-mini` |
| `HF_TOKEN` | Hugging Face / OpenAI API key | *(required)* |
| `PORT` | Server port | `7860` |

---

## 💡 Motivation

Email triage is a billion-dollar problem. The average knowledge worker spends 28% of their workweek managing email (McKinsey). This environment provides a principled, reproducible benchmark for evaluating whether LLM agents can handle the nuanced, context-dependent decisions that email triage requires — with meaningful partial credit at every step.

Unlike toy environments, every email here is drawn from realistic business scenarios that support and ops teams encounter daily.
