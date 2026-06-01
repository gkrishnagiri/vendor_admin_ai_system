from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def rewrite_query(query: str, llm_model: str = "gpt-4o-mini"):
    """
    Expand query to improve retrieval (generic, not hardcoded)
    """

    prompt = f"""
Rewrite the user query to improve semantic search retrieval.

- Keep the original meaning
- Expand with related terms and synonyms
- Do NOT change intent

User Query:
{query}

Rewritten Query:
"""

    response = client.chat.completions.create(
        model=llm_model,
        messages=[
            {"role": "system", "content": "You improve user queries."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    return response.choices[0].message.content.strip()