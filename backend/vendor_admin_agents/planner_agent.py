from openai import OpenAI
import os
import json
import re
from dotenv import load_dotenv
from agents.tracing import trace

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def plan_actions(query: str, context: str = None, structured_data: dict = None, history: list = None, llm_model: str = "gpt-4o-mini"):
    """
    Generate a clean, minimal, and executable UI plan.

    Principles:
    - Follow context strictly (RAG is source of truth)
    - Only include steps necessary for the user request
    - Avoid unnecessary or unrelated steps
    - Keep steps clear and unambiguous for execution
    """

    with trace("planner_agent"):

        history_context = ""
        if history and len(history) > 0:
            history_context = "Recent History:\n" + "\n".join([f"{m['role']}: {m['content']}" for m in history[-3:]])

        prompt = f"""
You are a GENERIC UI automation planner.

Your job is to convert a user request into a sequence of clear, minimal, executable UI steps.

---

CONTEXT USAGE RULE:

You are given CONTEXT (retrieved from system documentation).

- Treat CONTEXT as the source of truth
- Only use information present in CONTEXT
- Do NOT invent steps that are not supported by CONTEXT

---

TASK:

Generate ONLY the steps required to complete the USER REQUEST.

---

{history_context}

---

STRUCTURED DATA (if available):
{json.dumps(structured_data, indent=2) if structured_data else "None"}

🔥 CRITICAL RULE — ENTITY IDENTIFIERS:
- You MUST use the exact "identifier" value provided in the STRUCTURED DATA literally.
- DO NOT alter it, substitute it, or map it to an example identifier found in the CONTEXT.
- If STRUCTURED DATA says identifier="xyz", your generated steps MUST use "xyz" exactly.

---

🔥 STEP RULES (VERY IMPORTANT):

1. Each step MUST represent EXACTLY ONE action
2. Each step must be directly executable by a UI automation system
3. Steps must be deterministic and unambiguous
4. Avoid duplication

---

🔥 CRITICAL RULE — ATOMIC STEPS:

NEVER combine multiple actions in a single step.

✔ CORRECT:
- "Enter name [value]"
- "Enter info [value]"
- "Click [Button Name]"

❌ WRONG:
- "Enter details and click buttons"
- "Fill all form fields"
- "Perform login and navigate"

---

🔥 CRITICAL RULE — EXECUTION SCOPE:

The browser session is already initialized.

DO NOT generate steps like:
- "Open browser"
- "Launch browser"
- "Start browser"

✔ Instead, use:
- "Navigate to <URL>"

Navigation MUST always include a valid URL.

---

🔥 CRITICAL RULE — FORBIDDEN STEPS:

DO NOT generate steps that describe:
- waiting
- delays
- loading
- reviewing
- checking visually
- confirming manually

❌ Examples (FORBIDDEN):
- "Wait for page to load"
- "Wait for action to complete"
- "Wait for users list"
- "Review the list"
- "Check the table"

These are NOT executable actions and MUST NOT be included.

---

🔥 WHAT TO DO INSTEAD:

Use verification steps instead of wait/review steps.

✔ Examples:
- "Verify entity [identifier] exists"
- "Verify entity [identifier] does not exist"

These act as both validation and synchronization.

---

🔥 ACTION CLARITY RULE:

- Each input field MUST be a separate step
- Each click MUST be a separate step
- Do NOT merge actions
- When clicking generic action buttons (like Delete, Edit, or View) that appear multiple times in lists or tables, you MUST contextualize the action with its target entity.
  - ❌ WRONG: "Click Delete"
  - ✔ CORRECT: "Click Delete for user [identifier]"

---

DEPENDENCIES:

If the task requires prerequisites (e.g., access, login, navigation):

- Include them ONLY if they are present in CONTEXT
- Do NOT assume anything not in CONTEXT

---

VALIDATION RULES:

- Include validation ONLY when necessary
- Do NOT validate unrelated entities
- Do NOT repeat validation steps

Typical usage:
- Before action → prevent duplication
- After action → confirm success

---

🔥 LANGUAGE RULES (IMPORTANT FOR EXECUTION):

Use ONLY clear and unambiguous phrases:

✔ "Verify entity [identifier] exists"
✔ "Verify entity [identifier] does not exist"

❌ DO NOT use:
- "Check existence"
- "Verify outcome"
- "Confirm presence"

---

🔥 FINAL SELF-CHECK (MANDATORY):

Before generating output, ensure:

- No wait/review/check steps are present
- No combined actions exist
- All steps are executable
- Steps are minimal and relevant to the user request
- No unrelated entity is referenced

---

OUTPUT FORMAT:

- JSON array of strings
- Each string = one atomic step
- No explanations

---

CONTEXT:
{context if context else "None"}

---

USER REQUEST:
{query}

---

OUTPUT JSON ONLY:
"""

        response = client.chat.completions.create(
            model=llm_model,
            messages=[
                {
                    "role": "system",
                    "content": "You generate minimal, context-driven UI plans."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )

        content = response.choices[0].message.content.strip()

        print("\n[Planner] RAW OUTPUT:\n", content)

        content = re.sub(r"```json|```", "", content).strip()

        try:
            parsed = json.loads(content)

            if not isinstance(parsed, list):
                print("[Planner] Output is not a list")
                return []

            cleaned_steps = [
                step.strip()
                for step in parsed
                if isinstance(step, str) and step.strip()
            ]

            print("\n[Planner] FINAL STEPS:")
            for i, s in enumerate(cleaned_steps, 1):
                print(f"{i}. {s}")

            return cleaned_steps

        except Exception:
            print("[Planner] Failed to parse JSON:", content)
            return []