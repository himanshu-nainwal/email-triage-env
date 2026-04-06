"""
FastAPI server exposing the EmailTriageEnv via HTTP.
Endpoints: POST /reset, POST /step, GET /state, GET /health
"""

from __future__ import annotations
import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from env.environment import EmailTriageEnv
from env.models import Action, Observation, Reward, EnvironmentState

app = FastAPI(
    title="Email Triage OpenEnv",
    description="Real-world email triage environment for AI agent training and evaluation.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

env = EmailTriageEnv()


class ResetRequest(BaseModel):
    task_id: str = "task_easy"


class StepResponse(BaseModel):
    observation: Observation
    reward: Reward
    done: bool
    info: dict


@app.get("/health")
def health():
    return {"status": "ok", "environment": "email-triage-env", "version": "1.0.0"}


@app.post("/reset", response_model=Observation)
def reset(request: Optional[ResetRequest] = None):
    try:
        task_id = request.task_id if request else "task_easy"
        obs = env.reset(task_id=task_id)
        return obs
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/step", response_model=StepResponse)
def step(action: Action):
    try:
        obs, reward, done, info = env.step(action)
        return StepResponse(observation=obs, reward=reward, done=done, info=info)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/state", response_model=EnvironmentState)
def state():
    return env.state()


@app.get("/score")
def score():
    return {"episode_score": env.episode_score(), "scores": env.state().scores}


@app.get("/tasks")
def list_tasks():
    return {
        "tasks": [
            {"id": "task_easy", "name": "Email Classification", "difficulty": "easy",
             "description": "Classify emails into correct categories", "max_steps": 10, "num_emails": 5},
            {"id": "task_medium", "name": "Priority + Classification", "difficulty": "medium",
             "description": "Correctly classify AND prioritize emails", "max_steps": 15, "num_emails": 5},
            {"id": "task_hard", "name": "Full Triage with Reply", "difficulty": "hard",
             "description": "Classify, prioritize, escalate, AND draft a reply", "max_steps": 20, "num_emails": 5},
        ]
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
