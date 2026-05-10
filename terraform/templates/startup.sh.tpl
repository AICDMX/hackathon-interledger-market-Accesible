#!/bin/bash
set -euo pipefail

LOG="/var/log/voxvox-startup.log"
exec > >(tee -a "$LOG") 2>&1

MARKER="/var/lib/voxvox-startup-done"
DEV_USER="${dev_username}"
DEV_HOME="/home/$DEV_USER"
export HOME="/root"

if [ -f "$MARKER" ]; then
    echo "==> Startup already completed, skipping. Delete $MARKER to re-run."
    exit 0
fi

echo "=========================================="
echo "VoxVos Dev — VM Startup Script"
echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "=========================================="

# -- 1. System packages -------------------------------------------------------

echo "==> Installing system packages..."
apt-get update -qq
apt-get install -y -qq \
    apt-transport-https ca-certificates curl gnupg lsb-release \
    git make build-essential unzip wget jq software-properties-common \
    tmux

echo "==> Installing GitHub CLI (gh)..."
(type -p wget >/dev/null || apt-get install -y -qq wget) \
  && mkdir -p -m 755 /etc/apt/keyrings \
  && out=$(mktemp) && wget -nv -O"$out" https://cli.github.com/packages/githubcli-archive-keyring.gpg \
  && cat "$out" | tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
  && chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
  && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
    | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
  && apt-get update -qq && apt-get install -y -qq gh

# -- 2. Docker -----------------------------------------------------------------

echo "==> Installing Docker..."
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
  > /etc/apt/sources.list.d/docker.list

apt-get update -qq
apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

systemctl enable docker
systemctl start docker

echo "==> Docker version: $(docker --version)"

# -- 3. Create dev user --------------------------------------------------------

echo "==> Creating dev user '$DEV_USER'..."
if ! id "$DEV_USER" &>/dev/null; then
    useradd -m -s /bin/bash "$DEV_USER"
fi
usermod -aG docker "$DEV_USER"

# Passwordless sudo
echo "$DEV_USER ALL=(ALL) NOPASSWD:ALL" > "/etc/sudoers.d/$DEV_USER"
chmod 0440 "/etc/sudoers.d/$DEV_USER"

# SSH authorized_keys from instance metadata
echo "==> Setting up SSH authorized_keys for $DEV_USER..."
SSH_KEYS=$(curl -sf -H "Metadata-Flavor: Google" "http://metadata.google.internal/computeMetadata/v1/instance/attributes/ssh-keys" || true)
if [ -n "$SSH_KEYS" ]; then
    mkdir -p "$DEV_HOME/.ssh"
    echo "$SSH_KEYS" | cut -d: -f2- > "$DEV_HOME/.ssh/authorized_keys"
    chmod 700 "$DEV_HOME/.ssh"
    chmod 600 "$DEV_HOME/.ssh/authorized_keys"
    chown -R "$DEV_USER:$DEV_USER" "$DEV_HOME/.ssh"
fi

# -- 4. Node.js 20 LTS --------------------------------------------------------

echo "==> Installing Node.js 20 LTS..."
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y -qq nodejs

echo "==> Node version: $(node --version)"
echo "==> npm version: $(npm --version)"

# -- 5. Claude Code ------------------------------------------------------------

echo "==> Installing Claude Code..."
npm install -g @anthropic-ai/claude-code || echo "  (Claude Code install failed, can retry manually)"

# -- 6. OpenAI Codex CLI ------------------------------------------------------

echo "==> Installing OpenAI Codex CLI..."
npm install -g @openai/codex || echo "  (Codex CLI install failed, can retry manually)"

# -- 7. Tool auto-update cron -------------------------------------------------

echo "==> Setting up tool auto-update..."
UPDATE_SCRIPT="$DEV_HOME/vm-files/update-tools.sh"
UPDATE_LOG_DIR="$DEV_HOME/.tool-updates"

METADATA_URL="http://metadata.google.internal/computeMetadata/v1/instance/attributes"
METADATA_HEADER="Metadata-Flavor: Google"

mkdir -p "$DEV_HOME/vm-files"
curl -sf -H "$METADATA_HEADER" "$METADATA_URL/update-tools-sh" > "$UPDATE_SCRIPT"
chmod +x "$UPDATE_SCRIPT"
chown -R "$DEV_USER:$DEV_USER" "$DEV_HOME/vm-files"
mkdir -p "$UPDATE_LOG_DIR"
chown "$DEV_USER:$DEV_USER" "$UPDATE_LOG_DIR"

CRON_UPDATE="0 6 * * * $UPDATE_SCRIPT all >> $UPDATE_LOG_DIR/cron.log 2>&1"
( su - "$DEV_USER" -c "crontab -l" 2>/dev/null | grep -v 'update-tools.sh' || true ; echo "$CRON_UPDATE" ) | su - "$DEV_USER" -c "crontab -"
echo "==> Cron job installed: daily 6:00 AM UTC tool update"

# -- 8. uv (Python package manager) -------------------------------------------

echo "==> Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh
cp /root/.local/bin/uv /usr/local/bin/uv
cp /root/.local/bin/uvx /usr/local/bin/uvx
echo "==> uv version: $(uv --version)"

# -- 9. Clone marketplace repo ------------------------------------------------

echo "==> Cloning marketplace repo..."
REPO_TARGET="$DEV_HOME/marketplace"
GIT_BRANCH="${git_branch}"

if [ -d "$REPO_TARGET" ]; then
    echo "==> $REPO_TARGET already exists, skipping clone."
else
    sudo -u "$DEV_USER" git clone "${repo_url}" "$REPO_TARGET" || { echo "WARNING: Failed to clone repo"; }
    if [ -d "$REPO_TARGET" ]; then
        sudo -u "$DEV_USER" bash -c "cd '$REPO_TARGET' && git checkout '$GIT_BRANCH' 2>/dev/null || true"
    fi
fi

# -- 10. Install Python dependencies ------------------------------------------

echo "==> Installing Python dependencies..."
if [ -d "$REPO_TARGET/marketplace-py" ]; then
    sudo -u "$DEV_USER" bash -c "cd '$REPO_TARGET/marketplace-py' && uv sync" || echo "  (uv sync failed, can retry manually)"
fi

# -- 11. Extract VM Makefile from metadata -------------------------------------

echo "==> Extracting VM Makefile from metadata..."
curl -sf -H "$METADATA_HEADER" "$METADATA_URL/vm-makefile" > "$DEV_HOME/Makefile"
chown "$DEV_USER:$DEV_USER" "$DEV_HOME/Makefile"

# -- 12. Extract and set up Docker Compose -------------------------------------

echo "==> Setting up Docker Compose..."
DEPLOY_DIR="$DEV_HOME/marketplace-deploy"
mkdir -p "$DEPLOY_DIR"

curl -sf -H "$METADATA_HEADER" "$METADATA_URL/docker-compose" > "$DEPLOY_DIR/docker-compose.yml"
chown -R "$DEV_USER:$DEV_USER" "$DEPLOY_DIR"

# -- 13. Start services -------------------------------------------------------

echo "==> Starting services via Docker Compose..."
sudo -u "$DEV_USER" bash -c "cd $DEPLOY_DIR && docker compose up -d" || echo "  (docker compose up failed, can retry with: make up)"

# -- 14. Cloudflare Tunnel -----------------------------------------------------

CF_TOKEN="${cloudflare_tunnel_token}"
if [ -n "$CF_TOKEN" ]; then
    echo "==> Installing Cloudflare Tunnel..."
    curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o /tmp/cloudflared.deb
    dpkg -i /tmp/cloudflared.deb
    rm /tmp/cloudflared.deb
    cloudflared service install "$CF_TOKEN"
    echo "==> Cloudflare Tunnel installed and running."
else
    echo "==> Skipping Cloudflare Tunnel (no token provided)."
fi

# -- 15. Shell environment ------------------------------------------------------

echo "==> Configuring shell environment..."

cat > "$DEV_HOME/.voxvox-env" << 'ENVEOF'
# VoxVos Dev — API keys (auto-generated by Terraform)
export ANTHROPIC_API_KEY="${anthropic_api_key}"
export OPENAI_API_KEY="${openai_api_key}"
ENVEOF
chmod 600 "$DEV_HOME/.voxvox-env"
chown "$DEV_USER:$DEV_USER" "$DEV_HOME/.voxvox-env"

cat >> "$DEV_HOME/.bashrc" << 'BASHEOF'

# -- VoxVos Dev Environment ---------------------------------------------------
export PATH=/usr/local/bin:/usr/bin:$HOME/.local/bin:$PATH

# API keys
[ -f "$HOME/.voxvox-env" ] && source "$HOME/.voxvox-env"

# Aliases
alias dev-run='cd ~/marketplace/marketplace-py && uv run python manage.py runserver 0.0.0.0:8000'
alias dev-migrate='cd ~/marketplace/marketplace-py && uv run python manage.py migrate'
alias dev-test='cd ~/marketplace/marketplace-py && uv run python manage.py test'
alias claude-market='cd ~/marketplace && claude --dangerously-skip-permissions'
alias codex-market='cd ~/marketplace && codex --dangerously-bypass-approvals-and-sandbox'
alias logs='sudo tail -f /var/log/voxvox-startup.log'
alias dps='docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'
BASHEOF
chown "$DEV_USER:$DEV_USER" "$DEV_HOME/.bashrc"

# -- 16. Fix ownership ---------------------------------------------------------

echo "==> Fixing file ownership..."
chown -R "$DEV_USER:$DEV_USER" "$DEV_HOME"

# -- 17. Mark complete ---------------------------------------------------------

touch "$MARKER"

echo "=========================================="
echo "VoxVos Dev startup complete!"
echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo ""
echo "  dev-run        — Django dev server on :8000"
echo "  dev-migrate    — Run migrations"
echo "  dev-test       — Run tests"
echo "  claude-market  — Claude Code in marketplace repo"
echo "  codex-market   — Codex CLI in marketplace repo"
echo "  dps            — Show running containers"
echo "=========================================="
