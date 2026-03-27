#!/usr/bin/env bash
# deploy/deploy.sh — Deploy DORA dashboard + Jira proxy to Oracle VM
# Run from the repo root: ./deploy/deploy.sh
#
# Prerequisites:
#   1. DNS A record added: dora.techjalebi.com → 144.24.130.27
#   2. .env file present at repo root with JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN

set -euo pipefail

SSH_KEY="/home/amit/ai_projects/scrum_engg_team/ssh-key-2026-03-03.key"
VM="ubuntu@144.24.130.27"
REMOTE_DIR="/home/ubuntu/dora"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== DORA Dashboard Deployment ==="
echo "Target: $VM:$REMOTE_DIR"
echo ""

# ── 1. Read Jira creds from local .env ──────────────────────────────────────
ENV_FILE="$REPO_ROOT/.env"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: .env not found at $ENV_FILE"
  exit 1
fi

JIRA_BASE_URL=$(grep -E '^JIRA_BASE_URL=' "$ENV_FILE" | cut -d= -f2-)
JIRA_EMAIL=$(grep -E '^JIRA_EMAIL=' "$ENV_FILE" | cut -d= -f2-)
JIRA_API_TOKEN=$(grep -E '^JIRA_API_TOKEN=' "$ENV_FILE" | cut -d= -f2-)

if [[ -z "$JIRA_BASE_URL" || -z "$JIRA_EMAIL" || -z "$JIRA_API_TOKEN" ]]; then
  echo "ERROR: JIRA_BASE_URL, JIRA_EMAIL, or JIRA_API_TOKEN missing from .env"
  exit 1
fi

# ── 2. Create remote directory ───────────────────────────────────────────────
echo "→ Creating $REMOTE_DIR on VM..."
ssh -i "$SSH_KEY" "$VM" "mkdir -p $REMOTE_DIR"

# ── 3. Upload dashboard (static files) ──────────────────────────────────────
echo "→ Uploading dashboard/..."
scp -i "$SSH_KEY" -r "$REPO_ROOT/dashboard/" "$VM:$REMOTE_DIR/"

# ── 4. Upload proxy ──────────────────────────────────────────────────────────
echo "→ Uploading proxy/..."
scp -i "$SSH_KEY" -r "$REPO_ROOT/proxy/" "$VM:$REMOTE_DIR/"

# ── 5. Set up Python venv + install python-dotenv ───────────────────────────
echo "→ Setting up Python venv on VM..."
ssh -i "$SSH_KEY" "$VM" "
  cd $REMOTE_DIR
  python3 -m venv venv
  venv/bin/pip install --quiet --upgrade pip
  venv/bin/pip install --quiet python-dotenv
"

# ── 6. Write .env on VM (Jira creds only) ───────────────────────────────────
echo "→ Writing .env on VM..."
ssh -i "$SSH_KEY" "$VM" "cat > $REMOTE_DIR/.env" << EOF
JIRA_BASE_URL=$JIRA_BASE_URL
JIRA_EMAIL=$JIRA_EMAIL
JIRA_API_TOKEN=$JIRA_API_TOKEN
JIRA_PROJECT_KEY=DORA
PROXY_PORT=5002
EOF

# ── 7. Install systemd service ───────────────────────────────────────────────
echo "→ Installing dora-proxy.service..."
scp -i "$SSH_KEY" "$REPO_ROOT/deploy/dora-proxy.service" "$VM:/tmp/dora-proxy.service"
ssh -i "$SSH_KEY" "$VM" "
  sudo mv /tmp/dora-proxy.service /etc/systemd/system/dora-proxy.service
  sudo systemctl daemon-reload
  sudo systemctl enable dora-proxy
  sudo systemctl restart dora-proxy
  sudo systemctl status dora-proxy --no-pager
"

# ── 8. Install nginx site config ─────────────────────────────────────────────
echo "→ Installing nginx config..."
scp -i "$SSH_KEY" "$REPO_ROOT/deploy/nginx-dora" "$VM:/tmp/nginx-dora"
ssh -i "$SSH_KEY" "$VM" "
  sudo mv /tmp/nginx-dora /etc/nginx/sites-available/dora
  sudo ln -sf /etc/nginx/sites-available/dora /etc/nginx/sites-enabled/dora
  sudo nginx -t
  sudo systemctl reload nginx
"

# ── 9. Smoke test ────────────────────────────────────────────────────────────
echo ""
echo "→ Smoke test: proxy reachable from VM..."
ssh -i "$SSH_KEY" "$VM" \
  "curl -s -o /dev/null -w '%{http_code}' http://localhost:5002/jira/rest/api/3/myself" \
  | grep -q "200" && echo "  Proxy OK (200)" || echo "  WARNING: proxy returned non-200"

echo ""
echo "=== Deployment complete ==="
echo ""
echo "Next step — run certbot for SSL (only after DNS has propagated):"
echo ""
echo "  ssh -i $SSH_KEY $VM \\"
echo "    'sudo certbot --nginx -d dora.techjalebi.com'"
echo ""
echo "Then open: https://dora.techjalebi.com"
