import sys
import io
import asyncio
from services.intent_classifier import classify_intent
from rag.retriever import search
from vendor_admin_agents.planner_agent import plan_actions
from vendor_admin_agents.executor import Executor
from services.value_extractor import extract_values
from services.settings_service import get_current_settings
import re

def redact_plan_steps(steps: list) -> list:
    """Masks potentially sensitive information in plan steps for user display."""
    redacted = []
    # Pattern to match "password <value>" or "password as <value>" case-insensitively
    password_pattern = re.compile(r"(password\s+(?:as\s+)?)([^\s,.]+)", re.IGNORECASE)
    
    for step in steps:
        # Replace the value after 'password' with asterisks
        masked_step = password_pattern.sub(r"\1********", step)
        redacted.append(masked_step)
    return redacted


class QueueStream:
    def __init__(self, queue, buffer):
        self.queue = queue
        self.buffer = buffer
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            self.loop = None

    def write(self, text):
        if text and self.loop:
            self.loop.call_soon_threadsafe(self.queue.put_nowait, {"type": "log", "content": text})
        self.buffer.write(text)

    def flush(self):
        self.buffer.flush()

async def orchestrate(query: str, top_k=3, history: list = None, stream_queue: asyncio.Queue = None):
    history = history or []

    # Capture all print() output as a debug log
    debug_buffer = io.StringIO()
    old_stdout = sys.stdout
    if stream_queue:
        sys.stdout = QueueStream(stream_queue, debug_buffer)
    else:
        sys.stdout = debug_buffer

    try:
        print(f"\n[Orchestrator] Query: {query}")
        if history:
            print(f"[Orchestrator] History turns: {len(history)}")

        # Fetch dynamic LLM Settings from UI config
        settings = get_current_settings()
        llm_model = settings.get("llm_model", "gpt-4o-mini")
        embedding_model = settings.get("embedding_model", "text-embedding-3-small")

        intent = classify_intent(query, history=history, llm_model=llm_model)

        if intent == "RAG":
            result = search(
                query, top_k,
                llm_model=llm_model,
                embedding_model=embedding_model,
                history=history
            )
            result["debug_log"] = debug_buffer.getvalue().splitlines()
            # usage already in result from retriever
            return result

        elif intent == "ACTION":
            from services.action_coordinator import assess_action_state
            
            context_result = search(
                query, top_k,
                llm_model=llm_model,
                embedding_model=embedding_model,
                history=history
            )
            context = context_result.get("answer", "")
            rag_usage = context_result.get("usage", {})
            
            # 1. Assess state: Clarify vs Plan vs Execute
            action_state = assess_action_state(query, history, context, llm_model=llm_model)
            state_type = action_state.get("state", "READY_TO_PLAN")
            print(f"[Orchestrator] Action State: {state_type}")
            
            # --- Path A: Needs Clarification ---
            if state_type == "NEEDS_CLARIFICATION":
                message = action_state.get("message", "Could you provide more details?")
                return {
                    "status": "CLARIFICATION_NEEDED",
                    "answer": message,
                    "usage": rag_usage,
                    "debug_log": debug_buffer.getvalue().splitlines()
                }
                
            # --- Path B: Approved to Execute ---
            elif state_type == "APPROVED_TO_EXECUTE":
                # For security, we re-generate the plan from context rather than extracting 
                # from history, ensuring we have full credentials for execution.
                structured_data = extract_values(query, history=history, llm_model=llm_model)
                plan = plan_actions(query, context, structured_data, history=history, llm_model=llm_model)
                
                print(f"[Orchestrator] Executing re-generated plan: {plan}")
                
                executor = Executor(llm_model=llm_model)
                execution_result = await executor.execute(plan)

                from services.llm_service import summarize_execution
                answer_str, summarize_usage = summarize_execution(query, plan, execution_result, llm_model=llm_model)
                
                agg_usage = {
                    "prompt_tokens": rag_usage.get("prompt_tokens", 0) + summarize_usage.get("prompt_tokens", 0),
                    "completion_tokens": rag_usage.get("completion_tokens", 0) + summarize_usage.get("completion_tokens", 0),
                    "total_tokens": rag_usage.get("total_tokens", 0) + summarize_usage.get("total_tokens", 0),
                }

                return {
                    "plan": plan,
                    "execution": execution_result,
                    "status": "SUCCESS",
                    "answer": answer_str,
                    "usage": agg_usage,
                    "debug_log": debug_buffer.getvalue().splitlines()
                }

            # --- Path C: Ready to Plan (Default) ---
            else:
                structured_data = extract_values(query, history=history, llm_model=llm_model)
                print("[Orchestrator] Extracted:", structured_data)

                plan = plan_actions(query, context, structured_data, history=history, llm_model=llm_model)
                
                # Format plan for the user, REDACTING sensitive info (passwords) for security
                masked_plan = redact_plan_steps(plan)
                plan_md = "\n".join([f"{i+1}. {step}" for i, step in enumerate(masked_plan)])
                answer_str = f"Based on the SOP, here is my detailed plan to fulfill your request:\n\n{plan_md}\n\n**Do I have your explicit permission to proceed with this execution?**"
                
                return {
                    "plan": masked_plan, # Return masked plan to UI
                    "structured_data": structured_data,
                    "status": "PLAN_APPROVAL_REQUEST",
                    "answer": answer_str,
                    "usage": rag_usage,
                    "debug_log": debug_buffer.getvalue().splitlines()
                }

        # Fallback
        return {
            "status": "UNKNOWN_INTENT",
            "answer": None,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "debug_log": debug_buffer.getvalue().splitlines()
        }

    finally:
        sys.stdout = old_stdout