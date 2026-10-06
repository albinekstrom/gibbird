#!/usr/bin/env bash
# Deploy GibBird from this computer to the Raspberry Pi over SSH.
#
#   scripts/deploy.sh            sync code + config, reinstall if dependencies changed, restart
#   scripts/deploy.sh --setup    first time: system packages, SPI/I2C, venv, services
#   scripts/deploy.sh --logs     follow the service logs
#   scripts/deploy.sh --status   show service status and CPU temperature
#
# Target host: GIBBIRD_HOST (default albin@birdframe.local); code goes to ~/gibbird.
# Your local config.toml (if any) is copied too; data/ on the Pi is never touched.
set -euo pipefail

HOST=${GIBBIRD_HOST:-albin@birdframe.local}
DIR=gibbird
cd "$(dirname "$0")/.."

# macOS often picks the Pi's IPv6 link-local address for .local names and then fails
# with "Undefined error: 0"; IPv4 is reliable.
SSH_OPTS="-o AddressFamily=inet -o ConnectTimeout=10"
ssh() { command ssh $SSH_OPTS "$@"; }

case "${1:-}" in
  --logs) ssh -t "$HOST" "journalctl -f -u gibbird-cam -u gibbird-frame"; exit ;;
  --status) ssh "$HOST" "systemctl --no-pager status gibbird-cam gibbird-frame | grep -E '●|Active'; vcgencmd measure_temp"; exit ;;
  --setup | "") ;;
  *) sed -n '2,10p' "$0"; exit 1 ;;
esac

[ -f models/inat_bird_labels.txt ] || scripts/download_model.sh

echo "→ syncing to $HOST:~/$DIR"
ssh "$HOST" "command -v rsync >/dev/null" || { echo "Install rsync on the Pi: sudo apt install rsync"; exit 1; }
# Excluded paths are also protected from --delete, so the Pi's venv and data survive.
rsync -az --delete --exclude-from=.deployignore -e "ssh $SSH_OPTS" ./ "$HOST:$DIR/"
if [ -f config.toml ]; then rsync -az -e "ssh $SSH_OPTS" config.toml "$HOST:$DIR/config.toml"; fi

if [ "${1:-}" = --setup ]; then
  rc=0
  ssh -t "$HOST" "sudo bash $DIR/scripts/pi_setup.sh" || rc=$?
  if [ "$rc" = 10 ]; then
    echo "✓ setup done; the Pi is rebooting. Wait a minute, then run: scripts/deploy.sh"
    exit 0
  fi
  [ "$rc" = 0 ] || exit "$rc"
fi

ssh "$HOST" bash -s <<EOF
set -euo pipefail
cd $DIR
[ -d .venv ] || { echo "Not set up yet: run scripts/deploy.sh --setup"; exit 1; }
[ -f config.toml ] || cp config.example.toml config.toml
if ! cmp -s pyproject.toml .venv/.installed-pyproject; then
  echo "→ installing Python dependencies"
  .venv/bin/pip install -q -e '.[cam,frame]' && cp pyproject.toml .venv/.installed-pyproject
fi
echo "→ restarting services"
sudo -n systemctl restart gibbird-cam gibbird-frame
sleep 3
systemctl --no-pager is-active gibbird-cam gibbird-frame || true
EOF
echo "✓ deployed. Logs: scripts/deploy.sh --logs   Web: http://${HOST#*@}:8080"
