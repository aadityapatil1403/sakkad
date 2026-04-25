#!/usr/bin/env bash
# Sakkad — start backend + showcase UI together
# Usage: bash start.sh

set -e

REPO="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$REPO/sakad-backend"
FRONTEND="$REPO/.worktrees/backend-showcase-ui/web/sakkad-showcase"

# ── colours ──────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
AMBER='\033[0;33m'
BLUE='\033[0;34m'
RESET='\033[0m'

echo ""
echo -e "${AMBER}  SAKKAD${RESET}  starting backend + showcase UI"
echo "────────────────────────────────────────"

# ── kill leftover processes on exit ──────────────────────────────────────────
cleanup() {
  echo ""
  echo -e "${AMBER}  shutting down...${RESET}"
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# ── backend ───────────────────────────────────────────────────────────────────
echo -e "${BLUE}  [1/2]${RESET} starting FastAPI backend on :8000"
cd "$BACKEND"
uvicorn main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# wait for backend to be ready
echo -n "  waiting for backend"
for i in $(seq 1 30); do
  if curl -s http://127.0.0.1:8000/api/health > /dev/null 2>&1; then
    echo -e " ${GREEN}ready${RESET}"
    break
  fi
  echo -n "."
  sleep 1
done

# ── frontend ──────────────────────────────────────────────────────────────────
echo -e "${BLUE}  [2/2]${RESET} starting showcase UI on :5173"
cd "$FRONTEND"

# install deps if node_modules missing
if [ ! -d "node_modules" ]; then
  echo "  installing npm dependencies..."
  npm install --silent
fi

# write .env if missing
if [ ! -f ".env" ]; then
  echo "VITE_BACKEND_URL=http://127.0.0.1:8000" > .env
fi

npm run dev &
FRONTEND_PID=$!

echo ""
echo "────────────────────────────────────────"
echo -e "  ${GREEN}Backend${RESET}   http://127.0.0.1:8000"
echo -e "  ${GREEN}Showcase${RESET}  http://localhost:5173"
echo "────────────────────────────────────────"
echo "  Press Ctrl+C to stop both."
echo ""

# ── model warmup hint ─────────────────────────────────────────────────────────
echo -e "  ${AMBER}Tip:${RESET} first classification takes 30-60s (SigLIP loading)."
echo "  Run this to warm it up before demoing:"
echo "  curl -s -X POST http://127.0.0.1:8000/api/capture \\"
echo "    -F 'file=@$BACKEND/test-images/western.jpg' | python3 -m json.tool"
echo ""

wait
