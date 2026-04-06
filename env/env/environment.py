"""
EmailTriageEnv — Core OpenEnv environment implementation.

Implements the OpenEnv interface:
  - reset(task_id) -> Observation
  - step(action)   -> (Observation, Reward, done, info)
  - state()        -> EnvironmentState
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Tuple, Dict, Any

from env.models import Action, Observation, Reward, EnvironmentState, InboxMetadata
from env.graders import grade
from env.data import (
    EMAIL_LOOKUP,
    TASK_EASY_IDS,
    TASK_MEDIUM_IDS,
    TASK_HARD_IDS,
)

TASK_EMAIL_MAP: Dict[str, list] = {
    "task_easy":   TASK_EASY_IDS,
    "task_medium": TASK_MEDIUM_IDS,
    "task_hard":   TASK_HARD_IDS,
}

MAX_STEPS: Dict[str, int] = {
    "task_easy":   10,
    "task_medium": 15,
    "task_hard":   20,
}


class EmailTriageEnv:
    """
    Email Triage OpenEnv Environment.

    An AI agent works through a batch of business emails, making
    classification, prioritization, escalation, and reply decisions.
    """

    def __init__(self) -> None:
        self._task_id: str = "task_easy"
        self._email_ids: list[str] = []
        self._current_index: int = 0
        self._scores: list[float] = []
        self._done: bool = True
        self._step_count: int = 0
        self._max_steps: int = 10

    # ── OpenEnv Interface ─────────────────────────────────────────────────────

    def reset(self, task_id: str = "task_easy") -> Observation:
        """
        Reset the environment for a new episode.

        Args:
            task_id: One of 'task_easy', 'task_medium', 'task_hard'

        Returns:
            Initial Observation (first email in the batch)
        """
        if task_id not in TASK_EMAIL_MAP:
            raise ValueError(
                f"Unknown task_id {task_id!r}. Valid: {list(TASK_EMAIL_MAP)}"
            )

        self._task_id      = task_id
        self._email_ids    = list(TASK_EMAIL_MAP[task_id])
        self._current_index = 0
        self._scores       = []
        self._done         = False
        self._step_count   = 0
        self._max_steps    = MAX_STEPS[task_id]

        return self._make_observation()

    def step(self, action: Action) -> Tuple[Observation, Reward, bool, Dict[str, Any]]:
        """
        Process the agent's action for the current email.

        Args:
            action: Agent's triage decision

        Returns:
            (next_observation, reward, done, info)
        """
        if self._done:
            raise RuntimeError("Episode is done. Call reset() to start a new episode.")

        # Grade the action
        current_email = EMAIL_LOOKUP[self._email_ids[self._current_index]]
        reward = grade(self._task_id, action, current_email)
        self._scores.append(reward.value)
        self._step_count += 1

        # Advance
        self._current_index += 1
        all_processed = self._current_index >= len(self._email_ids)
        max_steps_hit = self._step_count >= self._max_steps
        self._done = all_processed or max_steps_hit

        obs = self._make_observation()

        info = {
            "email_id":       current_email["id"],
            "step":           self._step_count,
            "running_avg":    round(sum(self._scores) / len(self._scores), 4),
            "episode_done":   self._done,
            "termination":    (
                "all_processed" if all_processed
                else "max_steps" if max_steps_hit
                else "in_progress"
            ),
        }

        return obs, reward, self._done, info

    def state(self) -> EnvironmentState:
        """Return the current internal state of the environment."""
        return EnvironmentState(
            task_id=self._task_id,
            email_ids=self._email_ids,
            current_index=self._current_index,
            scores=list(self._scores),
            done=self._done,
            step_count=self._step_count,
            max_steps=self._max_steps,
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _make_observation(self) -> Observation:
        """Build the Observation for the current email."""
        if self._done or self._current_index >= len(self._email_ids):
            # Terminal observation
            return Observation(
                email_id="__done__",
                subject="",
                body="",
                sender="",
                timestamp=datetime.now(timezone.utc).isoformat(),
                thread_history=[],
                inbox_metadata=InboxMetadata(
                    total_emails=len(self._email_ids),
                    current_index=self._current_index,
                    processed=len(self._scores),
                ),
                task_id=self._task_id,
                done=True,
            )

        email = EMAIL_LOOKUP[self._email_ids[self._current_index]]
        return Observation(
            email_id=email["id"],
            subject=email["subject"],
            body=email["body"],
            sender=email["sender"],
            timestamp=datetime.now(timezone.utc).isoformat(),
            thread_history=email.get("thread_history", []),
            inbox_metadata=InboxMetadata(
                total_emails=len(self._email_ids),
                current_index=self._current_index,
                processed=len(self._scores),
            ),
            task_id=self._task_id,
            done=False,
        )

    def episode_score(self) -> float:
        """Return the mean reward over the episode so far."""
        if not self._scores:
            return 0.0
        return round(sum(self._scores) / len(self._scores), 4)
