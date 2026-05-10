#!/usr/bin/env bash
# deploy-bot.sh — Upload source, build image, and run the centinela Telegram bot on the AMD droplet.
# Idempotent: safe to run multiple times. Does NOT touch the demo container.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_NAME="centinela-bot"
ARCHIVE="$REPO_ROOT/centinela-src.tar.gz"

# Load SSH / droplet config from .env
set -a
# shellcheck disable=SC1091
source "$REPO_ROOT/.env"
set +a

REMOTE="root@${DROPLET_IP}"
SSH_OPTS=(-i "$DROPLET_SSH_PRV_KEY_PATH" -o StrictHostKeyChecking=no)
SCP_OPTS=(-i "$DROPLET_SSH_PRV_KEY_PATH" -o StrictHostKeyChecking=no)

echo "==> Archiving tracked files (git archive)"
git -C "$REPO_ROOT" archive --format=tar.gz HEAD -o "$ARCHIVE"

echo "==> Uploading source archive to droplet ($DROPLET_IP)"
scp "${SCP_OPTS[@]}" "$ARCHIVE" "$REMOTE:~/centinela-src.tar.gz"

echo "==> Uploading .env to droplet"
scp "${SCP_OPTS[@]}" "$REPO_ROOT/.env" "$REMOTE:~/centinela.env"

echo "==> Building and deploying bot on droplet"
ssh "${SSH_OPTS[@]}" "$REMOTE" bash <<'REMOTE_SCRIPT'
set -euo pipefail

IMAGE_NAME="centinela-bot"
DATA_DIR="$HOME/centinela-data"
SRC_DIR="$HOME/centinela-src"

echo "  -> Extracting source"
rm -rf "$SRC_DIR" && mkdir -p "$SRC_DIR"
tar -xzf ~/centinela-src.tar.gz -C "$SRC_DIR"

echo "  -> Building image on droplet"
docker build -f "$SRC_DIR/containers/Containerfile.bot" -t "$IMAGE_NAME" "$SRC_DIR"

echo "  -> Stopping and removing existing bot container (if any)"
docker stop "$IMAGE_NAME" 2>/dev/null || true
docker rm   "$IMAGE_NAME" 2>/dev/null || true

echo "  -> Ensuring data directory exists"
mkdir -p "$DATA_DIR"

echo "  -> Starting bot container (no public port)"
docker run -d \
  --name "$IMAGE_NAME" \
  --restart=unless-stopped \
  --env-file ~/centinela.env \
  -e SQLITE_PATH=/app/data/centinela.db \
  -v "$DATA_DIR:/app/data" \
  "$IMAGE_NAME"

echo "  -> Container status"
docker ps --filter "name=$IMAGE_NAME"
REMOTE_SCRIPT

echo "==> Deleting local archive"
rm -f "$ARCHIVE"

echo "==> Done. Tail logs with:"
echo "    ssh ${SSH_OPTS[*]} $REMOTE docker logs -f $IMAGE_NAME"
