#!/usr/bin/env bash
# ============================================================
# S06 Verification Script — Live E2E Integration Pipeline
# ============================================================
# Proves end-to-end: backend → session → scan → solve → solver_listener → solution in DB → frontend → E2E tests
set -euo pipefail

# Configuration
API_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:5173"
MAX_WAIT=45
POLL_INTERVAL=2

# State variables
BACKEND_PID=""
SOLVER_PID=""
FRONTEND_PID=""
SOLUTION_FOUND=false
PYTEST_EXIT_CODE=0

# ─────────────────────────────────────────────────────────────────────────────
# Cleanup Function
# ─────────────────────────────────────────────────────────────────────────────
cleanup() {
  echo ""
  echo "🧹 Cleaning up..."
  
  # Kill processes
  [ -n "$BACKEND_PID" ] && kill $BACKEND_PID 2>/dev/null || true
  [ -n "$SOLVER_PID" ] && kill $SOLVER_PID 2>/dev/null || true
  [ -n "$FRONTEND_PID" ] && kill $FRONTEND_PID 2>/dev/null || true
  
  # Kill any lingering processes on those ports
  if command -v lsof &> /dev/null; then
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    lsof -ti:5173 | xargs kill -9 2>/dev/null || true
  elif command -v fuser &> /dev/null; then
    fuser -k 8000/tcp 5173/tcp 2>/dev/null || true
  fi
  
  # Remove temporary database files
  rm -f /tmp/s06-*.db 2>/dev/null || true
}

trap cleanup EXIT

# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

wait_for_port() {
  local port=$1
  local max_attempts=20
  local attempt=0
  
  while [ $attempt -lt $max_attempts ]; do
    if curl -s "http://localhost:$port/" > /dev/null 2>&1; then
      return 0
    fi
    sleep 1
    attempt=$((attempt + 1))
  done
  
  echo "❌ Timeout waiting for port $port"
  return 1
}

# ─────────────────────────────────────────────────────────────────────────────
# Step 1: Start Backend
# ─────────────────────────────────────────────────────────────────────────────
echo "🚀 Starting backend server..."
DB_PATH="/tmp/s06-verify-$(date +%s).db"
export DATABASE_URL="$DB_PATH"
export PYTHONPATH="."

python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 > /tmp/s06-backend.log 2>&1 &
BACKEND_PID=$!

echo "   Waiting for backend to be ready..."
if ! wait_for_port 8000; then
  echo "❌ Backend failed to start"
  cat /tmp/s06-backend.log
  exit 1
fi
echo "✓ Backend ready"

# ─────────────────────────────────────────────────────────────────────────────
# Step 2: Create Session
# ─────────────────────────────────────────────────────────────────────────────
echo "📝 Creating new session..."
SESSION_RESPONSE=$(curl -sf -X POST "$API_URL/jobs/start" \
  -H "Content-Type: application/json" \
  -d '{"algorithm":"CFOP"}')

SESSION_ID=$(echo "$SESSION_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['session_id'])")
echo "✓ Session created: $SESSION_ID"

# ─────────────────────────────────────────────────────────────────────────────
# Step 3: Submit Scan
# ─────────────────────────────────────────────────────────────────────────────
echo "📸 Submitting cube scan..."
# Using solved cube (W,Y,R,O,B,G unique centers) — same as S02 verify script
CUBE_STATE="WWWWWWWWWYYYYYYYYYRRRRRRRRROOOOOOOOOBBBBBBBBBGGGGGGGGG"

curl -sf -X POST "$API_URL/scan/submit" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": $SESSION_ID, \"state_string\": \"$CUBE_STATE\", \"is_valid\": true, \"confidence\": 1.0}" > /dev/null

echo "✓ Scan submitted"

# ─────────────────────────────────────────────────────────────────────────────
# Step 4: Trigger Solve
# ─────────────────────────────────────────────────────────────────────────────
echo "🧠 Triggering solve transition..."
curl -sf -X POST "$API_URL/solve/start" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": $SESSION_ID}" > /dev/null

echo "✓ Solve triggered"

# ─────────────────────────────────────────────────────────────────────────────
# Step 5: Start Solver Listener
# ─────────────────────────────────────────────────────────────────────────────
echo "🤖 Starting solver listener..."
export API_BASE_URL="$API_URL"

python3 solver/solver_listener.py > /tmp/s06-solver.log 2>&1 &
SOLVER_PID=$!

echo "✓ Solver listener running (PID: $SOLVER_PID)"

# ─────────────────────────────────────────────────────────────────────────────
# Step 6: Wait for Solution
# ─────────────────────────────────────────────────────────────────────────────
echo "⏳ Waiting up to ${MAX_WAIT}s for solution..."
START_TIME=$(date +%s)

while [ $(($(date +%s) - START_TIME)) -lt $MAX_WAIT ]; do
  STATUS_CODE=$(curl -s -o /tmp/s06-verify-status.json -w "%{http_code}" "$API_URL/solve/$SESSION_ID")
  
  if [ "$STATUS_CODE" -eq 200 ]; then
    echo "✅ Solution found in DB!"
    SOLUTION_FOUND=true
    break
  fi
  
  echo -n "."
  sleep $POLL_INTERVAL
done

echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Step 7: Kill Solver Listener
# ─────────────────────────────────────────────────────────────────────────────
if [ -n "$SOLVER_PID" ]; then
  kill $SOLVER_PID || true
  SOLVER_PID=""
fi

# ─────────────────────────────────────────────────────────────────────────────
# Step 8: Build and Start Frontend (only if solution found)
# ─────────────────────────────────────────────────────────────────────────────
if [ "$SOLUTION_FOUND" = true ]; then
  echo "🏗️  Building frontend..."
  cd frontend
  npm run build > /tmp/s06-frontend-build.log 2>&1
  echo "✓ Frontend built"
  
  echo "🌐 Starting frontend preview server..."
  npm run preview > /tmp/s06-frontend.log 2>&1 &
  FRONTEND_PID=$!
  
  cd ..
  
  echo "   Waiting for frontend to be ready..."
  if ! wait_for_port 5173; then
    echo "❌ Frontend failed to start"
    cat /tmp/s06-frontend.log
    exit 1
  fi
  echo "✓ Frontend ready"
  
  # ───────────────────────────────────────────────────────────────────────────
  # Step 9: Run Live Playwright Tests
  # ───────────────────────────────────────────────────────────────────────────
  echo "🧪 Running live Playwright E2E tests..."
  export E2E_BASE_URL="$FRONTEND_URL"
  
  if pytest tests/e2e/test_live_e2e.py -v --timeout=120 2>&1 | tee /tmp/s06-playwright.log; then
    PYTEST_EXIT_CODE=0
    echo "✓ All E2E tests passed"
  else
    PYTEST_EXIT_CODE=$?
    echo "❌ E2E tests failed (exit code: $PYTEST_EXIT_CODE)"
  fi
else
  echo "❌ Solution not found — skipping frontend and E2E tests"
  PYTEST_EXIT_CODE=1
fi

# ─────────────────────────────────────────────────────────────────────────────
# Final Report
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"

if [ "$SOLUTION_FOUND" = true ] && [ "$PYTEST_EXIT_CODE" -eq 0 ]; then
  echo "║  ✅ S06 E2E VERIFICATION PASSED!                             ║"
  echo "╠════════════════════════════════════════════════════════════════╣"
  echo "║  Pipeline verified:                                            ║"
  echo "║    ✓ Backend started and ready                                ║"
  echo "║    ✓ Session created (ID: $SESSION_ID)"
  echo "║    ✓ Scan submitted with valid cube state                    ║"
  echo "║    ✓ Solve triggered                                          ║"
  echo "║    ✓ Solver listener ran and found solution                  ║"
  echo "║    ✓ Solution stored in database                              ║"
  echo "║    ✓ Frontend built and running                               ║"
  echo "║    ✓ E2E tests passed                                         ║"
  echo "╚════════════════════════════════════════════════════════════════╝"
  exit 0
else
  echo "║  ❌ S06 E2E VERIFICATION FAILED!                             ║"
  echo "╠════════════════════════════════════════════════════════════════╣"
  
  if [ "$SOLUTION_FOUND" = false ]; then
    echo "║  Reason: Solution not found within ${MAX_WAIT}s                 ║"
  else
    echo "║  Reason: E2E tests failed (exit code: $PYTEST_EXIT_CODE)        ║"
  fi
  
  echo "╠════════════════════════════════════════════════════════════════╣"
  echo "║  Logs:                                                         ║"
  echo "║    Backend:  /tmp/s06-backend.log                             ║"
  echo "║    Solver:   /tmp/s06-solver.log                              ║"
  echo "║    Frontend: /tmp/s06-frontend*.log                           ║"
  echo "║    Playwright: /tmp/s06-playwright.log                        ║"
  echo "╚════════════════════════════════════════════════════════════════╝"
  
  if [ -f /tmp/s06-backend.log ]; then
    echo ""
    echo "--- Backend Log (tail -20) ---"
    tail -20 /tmp/s06-backend.log || true
  fi
  
  if [ -f /tmp/s06-solver.log ]; then
    echo ""
    echo "--- Solver Log (tail -20) ---"
    tail -20 /tmp/s06-solver.log || true
  fi
  
  exit 1
fi
