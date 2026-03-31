#!/usr/bin/env bash
# ============================================================
# Pi³ — Demo Day Scanner Simulation
# Use this for video demos to bypass the physical camera
# ============================================================

set -e

# ── Configuration ──────────────────────────────────────────
# Load .env to get the server IP
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
fi

SERVER_IP="${PI_SERVER_IP:-localhost}"
SERVER_PORT="${PI_SERVER_PORT:-8000}"
SERVER_URL="http://${SERVER_IP}:${SERVER_PORT}"

# Known scrambled state (R U R' U') - valid and solvable
# SCRAMBLED_STATE="UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB" # Solved
SCRAMBLED_STATE="DUUBULDBFRBFRRULLLBRDFFFDRFDFDRDDUUBLRBLLRRLFBRFLBBUFL"

# ── Colors ──────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}🚀 Starting Scanner Simulation for Video Demo...${NC}"
echo -e "${BLUE}📡 Server: ${GREEN}${SERVER_URL}${NC}"

# 1. Create Session
echo -e "\n${YELLOW}1. Creating new solve session...${NC}"
SESSION_RESPONSE=$(curl -sf -X POST "${SERVER_URL}/jobs/start" \
    -H 'Content-Type: application/json' \
    -d '{"algorithm":"CFOP"}')

SESSION_ID=$(echo "$SESSION_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['session_id'])")
echo -e "   ${GREEN}✓${NC} Created session ${GREEN}#${SESSION_ID}${NC}"

# 2. Simulate "Scanning" delay
echo -e "\n${YELLOW}2. Simulating cube capture (3s delay)...${NC}"
sleep 3

# 3. Submit Scan Result
echo -e "${YELLOW}3. Submitting simulated scan data...${NC}"
curl -sf -X POST "${SERVER_URL}/scan/submit" \
    -H 'Content-Type: application/json' \
    -d "{
        \"session_id\": ${SESSION_ID},
        \"state_string\": \"${SCRAMBLED_STATE}\",
        \"is_valid\": true,
        \"confidence\": 1.0
    }" > /dev/null
echo -e "   ${GREEN}✓${NC} Scan submitted successfully"

# 4. Wait for processing
sleep 2

# 5. Trigger Solve
echo -e "\n${YELLOW}4. Triggering solve pipeline...${NC}"
curl -sf -X POST "${SERVER_URL}/solve/start" \
    -H 'Content-Type: application/json' \
    -d "{\"session_id\": ${SESSION_ID}}" > /dev/null

echo -e "   ${GREEN}✓${NC} Solve triggered!"
echo -e "\n${CYAN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ Simulation Complete!${NC}"
echo -e "  Watch the Dashboard: ${CYAN}http://${SERVER_IP}:5173${NC}"
echo -e "  The Solver Pi (Luke) will pick up the job now."
echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
