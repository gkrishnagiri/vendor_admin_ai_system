import asyncio
import os
from playwright.async_api import async_playwright
from mcp.server.fastmcp import FastMCP
import mcp.types as types

# --- BROWSER MANAGER ---

class BrowserManager:
    _instance = None
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
    @classmethod
    async def get_instance(cls):
        if cls._instance is None:
            cls._instance = BrowserManager()
        return cls._instance

    async def ensure_browser(self):
        """Ensures the browser is running and a page is open."""
        is_healthy = False
        if self.page:
            try:
                await self.page.evaluate("1")
                is_healthy = True
            except:
                is_healthy = False
                
        if not is_healthy:
            print("[MCP Browser] Service unhealthy or not started. (Re)launching...")
            await self.launch()
            
    async def launch(self):
        if self.playwright:
            await self.playwright.stop()
            
        self.playwright = await async_playwright().start()
        # Use headless=False for visibility during dev as requested
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context(ignore_https_errors=True)
        self.page = await self.context.new_page()
        print("[MCP Browser] Browser launched.")

    async def get_state(self):
        await self.ensure_browser()
        return {
            "url": self.page.url,
            "title": await self.page.title(),
            "dom": await self.page.content()
        }

# --- MCP SERVER DEFINITION (FastMCP) ---

mcp = FastMCP("browser-mcp-server")

@mcp.tool()
async def check_status() -> str:
    """Checks browser health and returns current URL and title."""
    bm = await BrowserManager.get_instance()
    state = await bm.get_state()
    return f"URL: {state['url']}\nTitle: {state['title']}"

@mcp.tool()
async def navigate(url: str) -> str:
    """Navigate to a specific URL."""
    bm = await BrowserManager.get_instance()
    await bm.ensure_browser()
    await bm.page.goto(url)
    return f"Navigated to {url}"

@mcp.tool()
async def ui_action(action: str, selector: str, value: str = "") -> str:
    """
    Perform a UI action on the browser.
    
    Args:
        action: Either 'click' or 'fill'.
        selector: CSS selector for the element.
        value: Text to enter if the action is 'fill'.
    """
    bm = await BrowserManager.get_instance()
    await bm.ensure_browser()
    
    if action == "click":
        await bm.page.click(selector)
        return f"Clicked {selector}"
    elif action == "fill":
        await bm.page.fill(selector, value)
        return f"Filled {selector} with {value}"
    else:
        return f"Unknown action: {action}"

# Helper for internal code that might want the manager directly
BrowserManagerInstance = BrowserManager
