import json
import re
from tools.browser_tools import BrowserSession
from services.llm_interpreter import interpret_step


class Executor:
    def __init__(self, max_retries=2, llm_model="gpt-4o-mini"):
        self.max_retries = max_retries
        self.llm_model = llm_model
        self.browser = None

        # 🔥 GENERIC EXECUTION STATE
        self.context = {
            "skip_mode": False,
            "last_verification": None
        }

    async def execute(self, steps):
        print("\n[Executor] Starting execution...")

        self.browser = await BrowserSession.get_instance()

        results = []

        for i, step in enumerate(steps):

            # 🔥 SKIP MODE
            if self.context["skip_mode"]:
                print(f"[Executor] Skipping step {i+1} due to condition: {step}")
                results.append({
                    "step": step,
                    "status": "skipped"
                })
                continue

            print(f"\n[Executor] Step {i+1}: {step}")

            step_result = await self._execute_step_with_retry(step, i)

            results.append(step_result)

            if step_result["status"] == "failed":
                print("[Executor] Stopping execution due to failure.")
                break

        print("\n[Executor] Execution complete")
        return results

    async def _execute_step_with_retry(self, step, step_index):

        last_error = "Unknown error"

        for attempt in range(1, self.max_retries + 2):

            print(f"[Executor] Attempt {attempt}")

            try:
                dom = await self.browser.get_full_dom()

                action_json = interpret_step(step, dom, llm_model=self.llm_model)

                print("[Executor] Interpreted Action:", action_json)

                action = action_json.get("action")

                # ----------------------------------------
                # VERIFY HANDLING (FIXED)
                # ----------------------------------------
                if action == "verify_present":
                    result = await self._verify_text(action_json.get("text"), True)

                    self.context["last_verification"] = result

                    # 🔥 FIX: Only activate skip for EARLY steps (pre-check)
                    if result["status"] == "success" and step_index <= 2:
                        print("[Executor] Pre-check detected → activating skip mode")
                        self.context["skip_mode"] = True

                    return result

                elif action == "verify_not_present":
                    result = await self._verify_text(action_json.get("text"), False)

                    self.context["last_verification"] = result

                    return result

                # ----------------------------------------
                # NORMALIZE
                # ----------------------------------------
                action_json = self._normalize_action(action_json)

                if action_json.get("action") == "unknown":
                    last_error = "Interpreter returned unknown action"
                    continue

                if action_json.get("action") == "error":
                    last_error = action_json.get("message", "Target element not found in current UI state.")
                    break  # Break retry loop immediately on explicit error

                # ----------------------------------------
                # SNAPSHOT BEFORE
                # ----------------------------------------
                prev_snapshot = await self.browser.get_dom_snapshot()

                # ----------------------------------------
                # EXECUTE
                # ----------------------------------------
                result = await self._perform_action(action_json)

                if result["status"] == "success":

                    dom_changed = await self._wait_for_dom_change(prev_snapshot)

                    # ----------------------------------------
                    # GENERIC OUTCOME DETECTION
                    # ----------------------------------------
                    if not dom_changed:

                        current_url = self.browser.page.url
                        prev_url = prev_snapshot["url"]

                        if action_json["action"] == "click" and current_url == prev_url:
                            # State is stable after an interactive click. 
                            # (Could be an idempotent link or a form that didn't visually update).
                            print("[Executor] No DOM change but state stable → SUCCESS")
                            return {"step": step, "status": "success", "attempts": attempt}

                        print("[Executor] No DOM change → treating as failure")
                        last_error = "No DOM change detected"
                        continue

                    return {
                        "step": step,
                        "status": "success",
                        "attempts": attempt
                    }

                else:
                    last_error = result.get("reason", "Action failed")

            except Exception as e:
                last_error = str(e)
                print("[Executor] Exception:", last_error)

        return {
            "step": step,
            "status": "failed",
            "error": last_error,
            "attempts": self.max_retries + 1,
            "debug": {
                "last_error": last_error,
                "context": self.context
            }
        }

    # ----------------------------------------
    # DOM CHANGE DETECTION
    # ----------------------------------------
    async def _wait_for_dom_change(self, prev_snapshot, timeout=3000):

        import time
        start = time.time()

        while (time.time() - start) * 1000 < timeout:

            current_snapshot = await self.browser.get_dom_snapshot()

            if current_snapshot["url"] != prev_snapshot["url"]:
                print("[Executor] URL changed")
                return True

            if current_snapshot["content"] != prev_snapshot["content"]:
                print("[Executor] DOM changed")
                return True

        print("[Executor] No DOM change detected")
        return False

    # ----------------------------------------
    # VERIFY (ROBUST)
    # ----------------------------------------
    async def _verify_text(self, text, present=True):

        print(f"[Executor] Verifying text (ROBUST): {text}")

        try:
            visible_text = await self.browser.page.inner_text("body")
        except Exception as e:
            return {
                "status": "failed",
                "reason": str(e)
            }

        visible_text_clean = re.sub(r"\s+", " ", visible_text.lower())
        target = text.lower().strip()

        escaped_target = re.escape(target)
        # Use word boundaries to prevent partial matches like "John" inside "john123"
        pattern = rf"(?:\b|\s|^){escaped_target}(?:\b|\s|$)"
        exists = bool(re.search(pattern, visible_text_clean))

        print(f"[Executor] VERIFY RESULT → exists={exists}, expected={present}")

        if present and exists:
            return {"status": "success"}

        if not present and not exists:
            return {"status": "success"}

        return {
            "status": "failed",
            "details": {
                "text": text,
                "expected": present,
                "actual": exists
            }
        }

    # ----------------------------------------
    # NORMALIZATION
    # ----------------------------------------
    def _normalize_action(self, action_json):

        if isinstance(action_json.get("action"), dict):
            inner = action_json["action"]
            action = list(inner.keys())[0]
            data = inner[action]

            normalized = {"action": action}
            normalized.update(data)
            action_json = normalized

        if "target" in action_json and "selector" not in action_json:
            action_json["selector"] = action_json.pop("target")

        if "data-testid" in action_json and "selector" not in action_json:
            action_json["selector"] = f"[data-testid=\"{action_json.pop('data-testid')}\"]"

        if action_json.get("action") == "fill":
            if "value" not in action_json and "text" in action_json:
                action_json["value"] = action_json.pop("text")

        return action_json

    # ----------------------------------------
    # ACTION EXECUTION
    # ----------------------------------------
    async def _perform_action(self, action_json):

        action = action_json.get("action")

        try:
            if action == "click":
                return await self.browser.click(action_json.get("selector"))

            elif action == "fill":
                await self.browser.fill(
                    action_json.get("selector"),
                    action_json.get("value", "")
                )
                return {"status": "success"}

            elif action == "navigate":
                await self.browser.navigate(action_json.get("url"))
                return {"status": "success"}

            else:
                return {"status": "failed", "reason": "Unknown action"}

        except Exception as e:
            return {"status": "failed", "reason": str(e)}