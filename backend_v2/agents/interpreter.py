from google.adk import Agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Tuple
import os
import json
from dotenv import load_dotenv

load_dotenv()

class ActionStep(BaseModel):
    action: Literal["navigate", "click", "fill", "select", "check", "uncheck", "wait", "verify_present", "verify_not_present", "success", "failed_as_unsupported", "extract_data"]
    target_selector: Optional[str] = None
    value: Optional[str] = None
    reasoning: str
    sop_citation: str # Mandatory citation from the SOP

class Interpreter(Agent):
    def __init__(self):
        super().__init__(
            name="Interpreter",
            description="Live UI Interpreter and Action Planner.",
            instruction="Compare the current browser state with the target SOP and decide the next step based on EXPLICIT evidence."
        )
        self._llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    async def interpret_step(self, step_instruction: str, ui_state: dict, goal: str = "", index: int = 1, total: int = 1, parameters: dict = {}):
        """
        Translates a single atomic string instruction into a structured JSON action.
        Returns: (ActionStep, usage_dict)
        """
        structured_llm = self._llm.with_structured_output(ActionStep, include_raw=True)

        prompt = ChatPromptTemplate.from_template("""
        You are a highly precise UI automation interpreter.
        Your ONLY job is to translate the given text instruction into EXACTLY ONE structured JSON action based on the visible DOM.

        ---
        OVERALL GOAL: {goal}
        CURRENT STEP PROGRESS: Step {index} of {total}
        
        EXPLICIT PARAMETERS: 
        {parameters}
        
        INSTRUCTION TO EXECUTE: 
        {step}

        ---
        CURRENT BROWSER STATE:
        URL: {url}
        Page Title: {title}
        Page Context (DOM Summary):
        {context_preview}
        
        ---
        STRICT RULES:
        1. Do NOT try to plan future steps. Only execute the single INSTRUCTION provided.
        2. Set 'sop_citation' to the exact INSTRUCTION string.
        
        3. RESOLVING AMBIGUITY (CRITICAL):
           - PRIORITIZE LITERALS: If the instruction specifies a literal value (e.g., "admin", "password123", or a specific ID in quotes), YOU MUST USE THAT LITERAL.
           - PARAMETER FALLBACK: ONLY use values from EXPLICIT PARAMETERS if the instruction is generic (e.g., "the user's email", "the generated id", "the provided password") AND NO literal value is specified in the instruction.
           - **CRITICAL**: If the instruction says "Fill username with admin", and parameters contain "username: john123", YOU MUST USE "admin". 
        
        4. VERIFICATION & 'WAIT' LOGIC:
           - If the instruction is to CLICK or FILL an element that is not visible, use action='wait'.
           - If the instruction is to VERIFY or CHECK that something is PRESENT, use action='verify_present'.
           - If the instruction is to VERIFY or CHECK that something is ABSENT or MISSING, use action='verify_not_present'.
           - **CRITICAL**: Never use 'success' or 'wait' for a verification instruction. Use 'verify_present' or 'verify_not_present' instead.
        
        4. SELECTOR PRECISION (CRITICAL): 
           - **USE THE SUGGESTED SELECTOR**: If an element in the DOM summary has a `| SUGGESTED SELECTOR: ...`, you SHOULD use that exact string as your `target_selector`. EXCEPT when the target selector is index-based or database-id based (e.g. ends with -1, -2, -3) AND you are targeting a specific row/entity. In that case, you MUST use RELATIONAL TARGETING instead.
           - **GENERIC CONTAINERS**: If verifying that a page, list, or table is present (e.g. "Verify list is present"), target a structural element like `table`, `ul`, or a header `h1`, `h2` containing the title. Do NOT guess `tr:has-text(...)` unless you specifically see that text in a row.
           - **RELATIONAL TARGETING (MANDATORY)**: If the instruction refers to a specific entity (e.g., a specific username, a custom label, or a target row item like "for the role 'HR'"), and that entity is inside a table row (`tr`), list item (`li`), or container, YOU MUST use a relational selector combining the parent row's text and the target element.
             - **NEVER** use bare, index-based selectors like `[data-testid="item-action-button-1"]` or `[data-testid="manage-role-permissions-4"]` directly, as they usually target a different row (e.g. the first row in the table, like AUDITOR instead of HR).
             - **Format for table rows**: `tr:has-text("ENTITY_NAME") >> button` or `tr:has-text("ENTITY_NAME") >> [data-testid^="manage-role-permissions-"]`.
             - Example: To click the action button for the entity "HR" in a table row, use: `tr:has-text("HR") >> [data-testid^="manage-role-permissions-"]` or `tr:has-text("HR") >> button`.
             - **CRITICAL**: Never click the first button you see if it belongs to a different entity (e.g. a default/different entity instead of your target entity).
           - **CHECKBOXES/TOGGLES VERIFICATION**: If the goal is to VERIFY if a checkbox is checked or not:
             - To verify it is NOT enabled/unchecked, append `:checked` to the selector and use action='verify_not_present'. Example: `[data-testid="checkbox-1"]:checked` with `verify_not_present`.
             - To verify it IS enabled/checked, append `:checked` to the selector and use action='verify_present'. Example: `[data-testid="checkbox-1"]:checked` with `verify_present`.
           - **CHECKBOXES/TOGGLES ACTIONS**: If the goal is to ENABLE or DISABLE a setting, use action='check' or action='uncheck'.
             - **CRITICAL**: Look for `(CHECKED)` in the DOM summary. 
             - If you see `(CHECKED)` and the goal is to ENABLE, use action='success'.
             - If you do NOT see `(CHECKED)` and the goal is to DISABLE, use action='success'.
             - Only issue a 'check' or 'uncheck' action if the current state is the OPPOSITE of the goal.

        5. PREREQUISITES: Fulfill login/navigation strictly according to SOP.
        6. URL WHITELIST: Only navigate to URLs explicitly in the SOP. Never construction backend URLs.
        7. REDUNDANCY CHECK: If URL matches target, do NOT 'navigate'.

        8. FIELD MAPPING RULES:
           - action='navigate': Put the URL in 'value'.
           - action='click': Put selector in 'target_selector'.
           - action='fill': Put selector in 'target_selector' and text in 'value'.
           - action='select': Put the dropdown `<select>` element's selector in 'target_selector' and the option label/value to select in 'value'.
           - action='check' / 'uncheck': Put selector in 'target_selector'.
           - action='wait': Wait 5 seconds.
           - action='extract_data': Use this when asked to list, scrape, or extract data. Put the selector of the table/list container in 'target_selector'.
           - action='success': Step complete.
           - action='failed_as_unsupported': Use if SOP doesn't describe how to do the task.

        Return the next single action to take.
        """)
        
        chain = prompt | structured_llm
        
        context_preview = ui_state.get("content", "")

        raw_result = await chain.ainvoke({
            "step": step_instruction,
            "url": ui_state.get("url"),
            "title": ui_state.get("title"),
            "context_preview": context_preview,
            "goal": goal,
            "index": index,
            "total": total,
            "parameters": json.dumps(parameters) if parameters else "NONE"
        })
        
        result = raw_result.get("parsed")
        
        # Extract usage stats (Mapping input_tokens -> prompt_tokens)
        usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
        
        raw_msg = raw_result.get("raw")
        if raw_msg and hasattr(raw_msg, "usage_metadata") and raw_msg.usage_metadata:
            usage = {
                "prompt_tokens": raw_msg.usage_metadata.get("input_tokens", 0),
                "completion_tokens": raw_msg.usage_metadata.get("output_tokens", 0),
                "total_tokens": raw_msg.usage_metadata.get("total_tokens", 0)
            }
            
        return result, usage

# Singleton instance
interpreter = Interpreter()
