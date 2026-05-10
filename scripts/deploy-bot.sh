#!/usr/bin/env bash
# deploy-bot.sh — Build, upload, and run the centinela bot on the AMD GPU droplet.
# Idempotent: safe to run multiple times.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_NAME="centinela-bot"
TAR_FILE="$REPO_ROOT/centinela-bot.tar"

# Load SSH / droplet config from .env
set -a
# shellcheck disable=SC1091
source "$REPO_ROOT/.env"
set +a

REMOTE="root@${DROPLET_IP}"
SSH_OPTS=(-i "$DROPLET_SSH_PRV_KEY_PATH" -o StrictHostKeyChecking=no)
SCP_OPTS=(-i "$DROPLET_SSH_PRV_KEY_PATH" -o StrictHostKeyChecking=no)

echo "==> Building image: $IMAGE_NAME"
podman build -f "$REPO_ROOT/containers/Containerfile.bot" -t "$IMAGE_NAME" "$REPO_ROOT"

echo "==> Saving image to $TAR_FILE"
podman save "$IMAGE_NAME" -o "$TAR_FILE"

echo "==> Uploading image tar to droplet ($DROPLET_IP)"
scp "${SCP_OPTS[@]}" "$TAR_FILE" "$REMOTE:~/centinela-bot.tar"

echo "==> Uploading .env to droplet"
scp "${SCP_OPTS[@]}" "$REPO_ROOT/.env" "$REMOTE:~/centinela.env"

echo "==> Deploying on droplet"
ssh "${SSH_OPTS[@]}" "$REMOTE" bash <<'REMOTE_SCRIPT'
set -euo pipefail

IMAGE_NAME="centinela-bot"
DATA_DIR="$HOME/centinela-data"

echo "  -> Loading image"
podman load -i ~/centinela-bot.tar

echo "  -> Stopping and removing existing container (if any)"
podman stop "$IMAGE_NAME" 2>/dev/null || true
podman rm   "$IMAGE_NAME" 2>/dev/null || true

echo "  -> Ensuring data directory exists"
mkdir -p "$DATA_DIR"

echo "  -> Starting container"
podman run -d \
  --name "$IMAGE_NAME" \
  --restart=unless-stopped \
  --env-file ~/centinela.env \
  -e SQLITE_PATH=/app/data/centinela.db \
  -v "$DATA_DIR:/app/data" \
  "$IMAGE_NAME"

echo "  -> Container status"
podman ps --filter "name=$IMAGE_NAME"
REMOTE_SCRIPT

echo "==> Deleting local tar file"
rm -f "$TAR_FILE"

echo "==> Done. Tail logs with:"
echo "    ssh ${SSH_OPTS[*]} $REMOTE podman logs -f $IMAGE_NAME"
