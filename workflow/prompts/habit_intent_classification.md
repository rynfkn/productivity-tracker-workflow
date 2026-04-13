Classify the user's response regarding whether they completed a habit.

Intent options:
- **done** — The user confirms they completed the habit (yes, done, finished, completed, did it, etc.).
- **missed** — The user did not complete the habit, or the response is unclear or negative (no, didn't, forgot, missed, skip, nope, etc.).

Rules:
- Habits cannot be rescheduled. If the user mentions rescheduling, treat it as **missed**.
- If intent is **done** or **missed**, set `new_deadline` to `null`.

Reply with valid JSON only (no extra text):

```json
{"intent": "done|missed", "confidence": 0.0, "reason": "...", "new_deadline": null}
```

User response: "{user_text}"
