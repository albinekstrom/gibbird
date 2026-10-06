#!/usr/bin/env bash
# One-time setup on the Raspberry Pi. Run via `scripts/deploy.sh --setup` (uses sudo).
set -euo pipefail

APP=$(cd "$(dirname "$0")/.." && pwd)
U=${SUDO_USER:?run with sudo as your normal user}
REBOOT=0

echo "→ system packages"
apt-get update -q
apt-get install -y -q python3-venv python3-pip python3-opencv python3-picamera2 fonts-dejavu-core

echo "→ enabling SPI + I2C for the Inky display"
raspi-config nonint do_spi 0
raspi-config nonint do_i2c 0
CFG=/boot/firmware/config.txt
# The 13.3" Inky drives both SPI chip-selects itself (see Pimoroni's inky README).
if ! grep -q '^dtoverlay=spi0-0cs' "$CFG"; then
  printf '\n[all]\ndtoverlay=spi0-0cs\n' >> "$CFG"
  REBOOT=1
fi

echo "→ Python environment"
[ -d "$APP/.venv" ] || sudo -u "$U" python3 -m venv --system-site-packages "$APP/.venv"
sudo -u "$U" "$APP/.venv/bin/pip" install -q --upgrade pip
sudo -u "$U" "$APP/.venv/bin/pip" install -q -e "$APP[cam,frame]"
sudo -u "$U" cp "$APP/pyproject.toml" "$APP/.venv/.installed-pyproject"

echo "→ services"
for s in cam frame; do
  sed -e "s|^User=.*|User=$U|" -e "s|/home/pi/gibbird|$APP|g" \
    "$APP/systemd/gibbird-$s.service" > "/etc/systemd/system/gibbird-$s.service"
done
systemctl daemon-reload
systemctl enable gibbird-cam gibbird-frame

if [ "$REBOOT" = 1 ]; then
  echo "→ display interface changed: rebooting"
  systemd-run --on-active=3 systemctl reboot >/dev/null
  exit 10  # tells deploy.sh to stop here
fi
