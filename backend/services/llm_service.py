from openai import OpenAI
import os
from dotenv import load_dotenv
from agents.tracing import trace

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_answer(query: str, context_chunks: list, llm_model: str = "gpt-4o-mini", history: list = None):
    history = history or []

    with trace("rag_answer_generation"):

        context_text = "\n\n".join([
            f"{i+1}. {chunk['content']}"
            for i, chunk in enumerate(context_chunks)
        ])

        prompt = f"""
You are an intelligent assistant with access to a knowledge base.

Your task:
1. Read FULL context carefully
2. Identify ALL relevant sections
3. Combine information across sections
4. Generate a COMPLETE, logical step-by-step answer
5. Use conversation history to understand follow-up questions and maintain context

IMPORTANT:
- DO NOT just copy one section
- You MUST merge all relevant information
- If steps are repeated, consolidate them
- Replace placeholders with actual values from query
- If the user refers to something mentioned earlier in the conversation, use that context

If NO relevant info:
Return EXACTLY: NO_RELEVANT_CONTEXT

---

Context from knowledge base:
{context_text}

---

User Query:
{query}

---

Final Answer (merged + contextualized steps):
"""

        # Build messages: system prompt + conversation history + current user query
        messages = [
            {"role": "system", "content": "You are a reasoning-based assistant with memory of the conversation."}
        ]
        # Inject prior turns for context
        for turn in history:
            messages.append({"role": turn["role"], "content": turn["content"]})
        # Current prompt
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=llm_model,
            messages=messages,
            temperature=0
        )

        answer = response.choices[0].message.content.strip()
        usage = response.usage
        token_usage = {
            "prompt_tokens": usage.prompt_tokens if usage else 0,
            "completion_tokens": usage.completion_tokens if usage else 0,
            "total_tokens": usage.total_tokens if usage else 0,
        }

        if "NO_RELEVANT_CONTEXT" in answer:
            return {
                "status": "NO_CONTEXT",
                "answer": None,
                "usage": token_usage
            }

        return {
            "status": "SUCCESS",
            "answer": answer,
            "usage": token_usage
        }

def summarize_execution(query: str, plan: list, execution_result: list, llm_model: str = "gpt-4o-mini"):
    with trace("summarize_execution"):
        prompt = f"""
You are an intelligent assistant in charge of executing tasks for a user.

The user asked you to perform the following task:
"{query}"

The plan that was determined to execute this:
{str(plan)}

The actual execution outcomes for those steps:
{str(execution_result)}

Your goal: Provide a concise, conversational final answer back to the user summarizing the outcome.
- If all steps are "success", summarize what you achieved based on the query (e.g., "I have successfully created a new user named Jane.")
- If there's a failed step, concisely explain what part failed and why.
- Keep it natural, polite, and brief (1-3 sentences max). Do NOT use bullet points unless necessary.
"""
        response = client.chat.completions.create(
            model=llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        usage = response.usage
        token_usage = {
            "prompt_tokens": usage.prompt_tokens if usage else 0,
            "completion_tokens": usage.completion_tokens if usage else 0,
            "total_tokens": usage.total_tokens if usage else 0,
        }
        return response.choices[0].message.content.strip(), token_usage