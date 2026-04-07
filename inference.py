import os, json, sys
from openai import OpenAI
from env.environment import EmailTriageEnv
from env.models import Action

API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME   = os.environ.get("MODEL_NAME",   "gpt-4o-mini")
HF_TOKEN     = os.environ.get("HF_TOKEN",     "")

client = OpenAI(api_key=HF_TOKEN or "sk-placeholder", base_url=API_BASE_URL)
TASKS = ["task_easy", "task_medium", "task_hard"]

SYSTEM_PROMPT = """You are an email triage agent. Respond ONLY with JSON:
{"category": "<billing|technical|general|spam|urgent>", "priority": "<low|medium|high|critical>", "escalate": <true|false>, "reply_draft": "<reply or empty>"}"""

def call_llm(obs, task_id):
    try:
        r = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"From: {obs.sender}\nSubject: {obs.subject}\nBody: {obs.body}\nTask: {task_id}"}
            ],
            temperature=0.1, max_tokens=512,
        )
        raw = r.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"): raw = raw[4:]
        data = json.loads(raw.strip())
        return Action(
            category=data.get("category","general"),
            priority=data.get("priority","medium"),
            escalate=bool(data.get("escalate",False)),
            reply_draft=data.get("reply_draft","") if task_id=="task_hard" else None,
        )
    except:
        return Action(category="general", priority="medium", escalate=False)

def run_task(task_id):
    env = EmailTriageEnv()
    obs = env.reset(task_id=task_id)
    rewards = []
    step = 0
    print(f"[START] task={task_id}", flush=True)
    while not obs.done:
        step += 1
        action = call_llm(obs, task_id)
        obs, reward, done, info = env.step(action)
        rewards.append(reward.value)
        print(f"[STEP] step={step} reward={reward.value}", flush=True)
    score = round(sum(rewards)/len(rewards), 4) if rewards else 0.0
    print(f"[END] task={task_id} score={score} steps={step}", flush=True)
    return score

def main():
    all_scores = {}
    for task_id in TASKS:
        all_scores[task_id] = run_task(task_id)
    overall = round(sum(all_scores.values())/len(all_scores), 4)
    print(f"[END] task=overall score={overall} steps={len(TASKS)}", flush=True)

if __name__ == "__main__":
    main()
