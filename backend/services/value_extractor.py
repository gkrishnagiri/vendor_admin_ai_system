from openai import OpenAI
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_values(query: str, history: list = None, llm_model: str = "gpt-4o-mini"):

    history_context = ""
    if history and len(history) > 0:
        history_context = "Recent History:\n" + "\n".join([f"{m['role']}: {m['content']}" for m in history[-3:]])

    prompt = f"""
Extract structured data from the user request.

---

Return JSON with:

- entity_type (e.g., user, order, item)
- identifier (PRIMARY unique identifier)
- attributes (other fields)

---

CRITICAL RULES:

1. "identifier" MUST be the UNIQUE ID
2. Extract the identifying value EXACTLY as the user provided it, even if it is a descriptive name. NEVER assume, infer, or substitute values using memory or external knowledge.

Example:

Input:
"Create user for dummy. User id is dummy123"

Output:
{{
  "entity_type": "user",
  "identifier": "dummy123",
  "attributes": {{
    "email": "...",
    "password": "..."
  }}
}}

---

{history_context}

User Request:
{query}

---

Output JSON ONLY:
"""

    response = client.chat.completions.create(
        model=llm_model,
        messages=[
            {"role": "system", "content": "Extract structured entities from text."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    content = response.choices[0].message.content.strip()
    content = re.sub(r"```json|```", "", content).strip()

    try:
        return json.loads(content)
    except:
        print("[Extractor] Failed:", content)
        return {}