import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.on("console", lambda msg: print(f"Console: {msg.text}"))
        await page.goto("http://localhost:5173/results")
        await page.wait_for_timeout(3000)
        await page.screenshot(path="debug_results.png")
        await browser.close()
asyncio.run(run())
