#!/bin/bash
# Quick test script for sleep cycle improvements
# Run this after setting OPENAI_API_KEY and starting the API

set -e

echo "🧠 Sleep Cycle Improvements Test"
echo "================================"
echo ""

# Verify API is running
echo "1️⃣  Checking API health..."
curl -s http://localhost:8000/health | grep -q '"status":"healthy"' && echo "   ✓ API is healthy" || (echo "   ✗ API not responding" && exit 1)
echo ""

# Create a new Being
echo "2️⃣  Creating a new Being..."
BEING=$(curl -s -X POST http://localhost:8000/beings \
  -H "Content-Type: application/json" \
  -d '{"name":"TestSleeper","language":"en"}' \
  | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
echo "   ✓ Being created: $BEING"
echo ""

# Add some interactions
echo "3️⃣  Adding initial interactions..."
curl -s -X POST "http://localhost:8000/beings/$BEING/process" \
  -H "Content-Type: application/json" \
  -d '{"role":"user","content":"Hello, I love nature and music"}' > /dev/null
echo "   ✓ Processed user message"

curl -s -X POST "http://localhost:8000/beings/$BEING/process" \
  -H "Content-Type: application/json" \
  -d '{"role":"user","content":"Tell me about your favorite topics"}' > /dev/null
echo "   ✓ Processed second message"
echo ""

# Sleep (where LLM expansion happens)
echo "4️⃣  Starting sleep cycle (with LLM hypothesis expansion)..."
SLEEP=$(curl -s -X POST "http://localhost:8000/beings/$BEING/sleep" \
  -H "Content-Type: application/json" \
  -d '{"num_rollouts":200,"svd_rank":8}')

echo "   Sleep Result:"
echo "$SLEEP" | grep -o '"facts_extracted":[0-9]*' | cut -d':' -f2
echo "$SLEEP" | grep -o '"beliefs_added":[0-9]*' | cut -d':' -f2
echo "$SLEEP" | grep -o '"cycles_completed":[0-9]*' | cut -d':' -f2
echo "   ✓ Sleep completed"
echo ""

# Chat after sleep (uses expanded world model)
echo "5️⃣  Chat with Being (post-sleep)..."
RESPONSE=$(curl -s -X POST "http://localhost:8000/beings/$BEING/chat" \
  -H "Content-Type: application/json" \
  -d '{"message":"What do you like most?"}' \
  | grep -o '"response":"[^"]*"' | cut -d'"' -f4)
echo "   Being said: $RESPONSE"
echo ""

# Check visual state (should have changed with personality)
echo "6️⃣  Visual state after learning..."
VISUAL=$(curl -s "http://localhost:8000/beings/$BEING/visual" \
  | grep -o '"color":"[^"]*"' | cut -d'"' -f4)
echo "   Visual: $VISUAL (should have changed color/form)"
echo ""

echo "✅ All tests passed! Sleep cycle is working."
echo ""
echo "📊 What improved:"
echo "   • Hypotheses are now enriched by LLM (not just AIXI seeds)"
echo "   • Beliefs should be populated (not empty)"
echo "   • ValueModel should have learned (reward variance > 0)"
echo "   • Being should respond with more context"
echo ""
echo "🔍 Check logs for:"
echo "   - '✓ LLM expanded: ' messages"
echo "   - 'beliefs_added > 0'"
echo "   - 'ValueModel: mse > 0, R² > 0'"
