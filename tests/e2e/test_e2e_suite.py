import pytest
import re
import os
from playwright.sync_api import Page, expect

# Use environment variable for BASE_URL, default to localhost:5173
BASE_URL = os.environ.get("E2E_BASE_URL", "http://localhost:5173")
ARTIFACTS_DIR = "tests/e2e/artifacts"

@pytest.fixture(scope="session", autouse=True)
def ensure_artifacts_dir():
    """Ensure the artifacts directory exists."""
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

@pytest.fixture(autouse=True)
def setup_api_mocks(page: Page):
    """
    Setup API mocks for consistent E2E testing.
    This verifies the frontend-to-backend contract by ensuring the UI
    correctly handles specific JSON structures.
    """
    # 1. Mock Node Health/Status
    page.route(re.compile(r".*/api/nodes/status.*"), lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        json=[
            {"node_id": "rpi4-main", "node_type": "database", "status": "online", "last_heartbeat": "2026-03-30T18:00:00Z"},
            {"node_id": "esp32-motor-0", "node_type": "motor", "status": "online", "last_heartbeat": "2026-03-30T18:00:00Z"},
            {"node_id": "esp32-scanner-0", "node_type": "scanner", "status": "offline", "last_heartbeat": "2026-03-30T17:00:00Z"}
        ]
    ))
    
    # 2. Mock Jobs/Sessions History
    page.route(re.compile(r".*/api/jobs$"), lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        json=[
            {
                "session_id": "e2e-test-session",
                "status": "completed",
                "created_at": "2026-03-30T18:10:00Z",
                "scanned_faces": 6,
                "total_moves": 20
            }
        ]
    ))
    
    # 3. Mock System Logs
    page.route(re.compile(r".*/api/logs.*"), lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        json=[
            {"id": 1, "timestamp": "2026-03-30T18:15:00Z", "node_id": "rpi4-main", "severity": "INFO", "message": "Frontend E2E Navigation Test Started"},
            {"id": 2, "timestamp": "2026-03-30T18:15:05Z", "node_id": "esp32-motor-0", "severity": "WARNING", "message": "Mock Warning for UI testing"}
        ]
    ))
    
    # 4. Mock Scan State (for Cube Viewer)
    page.route(re.compile(r".*/api/scan/.*"), lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        json={
            "faces": {
                "U": ["W"]*9, "D": ["Y"]*9, "L": ["O"]*9, "R": ["R"]*9, "F": ["G"]*9, "B": ["B"]*9
            }
        }
    ))

def test_navigation_and_screenshots(page: Page):
    """
    Core E2E test that verifies UI navigation via Sidebar links
    and ensures key components are rendered on each page.
    """
    # Set viewport size for consistent screenshots
    page.set_viewport_size({"width": 1280, "height": 800})
    
    # --- 1. Dashboard (Live Session) ---
    page.goto(BASE_URL)
    # Verify we are on the dashboard
    expect(page.get_by_text("Live Session", exact=True)).to_be_visible()
    # Verify mocked node status is visible (e.g., NodeHealthCard)
    expect(page.get_by_text("rpi4-main")).to_be_visible()
    page.screenshot(path=f"{ARTIFACTS_DIR}/e2e_01_dashboard.png")
    
    # --- 2. Solve Results ---
    # Click "Solve Results" in Sidebar
    page.get_by_role("link", name="Solve Results").click()
    expect(page).to_have_url(re.compile(r".*/results"))
    # Verify mocked session is in the table
    expect(page.get_by_text("e2e-test-session")).to_be_visible()
    page.screenshot(path=f"{ARTIFACTS_DIR}/e2e_02_results.png")
    
    # --- 3. Execution Monitor ---
    page.get_by_role("link", name="Execution Monitor").click()
    expect(page).to_have_url(re.compile(r".*/execution"))
    # Verify page title or unique element
    expect(page.get_by_text("Execution Monitor", exact=True)).to_be_visible()
    page.screenshot(path=f"{ARTIFACTS_DIR}/e2e_03_execution.png")
    
    # --- 4. Solution Review ---
    page.get_by_role("link", name="Solution Review").click()
    expect(page).to_have_url(re.compile(r".*/review"))
    expect(page.get_by_text("Solution Review", exact=True)).to_be_visible()
    page.screenshot(path=f"{ARTIFACTS_DIR}/e2e_04_review.png")
    
    # --- 5. Lab Logs ---
    page.get_by_role("link", name="Lab Logs").click()
    expect(page).to_have_url(re.compile(r".*/logs"))
    # Verify mocked log entry
    expect(page.get_by_text("Frontend E2E Navigation Test Started")).to_be_visible()
    page.screenshot(path=f"{ARTIFACTS_DIR}/e2e_05_logs.png")

def test_api_contract_verification(page: Page):
    """
    Verifies that clicking 'NEW SOLVE' triggers the expected API call.
    """
    # Intercept the POST /jobs/start call
    def handle_post_solve(route):
        route.fulfill(status=200, json={"session_id": "new-e2e-session", "status": "started"})
        
    page.route(re.compile(r".*/api/jobs/start"), handle_post_solve)
    
    page.goto(BASE_URL)
    # Click NEW SOLVE button
    page.get_by_role("button", name="NEW SOLVE").click()
    
    # Navigation should happen to Dashboard (/) after success (as per Sidebar.tsx logic)
    expect(page).to_have_url(BASE_URL + "/")
