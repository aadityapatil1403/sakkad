#!/bin/bash

# ============================================================
# Sakkad Demo Startup Script
# Run from: ~/Desktop/XR_Fashion/sakkad/sakad-backend
# ============================================================

set -e

BACKEND_DIR="$HOME/Desktop/XR_Fashion/sakkad/sakad-backend"
WARMUP_IMAGE="test-images/western.jpg"

echo ""
echo "🔷 SAKKAD DEMO STARTUP"
echo "========================"

# 1. Navigate to backend
cd "$BACKEND_DIR" || { echo "❌ Backend directory not found: $BACKEND_DIR"; exit 1; }
echo "✅ In backend directory"

# 2. Check uvicorn is installed
if ! command -v uvicorn &> /dev/null; then
  echo "❌ uvicorn not found. Run: pip install uvicorn"
  exit 1
fi
echo "✅ uvicorn found"

# 3. Check ngrok is installed
if ! command -v ngrok &> /dev/null; then
  echo "❌ ngrok not found. Install from https://ngrok.com/download"
  exit 1
fi
echo "✅ ngrok found"

# 4. Start uvicorn in background
echo ""
echo "▶️  Starting FastAPI server..."
uvicorn main:app --reload --port 8000 &
UVICORN_PID=$!
echo "   PID: $UVICORN_PID"

# 5. Wait for server to be ready
echo "   Waiting for server to come up..."
for i in {1..15}; do
  if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "✅ Server is up"
    break
  fi
  sleep 1
  if [ $i -eq 15 ]; then
    echo "❌ Server failed to start after 15s. Check logs."
    exit 1
  fi
done

# 6. Start ngrok in background
echo ""
echo "▶️  Starting ngrok tunnel..."
ngrok http 8000 > /tmp/ngrok.log 2>&1 &
NGROK_PID=$!
sleep 3

# 7. Get ngrok public URL
NGROK_URL=$(curl -s http://127.0.0.1:4040/api/tunnels | python3 -c "
import sys, json
tunnels = json.load(sys.stdin).get('tunnels', [])
for t in tunnels:
    if t.get('proto') == 'https':
        print(t['public_url'])
        break
" 2>/dev/null)

if [ -z "$NGROK_URL" ]; then
  echo "❌ Could not get ngrok URL. Check http://127.0.0.1:4040"
else
  echo "✅ ngrok tunnel active"
  echo ""
  echo "============================================"
  echo "  PUBLIC URL: $NGROK_URL"
  echo "  SEND THIS TO GABE NOW"
  echo "============================================"
fi

# 8. Warm up the model
echo ""
echo "▶️  Warming up SigLIP model (may take 30-60s)..."
WARMUP_RESPONSE=$(curl -s -X POST http://localhost:8000/api/capture \
  -F "file=@$WARMUP_IMAGE" 2>/dev/null)

if echo "$WARMUP_RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'taxonomy_matches' in d" 2>/dev/null; then
  echo "✅ Model warmed up — pipeline working"
else
  echo "⚠️  Warmup response unexpected. Check manually:"
  echo "   curl -s -X POST http://localhost:8000/api/capture -F 'file=@$WARMUP_IMAGE' | python3 -m json.tool"
fi

# 9. Final health check via ngrok
if [ -n "$NGROK_URL" ]; then
  echo ""
  echo "▶️  Testing ngrok end-to-end..."
  HEALTH=$(curl -s "$NGROK_URL/api/health" -H "ngrok-skip-browser-warning: true" 2>/dev/null)
  if echo "$HEALTH" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d.get('status')=='ok'" 2>/dev/null; then
    echo "✅ ngrok health check passed"
  else
    echo "⚠️  ngrok health check failed — check VPN"
  fi
fi

echo ""
echo "🟢 STARTUP COMPLETE"
echo ""
echo "Processes running:"
echo "  uvicorn PID: $UVICORN_PID"
echo "  ngrok   PID: $NGROK_PID"
echo ""
echo "To stop everything: kill $UVICORN_PID $NGROK_PID"
echo "Or just close this terminal."
echo ""
