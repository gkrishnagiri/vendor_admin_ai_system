from google.adk import Agent
from openai import OpenAI
import os
import json
from dotenv import load_dotenv

load_dotenv()

class IntentClassifier(Agent):
    def __init__(self):
        super().__init__(
            name="IntentClassifier",
            description="Classifies user queries into Informational or Actionable.",
            instruction="Determine if a user query is INFORMATIONAL (seeking knowledge) or ACTIONABLE (requesting a task execution)."
        )
        self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self._model = "gpt-4o-mini"

    async def classify(self, query: str, context: str = ""):
        """
        Classifies the query into INFORMATIONAL or ACTIONABLE categories.
        Neutral persona for application-agnostic reliability.
        Returns: (result_dict, usage_dict)
        """
        system_prompt = (
            "You are an Intent Classification Specialist for a universal AI Task Automation system.\n"
            "Your goal is to analyze user queries and categorize them regardless of the target application.\n\n"
            "Categories:\n"
            "1. INFORMATIONAL: Seeking facts, instructions, 'how to', or RAG-based context. The user wants to learn or understand.\n"
            "2. ACTIONABLE: Giving a command to perform a physical task in a UI (e.g., 'Submit', 'Delete', 'Create', 'Update', 'Apply').\n\n"
            "Return ONLY a JSON object with 'intent' and 'confidence'."
        )
        
        user_prompt = f"Query: {query}\n\nContext: {context[:2000]}"
        
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Capture usage stats
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }
        
        return result, usage

# Singleton instance
classifier = IntentClassifier()
