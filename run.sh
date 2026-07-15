#!/usr/bin/env bash
# Glass FM — one-command launcher.
# Uses the .venv from install.sh automatically if it exists, so you
# never hit "ModuleNotFoundError: No module named 'fastapi'" from
# accidentally running the system python3 instead of the venv one.
set -e
cd "$(dirname "$0")"

if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
  PYBIN="python3"
elif [ -f ".venv/bin/python3" ]; then
  PYBIN=".venv/bin/python3"
else
  echo "No .venv found — using system python3. Run install.sh first if this fails."
  PYBIN="python3"
fi

: "${ROOT_DIR:=$HOME}"
: "${PORT:=7860}"
export ROOT_DIR PORT

echo "Serving $ROOT_DIR on port $PORT ..."
echo "Open http://localhost:$PORT in the browser"
exec "$PYBIN" server.py
