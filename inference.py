"""
inference.py — Baseline inference script for Email Triage OpenEnv.

Uses the OpenAI client to run a model against all 3 tasks.
Emits structured [START], [STEP], [END] stdout logs per spec.

Required env vars:
  API_BASE_URL  — LLM API base URL
  MODEL_NAME    — model identifier
  HF_TOKEN      — Hugging Face / API key
"""

from __future__ import annotations
import os
import json
import time
import sys
from typing import Optional

from openai import OpenAI

# ── Import env directly (no server needed for inference) ──────────────────────
from env.environment import EmailTriageEnv
from env.models import Action

# ── Config from env vars ──────────────────────────────────────────────────────
API_BASE_URL: str = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME:   str = os.environ.get("MODEL_NAME",   "gpt-4o-mini")
HF_TOKEN:     str = os.environ.get("HF_TOKEN",     "")

if not HF_TOKEN:
    print("WARNING: HF_TOKEN not set. Set it as an environment variable.", file=sys.stderr)

client = OpenAI(api_key=HF_TOKEN or "sk-placeholder", base_url=API_BASE_URL)

TASKS = ["task_easy", "task_medium", "task_hard"]

SYSTEM_PROMPT = """You are an expert email triage agent for a B2B SaaS company.

For each email, you must respond with a JSON object containing exactly these fields:
{
  "category": "<billing|technical|general|spam|urgent>",
  "priority": "<low|medium|high|critical>",
  "escalate": <true|false>,
  "reply_draft": "<your reply text or empty string>"
}

Guidelines:
- category: billing (payment/invoice), technical (bugs/errors/access), general (feedback/requests), spam (unsolicited/promotional), urgent (legal/security/critical outages)
- priority: low (no urgency), medium (respond within 24h), high (respond within 4h), critical (respond immediately)
- escalate: true if requires human/manager intervention (legal threats, security issues, VIP clients, multi-month unresolved issues)
- reply_draft: professional, empathetic reply. Empty string for spam. Required for task_hard.

Always return ONLY valid JSON, no markdown, no extra text."""


def build_user_prompt(obs) -> str:
    thread = "\n".join(obs.thread_history) if obs.thread_history else "None"
    return f"""EMAIL TO TRIAGE:
From: {obs.sender}
Subject: {obs.subject}

Body:
{obs.body}

Thread History:
{thread}

Task: {obs.task_id}
Email {obs.inbox_metadata.current_index + 1} of {obs.inbox_metadata.total_emails}

Respond with JSON only."""


def call_llm(user_prompt: str, task_id: str) -> Optional[Action]:
    """Call the LLM and parse the response into an Action."""
    need_reply = (task_id == "task_hard")
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=512,
        )
        raw = response.choices[0].message.content.strip()

        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        data = json.loads(raw)
        return Action(
            category=data.get("category", "general"),
            priority=data.get("priority", "medium"),
            escalate=bool(data.get("escalate", False)),
            reply_draft=data.get("reply_draft", "") if need_reply else None,
        )
    except Exception as e:
        print(f"  [LLM ERROR] {e}", file=sys.stderr)
        # Fallback action
        return Action(category="general", priority="medium", escalate=False, reply_draft=None)


def run_task(task_id: str) -> dict:
    """Run a full episode for one task. Returns summary dict."""
    env = EmailTriageEnv()
    obs = env.reset(task_id=task_id)

    episode_rewards = []
    steps_log = []
    step_num = 0

    while not obs.done:
        step_num += 1
        user_prompt = build_user_prompt(obs)
        action = call_llm(user_prompt, task_id)

        obs_next, reward, done, info = env.step(action)

        step_log = {
            "step": step_num,
            "email_id":   info["email_id"],
            "action": {
                "category": action.category,
                "priority":  action.priority,
                "escalate":  action.escalate,
                "reply_len": len(action.reply_draft or ""),
            },
            "reward":      reward.value,
            "running_avg": info["running_avg"],
            "breakdown":   reward.breakdown,
        }

        # ── [STEP] log ────────────────────────────────────────────────────────
        print(json.dumps({"event": "STEP", **step_log}))
        sys.stdout.flush()

        episode_rewards.append(reward.value)
        steps_log.append(step_log)
        obs = obs_next

    final_score = round(sum(episode_rewards) / len(episode_rewards), 4) if episode_rewards else 0.0

    return {
        "task_id":     task_id,
        "num_steps":   step_num,
        "final_score": final_score,
        "scores":      episode_rewards,
        "steps":       steps_log,
    }


def main():
    all_results = {}
    total_start = time.time()

    # ── [START] ───────────────────────────────────────────────────────────────
    print(json.dumps({
        "event":   "START",
        "model":   MODEL_NAME,
        "tasks":   TASKS,
        "api_base": API_BASE_URL,
    }))
    sys.stdout.flush()

    for task_id in TASKS:
        print(json.dumps({"event": "TASK_START", "task_id": task_id}))
        sys.stdout.flush()

        task_start = time.time()
        result = run_task(task_id)
        result["elapsed_seconds"] = round(time.time() - task_start, 2)

        all_results[task_id] = result

        print(json.dumps({
            "event":         "TASK_END",
            "task_id":       task_id,
            "final_score":   result["final_score"],
            "num_steps":     result["num_steps"],
            "elapsed":       result["elapsed_seconds"],
        }))
        sys.stdout.flush()

    overall_score = round(
        sum(r["final_score"] for r in all_results.values()) / len(all_results), 4
    )
    total_elapsed = round(time.time() - total_start, 2)

    # ── [END] ─────────────────────────────────────────────────────────────────
    print(json.dumps({
        "event":         "END",
        "overall_score": overall_score,
        "task_scores": {
            tid: r["final_score"] for tid, r in all_results.items()
        },
        "total_elapsed_seconds": total_elapsed,
        "model": MODEL_NAME,
    }))
    sys.stdout.flush()

    # Also print a human-readable summary to stderr
    print("\n" + "="*60, file=sys.stderr)
    print("BASELINE INFERENCE RESULTS", file=sys.stderr)
    print("="*60, file=sys.stderr)
    for task_id, result in all_results.items():
        print(f"  {task_id:15s}: {result['final_score']:.4f}  ({result['num_steps']} steps)", file=sys.stderr)
    print(f"  {'OVERALL':15s}: {overall_score:.4f}", file=sys.stderr)
    print("="*60, file=sys.stderr)


if __name__ == "__main__":
    main()
