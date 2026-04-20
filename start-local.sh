#!/usr/bin/env bash
set -euo pipefail

HA_URL="http://localhost:8123"
USERNAME="homeassistant"
PASSWORD="homeassistant"

# ---------------------------------------------------------------------------
# Args
# ---------------------------------------------------------------------------

if [ $# -lt 1 ]; then
  echo "Usage: $0 <hub-ip-address>"
  echo "  hub-ip-address: IP address of the Norman Hub (e.g. 192.168.1.100)"
  echo ""
  echo "To reset and start fresh:"
  echo "  docker compose down && rm -rf ha-config/ && $0 <hub-ip>"
  exit 1
fi

HUB_HOST="$1"

# ---------------------------------------------------------------------------
# Start container
# ---------------------------------------------------------------------------

echo "Starting Home Assistant container..."
docker compose up -d

# ---------------------------------------------------------------------------
# If ha-config already existed before this run, HA is already onboarded.
# Just bring up the container and open the browser.
# ---------------------------------------------------------------------------

if [ -f "ha-config/.storage/auth" ]; then
  echo "Existing HA config detected — skipping onboarding."
  echo "Open $HA_URL and log in with: $USERNAME / $PASSWORD"
  open "$HA_URL" 2>/dev/null || true
  exit 0
fi

# ---------------------------------------------------------------------------
# Wait for HA to be ready (onboarding endpoint returns 200)
# ---------------------------------------------------------------------------

echo -n "Waiting for Home Assistant to start"
for i in $(seq 1 60); do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$HA_URL/api/onboarding" || true)
  if [ "$STATUS" = "200" ]; then
    echo " ready."
    break
  fi
  echo -n "."
  sleep 2
  if [ "$i" = "60" ]; then
    echo ""
    echo "ERROR: Home Assistant did not start within 120 seconds."
    echo "Check logs with: docker compose logs homeassistant"
    exit 1
  fi
done

# ---------------------------------------------------------------------------
# Helper: extract JSON field without jq
# ---------------------------------------------------------------------------
extract() {
  python3 -c "import sys, json; print(json.load(sys.stdin)['$1'])"
}

# ---------------------------------------------------------------------------
# Onboarding: create admin user
# ---------------------------------------------------------------------------

echo "Creating admin user..."
AUTH_CODE=$(curl -s -X POST "$HA_URL/api/onboarding/users" \
  -H "Content-Type: application/json" \
  -d "{
    \"client_id\": \"$HA_URL/\",
    \"name\": \"Admin\",
    \"username\": \"$USERNAME\",
    \"password\": \"$PASSWORD\",
    \"language\": \"en\"
  }" | extract "auth_code")

# ---------------------------------------------------------------------------
# Exchange auth code for access token
# ---------------------------------------------------------------------------

echo "Obtaining access token..."
TOKEN=$(curl -s -X POST "$HA_URL/auth/token" \
  -d "client_id=$HA_URL/&grant_type=authorization_code&code=$AUTH_CODE" \
  | extract "access_token")

AUTH_HEADER="Authorization: Bearer $TOKEN"

# ---------------------------------------------------------------------------
# Complete onboarding steps
# ---------------------------------------------------------------------------

echo "Completing core configuration..."
curl -s -X POST "$HA_URL/api/onboarding/core_config" \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{
    "location_name": "Home",
    "latitude": 37.3382,
    "longitude": -121.8863,
    "elevation": 0,
    "unit_system": "us_customary",
    "time_zone": "America/Chicago",
    "currency": "USD",
    "language": "en",
    "country": "US"
  }' > /dev/null

echo "Completing analytics setup..."
curl -s -X POST "$HA_URL/api/onboarding/analytics" \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{}' > /dev/null

# ---------------------------------------------------------------------------
# Wait for HA to finish loading custom components (pynormanshutters install)
# ---------------------------------------------------------------------------

echo -n "Waiting for Norman Shutters integration to load"
for i in $(seq 1 30); do
  HTTP=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "$AUTH_HEADER" \
    "$HA_URL/api/config/config_entries/flow" || true)
  if [ "$HTTP" = "200" ] || [ "$HTTP" = "405" ]; then
    echo " ready."
    break
  fi
  echo -n "."
  sleep 2
  if [ "$i" = "30" ]; then
    echo ""
    echo "WARNING: API not ready after 60s — proceeding anyway."
  fi
done

# ---------------------------------------------------------------------------
# Create Norman Shutters config entry via config flow
# ---------------------------------------------------------------------------

echo "Starting Norman Shutters config flow..."
FLOW_RESPONSE=$(curl -s -X POST "$HA_URL/api/config/config_entries/flow" \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{"handler": "norman_shutters"}')

FLOW_ID=$(echo "$FLOW_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['flow_id'])")

echo "Submitting hub address ($HUB_HOST)..."
RESULT=$(curl -s -X POST "$HA_URL/api/config/config_entries/flow/$FLOW_ID" \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d "{\"host\": \"$HUB_HOST\"}")

RESULT_TYPE=$(echo "$RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('type', 'unknown'))")

if [ "$RESULT_TYPE" = "create_entry" ]; then
  echo "Norman Shutters integration configured successfully."
else
  echo "WARNING: Config flow returned type='$RESULT_TYPE' — the integration may not have connected to the hub."
  echo "  Response: $RESULT"
  echo "  You can configure it manually at $HA_URL via Settings → Devices & Services."
fi

# ---------------------------------------------------------------------------
# Open browser
# ---------------------------------------------------------------------------

echo ""
echo "Setup complete!"
echo "  URL:      $HA_URL"
echo "  Username: $USERNAME"
echo "  Password: $PASSWORD"
echo ""
open "$HA_URL" 2>/dev/null || echo "Open $HA_URL in your browser."
