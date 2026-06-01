import os
import asyncio
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

class BrowserManager:
    _instance = None
    _playwright = None
    _browser = None
    _context = None
    _page = None

    def __init__(self):
        # Using singleton pattern to avoid multiple browser instances
        pass

    @classmethod
    async def get_instance(cls):
        if cls._instance is None:
            cls._instance = BrowserManager()
            await cls._instance._init_browser()
        return cls._instance

    async def _init_browser(self):
        """Initializes playwright browser and page, recovering if closed."""
        needs_init = False
        
        if self._playwright is None or self._browser is None or self._page is None:
            needs_init = True
        else:
            try:
                if self._page.is_closed() or not self._browser.is_connected():
                    needs_init = True
            except Exception:
                needs_init = True
                
        if needs_init:
            print("[BrowserManager] Initializing or recovering browser...")
            if self._playwright:
                try:
                    await self._playwright.stop()
                except Exception:
                    pass

            self._playwright = await async_playwright().start()
            
            mode = os.getenv("BROWSER_MODE", "headless").lower()
            is_headless = mode != "headed"
            
            print(f"[BrowserManager] Launching browser (Headless: {is_headless})")
            self._browser = await self._playwright.chromium.launch(headless=is_headless)
            self._context = await self._browser.new_context()
            self._page = await self._context.new_page()

    async def navigate(self, url: str):
        """Navigates to a specific URL."""
        await self._init_browser() # Ensure initialized
        print(f"[BrowserManager] Navigating to: {url}")
        await self._page.goto(url, wait_until="networkidle")

    async def click(self, selector: str):
        """Clicks an element."""
        print(f"[BrowserManager] Clicking: {selector}")
        await self._page.click(selector)

    async def fill(self, selector: str, value: str):
        """Fills an input field."""
        print(f"[BrowserManager] Filling {selector} with value: [REDACTED]")
        await self._page.fill(selector, value)

    async def select(self, selector: str, value: str):
        """Selects an option from a dropdown `<select>` element."""
        print(f"[BrowserManager] Selecting option '{value}' in dropdown {selector}")
        try:
            await self._page.select_option(selector, label=value, timeout=2000)
        except Exception:
            try:
                await self._page.select_option(selector, value=value, timeout=2000)
            except Exception:
                # Robust JS fallback for trailing spaces or slightly mismatched labels
                await self._page.evaluate("""
                    ([sel, val]) => {
                        const select = document.querySelector(sel);
                        if (!select) throw new Error("Select not found");
                        const options = Array.from(select.options);
                        
                        let match = options.find(o => o.text.trim() === val.trim() || o.value.trim() === val.trim() || o.label.trim() === val.trim());
                        
                        if (!match) {
                            const valLower = val.toLowerCase().trim();
                            match = options.find(o => o.text.toLowerCase().includes(valLower) || o.label.toLowerCase().includes(valLower));
                        }
                        
                        if (match) {
                            select.value = match.value;
                            select.dispatchEvent(new Event('change', { bubbles: true }));
                            select.dispatchEvent(new Event('input', { bubbles: true }));
                            return true;
                        }
                        throw new Error("Option not found: " + val);
                    }
                """, [selector, value])

    async def is_visible(self, selector: str) -> bool:
        """Checks if an element is visible on the page."""
        try:
            return await self._page.is_visible(selector, timeout=2000)
        except:
            return False

    async def get_ui_state(self):
        """Returns the current page state for the agent to analyze."""
        await self._init_browser()
        
        # Ensure the page is initialized
        if self._page is None:
             await self._init_browser()
             
        if self._page is None:
            return {
                "url": "about:blank",
                "title": "Error",
                "content": "Browser page not initialized."
            }

        # Safely wait for any active navigation to complete to avoid "Execution context was destroyed"
        try:
            await self._page.wait_for_load_state("domcontentloaded", timeout=2000)
        except Exception:
            pass

        url = self._page.url
        try:
            title = await self._page.title()
            
            # Extract visible text and all interactive elements (buttons, inputs, links)
            # to ensure the agent sees the actual form, not just <head> scripts.
            content = await self._page.evaluate("""() => {
                const interactives = Array.from(document.querySelectorAll('button, input, select, textarea, a, [role="button"], [type="submit"], [onclick]'))
                    .map((el, index) => {
                        const tag = el.tagName.toLowerCase();
                        const type = el.getAttribute('type') || '';
                        const name = el.getAttribute('name') || '';
                        const placeholder = el.getAttribute('placeholder') || '';
                        const value = el.value || '';
                        const checked = el.checked ? ' (CHECKED)' : '';
                        const text = el.innerText.trim();
                        const id = el.id ? `#${el.id}` : '';
                        const cls = el.className ? `.${el.className.trim().split(/\\s+/).join('.')}` : '';
                        const testId = el.getAttribute('data-testid') || '';
                        
                        let label = '';
                        if (el.labels && el.labels.length > 0) {
                            label = Array.from(el.labels).map(l => l.innerText.trim()).join(' ');
                        } else {
                            // Fallback 1: look for aria-label or title
                            label = el.getAttribute('aria-label') || el.getAttribute('title') || '';
                            
                            // Fallback 2: Check for adjacent text node if label is still empty
                            if (!label && el.parentElement) {
                                label = el.parentElement.innerText.replace(text, '').trim();
                            }
                        }

                        // Determine the best selector to use
                        let suggested = '';
                        if (testId) suggested = `[data-testid="${testId}"]`;
                        else if (name) suggested = `${tag}[name="${name}"]`;
                        else if (id) suggested = `#${id.replace('#', '')}`;
                        else if (text) suggested = `${tag}:has-text("${text.slice(0, 20)}")`;
                        else if (label) suggested = `${tag}:near(:text("${label.slice(0, 20)}"))`;

                        // Return a structured summary for the LLM
                        return `(Element ${index}) <${tag}${id}${cls}` + 
                               (name ? ` name="${name}"` : '') +
                               (type ? ` type="${type}"` : '') +
                               (placeholder ? ` placeholder="${placeholder}"` : '') +
                               (testId ? ` data-testid="${testId}"` : '') +
                               (label ? ` label="${label}"` : '') +
                               ` value="${value}"> "${text}"${checked}` +
                               (suggested ? ` | SUGGESTED SELECTOR: ${suggested}` : '');
                    }).join('\\n');

                const visibleText = document.body.innerText.slice(0, 3000);

                return `VISIBLE TEXT:\\n${visibleText}\\n\\nINTERACTIVE ELEMENTS:\\n${interactives}`;
            }""")
        except Exception as e:
            try:
                await asyncio.sleep(1)
                url = self._page.url
                title = await self._page.title()
                content = await self._page.evaluate("() => document.body.innerText.slice(0, 3000)")
            except Exception as e2:
                title = "Unknown"
                content = f"Error capturing state: {e} | Retry error: {e2}"
        
        return {
            "url": url,
            "title": title,
            "content": content
        }

    async def close(self):
        """Cleanly closes browser resources."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        BrowserManager._instance = None

# Global access point
async def get_browser():
    return await BrowserManager.get_instance()
