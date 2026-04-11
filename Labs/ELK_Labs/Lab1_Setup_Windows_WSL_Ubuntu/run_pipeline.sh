#!/bin/bash
# run_pipeline.sh — Full pipeline: install → train → API → traffic → Logstash → Kibana setup
# Run this in WSL Ubuntu AFTER Elasticsearch and Kibana are already started.

set -e

LAB_DIR="/mnt/c/Users/jithi/OneDrive/Desktop/MLops/MLOps/Labs/ELK_Labs/Lab1_Setup_Windows_WSL_Ubuntu"
PYTHON="/home/jithin/mlenv/bin/python"
PIP="/home/jithin/mlenv/bin/pip"
LOGSTASH="/home/jithin/logstash-8.12.2/bin/logstash"
ES_URL="https://localhost:9200"
ES_USER="elastic"
ES_PASS="gn99-s_mYqreuaYnHKa*"
KIBANA_URL="http://localhost:5601"
INDEX="iris-api-$(date +%Y.%m.%d)"

cd "$LAB_DIR"

echo "============================================"
echo " Step 1: Install Python packages"
echo "============================================"
$PIP install --quiet scikit-learn fastapi uvicorn requests joblib numpy
echo "Done."

echo ""
echo "============================================"
echo " Step 2: Train model"
echo "============================================"
$PYTHON train_model.py

echo ""
echo "============================================"
echo " Step 3: Wait for Elasticsearch"
echo "============================================"
echo "Waiting for ES to be ready..."
for i in $(seq 1 30); do
  if curl -sk -u "$ES_USER:$ES_PASS" "$ES_URL/_cluster/health" | grep -q '"status"'; then
    echo "Elasticsearch is up."
    break
  fi
  echo "  attempt $i/30..."
  sleep 5
done

echo ""
echo "============================================"
echo " Step 4: Clear old api.log and ES index"
echo "============================================"
# Remove old log so Logstash only ships fresh data
> "$LAB_DIR/api.log"
echo "api.log cleared."

# Delete old index if exists so @timestamp mapping is clean
curl -sk -u "$ES_USER:$ES_PASS" -X DELETE "$ES_URL/iris-api-*" > /dev/null && echo "Old ES index deleted." || true

echo ""
echo "============================================"
echo " Step 5: Start API server (background)"
echo "============================================"
pkill -f "uvicorn api:app" 2>/dev/null || true
sleep 1

nohup /home/jithin/mlenv/bin/uvicorn api:app --host 0.0.0.0 --port 8000 > uvicorn.log 2>&1 &
UVICORN_PID=$!
echo "Uvicorn started (PID $UVICORN_PID). Waiting for it to be ready..."
sleep 3

for i in $(seq 1 10); do
  if curl -s http://localhost:8000/health | grep -q "ok"; then
    echo "API is ready."
    break
  fi
  echo "  waiting... attempt $i/10"
  sleep 2
done

echo ""
echo "============================================"
echo " Step 6: Simulate traffic (200 requests)"
echo "============================================"
$PYTHON simulate_traffic.py
echo "api.log now has $(wc -l < api.log) lines."

echo ""
echo "============================================"
echo " Step 7: Ship logs via Logstash"
echo "============================================"
echo "Starting Logstash (will run for 90s to flush all events)..."

# Run Logstash in background, give it time to read and ship the file
nohup $LOGSTASH \
  -f "$LAB_DIR/logstash.conf" \
  --path.data /tmp/logstash-iris \
  > /tmp/logstash-iris.log 2>&1 &
LOGSTASH_PID=$!
echo "Logstash PID: $LOGSTASH_PID"

# Wait for Logstash to start up and process the file (~60-90s)
echo "Waiting for Logstash to ship events..."
for i in $(seq 1 18); do
  sleep 10
  # Check how many docs are in ES so far
  COUNT=$(curl -sk -u "$ES_USER:$ES_PASS" "$ES_URL/iris-api-*/_count" 2>/dev/null | \
    python3 -c "import sys,json; print(json.load(sys.stdin).get('count',0))" 2>/dev/null || echo 0)
  echo "  $((i*10))s — documents in ES: $COUNT"
  if [ "$COUNT" -ge 190 ]; then
    echo "All events shipped!"
    break
  fi
done

kill $LOGSTASH_PID 2>/dev/null || true
echo "Logstash stopped."

FINAL_COUNT=$(curl -sk -u "$ES_USER:$ES_PASS" "$ES_URL/iris-api-*/_count" 2>/dev/null | \
  python3 -c "import sys,json; print(json.load(sys.stdin).get('count',0))" 2>/dev/null || echo "unknown")
echo "Final document count in ES: $FINAL_COUNT"

echo ""
echo "============================================"
echo " Step 8: Create Kibana data view"
echo "============================================"
echo "Waiting for Kibana..."
for i in $(seq 1 20); do
  if curl -s "$KIBANA_URL/api/status" | grep -q '"level"'; then
    echo "Kibana is up."
    break
  fi
  echo "  attempt $i/20..."
  sleep 5
done

# Delete old data view if exists, then recreate with @timestamp
OLD_DV_ID=$(curl -sk -u "$ES_USER:$ES_PASS" "$KIBANA_URL/api/data_views" -H "kbn-xsrf: true" | \
  python3 -c "
import sys,json
for v in json.load(sys.stdin).get('data_view',[]):
    if 'iris-api' in v.get('title',''):
        print(v['id']); break
" 2>/dev/null)

if [ -n "$OLD_DV_ID" ]; then
  curl -sk -u "$ES_USER:$ES_PASS" \
    -X DELETE "$KIBANA_URL/api/data_views/data_view/$OLD_DV_ID" \
    -H "kbn-xsrf: true" > /dev/null
  echo "Old data view deleted."
fi

# Create fresh data view using @timestamp (set by Logstash date filter)
DV_RESULT=$(curl -sk -u "$ES_USER:$ES_PASS" \
  -X POST "$KIBANA_URL/api/data_views/data_view" \
  -H "Content-Type: application/json" \
  -H "kbn-xsrf: true" \
  -d '{"data_view":{"title":"iris-api-*","name":"Iris API Logs","timeFieldName":"timestamp"}}')

DV_ID=$(echo "$DV_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['data_view']['id'])" 2>/dev/null)
echo "Data view created. ID: $DV_ID"

echo ""
echo "============================================"
echo " DONE!"
echo "============================================"
echo ""
echo "ES index:            $INDEX"
echo "Documents in ES:     $FINAL_COUNT"
echo "API server log:      $LAB_DIR/uvicorn.log"
echo "Logstash log:        /tmp/logstash-iris.log"
echo ""
echo "Now run: bash $LAB_DIR/create_kibana_dashboard.sh"
echo "Then open: http://localhost:5601/app/dashboards"
echo ""
echo "To stop the API server: kill $UVICORN_PID"
