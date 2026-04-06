"""
Typed Pydantic models for the Email Triage OpenEnv environment.
Implements the OpenEnv spec: Observation, Action, Reward.
"""

from __future__ import annotations
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


# ── Observation ───────────────────────────────────────────────────────────────

class InboxMetadata(BaseModel):
    total_emails: int = Field(description="Total emails in the current task batch")
    current_index: int = Field(description="Index of current email (0-based)")
    processed: int = Field(description="Number of emails processed so far")


class Observation(BaseModel):
    email_id: str = Field(description="Unique ID of the current email")
    subject: str = Field(description="Email subject line")
    body: str = Field(description="Full email body text")
    sender: str = Field(description="Sender email address")
    timestamp: str = Field(description="ISO timestamp of the email")
    thread_history: List[str] = Field(
        default_factory=list,
        description="Previous messages in the thread (oldest first)",
    )
    inbox_metadata: InboxMetadata = Field(description="Metadata about the inbox state")
    task_id: str = Field(description="Current task identifier")
    done: bool = Field(default=False, description="Whether the episode is complete")


# ── Action ────────────────────────────────────────────────────────────────────

CategoryType  = Literal["billing", "technical", "general", "spam", "urgent"]
PriorityType  = Literal["low", "medium", "high", "critical"]


class Action(BaseModel):
    category: CategoryType = Field(
        description="Email category: billing | technical | general | spam | urgent"
    )
    priority: PriorityType = Field(
        description="Email priority: low | medium | high | critical"
    )
    reply_draft: Optional[str] = Field(
        default=None,
        description="Draft reply text (required for task_hard, optional otherwise)",
    )
    escalate: bool = Field(
        default=False,
        description="Whether to escalate this email to a human agent",
    )


# ── Reward ────────────────────────────────────────────────────────────────────

class Reward(BaseModel):
    value: float = Field(ge=0.0, le=1.0, description="Reward signal for this step [0.0, 1.0]")
    category_correct: bool = Field(description="Whether category was correctly classified")
    priority_correct: bool = Field(description="Whether priority was correctly assigned")
    escalation_correct: bool = Field(description="Whether escalation decision was correct")
    reply_quality: float = Field(
        ge=0.0, le=1.0,
        description="Quality score of the reply draft (0.0 if not applicable)",
    )
    breakdown: dict = Field(
        default_factory=dict,
        description="Detailed score breakdown per component",
    )


# ── State ─────────────────────────────────────────────────────────────────────

class EnvironmentState(BaseModel):
    task_id: str
    email_ids: List[str]
    current_index: int
    scores: List[float]
    done: bool
    step_count: int
    max_steps: int
