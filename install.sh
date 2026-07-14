#!/usr/bin/env bash
# Glass FM — installer for a Linux VM or Termux / proot-distro.
# Use Dockerfile instead when deploying to a HF Docker Space.
set -e

echo "== Glass FM installer =="

# ---- detect environment + get python3/pip in place ----
if command -v pkg >/dev/null 2>&1; then
  echo "-> Termux detected"
  pkg update -y
  pkg install -y python
elif command -v apt-get >/dev/null 2>&1; then
  echo "-> Debian/Ubuntu (VM or proot-distro) detected"
  apt-get update -y
  apt-get install -y python3 python3-venv python3-pip
elif command -v python3 >/dev/null 2>&1; then
  echo "-> python3 already present, skipping package manager step"
else
  echo "No python3 and no known package manager found. Install python3 manually, then re-run this script."
  exit 1
fi

# ---- create an isolated venv next to this script ----
cd "$(dirname "$0")"
python3 -m venv .venv 2>/dev/null || true   # some Termux setups lack venv; fall back below
if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
else
  echo "-> venv unavailable, installing directly with pip (Termux fallback)"
  pip install --upgrade pip
  pip install -r requirements.txt
fi

echo ""
echo "== Install complete =="
echo ""
echo "Run it with:"
echo "  ROOT_DIR=/path/to/expose PORT=7860 python3 server.py"
echo ""
echo "ROOT_DIR is whatever folder you want Glass FM to browse (defaults to the current directory if unset)."
echo "Then open http://<this-machine-ip>:7860 in a browser."
