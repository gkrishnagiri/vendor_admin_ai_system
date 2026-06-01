import os
from typing import TypedDict, List, Optional, Dict
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage
from agents.interpreter import interpreter
from engine.secrets_manager import secrets_manager
from engine.browser_manager import get_browser

# --- STATE DEFINITION ---
class AgentState(TypedDict):
    messages: List[BaseMessage]
    target_goal: str
    sop_context: str
    steps: List[str]
    current_step_index: int
    retry_count: int
    max_retries: int
    step_count: int
    last_status: str
    last_ui_state: Optional[dict]
    parameters: Optional[Dict[str, str]] # Explicit parameters extracted from query/history
    approved_plan: Optional[str] # The high-level plan approved by the user
    # Standardized tracking
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

# --- NODES ---

async def plan_node(state: AgentState):
    """Generates the static list of atomic steps once, being mindful of current state."""
    steps = state.get("steps", [])
    if steps:
        return {}
        
    goal = state["target_goal"]
    sop = state["sop_context"]

    # --- SENSE CURRENT STATE BEFORE PLANNING ---
    browser = await get_browser()
    current_state = await browser.get_ui_state()
    current_url = current_state.get("url", "about:blank")
    current_title = current_state.get("title", "No Title")

    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    from pydantic import BaseModel, Field

    class PlanSteps(BaseModel):
        steps: List[str] = Field(description="List of atomic executable UI steps.")

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = llm.with_structured_output(PlanSteps)

    prompt = ChatPromptTemplate.from_template("""
    You are a GENERIC UI automation planner.
    Your job is to convert a user request into a sequence of clear, minimal, executable UI steps.
    
    GOAL: {goal}
    SOP: {sop}

    ---
    CURRENT BROWSER CONTEXT:
    URL: {url}
    Title: {title}

    APPROVED HIGH-LEVEL PLAN: {approved_plan}

    ---
    CRITICAL PLANNING RULES:
    1. ALIGNMENT: Your atomic steps MUST follow the logical sequence of the APPROVED HIGH-LEVEL PLAN. 
       - Do NOT add unnecessary intermediate steps (e.g. "Verify page is loaded" or "Verify table exists") unless explicitly present in the high-level plan.
       - Do NOT hallucinate UI actions like "Save", "Submit", or "Apply" unless they are explicitly written in the APPROVED HIGH-LEVEL PLAN. Many actions like toggling a checkbox save automatically.
    2. NO REDUNDANCY: Do NOT generate steps like "Open the browser" or "Launch application". The browser is already managed. Your first step should be an actionable UI step (e.g. "Navigate to [URL]"). Do NOT generate steps to verify the page title or URL.
    3. SMART SKIPPING (STATE-AWARENESS): Look at the CURRENT BROWSER CONTEXT. 
       - If the browser is ALREADY on the correct page (e.g. inside the application) and logged in, you MAY skip navigation/login steps from the high-level plan.
       - HOWEVER, if the browser is on 'about:blank' or a login page, you MUST include the setup steps.
    4. EFFICIENCY: Start the atomic steps from the earliest point in the high-level plan that hasn't been achieved yet.
    5. Each step MUST represent EXACTLY ONE action (e.g. "Fill username with admin", "Click Login").
    6. NO CONDITIONALS: Do NOT generate conditional branches like "If the user does not exist, do X".
    7. PRECONDITIONS: If the goal implies a precondition, translate it into a strict assertion for the "happy path" using "Verify that [element] is PRESENT/ABSENT". 
       - If CREATING an entity, assert it is ABSENT.
       - If ASSIGNING/UPDATING an entity, assert it is PRESENT. Do NOT hallucinate steps to create the entity first.
       - If ENABLING/CHECKING a checkbox, assert that it is currently NOT enabled (ABSENT).
       - NEVER generate an ambiguous "Check if [X] is enabled" step. Always state the EXPECTED happy-path state (e.g., "Verify that the permission 'X' is NOT enabled").
    8. BLOCKING VERIFICATION: Every "Verify" step is a mandatory blocker.
    9. NO WAIT STEPS: Do NOT generate steps like "Wait for page to load" or "Wait for table". The execution engine implicitly handles wait states. Just provide the next actionable click/fill/verify/extract step.
    10. DATA EXTRACTION: If the APPROVED HIGH-LEVEL PLAN contains a step to "Extract the data" or implies reading a list, you MUST explicitly include a final atomic step to extract the relevant data requested in the user's query. Do NOT replace it with vague terms like "Review the list".
    """)

    chain = prompt | structured_llm
    result = await chain.ainvoke({
        "goal": goal, 
        "sop": sop,
        "url": current_url,
        "title": current_title,
        "approved_plan": state.get("approved_plan", "NONE PROVIDED")
    })
    
    print("\n[Execution-Plan] GENERATED ATOMIC STEPS:")
    for i, s in enumerate(result.steps, 1):
        print(f"  {i}. {s}")

    return {"steps": result.steps, "current_step_index": 0}

async def sense_node(state: AgentState):
    """Captures the current browser state (URL, Title, DOM snapshot)."""
    browser = await get_browser()
    ui_state = await browser.get_ui_state()
    return {"last_ui_state": ui_state}

async def think_node(state: AgentState):
    """Interpreter analyzes state and plans next action."""
    ui_state = state["last_ui_state"]
    steps = state.get("steps", [])
    current_index = state.get("current_step_index", 0)

    if current_index >= len(steps):
        # Should be caught by route_next, but just in case
        return {"last_status": "success"}

    current_step = steps[current_index]

    print(f"\n[Execution] Step {current_index + 1}/{len(steps)}: {current_step}")

    # Use Interpreter to decide the action based on DOM state
    # We pass the goal, current index, and parameters for situational awareness
    action_step, usage = await interpreter.interpret_step(
        current_step, 
        ui_state, 
        goal=state.get("target_goal", ""),
        index=current_index + 1,
        total=len(steps),
        parameters=state.get("parameters", {})
    )

    # Accumulate tokens
    new_prompt = state.get("prompt_tokens", 0) + usage.get("prompt_tokens", 0)
    new_completion = state.get("completion_tokens", 0) + usage.get("completion_tokens", 0)
    new_total = state.get("total_tokens", 0) + usage.get("total_tokens", 0)

    print(f"[Execution] -> Action: {action_step.action} | Target: {action_step.target_selector} | Value: {action_step.value}")

    return {
        "messages": [HumanMessage(content=action_step.model_dump_json())],
        "prompt_tokens": new_prompt,
        "completion_tokens": new_completion,
        "total_tokens": new_total
    }

async def act_node(state: AgentState):
    """Browser agent performs the physical action using Playwright."""
    
    # If the task is already marked as success or unsupported from think_node, skip acting.
    if state.get("last_status") in ["success", "unsupported"]:
        return {}

    browser = await get_browser()
    last_msg = state["messages"][-1].content

    import json
    # Safely load JSON instead of relying on eval
    try:
        action_data = json.loads(last_msg)
    except Exception as e:
        print(f"[Execution] JSON Parsing Error on message: {last_msg}")
        raise e

    action = action_data["action"]
    selector = action_data.get("target_selector") or ""

    # --- SELECTOR NORMALIZATION (Robust) ---
    # 1. If LLM provides data-testid="value", wrap it in brackets
    if selector.startswith('data-testid="') and selector.endswith('"') and '[' not in selector:
        selector = f"[{selector}]"
    
    # 2. If it's a bare attribute-like string e.g. "name=username", wrap it
    elif "=" in selector and not selector.startswith(("[", "text=", ":text-is(")) and "[" not in selector:
        # But only if it's not already complex
        if '"' in selector or "'" in selector:
            selector = f"[{selector}]"

    # 3. If the LLM just gives a bare testid or name without =, wrap it as data-testid
    elif selector and not selector.startswith((".", "#", "[", "text=", ":text-is(")):
        import re
        html_tags = {"a", "button", "div", "input", "select", "textarea", "span", "table", "tr", "td", "th", "ul", "li", "h1", "h2", "h3", "h4", "h5", "h6", "p", "form", "body", "nav", "header", "footer"}
        if re.match(r"^[a-zA-Z0-9_-]+$", selector) and selector.lower() not in html_tags:
            print(f"[Execution] Normalizing bare selector '{selector}' to [data-testid='{selector}']")
            selector = f'[data-testid="{selector}"]'

    # SECRET RESOLUTION (Just-In-Time)
    raw_value = action_data.get("value") or ""
    target_value = secrets_manager.resolve(raw_value)

    # --- PROGRESS TRACKING ---
    new_step_count = state.get("step_count", 0) + 1
    new_retry_count = state.get("retry_count", 0)

    # Replace loop detection logic with simple step tracking
    current_index = state.get("current_step_index", 0)

    if action == "navigate":
        url = target_value if target_value else selector
        try:
            await browser.navigate(url)
            current_index += 1
            new_retry_count = 0 # Reset on success
        except Exception as e:
            print(f"[Execution] Navigation error to {url}: {e}")
            new_retry_count += 1

    elif action == "click":
        try:
            await browser.click(selector)
            import asyncio
            await asyncio.sleep(0.5) 
            current_index += 1
            new_retry_count = 0 # Reset on success
        except Exception as e:
            print(f"[Execution] Click error on '{selector}': {e}")
            new_retry_count += 1

    elif action == "fill":
        try:
            await browser.fill(selector, target_value)
            import asyncio
            await asyncio.sleep(0.5) 
            current_index += 1
            new_retry_count = 0 # Reset on success
        except Exception as e:
            print(f"[Execution] Fill error on '{selector}': {e}")
            new_retry_count += 1

    elif action == "select":
        try:
            await browser.select(selector, target_value)
            import asyncio
            await asyncio.sleep(0.5) 
            current_index += 1
            new_retry_count = 0 # Reset on success
        except Exception as e:
            print(f"[Execution] Select error on '{selector}': {e}")
            new_retry_count += 1

    elif action == "check":
        try:
            # Playwright's check() is idempotent and won't toggle if already checked
            await browser._page.check(selector)
            current_index += 1
            new_retry_count = 0
        except Exception as e:
            print(f"[Execution] Check error on '{selector}': {e}")
            new_retry_count += 1

    elif action == "uncheck":
        try:
            await browser._page.uncheck(selector)
            current_index += 1
            new_retry_count = 0
        except Exception as e:
            print(f"[Execution] Uncheck error on '{selector}': {e}")
            new_retry_count += 1

    elif action == "wait":
        import asyncio
        await asyncio.sleep(5)
        # Note: We do NOT increment current_index here. 
        # This allows the 'think' node to re-evaluate the SAME step after waiting.
        new_retry_count += 1

    elif action == "verify_present":
        is_there = await browser.is_visible(selector)
        if is_there:
            current_index += 1
            new_retry_count = 0 # Reset on success
        else:
            # Condition not met - trigger a wait/retry
            import asyncio
            await asyncio.sleep(5)
            new_retry_count += 1

    elif action == "verify_not_present":
        is_there = await browser.is_visible(selector)
        if not is_there:
            current_index += 1
            new_retry_count = 0 # Reset on success
        else:
            # Condition not met (it is present) - trigger a wait/retry
            import asyncio
            await asyncio.sleep(5)
            new_retry_count += 1

    elif action == "success":
        current_index += 1
        new_retry_count = 0 # Reset on success
        steps = state.get("steps", [])
        if current_index < len(steps):
             print(f"[Execution] Step marked as SUCCESS/SKIP. Moving to next.")

    elif action == "extract_data":
        try:
            # Extract data from the target element or the entire body if none
            target = selector if selector else "body"
            extracted_text = await browser._page.evaluate(f"() => {{ const el = document.querySelector('{target}'); return el ? el.innerText : ''; }}")
            
            # Save the extracted data to the state so the reporter can use it
            state["extracted_data"] = extracted_text
            print(f"[Execution] Extracted data successfully. Length: {len(extracted_text)}")
            
            current_index += 1
            new_retry_count = 0
        except Exception as e:
            print(f"[Execution] Extract data error on '{selector}': {e}")
            new_retry_count += 1

    elif action == "failed_as_unsupported":
        return {"last_status": "unsupported", "retry_count": new_retry_count, "step_count": new_step_count}

    # --- FINAL STATUS CALCULATION ---
    steps = state.get("steps", [])
    status = "running"
    
    if new_retry_count >= state.get("max_retries", 3):
        status = "failed"
    elif current_index >= len(steps):
        status = "success"

    return {
        "last_status": status, 
        "retry_count": new_retry_count, 
        "step_count": new_step_count, 
        "current_step_index": current_index,
        "extracted_data": state.get("extracted_data")
    }


def route_next(state: AgentState):
    """Decides whether to continue or stop."""
    status = state["last_status"]
    if status in ["success", "unsupported", "failed"]:
        return END

    if state["retry_count"] >= state.get("max_retries", 3):
        print(f"[Execution] STUCK DETECTED – Failed to execute step {state['retry_count']} times. Aborting.")
        return END

    steps = state.get("steps", [])
    if state["current_step_index"] >= len(steps):
        print(f"[Execution] Completed all {len(steps)} steps.")
        return END

    # --- SAFETY LIMIT ---
    max_steps = state.get("max_steps", 50) 
    if state["step_count"] >= max_steps:
        print(f"[Execution] Safety step limit ({max_steps}) reached. Stopping to prevent runaway cost.")
        return END

    return "sense"

# --- GRAPH CONSTRUCTION ---

workflow = StateGraph(AgentState)

workflow.add_node("plan", plan_node)
workflow.add_node("sense", sense_node)
workflow.add_node("think", think_node)
workflow.add_node("act", act_node)

workflow.set_entry_point("plan")

workflow.add_edge("plan", "sense")
workflow.add_edge("sense", "think")
workflow.add_edge("think", "act")
workflow.add_conditional_edges("act", route_next)

execution_engine = workflow.compile()
