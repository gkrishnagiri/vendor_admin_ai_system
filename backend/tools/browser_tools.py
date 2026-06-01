from playwright.async_api import async_playwright


class BrowserSession:
    _instance = None  # 🔥 Singleton

    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None

    @classmethod
    async def get_instance(cls):
        if cls._instance is None:
            cls._instance = BrowserSession()
            await cls._instance.start()
        return cls._instance

    async def start(self):
        print("[Browser] Launching persistent browser...")

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)

        context = await self.browser.new_context(ignore_https_errors=True)
        self.page = await context.new_page()

    async def navigate(self, url):
        print(f"[Browser] Navigating to {url}")
        await self.page.goto(url)
        await self._wait_for_page_load()

    # ----------------------------------------
    # 🔥 FULL DOM EXTRACTION
    # ----------------------------------------
    async def get_full_dom(self):
        print("[Browser] Extracting FULL DOM...")
        try:
            return await self.page.content()
        except Exception as e:
            print("[Browser] DOM extraction failed:", e)
            return ""

    # ----------------------------------------
    # 🔥 CLICK
    # ----------------------------------------
    async def click(self, selector):
        print(f"[Browser] Clicking: {selector}")

        if self._is_login_button(selector):
            return await self._handle_login_submit(selector)

        return await self._generic_click(selector)

    async def _generic_click(self, selector):
        await self.page.wait_for_selector(selector, timeout=10000)
        await self.page.click(selector)

        print("[Browser] Click done. URL:", self.page.url)

        return {"status": "success"}

    # ----------------------------------------
    # 🔥 LOGIN HANDLER
    # ----------------------------------------
    async def _handle_login_submit(self, selector):
        print("[Browser] Handling LOGIN submit")

        await self.page.wait_for_selector(selector, timeout=10000)

        await self.page.keyboard.press("Enter")

        success = await self._wait_for_login_success()

        if not success:
            raise Exception("Login failed or no navigation detected")

        return {"status": "success"}

    async def _wait_for_login_success(self):
        print("[Browser] Waiting for login success...")

        try:
            await self.page.wait_for_url("**/users", timeout=5000)
            print("[Browser] Login success via URL")
            return True
        except:
            pass

        try:
            await self.page.wait_for_selector("text=Users", timeout=5000)
            print("[Browser] Login success via UI")
            return True
        except:
            pass

        print("[Browser] Login NOT successful")
        return False

    # ----------------------------------------
    # 🔥 HELPERS
    # ----------------------------------------
    def _is_login_button(self, selector):
        return selector and "login" in selector.lower()

    async def fill(self, selector, value):
        print(f"[Browser] Filling: {selector} → {value}")
        await self.page.wait_for_selector(selector, timeout=10000)
        await self.page.fill(selector, value)

    async def wait_for(self, selector):
        print(f"[Browser] Waiting for: {selector}")
        await self.page.wait_for_selector(selector, timeout=15000)

    async def _wait_for_page_load(self):
        try:
            await self.page.wait_for_load_state("networkidle", timeout=5000)
        except:
            pass

        # ----------------------------------------
    # 🔥 DOM SNAPSHOT (NEW - EVENT DRIVEN)
    # ----------------------------------------
    async def get_dom_snapshot(self):
        try:
            return {
                "url": self.page.url,
                "content": await self.page.content()
            }
        except Exception as e:
            print("[Browser] Snapshot failed:", e)
            return {
                "url": None,
                "content": ""
            }