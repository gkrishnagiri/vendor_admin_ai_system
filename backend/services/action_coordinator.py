import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from agents.tracing import trace

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def assess_action_state(query: str, history: list, context: str, llm_model: str = "gpt-4o-mini") -> dict:
    """
    Evaluates the current state of an action request to determine if we should:
    1. Ask for clarification (missing parameters)
    2. Generate and present a plan for approval
    3. Execute a previously approved plan
    """
    
    print("\n[ActionCoordinator] Assessing action readiness state...")
    
    # Process history to provide context to LLM
    history_context = ""
    if history and len(history) > 0:
        history_context = "Conversation History:\n"
        for m in history:
            history_context += f"[{m['role'].upper()}]: {m['content']}\n"
    
    prompt = f"""
You are an Action Coordinator for an AI agent system.
Your job is to determine the state of an action request based on the Standard Operating Procedure (SOP Context), the User's latest query, and the Conversation History.

---
SOP Context (The procedure the user wants to execute):
{context}

---
{history_context}

User's Latest Query: {query}
---

EVALUATION RULES:

1. STATE: APPROVED_TO_EXECUTE
   - Trigger: The User's latest query is an affirmative approval (e.g., "yes", "proceed", "go ahead").
   - CRITICAL REQUIREMENT: You can ONLY choose this state if the ASSISTANT'S PREVIOUS MESSAGE explicitly contains a numbered plan (e.g., 1., 2., 3.) AND asks for permission to proceed.
   - Action: DO NOT GENERATE YOUR OWN PLAN. Extract the EXACT numbered plan lines from the assistant's previous message.
   - Output format:
     {{"state": "APPROVED_TO_EXECUTE", "plan": ["step 1", "step 2", ...]}}

2. STATE: NEEDS_CLARIFICATION
   - Trigger: The User is requesting an action, but based on the SOP Context, vital parameters are missing (e.g. target entity identifier).
   - Action: Generate a polite response asking the user for the SPECIFIC missing information based on the SOP.
   - Output format:
     {{"state": "NEEDS_CLARIFICATION", "message": "<Politely ask for the specific missing information, e.g. 'I can help with that action. Could you please specify the [parameter]?' >"}}

3. STATE: READY_TO_PLAN
   - Trigger: The User has provided all necessary parameters required by the SOP Context. 
   - VERY IMPORTANT: If the assistant previously asked for missing information (e.g., "Could you please specify the [parameter]?") and the user's latest query provides the answer (e.g., "value" or "admin"), then the missing info has been provided. The state MUST become READY_TO_PLAN. Do not ask for the same information again.
   - IMPORTANT: If the assistant asks a yes/no question and the user says "yes" with NO numbered plan in history, the state is also READY_TO_PLAN.
   - Action: We are ready to generate a formal plan.
   - Output format:
     {{"state": "READY_TO_PLAN"}}

---
Analyze the conversation and output ONLY valid JSON matching one of the three states above. Do not include markdown formatting like ```json.
"""

    with trace("assess_action_state"):
        try:
            response = client.chat.completions.create(
                model=llm_model,
                messages=[
                    {"role": "system", "content": "You are a robust Action Coordinator that returns ONLY raw JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content.strip()
            print(f"[ActionCoordinator] LLM Response: {result_text}")
            
            result = json.loads(result_text)
            return result
        except Exception as e:
            print(f"[ActionCoordinator] Error: {str(e)}")
            # Fallback to READY_TO_PLAN if JSON parsing fails so the system doesn't get stuck
            return {"state": "READY_TO_PLAN"}
