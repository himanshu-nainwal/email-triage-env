"""
Email dataset for the triage environment.
Each email has ground-truth labels for category, priority, escalation, and a reference reply.
"""

EMAILS = [
    # ── EASY / CLEAR-CUT EMAILS ──────────────────────────────────────────────
    {
        "id": "e001",
        "subject": "Invoice #4521 overcharge",
        "sender": "john.doe@company.com",
        "body": (
            "Hi, I was charged $250 on my last invoice but my plan is $199/month. "
            "Please refund the difference. My account ID is 8821."
        ),
        "thread_history": [],
        "gt_category": "billing",
        "gt_priority": "medium",
        "gt_escalate": False,
        "gt_reply_keywords": ["refund", "review", "account", "apologize"],
        "difficulty": "easy",
    },
    {
        "id": "e002",
        "subject": "Win a free iPhone!!!",
        "sender": "promo@totallylegit-offers.xyz",
        "body": (
            "Congratulations! You have been selected to win a free iPhone 15 Pro. "
            "Click here now: http://bit.ly/scam123 to claim your prize!"
        ),
        "thread_history": [],
        "gt_category": "spam",
        "gt_priority": "low",
        "gt_escalate": False,
        "gt_reply_keywords": [],
        "difficulty": "easy",
    },
    {
        "id": "e003",
        "subject": "How do I reset my password?",
        "sender": "alice@startup.io",
        "body": (
            "Hello, I forgot my password and the reset email isn't arriving. "
            "I checked my spam folder too. Can you help?"
        ),
        "thread_history": [],
        "gt_category": "technical",
        "gt_priority": "medium",
        "gt_escalate": False,
        "gt_reply_keywords": ["reset", "email", "check", "steps", "help"],
        "difficulty": "easy",
    },
    {
        "id": "e004",
        "subject": "Just wanted to say thanks!",
        "sender": "happy.customer@gmail.com",
        "body": (
            "Your support team was amazing yesterday. Bob helped me resolve my "
            "issue in under 10 minutes. Keep up the great work!"
        ),
        "thread_history": [],
        "gt_category": "general",
        "gt_priority": "low",
        "gt_escalate": False,
        "gt_reply_keywords": ["thank", "feedback", "team"],
        "difficulty": "easy",
    },
    {
        "id": "e005",
        "subject": "URGENT: Production server is down",
        "sender": "cto@bigclient.com",
        "body": (
            "Our entire production environment is returning 503 errors since 2:00 AM. "
            "We have 50,000 users affected. This is costing us $10k/hour. "
            "We need immediate escalation to your engineering team NOW."
        ),
        "thread_history": [],
        "gt_category": "urgent",
        "gt_priority": "critical",
        "gt_escalate": True,
        "gt_reply_keywords": ["escalat", "engineer", "immediately", "priority", "sorry"],
        "difficulty": "easy",
    },

    # ── MEDIUM / NUANCED EMAILS ───────────────────────────────────────────────
    {
        "id": "m001",
        "subject": "Re: API rate limits",
        "sender": "dev@fintech-startup.com",
        "body": (
            "Following up on my previous ticket. We're hitting rate limits constantly "
            "which is breaking our payment processing pipeline. Our customers are "
            "getting failed transactions. We've been waiting 3 days for a response."
        ),
        "thread_history": [
            "Day 1 - Dev: We're hitting rate limits on the /payments endpoint",
            "Day 2 - Dev: Still no response, this is becoming urgent",
        ],
        "gt_category": "technical",
        "gt_priority": "high",
        "gt_escalate": True,
        "gt_reply_keywords": ["rate limit", "escalat", "apologize", "urgent", "engineer"],
        "difficulty": "medium",
    },
    {
        "id": "m002",
        "subject": "Cancellation and refund request",
        "sender": "frustrated@user.net",
        "body": (
            "I want to cancel my annual subscription immediately. I was promised "
            "a 30-day money-back guarantee but you're telling me I'm outside that window. "
            "I have the original sales email where your rep promised this. "
            "I will dispute this with my credit card company if needed."
        ),
        "thread_history": [],
        "gt_category": "billing",
        "gt_priority": "high",
        "gt_escalate": True,
        "gt_reply_keywords": ["review", "sales", "refund", "escalat", "apolog"],
        "difficulty": "medium",
    },
    {
        "id": "m003",
        "subject": "Feature request: bulk export",
        "sender": "poweruser@enterprise.com",
        "body": (
            "We have 50 team members and manually exporting reports one by one is "
            "inefficient. Can you add bulk CSV export? We're on the Enterprise plan "
            "and this is blocking our quarterly reporting."
        ),
        "thread_history": [],
        "gt_category": "general",
        "gt_priority": "medium",
        "gt_escalate": False,
        "gt_reply_keywords": ["feature", "roadmap", "note", "team", "workaround"],
        "difficulty": "medium",
    },
    {
        "id": "m004",
        "subject": "Security concern with data sharing",
        "sender": "compliance@legalfirm.com",
        "body": (
            "We noticed in your updated privacy policy that user data may be shared "
            "with third-party analytics providers. As a law firm handling privileged "
            "communications, this is a potential compliance issue for us. "
            "We need written clarification urgently before our audit next week."
        ),
        "thread_history": [],
        "gt_category": "urgent",
        "gt_priority": "high",
        "gt_escalate": True,
        "gt_reply_keywords": ["privacy", "compliance", "legal", "escalat", "clarif"],
        "difficulty": "medium",
    },
    {
        "id": "m005",
        "subject": "Login issues after recent update",
        "sender": "beta.tester@techcorp.io",
        "body": (
            "After your update on Tuesday, SSO login stopped working for our entire "
            "organization. We use Okta integration. Error: SAML assertion failed. "
            "Affects 200 users. Can you check if the update broke SAML?"
        ),
        "thread_history": [
            "Tuesday - System: Platform update v3.4.1 deployed",
        ],
        "gt_category": "technical",
        "gt_priority": "high",
        "gt_escalate": True,
        "gt_reply_keywords": ["SSO", "SAML", "Okta", "engineer", "investigate"],
        "difficulty": "medium",
    },

    # ── HARD / AMBIGUOUS / MULTI-SIGNAL EMAILS ───────────────────────────────
    {
        "id": "h001",
        "subject": "Re: Re: Re: Billing dispute + legal notice",
        "sender": "legal@enterprise-client.com",
        "body": (
            "This is our fourth attempt to resolve this. We have been incorrectly billed "
            "$15,000 over the past 6 months due to a bug in your usage metering. "
            "Our legal team has prepared a formal demand letter. We are also considering "
            "going public with this on social media unless resolved within 24 hours. "
            "We expect a call from your VP of Customer Success today."
        ),
        "thread_history": [
            "Month 1 - Client: Billing seems off",
            "Month 3 - Client: Still overbilled, please fix",
            "Month 5 - Client: Escalating this formally",
        ],
        "gt_category": "billing",
        "gt_priority": "critical",
        "gt_escalate": True,
        "gt_reply_keywords": ["escalat", "VP", "legal", "24 hour", "resolve", "apologize", "call"],
        "difficulty": "hard",
    },
    {
        "id": "h002",
        "subject": "Data deletion request under GDPR",
        "sender": "privacy@eu-regulator.org",
        "body": (
            "Under Article 17 of the GDPR, we are formally requesting complete deletion "
            "of all personal data associated with account ID EU-88210. "
            "You have 30 days to comply. Please confirm receipt and provide a deletion "
            "certificate upon completion. Failure to comply may result in regulatory action."
        ),
        "thread_history": [],
        "gt_category": "urgent",
        "gt_priority": "critical",
        "gt_escalate": True,
        "gt_reply_keywords": ["GDPR", "deletion", "confirm", "legal", "comply", "receipt"],
        "difficulty": "hard",
    },
    {
        "id": "h003",
        "subject": "Potential security breach in your system",
        "sender": "security.researcher@ethicalhack.com",
        "body": (
            "I am a security researcher and have discovered a critical SQL injection "
            "vulnerability in your /api/v2/search endpoint that exposes your entire "
            "user database. I have a 30-day responsible disclosure policy. "
            "I am notifying you now. Please acknowledge within 48 hours or I will "
            "publish my findings. I have proof-of-concept code."
        ),
        "thread_history": [],
        "gt_category": "urgent",
        "gt_priority": "critical",
        "gt_escalate": True,
        "gt_reply_keywords": ["security", "team", "48 hour", "acknowledge", "investigate", "thank"],
        "difficulty": "hard",
    },
    {
        "id": "h004",
        "subject": "Account access — deceased user estate",
        "sender": "executor@lawoffice.com",
        "body": (
            "I am the legal executor for the estate of John Smith (account: JS-44012) "
            "who passed away on March 3rd. I am requesting access to download his "
            "business documents stored on your platform for estate proceedings. "
            "I can provide a death certificate and probate court documents."
        ),
        "thread_history": [],
        "gt_category": "general",
        "gt_priority": "high",
        "gt_escalate": True,
        "gt_reply_keywords": ["condolence", "legal", "document", "escalat", "process", "verify"],
        "difficulty": "hard",
    },
    {
        "id": "h005",
        "subject": "Whistleblower: Internal misuse of customer data",
        "sender": "anonymous@protonmail.com",
        "body": (
            "I am a current employee. I have evidence that a senior manager is "
            "accessing customer data without authorization for personal use. "
            "I am afraid of retaliation. Please take this seriously and do not "
            "disclose my identity. I can provide logs and screenshots."
        ),
        "thread_history": [],
        "gt_category": "urgent",
        "gt_priority": "critical",
        "gt_escalate": True,
        "gt_reply_keywords": ["confidential", "serious", "investigate", "HR", "legal", "identity"],
        "difficulty": "hard",
    },
]

TASK_EASY_IDS   = ["e001", "e002", "e003", "e004", "e005"]
TASK_MEDIUM_IDS = ["m001", "m002", "m003", "m004", "m005"]
TASK_HARD_IDS   = ["h001", "h002", "h003", "h004", "h005"]

EMAIL_LOOKUP = {e["id"]: e for e in EMAILS}
