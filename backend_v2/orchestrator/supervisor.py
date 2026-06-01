from google.adk import Agent
import asyncio
import re
from typing import Optional, List
from agents.info_gatherer import info_gatherer, normalize_key
from agents.intent_classifier import classifier
from agents.responder import responder
from agents.query_decomposer import decomposer
from rag.retriever import retriever
from engine.execution_graph import execution_engine
from langchain_core.messages import HumanMessage
from agents.planner import planner

class SupervisorAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Supervisor",
            description="Multi-step orchestrator for complex digital tasks.",
            instruction="Decompose user requests into atomic tasks and execute them sequentially against any provided system context."
        )

# ── Module-level cache: task queue ──────────────────────────────────────────
_task_queue: list = []
_current_task_sop: Optional[str] = None
_last_generated_plan: Optional[str] = None
_last_extracted_params: dict = {}

# A form-only message consists entirely of key: value pairs (e.g. from the DynamicForm)
_FORM_ONLY_RE = re.compile(r"^(\s*[\w\s]+\s*:\s*[^,\n]+\s*,?\s*)+$")

def _is_form_only(query: str) -> bool:
    """Return True if the query looks like a pure key-value submission from the dynamic form."""
    return bool(_FORM_ONLY_RE.match(query.strip()))

def _get_actionable_history(history: list) -> list:
    """
    Returns only the history since the last task completion.
    This implements 'Task-Isolated Memory' to prevent stale context from causing hallucinations.
    """
    if not history:
        return []
    
    # Always preserve the very first message (the original user intent)
    original_intent = history[0:1]
    
    # Iterate backwards to find the last completion message
    for i in range(len(history) - 1, 0, -1):
        content = history[i].get("content", "")
        if history[i].get("role") == "assistant":
            # Detection markers for completed tasks
            if content.startswith("Success!") or content.startswith("Interrupted:"):
                # Return original intent + everything AFTER this message
                return original_intent + history[i+1:]
    
    return history


def _extract_params_from_history(history: list) -> dict:
    """
    Manually scan history for form-like submissions (key: value)
    and aggregate them into a single parameter dictionary.
    """
    params = {}
    for msg in history:
        content = msg.get("content", "")
        # Use the same form-detection logic
        if _is_form_only(content):
            pairs = content.split(",")
            for pair in pairs:
                if ":" in pair:
                    try:
                        k, v = pair.split(":", 1)
                        params[normalize_key(k)] = v.strip()
                    except Exception:
                        continue
    return params

async def run_chat_v2(query: str, history: list, log_queue: asyncio.Queue = None):
    """
    Generic Orchestrator v2 with Query Decomposition and Task Queue.
    """
    global _task_queue, _current_task_sop, _last_generated_plan, _last_extracted_params

    usage_stats = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0
    }

    async def log(msg):
        if log_queue:
            await log_queue.put({"type": "log", "content": f"[Supervisor] {msg}"})
        print(f"[Supervisor] {msg}")

    def add_usage(new_usage):
        for k in usage_stats:
            usage_stats[k] += new_usage.get(k, 0)

    skip_planner = False
    actual_query = query
    if query.startswith("/execute-approved-plan "):
        skip_planner = True
        actual_query = query.replace("/execute-approved-plan ", "").strip()

    await log(f"Received query: {actual_query}")

    # --- 0. Cancel Check ---
    if actual_query.lower() in ["cancel", "cancel execution", "stop"]:
        await log("Cancellation received. Clearing task queue.")
        _task_queue = []
        _current_task_sop = None
        _last_extracted_params = {}
        return {
            "status": "CANCELLED",
            "answer": "Execution has been cancelled as requested. The task queue is now empty.",
            "usage": usage_stats
        }

    # --- 1. Queue Management ---
    is_new_request = False
    if skip_planner and _task_queue:
        await log("Executing approved plan with cached task context.")
    elif _is_form_only(actual_query) and _task_queue:
        await log("Detected form submission – resuming current task.")
    else:
        await log("Decomposing request into atomic sub-tasks...")
        decomposition, usage = await decomposer.decompose(actual_query)
        add_usage(usage)

        if not decomposition:
            await log("Error: Failed to decompose query.")
            return {
                "status": "FAILED",
                "answer": "I apologize, but I was unable to break down your request into manageable steps. Please try rephrasing it.",
                "usage": usage_stats
            }

        await log(f"Decomposition complete: {len(decomposition.tasks)} tasks identified.")
        _task_queue = decomposition.tasks
        _current_task_sop = None # Reset SOP for the new queue
        is_new_request = True # Flag for the first task iteration
        _last_extracted_params = {} # Reset parameters for new request

    all_answers = []
    final_status = "SUCCESS"

    # --- 2. Sequential Task Execution ---
    while _task_queue:
        task = _task_queue[0]
        await log(f"--- Task #{task.task_id}: {task.intent} | {task.description} ---")

        # ── 2.1. RAG Retrieval ───────────────────────────────────────────────
        # Reuse cached SOP context if applicable
        if _current_task_sop:
            context_text = _current_task_sop
        else:
            # For actionable tasks, include 'Login Authentication' in search to ensure prerequisites are found
            if task.intent == "ACTIONABLE":
                search_query = f"System Access Login Authentication and {task.description}"
            else:
                search_query = task.description

            await log(f"Retrieving context for: {search_query}")
            chunks = await retriever.search(search_query, top_k=15)
            context_text = "\n\n".join([f"Source: {c['source']}\nSection: {c['section']}\nContent: {c['content']}" for c in chunks])

            if not chunks:
                context_text = "NONE FOUND."
            
            _current_task_sop = context_text

        if task.intent == "INFORMATIONAL":
            await log("Generating synthesis for sub-task...")
            answer, usage = await responder.answer_informational(task.description, context_text, history)
            add_usage(usage)
            all_answers.append(answer)
            _task_queue.pop(0)
            _current_task_sop = None

        elif task.intent == "ACTIONABLE":
            # ── 2.2. Validation & Parameter Persistence ──────────────────────────────
            # Dynamic Context Reset: If this is a brand new request decomposition,
            # we ignore previous history to start with a "clean slate".
            if is_new_request:
                actionable_history = []
                persistent_params = {}
                await log("New request detected – starting with a clean context slate.")
                is_new_request = False # Only reset for the very first iteration of the new queue
            else:
                actionable_history = _get_actionable_history(history)
                # 1. Manual extraction from history (Persistence)
                persistent_params = _extract_params_from_history(actionable_history)
            
            await log(f"Isolated History for validation: {len(actionable_history)} messages")
            
            # 2. Add current query if it's form-like
            if _is_form_only(actual_query):
                current_pairs = actual_query.split(",")
                for cp in current_pairs:
                    if ":" in cp:
                        k, v = cp.split(":", 1)
                        persistent_params[normalize_key(k)] = v.strip()
            
            if persistent_params:
                await log(f"Persistent parameters detected: {list(persistent_params.keys())}")

            if persistent_params:
                await log(f"Persistent parameters detected: {list(persistent_params.keys())}")

            # If the user just approved a plan, we don't need to re-gather info. 
            # We can use the params cached from the previous turn to avoid LLM hallucinations.
            if skip_planner:
                form_needed = None
                llm_extracted = {}
                usage = {}
                extracted_params = _last_extracted_params
            else:
                # Shield info_gatherer from multi-task queries
                ig_query = actual_query
                if not _is_form_only(actual_query) and len(decomposition.tasks if 'decomposition' in locals() else []) > 1:
                    ig_query = task.description

                form_needed, llm_extracted, usage = await info_gatherer.check_missing_info(
                    ig_query, task.description, context_text, actionable_history
                )
                add_usage(usage)
                extracted_params = {**llm_extracted, **persistent_params}
                _last_extracted_params = extracted_params

            if form_needed:
                if form_needed.unsupported_action:
                    await log(f"Abort: Task '{task.description}' is not supported by provided documentation (InfoGatherer marked unsupported).")
                    all_answers.append(f"FAILED: The operation '{task.description}' is not supported by documentation.")
                    final_status = "UNSUPPORTED"
                    _task_queue.clear()
                    break

                if not getattr(form_needed, 'is_complete', False) and form_needed.fields:
                    # Filter out fields that we ALREADY have in extracted_params
                    missing_fields = []
                    for f in form_needed.fields:
                        if normalize_key(f.name) not in extracted_params:
                            missing_fields.append(f)
                    
                    if not missing_fields:
                        form_needed.is_complete = True
                        form_needed.fields = []
                    else:
                        form_needed.fields = missing_fields
                        await log(f"Interrupt: Information required for task. Missing fields: {[f.name for f in form_needed.fields]}")
                        
                        prefix = ""
                        if all_answers:
                            prefix = "\n\n".join(all_answers) + "\n\n---\n\n"
                        
                        return {
                            "status": "CLARIFICATION_REQUIRED",
                            "answer": prefix + form_needed.description,
                            "form_schema": form_needed.model_dump(),
                            "usage": usage_stats
                        }

            if not skip_planner:
                await log("Generating execution plan for approval...")
                safe_plan, p_usage = await planner.generate_plan(task.description, context_text)
                add_usage(p_usage)
                
                _last_generated_plan = safe_plan

                prefix = ""
                if all_answers:
                    prefix = "\n\n".join(all_answers) + "\n\n---\n\n"

                return {
                    "status": "PLAN_APPROVAL_REQUIRED",
                    "plan": safe_plan,
                    "answer": prefix + f"I have generated an execution plan for Task {task.task_id}: {task.description}\nPlease review and approve it before I proceed.",
                    "usage": usage_stats
                }

            # --- 2.3. Browser Execution ---
            # The executor goal is simply the task description.
            # The extracted_params are passed directly to the Interpreter via state.
            executor_goal = task.description
            
            await log(f"Executing automation for: {executor_goal}")
            inputs = {
                "messages": [HumanMessage(content=task.description)],
                "target_goal": executor_goal,
                "sop_context": context_text,
                "parameters": extracted_params, # Pass explicit parameters
                "steps": [],
                "current_step_index": 0,
                "retry_count": 0,
                "max_retries": 3,
                "step_count": 0,
                "last_status": "running",
                "last_ui_state": None,
                "approved_plan": _last_generated_plan, # Pass the high-level roadmap
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }

            result_state = await execution_engine.ainvoke(inputs)
            add_usage({
                "prompt_tokens": result_state.get("prompt_tokens", 0),
                "completion_tokens": result_state.get("completion_tokens", 0),
                "total_tokens": result_state.get("total_tokens", 0)
            })

            # --- 2.4. Report Result ---
            from agents.reporter import reporter
            status = result_state["last_status"]
            
            summary = await reporter.generate_summary(
                goal=executor_goal,
                steps=result_state.get("steps", []),
                result_status=status,
                current_step_index=result_state.get("current_step_index", 0),
                extracted_data=result_state.get("extracted_data", "")
            )

            # --- 2.5. Send Intermediate Feedback ---
            await log(f"TASK COMPLETED: {summary}")
            if log_queue:
                await log_queue.put({
                    "type": "intermediate_result",
                    "content": summary,
                    "task_id": task.task_id,
                    "status": status
                })

            all_answers.append(summary)

            if status == "success":
                # Clear this task from the queue and proceed to the next
                _task_queue.pop(0)
                _current_task_sop = None
                skip_planner = False # VERY IMPORTANT: Force planner approval for the next task!
                if _task_queue:
                    # Reset actual_query to the next task's description, so we don't carry over the old command
                    actual_query = _task_queue[0].description
            elif status == "unsupported":
                await log(f"Abort: Task '{task.description}' is not supported by the system.")
                final_status = "UNSUPPORTED"
                _task_queue.clear()
                _last_extracted_params = {}
                break
            else:
                # status is 'failed' or 'running' (safety limit)
                await log(f"Abort: Execution failure at step '{task.description}' (Status: {status}).")
                final_status = "FAILED"
                _task_queue.clear()
                _last_extracted_params = {}
                break

    # --- 3. Final Response Synthesis ---
    synthesized_answer = "\n\n".join(all_answers)

    # Add a session finalization marker if the queue is empty
    if not _task_queue and final_status == "SUCCESS":
        synthesized_answer += "\n\nSuccess! All requested tasks are complete."
        _last_extracted_params = {}

    return {
        "status": final_status,
        "answer": synthesized_answer,
        "usage": usage_stats
    }
