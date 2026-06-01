from openai import OpenAI
import os
from dotenv import load_dotenv
from agents.tracing import trace

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def classify_intent(query: str, history: list = None, llm_model: str = "gpt-4o-mini"):

    print(f"\n[IntentClassifier] Query: {query}")
    history_context = ""
    if history and len(history) > 0:
        history_context = "Recent History:\n" + "\n".join([f"{m['role']}: {m['content']}" for m in history[-3:]])

    with trace("intent_classification"):

        prompt = f"""
You are an intent classification system.

Your task is to determine whether the user input is:

1. RAG (Information Intent)
   - The user is seeking knowledge, explanation, guidance, or understanding
   - Includes questions about how to perform an action
   - Includes asking for prerequisites, requirements, steps, or information needed before performing an action

2. ACTION (Execution Intent)
   - The user expects the system to perform an operation or take action
   - The request is a direct instruction to execute something
   - IMPORTANT: If the user is confirming, approving, or authorizing a previously discussed action or plan (e.g., "yes", "proceed", "go ahead", "do it"), this is ALWAYS an ACTION intent.

---

DECISION GUIDELINES:

- Focus on the user’s goal, not just keywords
- If the user is asking for understanding, explanation, or guidance → RAG
- If the user is asking what is needed before doing something → RAG
- If the user gives a direct command to execute → ACTION
- If the user explicitly confirms a pending execution plan → ACTION
- If the intent is mixed or unclear → prefer RAG

---
{history_context}

User Input:
{query}

---

Respond with ONLY one word:
RAG or ACTION
"""

        print("\n[IntentClassifier] Sending prompt to LLM...")

        response = client.chat.completions.create(
            model=llm_model,
            messages=[
                {"role": "system", "content": "You are a precise intent classifier."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        result = response.choices[0].message.content.strip()

        print(f"[IntentClassifier] LLM Response: {result}")

        return result