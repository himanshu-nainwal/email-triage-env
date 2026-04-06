"""
Agent graders for the Email Triage environment.
Each grader scores an action against ground-truth labels, returning 0.0–1.0.
Graders are deterministic and reproducible.
"""

from __future__ import annotations
from typing import Dict, Any
from env.models import Action, Reward


# ── Priority adjacency (for partial credit) ───────────────────────────────────
PRIORITY_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def _priority_score(predicted: str, ground_truth: str) -> float:
    """Partial credit for priority: exact=1.0, off-by-1=0.5, off-by-2+=0.0"""
    diff = abs(PRIORITY_ORDER[predicted] - PRIORITY_ORDER[ground_truth])
    if diff == 0:
        return 1.0
    elif diff == 1:
        return 0.5
    else:
        return 0.0


def _reply_quality_score(reply: str | None, keywords: list[str]) -> float:
    """
    Score reply quality by checking presence of expected semantic keywords.
    Returns 0.0 if no reply provided and keywords are expected.
    Returns 1.0 if no keywords expected (spam, etc.) and no reply given.
    """
    if not keywords:
        # No reply needed (e.g., spam) — penalize if reply is given unnecessarily
        if reply and len(reply.strip()) > 10:
            return 0.8  # Minor penalty for unnecessary reply
        return 1.0

    if not reply or len(reply.strip()) < 20:
        return 0.0

    reply_lower = reply.lower()
    matched = sum(1 for kw in keywords if kw.lower() in reply_lower)
    base_score = matched / len(keywords)

    # Bonus for reply length (shows effort), capped
    length_bonus = min(len(reply.split()) / 80, 0.1)

    return min(base_score + length_bonus, 1.0)


# ── Task Easy Grader ──────────────────────────────────────────────────────────

def grade_easy(action: Action, email: Dict[str, Any]) -> Reward:
    """
    Task 1 — Email Classification.
    Scores: category (70%) + escalation (30%).
    Priority not evaluated in easy task.
    """
    cat_correct = action.category == email["gt_category"]
    esc_correct = action.escalate == email["gt_escalate"]

    cat_score = 1.0 if cat_correct else 0.0
    esc_score = 1.0 if esc_correct else 0.0

    value = round(0.70 * cat_score + 0.30 * esc_score, 4)

    return Reward(
        value=value,
        category_correct=cat_correct,
        priority_correct=False,   # not graded in easy
        escalation_correct=esc_correct,
        reply_quality=0.0,
        breakdown={
            "category": cat_score,
            "escalation": esc_score,
            "weights": {"category": 0.70, "escalation": 0.30},
        },
    )


# ── Task Medium Grader ────────────────────────────────────────────────────────

def grade_medium(action: Action, email: Dict[str, Any]) -> Reward:
    """
    Task 2 — Priority + Classification.
    Scores: category (40%) + priority (40%) + escalation (20%).
    Priority uses partial credit (off-by-1 = 0.5).
    """
    cat_correct  = action.category == email["gt_category"]
    pri_score    = _priority_score(action.priority, email["gt_priority"])
    esc_correct  = action.escalate == email["gt_escalate"]

    cat_score = 1.0 if cat_correct else 0.0
    esc_score = 1.0 if esc_correct else 0.0

    value = round(
        0.40 * cat_score +
        0.40 * pri_score +
        0.20 * esc_score,
        4,
    )

    return Reward(
        value=value,
        category_correct=cat_correct,
        priority_correct=(pri_score == 1.0),
        escalation_correct=esc_correct,
        reply_quality=0.0,
        breakdown={
            "category":   cat_score,
            "priority":   pri_score,
            "escalation": esc_score,
            "weights": {"category": 0.40, "priority": 0.40, "escalation": 0.20},
        },
    )


# ── Task Hard Grader ──────────────────────────────────────────────────────────

def grade_hard(action: Action, email: Dict[str, Any]) -> Reward:
    """
    Task 3 — Full Triage with Reply.
    Scores: category (25%) + priority (25%) + escalation (20%) + reply (30%).
    All components matter. Reply quality uses keyword matching.
    """
    cat_correct = action.category == email["gt_category"]
    pri_score   = _priority_score(action.priority, email["gt_priority"])
    esc_correct = action.escalate == email["gt_escalate"]
    rep_score   = _reply_quality_score(action.reply_draft, email["gt_reply_keywords"])

    cat_score = 1.0 if cat_correct else 0.0
    esc_score = 1.0 if esc_correct else 0.0

    value = round(
        0.25 * cat_score +
        0.25 * pri_score +
        0.20 * esc_score +
        0.30 * rep_score,
        4,
    )

    return Reward(
        value=value,
        category_correct=cat_correct,
        priority_correct=(pri_score == 1.0),
        escalation_correct=esc_correct,
        reply_quality=rep_score,
        breakdown={
            "category":  cat_score,
            "priority":  pri_score,
            "escalation": esc_score,
            "reply":     rep_score,
            "weights": {
                "category":   0.25,
                "priority":   0.25,
                "escalation": 0.20,
                "reply":      0.30,
            },
        },
    )


# ── Dispatcher ────────────────────────────────────────────────────────────────

GRADERS = {
    "task_easy":   grade_easy,
    "task_medium": grade_medium,
    "task_hard":   grade_hard,
}


def grade(task_id: str, action: Action, email: Dict[str, Any]) -> Reward:
    """Route to the correct grader based on task_id."""
    grader = GRADERS.get(task_id)
    if grader is None:
        raise ValueError(f"Unknown task_id: {task_id!r}. Valid: {list(GRADERS)}")
    return grader(action, email)
