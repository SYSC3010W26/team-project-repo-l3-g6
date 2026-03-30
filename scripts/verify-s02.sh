#!/usr/bin/env bash
# ============================================================
# S02 Verification Script — Solver Pi Polling Listener
# ============================================================
set -e

# Configuration
API_URL="http://localhost:8000"
POLL_INTERVAL=2
MAX_WAIT=30

# 1. Start Backend in background
if ! curl -s "$API_URL/" > /dev/null; then
  echo "🚀 Starting backend server..."
  export PORT=8000
  export PYTHONPATH=$PWD
  python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 > /tmp/backend-verify.log 2>&1 &
  BACKEND_PID=$!
  
  # Wait for backend to be ready
  for i in $(seq 1 10); do
    if curl -s "$API_URL/" > /dev/null; then
      echo "✓ Backend ready"
      break
    fi
    sleep 1
  done
else
  echo "✓ Backend already running"
fi

# 2. Create a Session
echo "📝 Creating new session..."
# Using JobStartRequest: algorithm, session_name
SESSION_ID=$(curl -s -X POST "$API_URL/jobs/start" -H "Content-Type: application/json" -d '{"algorithm":"CFOP"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['session_id'])")
echo "✓ Session created: $SESSION_ID"

# 3. Submit a Scan
# ScanSubmitRequest: session_id, state_string, is_valid, confidence
echo "📸 Submitting cube scan..."
# Corrected state_string to use colors WYROBG
# White(W), Yellow(Y), Red(R), Orange(O), Blue(B), Green(G)
CUBE_STATE="WWWWWWWWWYYYYYYYYYRRRRRRRRROOOOOOOOOBBBBBBBBBGGGGGGGGG"
curl -s -X POST "$API_URL/scan/submit" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": $SESSION_ID, \"state_string\": \"$CUBE_STATE\", \"is_valid\": true, \"confidence\": 1.0}" > /dev/null
echo "✓ Scan submitted"

# 4. Start Solving
# SolveStartRequest: session_id
echo "🧠 Triggering solve transition..."
curl -s -X POST "$API_URL/solve/start" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": $SESSION_ID}" > /dev/null
echo "✓ Solve acknowledged"

# 5. Start Solver Node
echo "🤖 Starting Solver Node..."
export PI_SERVER_IP="127.0.0.1"
export PI_SERVER_PORT="8000"
export NODE_ID="rpi2-solver-verify"
export NODE_TYPE="solver"
export PYTHONPATH=$PWD
# Run the listener directly
export API_BASE_URL=$API_URL
python3 solver/solver_listener.py > /tmp/solver-verify.log 2>&1 &
SOLVER_PID=$!

# 6. Wait for solution
echo "⏳ Waiting up to ${MAX_WAIT}s for solution..."
START_TIME=$(date +%s)
SOLUTION_FOUND=false

while [ $(($(date +%s) - START_TIME)) -lt $MAX_WAIT ]; do
  # Get solution result (should return 200 OK with schemas.SolveResultResponse)
  STATUS_CODE=$(curl -s -o /tmp/verify-status.json -w "%{http_code}" "$API_URL/solve/$SESSION_ID")
  
  if [ "$STATUS_CODE" -eq 200 ]; then
    echo "✅ Solution found in DB!"
    cat /tmp/verify-status.json | python3 -m json.tool
    SOLUTION_FOUND=true
    break
  fi
  echo -n "."
  sleep $POLL_INTERVAL
done

# Cleanup
echo ""
echo "🧹 Cleaning up..."
[ -n "$SOLVER_PID" ] && kill $SOLVER_PID || true
# Only kill backend if we started it
if [ -n "$BACKEND_PID" ]; then
    kill $BACKEND_PID || true
fi

if [ "$SOLUTION_FOUND" = true ]; then
  echo "🚀 Verification SUCCESS!"
  exit 0
else
  echo "❌ Verification FAILED: Solution did not appear within ${MAX_WAIT}s"
  echo "--- Backend Log ---"
  cat /tmp/backend-verify.log || true
  echo "--- Solver Log ---"
  cat /tmp/solver-verify.log || true
  exit 1
fi
