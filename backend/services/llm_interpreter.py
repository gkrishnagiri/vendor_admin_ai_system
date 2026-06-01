from openai import OpenAI
import os
import json
import re
from dotenv import load_dotenv
from agents.tracing import trace

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def interpret_step(step: str, dom: str, llm_model: str = "gpt-4o-mini"):

    print("\n================ INTERPRETER DEBUG START ================")
    print("[Interpreter] Step:", step)

    dom_snippet = dom[:] if dom else ""

    with trace("llm_interpreter"):

        prompt = f"""
You are a UI automation interpreter.

Convert the given instruction into EXACTLY ONE structured JSON action.

---

SUPPORTED ACTIONS:
click, fill, navigate, verify_present, verify_not_present, error

---

RULES:

1. Return EXACTLY ONE JSON object
2. Do NOT return multiple actions
3. Do NOT include explanations
4. Do NOT hallucinate values not present in the instruction

---

🔥 STRICT TARGET MATCHING RULE (For Interactive Actions):
If the instruction is an action (like click or fill) and specifies an entity (e.g. "for user X"), you MUST locate it in the DOM using an EXACT literal string match.
DO NOT use partial matching or fuzzy selectors. In Playwright, you MUST use exact-match text selectors (like `text="X"` with quotes or `:text-is('X')`).
Example: If the instruction says "for user John" but the DOM only contains "john123", you MUST treat it as a missing target.
If the exact literal target for an action cannot be found in the DOM, you MUST explicitly abort by returning an error: {{"action": "error", "message": "Target not found in DOM"}}

IMPORTANT EXCEPTION: This error abort rule does NOT apply to VERIFY instructions. Verification instructions must ALWAYS output the corresponding verify action, regardless of what is in the DOM.

---

ACTION FORMATS:

NAVIGATE:
{{"action":"navigate","url":"http://..."}}
(Only use navigate if a valid, full HTTP URL is explicitly provided in the instruction. If the instruction says "Navigate to [Page Name]" without a URL, you MUST translate this into a CLICK action targeting that page's link in the DOM. DO NOT hallucinate a partial URL.)

FILL:
{{"action":"fill","selector":"...","value":"..."}}

CLICK:
{{"action":"click","selector":"..."}}

VERIFY PRESENT:
{{"action":"verify_present","text":"..."}}

VERIFY NOT PRESENT:
{{"action":"verify_not_present","text":"..."}}

ERROR (Target not found):
{{"action":"error","message":"..."}}

---

VERIFICATION RULE (IMPORTANT):

- If the instruction indicates something exists (e.g. "Verify X exists") → ALWAYS use "verify_present"
- If the instruction indicates something NOT exists (e.g. "Verify X does not exist") → ALWAYS use "verify_not_present"

DO NOT evaluate the truthfulness of the verification yourself against the DOM. Your ONLY job is to translate the instruction verbatim into the correct action type, regardless of what the DOM shows.

Use the exact identifier/text from the instruction as "text".

---

SELECTOR PRIORITY:

1. data-testid (e.g. data-testid=login-submit-button) - ALWAYS preferred for buttons.
2. placeholder
3. visible text (If clicking by text, you MUST target interactive elements explicitly, e.g. `button:has-text('Create')`. Avoid generic `text='Create User'` as it might accidentally click non-interactive headers).

RELATIONAL SELECTORS:
If the instruction scopes an action to a specific entity (e.g., "Click Delete for user john123"), you MUST construct a Playwright relational selector to ensure you hit the button for that specific row/container, not just the first generic button on the page.
Use Playwright's `>>` combinator. 
Example: `tr:has-text("john123") >> button:has-text("Delete")`
NEVER output a generic `button:has-text("Delete")` if it's supposed to target a specific entity.

---

DOM:
{dom_snippet}

---

Instruction:
{step}

---

Output JSON ONLY:
"""

        response = client.chat.completions.create(
            model=llm_model,
            messages=[
                {
                    "role": "system",
                    "content": "You convert UI instructions into a single structured JSON action."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        content = response.choices[0].message.content.strip()

        print("\n[Interpreter] RAW OUTPUT:\n", content)

        content = re.sub(r"```json|```", "", content).strip()

        try:
            parsed = json.loads(content)

            if isinstance(parsed, list):
                print("[Interpreter] ERROR: Returned list instead of object")
                return {"action": "unknown"}

            print("\n[Interpreter] PARSED ACTION:", parsed)
            print("================ INTERPRETER DEBUG END ================\n")

            return parsed

        except Exception:
            print("[Interpreter] Failed JSON:", content)
            return {"action": "unknown"}