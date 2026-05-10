#!/usr/bin/env bash
# Usage: ./scripts/start_vllm.sh
#
# Reads DROPLET_IP, DROPLET_SSH_PRV_KEY_PATH, HF_TOKEN, VLLM_MODEL
# from .env in the repo root, then SSHes into the AMD droplet and
# starts (or restarts) the vllm/vllm-openai-rocm container.
#
# Pre-conditions:
#   - .env is populated (copy .env.example and fill in the blanks)
#   - The droplet must be reachable on port 22
#   - HF_TOKEN must have read access to google/gemma-4-31B-it

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../.env"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: .env not found at $ENV_FILE" >&2
  exit 1
fi

# Load only the vars we need from .env (ignore comments, blank lines)
get_env() {
  grep -E "^$1=" "$ENV_FILE" | head -1 | cut -d= -f2- | tr -d '\r'
}

DROPLET_IP=$(get_env DROPLET_IP)
SSH_KEY=$(get_env DROPLET_SSH_PRV_KEY_PATH)
HF_TOKEN=$(get_env HF_TOKEN)
VLLM_MODEL=$(get_env VLLM_MODEL)
CONTAINER_NAME="vllm-centinela"
VLLM_IMAGE="vllm/vllm-openai-rocm:nightly"

if [[ -z "$HF_TOKEN" || "$HF_TOKEN" == "REPLACE_ME" ]]; then
  echo "ERROR: HF_TOKEN is not set in .env. Fill it in before running this script." >&2
  exit 1
fi

SSH_OPTS="-o StrictHostKeyChecking=no -o BatchMode=yes"
[[ -n "$SSH_KEY" && -f "$SSH_KEY" ]] && SSH_OPTS="$SSH_OPTS -i $SSH_KEY"

echo "==> Connecting to $DROPLET_IP ..."
echo "==> Model: $VLLM_MODEL"

# Build the docker run command executed on the remote host
REMOTE_CMD=$(cat <<EOF
set -euo pipefail

# Stop and remove any existing instance
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm   $CONTAINER_NAME 2>/dev/null || true

docker run -d \\
  --name $CONTAINER_NAME \\
  --device /dev/kfd \\
  --device /dev/dri \\
  --group-add video \\
  --ipc=host \\
  --cap-add=SYS_PTRACE \\
  --security-opt seccomp=unconfined \\
  --shm-size=16g \\
  -p 8000:8000 \\
  -v /root/.cache/huggingface:/root/.cache/huggingface \\
  -e HF_TOKEN=$HF_TOKEN \\
  -e HUGGING_FACE_HUB_TOKEN=$HF_TOKEN \\
  -e HSA_OVERRIDE_GFX_VERSION=9.4.2 \\
  $VLLM_IMAGE \\
  --model $VLLM_MODEL \\
  --dtype bfloat16 \\
  --max-model-len 16384 \\
  --gpu-memory-utilization 0.90 \\
  --trust-remote-code \\
  --enforce-eager

echo "Container started. Tailing logs for 30s to confirm model load..."
sleep 5
docker logs -f --tail=50 $CONTAINER_NAME &
LOGS_PID=\$!
sleep 25
kill \$LOGS_PID 2>/dev/null || true
echo ""
echo "==> Check status: docker ps | grep $CONTAINER_NAME"
echo "==> Full logs:    docker logs -f $CONTAINER_NAME"
echo "==> Test:         curl http://localhost:8000/v1/models"
EOF
)

# shellcheck disable=SC2029
ssh $SSH_OPTS root@"$DROPLET_IP" "$REMOTE_CMD"
