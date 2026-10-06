#!/usr/bin/env bash
# One-time setup on the Raspberry Pi. Run via `scripts/deploy.sh --setup` (uses sudo).
set -euo pipefail

APP=$(cd "$(dirname "$0")/.." && pwd)
U=${SUDO_USER:?run with sudo as your normal user}
REBOOT=0

echo "→ system packages"
apt-get update -q
apt-get install -y -q python3-venv python3-pip python3-opencv python3-picamera2 fonts-dejavu-core \
  python3-gpiozero python3-lgpio python3-spidev

# Which display? (config.toml [frame] display = "inky" | "waveshare:...")
DISPLAY_KIND=$(python3 -c 'import sys, tomllib; print(tomllib.load(open(sys.argv[1], "rb")).get("frame", {}).get("display", "inky"))' \
  "$APP/config.toml" 2>/dev/null || echo inky)
echo "→ enabling SPI + I2C for the display ($DISPLAY_KIND)"
raspi-config nonint do_spi 0
raspi-config nonint do_i2c 0
CFG=/boot/firmware/config.txt
if [ "$DISPLAY_KIND" = inky ]; then
  # Pimoroni's Spectra Inkys drive the SPI chip-select themselves (see their inky README).
  if ! grep -q '^dtoverlay=spi0-0cs' "$CFG"; then
    printf '\n[all]\ndtoverlay=spi0-0cs\n' >> "$CFG"
    REBOOT=1
  fi
else
  # Waveshare uses the normal hardware chip-select, which spi0-0cs would switch off.
  if grep -q '^dtoverlay=spi0-0cs' "$CFG"; then
    sed -i '/^dtoverlay=spi0-0cs/d' "$CFG"
    REBOOT=1
  fi
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

# Let deploy.sh restart the services without a password (only these commands).
SUDOERS=/etc/sudoers.d/gibbird
for a in start stop restart; do echo "$U ALL=(root) NOPASSWD: /usr/bin/systemctl $a gibbird-cam gibbird-frame"; done > "$SUDOERS.tmp"
chmod 440 "$SUDOERS.tmp"
visudo -cf "$SUDOERS.tmp" >/dev/null && mv "$SUDOERS.tmp" "$SUDOERS"

if [ "$REBOOT" = 1 ]; then
  echo "→ display interface changed: rebooting"
  systemd-run --on-active=3 systemctl reboot >/dev/null
  exit 10  # tells deploy.sh to stop here
fi
