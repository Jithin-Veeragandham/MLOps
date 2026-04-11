#!/bin/bash
# create_kibana_dashboard.sh
# Creates the Iris API monitoring dashboard in Kibana using individual saved object POSTs.

KIBANA_URL="http://localhost:5601"
ES_USER="elastic"
ES_PASS="gn99-s_mYqreuaYnHKa*"

post_object() {
  local type=$1
  local id=$2
  local body=$3
  local result
  result=$(curl -sk -u "$ES_USER:$ES_PASS" \
    -X POST "$KIBANA_URL/api/saved_objects/$type/$id?overwrite=true" \
    -H "Content-Type: application/json" \
    -H "kbn-xsrf: true" \
    -d "$body")
  if echo "$result" | python3 -c "import sys,json; r=json.load(sys.stdin); exit(0 if 'id' in r else 1)" 2>/dev/null; then
    echo "  OK: $type/$id"
  else
    echo "  FAIL: $type/$id — $result"
  fi
}

echo "Fetching data view ID for iris-api-*..."
DV_ID=$(curl -sk -u "$ES_USER:$ES_PASS" "$KIBANA_URL/api/data_views" -H "kbn-xsrf: true" | \
  python3 -c "
import sys, json
data = json.load(sys.stdin)
for v in data.get('data_view', []):
    if 'iris-api' in v.get('title',''):
        print(v['id'])
        break
" 2>/dev/null)

if [ -z "$DV_ID" ]; then
  echo "Data view not found — creating it now..."
  DV_RESULT=$(curl -sk -u "$ES_USER:$ES_PASS" \
    -X POST "$KIBANA_URL/api/data_views/data_view" \
    -H "Content-Type: application/json" \
    -H "kbn-xsrf: true" \
    -d '{"data_view":{"title":"iris-api-*","name":"Iris API Logs","timeFieldName":"@timestamp"}}')
  DV_ID=$(echo "$DV_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['data_view']['id'])" 2>/dev/null)
fi

echo "Data view ID: $DV_ID"
echo ""
echo "Creating visualizations..."

# 1 — Requests over time (bar chart)
post_object "lens" "iris-requests-over-time" "{
  \"attributes\": {
    \"title\": \"Requests Over Time\",
    \"visualizationType\": \"lnsXY\",
    \"state\": {
      \"datasourceStates\": {
        \"formBased\": {
          \"layers\": {
            \"layer1\": {
              \"columnOrder\": [\"col-date\",\"col-count\"],
              \"columns\": {
                \"col-date\": {\"label\":\"timestamp\",\"dataType\":\"date\",\"operationType\":\"date_histogram\",\"sourceField\":\"timestamp\",\"isBucketed\":true,\"params\":{\"interval\":\"auto\",\"includeEmptyRows\":true}},
                \"col-count\": {\"label\":\"Count\",\"dataType\":\"number\",\"operationType\":\"count\",\"sourceField\":\"___records___\",\"isBucketed\":false,\"scale\":\"ratio\"}
              },
              \"indexPatternId\": \"$DV_ID\"
            }
          }
        }
      },
      \"visualization\": {
        \"layers\": [{\"layerId\":\"layer1\",\"layerType\":\"data\",\"seriesType\":\"bar_stacked\",\"xAccessor\":\"col-date\",\"accessors\":[\"col-count\"]}],
        \"legend\": {\"isVisible\":true},
        \"valueLabels\": \"hide\"
      },
      \"query\": {\"query\":\"\",\"language\":\"kuery\"},
      \"filters\": []
    }
  },
  \"references\": [{\"type\":\"index-pattern\",\"id\":\"$DV_ID\",\"name\":\"indexpattern-datasource-layer-layer1\"}]
}"

# 2 — Prediction distribution (pie)
post_object "lens" "iris-prediction-distribution" "{
  \"attributes\": {
    \"title\": \"Prediction Class Distribution\",
    \"visualizationType\": \"lnsPie\",
    \"state\": {
      \"datasourceStates\": {
        \"formBased\": {
          \"layers\": {
            \"layer1\": {
              \"columnOrder\": [\"col-pred\",\"col-count\"],
              \"columns\": {
                \"col-pred\": {\"label\":\"Prediction\",\"dataType\":\"string\",\"operationType\":\"terms\",\"sourceField\":\"prediction.keyword\",\"isBucketed\":true,\"params\":{\"size\":10,\"orderBy\":{\"type\":\"column\",\"columnId\":\"col-count\"},\"orderDirection\":\"desc\",\"otherBucket\":false}},
                \"col-count\": {\"label\":\"Count\",\"dataType\":\"number\",\"operationType\":\"count\",\"sourceField\":\"___records___\",\"isBucketed\":false,\"scale\":\"ratio\"}
              },
              \"indexPatternId\": \"$DV_ID\"
            }
          }
        }
      },
      \"visualization\": {
        \"shape\": \"pie\",
        \"layers\": [{\"layerId\":\"layer1\",\"layerType\":\"data\",\"primaryGroups\":[\"col-pred\"],\"metrics\":[\"col-count\"]}]
      },
      \"query\": {\"query\":\"\",\"language\":\"kuery\"},
      \"filters\": []
    }
  },
  \"references\": [{\"type\":\"index-pattern\",\"id\":\"$DV_ID\",\"name\":\"indexpattern-datasource-layer-layer1\"}]
}"

# 3 — Avg latency over time (line)
post_object "lens" "iris-avg-latency" "{
  \"attributes\": {
    \"title\": \"Average Latency Over Time (ms)\",
    \"visualizationType\": \"lnsXY\",
    \"state\": {
      \"datasourceStates\": {
        \"formBased\": {
          \"layers\": {
            \"layer1\": {
              \"columnOrder\": [\"col-date\",\"col-latency\"],
              \"columns\": {
                \"col-date\": {\"label\":\"timestamp\",\"dataType\":\"date\",\"operationType\":\"date_histogram\",\"sourceField\":\"timestamp\",\"isBucketed\":true,\"params\":{\"interval\":\"auto\",\"includeEmptyRows\":true}},
                \"col-latency\": {\"label\":\"Avg Latency (ms)\",\"dataType\":\"number\",\"operationType\":\"average\",\"sourceField\":\"latency_ms\",\"isBucketed\":false,\"scale\":\"ratio\"}
              },
              \"indexPatternId\": \"$DV_ID\"
            }
          }
        }
      },
      \"visualization\": {
        \"layers\": [{\"layerId\":\"layer1\",\"layerType\":\"data\",\"seriesType\":\"line\",\"xAccessor\":\"col-date\",\"accessors\":[\"col-latency\"]}],
        \"legend\": {\"isVisible\":true},
        \"valueLabels\": \"hide\"
      },
      \"query\": {\"query\":\"\",\"language\":\"kuery\"},
      \"filters\": []
    }
  },
  \"references\": [{\"type\":\"index-pattern\",\"id\":\"$DV_ID\",\"name\":\"indexpattern-datasource-layer-layer1\"}]
}"

# 4 — Error count (metric)
post_object "lens" "iris-error-count" "{
  \"attributes\": {
    \"title\": \"Error Count (status 422)\",
    \"visualizationType\": \"lnsLegacyMetric\",
    \"state\": {
      \"datasourceStates\": {
        \"formBased\": {
          \"layers\": {
            \"layer1\": {
              \"columnOrder\": [\"col-count\"],
              \"columns\": {
                \"col-count\": {\"label\":\"Error Count\",\"dataType\":\"number\",\"operationType\":\"count\",\"sourceField\":\"___records___\",\"isBucketed\":false,\"scale\":\"ratio\"}
              },
              \"indexPatternId\": \"$DV_ID\"
            }
          }
        }
      },
      \"visualization\": {\"layerId\":\"layer1\",\"layerType\":\"data\",\"accessor\":\"col-count\"},
      \"query\": {\"query\":\"status_code: 422\",\"language\":\"kuery\"},
      \"filters\": []
    }
  },
  \"references\": [{\"type\":\"index-pattern\",\"id\":\"$DV_ID\",\"name\":\"indexpattern-datasource-layer-layer1\"}]
}"

# 5 — Confidence histogram
post_object "lens" "iris-confidence-histogram" "{
  \"attributes\": {
    \"title\": \"Confidence Score Distribution\",
    \"visualizationType\": \"lnsXY\",
    \"state\": {
      \"datasourceStates\": {
        \"formBased\": {
          \"layers\": {
            \"layer1\": {
              \"columnOrder\": [\"col-conf\",\"col-count\"],
              \"columns\": {
                \"col-conf\": {\"label\":\"Confidence\",\"dataType\":\"number\",\"operationType\":\"range\",\"sourceField\":\"confidence\",\"isBucketed\":true,\"params\":{\"type\":\"histogram\",\"ranges\":[{\"from\":0,\"to\":1,\"label\":\"\"}],\"maxBars\":\"auto\",\"includeEmptyRows\":true}},
                \"col-count\": {\"label\":\"Count\",\"dataType\":\"number\",\"operationType\":\"count\",\"sourceField\":\"___records___\",\"isBucketed\":false,\"scale\":\"ratio\"}
              },
              \"indexPatternId\": \"$DV_ID\"
            }
          }
        }
      },
      \"visualization\": {
        \"layers\": [{\"layerId\":\"layer1\",\"layerType\":\"data\",\"seriesType\":\"bar\",\"xAccessor\":\"col-conf\",\"accessors\":[\"col-count\"]}],
        \"legend\": {\"isVisible\":false},
        \"valueLabels\": \"hide\"
      },
      \"query\": {\"query\":\"status_code: 200\",\"language\":\"kuery\"},
      \"filters\": []
    }
  },
  \"references\": [{\"type\":\"index-pattern\",\"id\":\"$DV_ID\",\"name\":\"indexpattern-datasource-layer-layer1\"}]
}"

echo ""
echo "Creating dashboard..."

# Write dashboard payload to temp file to avoid escaping issues
TMPFILE=$(mktemp /tmp/iris-dashboard-XXXX.json)
python3 - <<PYEOF > "$TMPFILE"
import json

panels = [
  {"version":"8.12.2","type":"lens","gridData":{"x":0,"y":0,"w":24,"h":15,"i":"p1"},"panelIndex":"p1","embeddableConfig":{},"panelRefName":"panel_p1"},
  {"version":"8.12.2","type":"lens","gridData":{"x":24,"y":0,"w":24,"h":15,"i":"p2"},"panelIndex":"p2","embeddableConfig":{},"panelRefName":"panel_p2"},
  {"version":"8.12.2","type":"lens","gridData":{"x":0,"y":15,"w":24,"h":15,"i":"p3"},"panelIndex":"p3","embeddableConfig":{},"panelRefName":"panel_p3"},
  {"version":"8.12.2","type":"lens","gridData":{"x":24,"y":15,"w":12,"h":15,"i":"p4"},"panelIndex":"p4","embeddableConfig":{},"panelRefName":"panel_p4"},
  {"version":"8.12.2","type":"lens","gridData":{"x":36,"y":15,"w":12,"h":15,"i":"p5"},"panelIndex":"p5","embeddableConfig":{},"panelRefName":"panel_p5"},
]

payload = {
  "attributes": {
    "title": "Iris API Monitoring",
    "description": "Real-time monitoring: requests, predictions, latency, errors, confidence",
    "panelsJSON": json.dumps(panels),
    "optionsJSON": json.dumps({"useMargins": True, "syncColors": False, "hidePanelTitles": False}),
    "timeRestore": False,
    "kibanaSavedObjectMeta": {
      "searchSourceJSON": json.dumps({"query": {"query": "", "language": "kuery"}, "filter": []})
    }
  },
  "references": [
    {"name": "panel_p1", "type": "lens", "id": "iris-requests-over-time"},
    {"name": "panel_p2", "type": "lens", "id": "iris-prediction-distribution"},
    {"name": "panel_p3", "type": "lens", "id": "iris-avg-latency"},
    {"name": "panel_p4", "type": "lens", "id": "iris-error-count"},
    {"name": "panel_p5", "type": "lens", "id": "iris-confidence-histogram"},
  ]
}
print(json.dumps(payload))
PYEOF

result=$(curl -sk -u "$ES_USER:$ES_PASS" \
  -X POST "$KIBANA_URL/api/saved_objects/dashboard/iris-api-monitoring-dashboard?overwrite=true" \
  -H "Content-Type: application/json" \
  -H "kbn-xsrf: true" \
  -d "@$TMPFILE")
rm -f "$TMPFILE"

if echo "$result" | python3 -c "import sys,json; r=json.load(sys.stdin); exit(0 if 'id' in r else 1)" 2>/dev/null; then
  echo "  OK: dashboard/iris-api-monitoring-dashboard"
else
  echo "  FAIL: $result"
fi

echo ""
echo "Done! Open: http://localhost:5601/app/dashboards"
echo "Look for: 'Iris API Monitoring'"
