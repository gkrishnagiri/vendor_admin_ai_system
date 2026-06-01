import re
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class FormField(BaseModel):
    name: str
    label: str
    type: str = "text"
    required: bool = True
    placeholder: Optional[str] = None

class Parameter(BaseModel):
    key: str = Field(description="The canonical name of the parameter, e.g. 'username' or 'role_name'")
    value: str = Field(description="The value of the parameter")

class FormSchema(BaseModel):
    is_complete: bool = Field(description="CRITICAL: Set to True if ALL required information is already present. Set to False if ANY required information is missing.")
    title: str = Field(description="Title of the form to show the user")
    description: str = Field(description="Polite message explaining exactly what information is required.")
    fields: List[FormField] = Field(description="ONLY include fields for information that is MISSING. If all required details are provided, this list MUST BE EMPTY []")
    unsupported_action: bool = Field(description="Set to true ONLY if the general workflow/procedure for the action is completely absent/unsupported by the documentation. Set to false if the general workflow exists, even if the specific entity names/parameters (e.g. specific role names or permission names) are not mentioned in the text.")
    extracted_parameters: List[Parameter] = Field(description="Extract any key-value pairs, parameters, or entity names provided in the USER REQUEST or CONVERSATION HISTORY (e.g. key='entity_name', value='Value1').")


# ── Canonical field-name aliases ──────────────────────────────────────────────
_FIELD_ALIASES: Dict[str, str] = {
    "user id": "username",
    "userid": "username",
    "uid": "username",
    "user_id": "username",
    "user name": "username",
    "username": "username",
    "email": "email",
    "emailid": "email",
    "email id": "email",
    "email address": "email",
    "pwd": "password",
    "password": "password",
    "pass": "password",
    "secret": "password",
    "pwd": "password",
}

# ── Sensitive field-name pattern ──────────────────────────────────────────────
_SENSITIVE_RE = re.compile(r"(?i).*(password|pwd|secret|token|key|api[_\s]?key|auth).*")

def normalize_key(raw: str) -> str:
    """Return a canonical field name for a raw key string."""
    k = raw.strip().lower()
    return _FIELD_ALIASES.get(k, k)


class InfoGatherer:
    def __init__(self, model="gpt-4o-mini"):
        self.llm = ChatOpenAI(model=model, temperature=0)

    # ── Internal: LLM sensitivity classifier ─────────────────────────────────
    async def _classify_sensitivity(self, fields: Dict[str, str]) -> Dict[str, bool]:
        """
        Ask the LLM which of the provided fields are sensitive.
        Falls back to regex heuristic if the LLM call fails.
        Returns {field_name: is_sensitive}.
        """
        if not fields:
            return {}

        field_list = json.dumps(list(fields.keys()))
        prompt = (
            "You are a security-sensitivity classifier.\n"
            "Given the following field names extracted from a user form submission, "
            "return a JSON object where each field name maps to true if it is sensitive "
            "(e.g. passwords, secrets, tokens, API keys, private keys) and false otherwise.\n\n"
            f"Fields: {field_list}\n\n"
            "Return ONLY a JSON object, no explanation."
        )
        try:
            response = await self.llm.ainvoke(prompt)
            sensitivity: Dict[str, bool] = json.loads(response.content)
            return sensitivity
        except Exception:
            # Fallback: purely regex-based
            return {k: bool(_SENSITIVE_RE.match(k)) for k in fields}

    # ── Internal: mask sensitive values ──────────────────────────────────────
    @staticmethod
    def _mask_based_on_labeled(
        fields: Dict[str, str], sensitivity: Dict[str, bool]
    ) -> Dict[str, str]:
        """Replace sensitive values with '*****' for logging."""
        return {
            k: ("*****" if sensitivity.get(k, False) else v)
            for k, v in fields.items()
        }

    # ── Public: check missing info ────────────────────────────────────────────
    async def check_missing_info(self, query: str, task_description: str, sop_context: str, history: list):
        """
        Determines if there are gaps in the information provided by the user.
        Returns: (FormSchema | None, extracted_parameters, usage_dict)
        """
        structured_llm = self.llm.with_structured_output(FormSchema, include_raw=True, method="function_calling")

        prompt = ChatPromptTemplate.from_template("""
        You are an SOP Compliance Validator for an AI UI Automation system.
        Your goal is to identify if the user's requested action is supported by the provided documentation and if all required information is present.

        --- 
        STRICT RULES:
        1. ACTION VERIFICATION & SEMANTIC MATCHING (CRITICAL):
           - Determine if the requested action's PROCEDURE (workflow/steps) is supported by the DOCUMENT CONTEXT.
           - The documentation typically describes GENERAL workflows/procedures (e.g., how to configure a system setting, assign an option to a category, create an entity, add a user).
           - The user's query provides SPECIFIC PARAMETERS/VALUES (e.g., specific usernames, passwords, custom entity names, category labels, or numeric values) to be filled into the procedure.
           - DO NOT reject an action as unsupported just because the specific parameter values (like specific names or labels) are not mentioned in the documentation text. If the document describes the GENERAL procedure for the action (e.g., assigning an option to a category), the action IS SUPPORTED.
           - Only set 'unsupported_action' to True if the document clearly lacks any workflow/procedure for the intended goal.
        
        2. NO HALLUCINATIONS ON PROCEDURES:
           - Do NOT invent procedures or steps that are not present in the document.
           - Accept and extract user-supplied parameter values (like names, passwords, selections) to be used as variables in those procedures.
        
        3. PREREQUISITES & LINEAR TASKS (CRITICAL): 
           - Scan the ENTIRE DOCUMENT CONTEXT for any prerequisite validations.
           - ONLY perform the requested task. Do NOT suggest or plan steps for creating missing entities unless requested.
        
        4. ADDITIONAL INFO: The user may provide supplementary details as key: value pairs. These count as supplied information.
        
        5. PARAMETER EXTRACTION (MOST IMPORTANT):
           - Carefully analyze the USER REQUEST, CURRENT TASK, and CONVERSATION HISTORY.
           - This is a MULTI-TURN conversation. If a user provides information in Turn 1 or Turn 2, YOU MUST NOT ask for it again in Turn 3.
           - If the USER LATEST INPUT or CURRENT TASK contains explicit entity names or values in quotes (e.g. "Value1", 'Item A'), you MUST extract them into 'extracted_parameters' (e.g. key='entity_name', value='Value1'). Do NOT ask the user to provide them again.
           - Values provided in 'key: value' format in the history are high-priority supplied parameters.
           - If a value is provided (even if slightly misspelled), extract it into 'extracted_parameters'.
           - IF A PARAMETER IS EXTRACTED OR FOUND IN HISTORY, YOU MUST NOT INCLUDE IT IN THE 'fields' LIST.
           - ONLY set 'is_complete' to False if a MANDATORY parameter is truly missing from the entire session context.
        ---

        DOCUMENT CONTEXT:
        {sop}

        CURRENT TASK DESCRIPTION:
        {task}

        USER LATEST INPUT:
        {query}

        CONVERSATION HISTORY:
        {history}

        RESULT REQUIREMENTS:
        - If action is UNSUPPORTED, set 'unsupported_action': True.
        - If SUPPORTED and all required information is already provided (check 'query', 'task', and 'history' carefully), YOU MUST SET 'is_complete': True and leave 'fields' empty.
        - If SUPPORTED but info is missing, set 'is_complete': False and generate a FormSchema ONLY for the exact missing fields.
        - Use the 'description' field to politely explain what is needed based ONLY on the requested task.
        """)

        chain = prompt | structured_llm

        try:
            raw_result = await chain.ainvoke({
                "sop": sop_context,
                "task": task_description,
                "query": query,
                "history": history
            })

            result: FormSchema = raw_result.get("parsed")
            
            # Normalize extracted keys
            extracted = {}
            if result and result.extracted_parameters:
                extracted = {normalize_key(p.key): p.value for p in result.extracted_parameters}

            if extracted:
                # Classify sensitivity and log (masked)
                sensitivity = await self._classify_sensitivity(extracted)
                masked = self._mask_based_on_labeled(extracted, sensitivity)
                print(f"[InfoGatherer] Extracted fields (masked): {masked}")

                if result and not result.is_complete:
                    # Remove fields the user already supplied
                    supplied_keys = set(extracted.keys())
                    result.fields = [
                        f for f in result.fields
                        if normalize_key(f.name) not in supplied_keys
                    ]
                    if not result.fields:
                        result.is_complete = True
                        print("[InfoGatherer] All required fields supplied – marking complete.")

                if result and result.is_complete:
                    # Implicit validation safeguard: If all required fields/parameters are completed,
                    # the action is supported by the SOP procedures. Override unsupported_action to False.
                    result.unsupported_action = False

            # ── Capture usage stats ──────────────────────────────────────────
            usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            raw_msg = raw_result.get("raw")
            if raw_msg and hasattr(raw_msg, "usage_metadata") and raw_msg.usage_metadata:
                usage = {
                    "prompt_tokens": raw_msg.usage_metadata.get("input_tokens", 0),
                    "completion_tokens": raw_msg.usage_metadata.get("output_tokens", 0),
                    "total_tokens": raw_msg.usage_metadata.get("total_tokens", 0),
                }

            return result, extracted, usage

        except Exception as e:
            print(f"[InfoGatherer] Error during validation: {e}")
            return None, {}, {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}


# Singleton
info_gatherer = InfoGatherer()
