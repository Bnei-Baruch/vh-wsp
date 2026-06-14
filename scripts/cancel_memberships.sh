#!/usr/bin/env bash
#
# One-off script to cancel memberships for a fixed list of keycloak_ids.
# Usage: ./cancel_memberships.sh
#

set -e

# --- Config ---
BASE_URL="https://api.kli.one"
AUTH_TOKEN="Bearer ..."

# Fixed list of keycloak_ids to cancel
KEYCLOAK_IDS=(
	
)
# --------------


ENDPOINT="${BASE_URL}/profile/v1/membership/cancellation"

if [[ ${#KEYCLOAK_IDS[@]} -eq 0 ]]; then
	echo "KEYCLOAK_IDS is empty. Add keycloak_ids to the array in the script."
	exit 1
fi

echo "Cancelling ${#KEYCLOAK_IDS[@]} memberships..."
echo

for kid in "${KEYCLOAK_IDS[@]}"; do
	out=$(curl -s -w "\n%{http_code}" --max-time 15 \
		-X POST \
		-H "Authorization: ${AUTH_TOKEN}" \
		-H "Content-Type: application/json" \
		-d "{\"keycloak_id\": \"${kid}\"}" \
		"${ENDPOINT}") || { echo "[ERROR]  ${kid} — curl failed"; continue; }
	status=$(echo "$out" | tail -n1)
	body=$(echo "$out" | sed '$d')
	if [[ "$status" -ge 200 && "$status" -lt 300 ]]; then
		msg=$(echo "$body" | sed -n 's/.*"message"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
		echo "[OK]     ${kid} — ${status} ${msg}"
	else
		echo "[FAIL]   ${kid} — ${status} ${body}"
	fi
done

echo
echo "Done."
