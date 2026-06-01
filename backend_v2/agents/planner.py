from google.adk import Agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from engine.secrets_manager import secrets_manager
import os
from dotenv import load_dotenv

load_dotenv()

class PlannerAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Planner",
            description="Generates upfront execution plans for user approval.",
            instruction="Create a detailed, step-by-step markdown plan describing exactly what the agent will do based on the SOP context."
        )
        self._llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    async def generate_plan(self, target_goal: str, sop_context: str):
        """
        Generates a markdown execution plan and strictly redacts credentials.
        Returns: (plan_str, usage_dict)
        """
        prompt = ChatPromptTemplate.from_template("""
        You are a Universal UI Execution Planner.
        Your goal is to generate a step-by-step roadmap of exactly what you are about to execute physically on the browser to achieve the user's goal.
        
        ---
        GOAL: {goal}
        
        SOP CONTEXT (YOUR INSTRUCTIONS):
        {sop}
        
        ---
        STRICT RULES:
        1. LINEAR ADHERENCE (CRITICAL): 
           - Provide a deterministic, sequential list of actions. Avoid branching logic like "If X, then Y". 
           - ONLY perform the requested task. Do NOT add steps to create missing entities (records, accounts, items) unless the user explicitly requested their creation in the GOAL.
           - If the SOP requires a pre-check (e.g., "Verify the item exists"), include the check as a physical step, but do NOT add a "Create if missing" branch if it's not part of the requested goal.
           - **STATE-CHECK (IDEMPOTENCY)**: For settings, checkboxes, or toggles, always include a step to check the current state (e.g., "Check if permission X is already enabled"). If it matches the goal, the task should be reported as already complete.

        2. START FROM THE BEGINNING (CRITICAL):
           - ALWAYS include the baseline setup steps: Navigate to the target URL provided in the SOP, and perform any required authentication/login procedures as described in the SOP.
           - Do not assume the agent is already logged in or on the correct page.

        3. BE SPECIFIC: Detail the navigation URL, what fields you will fill, and what buttons you will click.
        4. NO HALLUCINATION & NO UNNECESSARY VERIFICATION: 
           - Only plan steps that are explicitly supported by the SOP CONTEXT.
           - EXCEPTION FOR READ-ONLY QUERIES: If the user's GOAL asks to list, read, or extract data (e.g. "Show me the permissions"), you MUST append a final step to "Extract the data" after navigating to the correct page.
           - Do NOT add unnecessary intermediate steps like "Verify that the list of [entities] is present", "Verify page is loaded", or "Verify table exists". Assume the page loads successfully after navigation clicks.
        5. REDACT CREDENTIALS (SECURITY SHIELD): You MUST mask sensitive passwords and usernames in the generated plan.
           - Instead of using smart placeholders or variables, simply use asterisks like `***` for BOTH the username and password (e.g. `enter the username as "***" and the password as "***"`).
        6. NO WAIT STEPS (STABILITY RULE): Do NOT generate steps like "Wait for page to load" or "Wait for X to appear". The execution engine automatically handles waiting and sensing. Just proceed to the next actionable step (e.g. clicking the button).
        7. FORMAT: Use a continuous, numbered Markdown list (1. 2. 3.). Do NOT put blank lines between the numbered items, as this resets the counter in some renderers. Do not apologize or add conversational filler.
        """)
        
        chain = prompt | self._llm
        
        response = await chain.ainvoke({
            "goal": target_goal,
            "sop": sop_context
        })
        
        # Extra layer of security: mechanically mask any leaked secrets
        safe_plan = secrets_manager.mask(response.content)
        
        usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
        
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = {
                "prompt_tokens": response.usage_metadata.get("input_tokens", 0),
                "completion_tokens": response.usage_metadata.get("output_tokens", 0),
                "total_tokens": response.usage_metadata.get("total_tokens", 0)
            }
            
        return safe_plan, usage

# Singleton instance
planner = PlannerAgent()
