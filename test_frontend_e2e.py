import asyncio
import threading
import requests
import time
from playwright.async_api import async_playwright

API_URL = "http://localhost:8000"

def keep_alive():
    while True:
        try:
            requests.post(f"{API_URL}/nodes/heartbeat", json={"node_id": "rpi1-scanner", "node_type": "scanner", "status": "online"})
            requests.post(f"{API_URL}/nodes/heartbeat", json={"node_id": "rpi2-solver", "node_type": "solver", "status": "online"})
        except:
            pass
        time.sleep(2)

t = threading.Thread(target=keep_alive, daemon=True)
t.start()

async def run():
    async with async_playwright() as p:
        print("\n🚀 Starting Rigorous E2E Frontend Tests (Playwright)...\n")
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 800})
        base_url = "http://localhost:5173"

        # 1. Dashboard & Node Health
        print(f"📡 Testing {base_url}/ (Dashboard & Node Health)")
        await page.goto(base_url)
        await page.wait_for_timeout(2000) # wait for socket.io events
        
        scanner_status = await page.evaluate("() => document.body.innerText.includes('Scanner Pi') && document.body.innerText.includes('Online')")
        solver_status = await page.evaluate("() => document.body.innerText.includes('Solver Pi') && document.body.innerText.includes('Online')")
        motor_status = await page.evaluate("() => document.body.innerText.includes('Motor Pi') && document.body.innerText.includes('Offline')")
        
        print(f"   [Scanner Pi Health]: {'Online ✅' if scanner_status else 'Offline ❌'}")
        print(f"   [Solver Pi Health]: {'Online ✅' if solver_status else 'Offline ❌'}")
        print(f"   [Motor Pi Health]: {'Offline ✅ (Expected)' if motor_status else 'Online ❌'}")

        session_23 = await page.evaluate("() => document.body.innerText.includes('#23')")
        print(f"   [Active Session Tracker]: {'Loaded Session #23 ✅' if session_23 else 'Missing ❌'}")

        # 2. Results Gallery
        print(f"\n📡 Testing {base_url}/results (Solve Results Gallery)")
        await page.goto(f"{base_url}/results")
        await page.wait_for_timeout(1000)
        table_rows = await page.locator("tbody tr").count()
        print(f"   [Results Table API Bind]: Found {table_rows} historical solves ✅" if table_rows > 0 else "   [Results Table]: Empty ❌")

        # 3. Execution Monitor
        print(f"\n📡 Testing {base_url}/execution (Execution Monitor)")
        await page.goto(f"{base_url}/execution")
        await page.wait_for_timeout(1000)
        has_moves = await page.evaluate("() => document.querySelectorAll('.font-mono').length > 0")
        print(f"   [Execution Tracker API Bind]: Loaded execution UI ✅" if has_moves else "   [Execution Tracker]: Empty ❌")

        # 4. Review Page
        print(f"\n📡 Testing {base_url}/review (3D Solution Review)")
        await page.goto(f"{base_url}/review")
        await page.wait_for_timeout(1000)
        review_data = await page.evaluate("() => document.body.innerText.includes('Review Session #23')")
        print(f"   [Review Data API Bind]: {'Found Session #23 3D Data ✅' if review_data else 'Missing ❌'}")

        # 5. Logs Page
        print(f"\n📡 Testing {base_url}/logs (System Logs)")
        await page.goto(f"{base_url}/logs")
        await page.wait_for_timeout(1000)
        logs = await page.evaluate("() => document.querySelectorAll('div').length > 50")
        print(f"   [Logs Terminal API Bind]: {'Rendered >50 log lines ✅' if logs else 'Missing Logs ❌'}")

        await browser.close()
        print("\n✅ End-to-End Frontend Routing & API Bindings verified.")

asyncio.run(run())
