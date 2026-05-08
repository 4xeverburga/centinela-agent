#!/usr/bin/env bash
# Usage: ./scripts/stop_vllm.sh
# Stops and removes the vllm-centinela container on the droplet.

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

ssh $SSH_OPTS root@"$DROPLET_IP" "
  docker stop vllm-centinela 2>/dev/null && echo 'Container stopped.' || echo 'Container was not running.'
  docker rm   vllm-centinela 2>/dev/null || true
"
