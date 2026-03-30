#!/usr/bin/env bash
# ============================================================
# Pi³ S01 E2E Verification Script
# Checks that start_node.sh correctly launches scanner_bridge.py
# and that scan results are posted to the backend.
# ============================================================

set -e

# Configuration
PORT=8080
API_URL="http://127.0.0.1:$PORT"
TEST_DB="test_verify_s01.db"

echo "🚀 Starting S01 E2E Verification..."

# 1. Cleanup old artifacts
echo "🧹 Cleaning up old processes and database..."
pkill -f "uvicorn backend.main:app" || true
pkill -f "start_node.sh" || true
pkill -f "scanner_bridge.py" || true
pkill -f "stream_server.py" || true
rm -f "$TEST_DB"
rm -f .env

# 2. Start the FastAPI backend
echo "📦 Starting FastAPI backend on port $PORT..."
export DATABASE_URL="$TEST_DB"
uvicorn backend.main:app --port $PORT --host 127.0.0.1 > backend_test.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
MAX_WAIT=20
WAIT_COUNT=0
while ! curl -s "$API_URL/" > /dev/null; do
    sleep 1
    WAIT_COUNT=$((WAIT_COUNT + 1))
    if [ $WAIT_COUNT -ge $MAX_WAIT ]; then
        echo "❌ Backend failed to start (logs follow):"
        cat backend_test.log
        kill $BACKEND_PID
        exit 1
    fi
done
echo "✅ Backend is UP"

# 3. Create a solve session
echo "🔑 Creating a solve session..."
SESSION_RESP=$(curl -s -X POST "$API_URL/jobs/start" \
    -H "Content-Type: application/json" \
    -d '{"algorithm": "Kociemba", "session_name": "S01-E2E-Verify"}')
SESSION_ID=$(echo "$SESSION_RESP" | grep -o '"session_id":[0-9]*' | cut -d: -f2)

if [ -z "$SESSION_ID" ]; then
    echo "❌ Failed to create session. Response: $SESSION_RESP"
    kill $BACKEND_PID
    exit 1
fi
echo "✅ Session ID: $SESSION_ID"

# 4. Configure .env for start_node.sh
echo "⚙️  Configuring .env..."
cat > .env <<EOF
PI_SERVER_IP=127.0.0.1
PI_SERVER_PORT=$PORT
NODE_TYPE=scanner
SESSION_ID=$SESSION_ID
SCANNER_OUTPUT_DIR=.
EOF

# 5. Start start_node.sh
echo "🏃 Starting start_node.sh..."
# Use a separate log for node output
# We need to run it in background
./start_node.sh > node_test.log 2>&1 &
NODE_PID=$!

# 6. Wait for node to be ready (scanner_bridge.py launched)
echo "⏳ Waiting for scanner_bridge.py to start..."
MAX_WAIT=30
WAIT_COUNT=0
while ! grep -q "Starting Scanner Bridge" node_test.log; do
    sleep 1
    WAIT_COUNT=$((WAIT_COUNT + 1))
    if [ $WAIT_COUNT -ge $MAX_WAIT ]; then
        echo "❌ start_node.sh failed to launch scanner_bridge.py (logs follow):"
        cat node_test.log
        pkill -P $NODE_PID || true
        kill $NODE_PID || true
        kill $BACKEND_PID
        exit 1
    fi
done
echo "✅ scanner_bridge.py is LAUNCHED"

# 7. Provide scan results (fixture files)
echo "📄 Providing scan fixtures in Scanner/..."
mkdir -p Scanner
# Update timestamps by copying
cp tests/fixtures/cube_string.txt Scanner/cube_string.txt
cp tests/fixtures/cube_state.json Scanner/cube_state.json

# 8. Polling for scan result in backend
echo "🔍 Polling for scan result at $API_URL/scan/$SESSION_ID..."
MAX_WAIT=20
WAIT_COUNT=0
SUCCESS=0
while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    SCAN_RESP=$(curl -s "$API_URL/scan/$SESSION_ID" || true)
    if echo "$SCAN_RESP" | grep -q "WWWWWWWWWRRRRRRRRRGGGGGGGGGOOOOOOOOOBBBBBBBBBYYYYYYYYY"; then
        echo "✅ SUCCESS: Scan result verified in backend!"
        SUCCESS=1
        break
    fi
    echo "   ...waiting for result ($WAIT_COUNT/$MAX_WAIT)"
    sleep 1
    WAIT_COUNT=$((WAIT_COUNT + 1))
done

# 9. Cleanup
echo "🧹 Cleaning up..."
# Kill all child processes of the node shell script
pkill -P $NODE_PID || true
kill $NODE_PID || true
pkill -f "scanner_bridge.py" || true
pkill -f "stream_server.py" || true
kill $BACKEND_PID || true

# Check if success
if [ $SUCCESS -eq 1 ]; then
    echo "🎉 S01 E2E Verification PASSED!"
    exit 0
else
    echo "❌ S01 E2E Verification FAILED: Scan result never reached backend."
    echo "--- backend_test.log ---"
    cat backend_test.log
    echo "--- node_test.log ---"
    cat node_test.log
    exit 1
fi
