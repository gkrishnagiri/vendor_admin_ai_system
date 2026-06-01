import asyncio
from playwright.async_api import async_playwright
import time

async def main():
    print("Starting playwright...")
    t0 = time.time()
    p = await async_playwright().start()
    t1 = time.time()
    print(f"Playwright started in {t1-t0:.2f}s")
    
    print("Launching chromium...")
    browser = await p.chromium.launch(headless=True)
    t2 = time.time()
    print(f"Chromium launched in {t2-t1:.2f}s")
    await browser.close()
    await p.stop()

asyncio.run(main())
