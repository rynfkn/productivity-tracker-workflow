Classify the user's response regarding their activity.

Intent options:
- **done** — The user confirms the activity is completed.
- **reschedule** — The user wants to postpone or reschedule the activity. Extract a new deadline if provided.
- **failed** — The user did not complete the activity or the response is unclear.

Rules:
- If intent is **reschedule**, set `new_deadline` to an ISO-8601 datetime string when possible, otherwise `null`.
- If intent is **done** or **failed**, set `new_deadline` to `null`.

Reply with valid JSON only (no extra text):

```json
{"intent": "done|reschedule|failed", "confidence": 0.0, "reason": "...", "new_deadline": null}
```

User response: "{user_text}"
