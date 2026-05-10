#!/usr/bin/env bash
# deploy-bot.sh — Upload source and build/run the centinela bot + demo API on the AMD GPU droplet.
# Idempotent: safe to run multiple times.
#
# Containers deployed:
#   centinela-bot   — Telegram bot (no exposed port, outbound only via PTB)
#   centinela-demo  — Demo Flask API  (host port DEMO_PORT, sourced from .env)
#
# Firewall: opens DEMO_PORT via ufw on the remote host if not already open.
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

echo "==> Building and deploying on droplet"
ssh "${SSH_OPTS[@]}" "$REMOTE" bash <<REMOTE_SCRIPT
set -euo pipefail

IMAGE_NAME="centinela-bot"
DATA_DIR="\$HOME/centinela-data"
SRC_DIR="\$HOME/centinela-src"
DEMO_PORT="${DEMO_PORT}"

echo "  -> Extracting source"
rm -rf "\$SRC_DIR" && mkdir -p "\$SRC_DIR"
tar -xzf ~/centinela-src.tar.gz -C "\$SRC_DIR"

echo "  -> Building image on droplet"
docker build -f "\$SRC_DIR/containers/Containerfile.bot" -t "\$IMAGE_NAME" "\$SRC_DIR"

echo "  -> Stopping and removing existing containers (if any)"
docker stop "\$IMAGE_NAME"      2>/dev/null || true
docker rm   "\$IMAGE_NAME"      2>/dev/null || true
docker stop centinela-demo      2>/dev/null || true
docker rm   centinela-demo      2>/dev/null || true

echo "  -> Ensuring data directory exists"
mkdir -p "\$DATA_DIR"

echo "  -> Opening firewall port \$DEMO_PORT (ufw)"
if command -v ufw &>/dev/null; then
  ufw allow "\$DEMO_PORT"/tcp || true
fi

echo "  -> Starting bot container"
docker run -d \\
  --name "\$IMAGE_NAME" \\
  --restart=unless-stopped \\
  --env-file ~/centinela.env \\
  -e SQLITE_PATH=/app/data/centinela.db \\
  -v "\$DATA_DIR:/app/data" \\
  "\$IMAGE_NAME"

echo "  -> Starting demo API container (port \$DEMO_PORT)"
docker run -d \\
  --name centinela-demo \\
  --restart=unless-stopped \\
  --env-file ~/centinela.env \\
  -e SQLITE_PATH=/app/data/centinela.db \\
  -e DEMO_PORT=\$DEMO_PORT \\
  -v "\$DATA_DIR:/app/data" \\
  -p "\$DEMO_PORT:\$DEMO_PORT" \\
  "\$IMAGE_NAME" \\
  python src/demo_server.py

echo "  -> Container status"
docker ps --filter "name=centinela"
REMOTE_SCRIPT

echo "==> Deleting local archive"
rm -f "$ARCHIVE"

echo "==> Done. Tail logs with:"
echo "    ssh ${SSH_OPTS[*]} $REMOTE docker logs -f $IMAGE_NAME"
echo "    ssh ${SSH_OPTS[*]} $REMOTE docker logs -f centinela-demo"
echo "==> Demo API reachable at: http://$DROPLET_IP:$DEMO_PORT"
