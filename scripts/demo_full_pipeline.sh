#!/usr/bin/env bash
# ============================================================
# Pi³ — Full Pipeline Demo Simulation
# This script proves the entire system works:
# Backend -> Scanner Sim -> Solver (Live) -> Database -> UI
# ============================================================

set -e

# ── Configuration ──────────────────────────────────────────
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
fi

SERVER_IP="${PI_SERVER_IP:-localhost}"
SERVER_PORT="${PI_SERVER_PORT:-8000}"
SERVER_URL="http://${SERVER_IP}:${SERVER_PORT}"
DASHBOARD_URL="http://${SERVER_IP}:5173"

# Scrambled state string
SCRAMBLED_STATE="DUUBULDBFRBFRRULLLBRDFFFDRFDFDRDDUUBLRBLLRRLFBRFLBBUFL"

# ── Colors ──────────────────────────────────────────────────
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}🏁 Starting Full Pipeline Demo...${NC}"
echo -e "${BLUE}📡 Server: ${GREEN}${SERVER_URL}${NC}"

# 1. Check if Solver Pi is online
echo -e "\n${YELLOW}🔍 Checking if Solver Pi is online...${NC}"
NODES=$(curl -sf "${SERVER_URL}/nodes/")
SOLVER_ONLINE=$(echo "$NODES" | python3 -c "import sys,json; nodes=json.load(sys.stdin); print(any(n['node_type']=='solver' and n['status']=='online' for n in nodes))")

if [ "$SOLVER_ONLINE" != "True" ]; then
    echo -e "   ${RED}❌ Error: Solver Pi is OFFLINE.${NC}"
    echo -e "   ${YELLOW}Please have Luke run ./start_node.sh (option 2) before continuing.${NC}"
    exit 1
fi
echo -e "   ${GREEN}✓${NC} Solver Pi is online and ready!"

# 2. Create Session
echo -e "\n${YELLOW}🚀 Creating new solve session...${NC}"
SESSION_RESPONSE=$(curl -sf -X POST "${SERVER_URL}/jobs/start" \
    -H 'Content-Type: application/json' \
    -d '{"algorithm":"CFOP"}')

SESSION_ID=$(echo "$SESSION_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['session_id'])")
echo -e "   ${GREEN}✓${NC} Created session ${GREEN}#${SESSION_ID}${NC}"

# 3. Submit Scan
echo -e "\n${YELLOW}📸 Submitting scrambled cube state...${NC}"
curl -sf -X POST "${SERVER_URL}/scan/submit" \
    -H 'Content-Type: application/json' \
    -d "{
        \"session_id\": ${SESSION_ID},
        \"state_string\": \"${SCRAMBLED_STATE}\",
        \"is_valid\": true,
        \"confidence\": 1.0
    }" > /dev/null
echo -e "   ${GREEN}✓${NC} Scan submitted"

# 4. Trigger Solve
echo -e "\n${YELLOW}🧠 Triggering solver pipeline...${NC}"
curl -sf -X POST "${SERVER_URL}/solve/start" \
    -H 'Content-Type: application/json' \
    -d "{\"session_id\": ${SESSION_ID}}" > /dev/null
echo -e "   ${GREEN}✓${NC} Solve triggered! Luke's Pi is now calculating..."

# 5. Wait and Poll for results
echo -e "\n${YELLOW}⏳ Waiting for solution from Solver Pi...${NC}"
MAX_RETRIES=15
COUNT=0
SOLVED=false

while [ $COUNT -lt $MAX_RETRIES ]; do
    echo -n "   Polling... "
    # Check session status
    STATUS_RESP=$(curl -sf "${SERVER_URL}/sessions/${SESSION_ID}")
    STATUS=$(echo "$STATUS_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
    
    if [ "$STATUS" == "done" ]; then
        echo -e "${GREEN}SOLVED!${NC}"
        SOLVED=true
        break
    fi
    
    echo -e "${BLUE}${STATUS}${NC}"
    sleep 3
    COUNT=$((COUNT+1))
done

if [ "$SOLVED" = "false" ]; then
    echo -e "\n${RED}❌ Timeout waiting for solver. Check Luke's logs.${NC}"
    exit 1
fi

# 6. Final Report
echo -e "\n${CYAN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ FULL PIPELINE SUCCESSFUL!${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BLUE}Session:${NC}      #${SESSION_ID}"
echo -e "  ${BLUE}Result:${NC}       ${GREEN}SUCCESS${NC}"
echo -e "  ${BLUE}Dashboard:${NC}    ${CYAN}${DASHBOARD_URL}${NC}"
echo -e "  ${BLUE}Review Link:${NC}  ${CYAN}${DASHBOARD_URL}/review/${SESSION_ID}${NC}"
echo ""
echo -e "  Open the ${YELLOW}Review Link${NC} above to see the 3D solution!"
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
