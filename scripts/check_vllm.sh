#!/usr/bin/env bash
# Usage: ./scripts/check_vllm.sh
# Prints container status and probes the /v1/models endpoint.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../.env"

get_env() {
  grep -E "^$1=" "$ENV_FILE" | head -1 | cut -d= -f2- | tr -d '\r'
}

DROPLET_IP=$(get_env DROPLET_IP)
SSH_KEY=$(get_env DROPLET_SSH_PRV_KEY_PATH)

SSH_OPTS="-o StrictHostKeyChecking=no -o BatchMode=yes"
[[ -n "$SSH_KEY" && -f "$SSH_KEY" ]] && SSH_OPTS="$SSH_OPTS -i $SSH_KEY"

echo "==> Container status:"
ssh $SSH_OPTS root@"$DROPLET_IP" "docker ps --filter name=vllm-centinela --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"

echo ""
echo "==> /v1/models probe:"
ssh $SSH_OPTS root@"$DROPLET_IP" "curl -sf http://localhost:8000/v1/models | python3 -m json.tool 2>/dev/null || echo 'Not ready yet (model may still be loading).'"
