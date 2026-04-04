Classify the user's response regarding their activity.

Intent options:
- **done** — The user confirms the activity is completed.
- **reschedule** — The user wants to postpone or reschedule the activity.
- **failed** — The user did not complete the activity or the response is unclear.

Reply with valid JSON only (no extra text):

```json
{"intent": "done|reschedule|failed", "confidence": 0.0, "reason": "..."}
```

User response: "{user_text}"
