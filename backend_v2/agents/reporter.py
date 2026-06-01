from google.adk import Agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os

load_dotenv()

class ReporterAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Reporter",
            description="Generates human-friendly summaries of task execution results.",
            instruction="Contextualize execution feedback using specific details from the task and actions."
        )
        self._llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

    async def generate_summary(self, goal: str, steps: list, result_status: str, current_step_index: int = 0, extracted_data: str = ""):
        """
        Creates a natural language summary of what was accomplished.
        """
        prompt = ChatPromptTemplate.from_template("""
        You are a helpful AI Assistant Reporter.
        The user just executed an automation task. Your job is to provide a concise, friendly, and CONTEXTUAL summary of the result.

        ---
        ORIGINAL GOAL: {goal}
        STEPS ACTUALLY PERFORMED:
        {steps_list}
        FINAL STATUS: {status}
        PROGRESS: {index} out of {total_steps} steps in the plan were attempted.

        ---
        RULES:
        1. BE TRUTHFUL: Only mention what was actually performed in the STEPS ACTUALLY PERFORMED list.
        2. BE CONTEXTUAL: Use specific names, emails, or IDs found in the GOAL or STEPS.
        3. BE CONCISE: 1-2 sentences max.
        4. STATUS REPORTING (CRITICAL):
           - If status is "success", start with "Success!".
           - If status is "failed", "unsupported", or "running", start with "Interrupted:".
           - Even if all steps were performed, if the status is NOT "success", do NOT say "Success!". Instead, explain that the final verification or action could not be confirmed.
        5. If status is success but (index < total_steps), explain that it stopped early because the objective appeared to be met.
        6. PARTIAL SUCCESS (LAST STEP FAILURE):
           - If status is "failed" or "running" but the current progress is at the LAST step of the plan, explain that all primary actions were successfully completed, but the final confirmation/verification could not be validated.
        7. EXTRACTED DATA: If EXTRACTED DATA is provided below, format it nicely (e.g. as a bulleted list or markdown table) and append it to your response.

        ---
        EXTRACTED DATA:
        {extracted_data}
        """)

        # Only show steps up to the index actually reached
        executed_steps = steps[:current_step_index]
        steps_str = "\n".join([f"- {s}" for s in executed_steps]) if executed_steps else "No steps were performed."
        
        chain = prompt | self._llm
        response = await chain.ainvoke({
            "goal": goal,
            "steps_list": steps_str,
            "status": result_status,
            "index": current_step_index,
            "total_steps": len(steps),
            "extracted_data": extracted_data
        })
        
        return response.content

# Singleton
reporter = ReporterAgent()
