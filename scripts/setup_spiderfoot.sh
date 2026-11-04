#!/bin/sh

set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
SPIDERFOOT_ROOT="$PROJECT_ROOT/integrations/spiderfoot"
VENV_PATH="$SPIDERFOOT_ROOT/.venv"

if ! command -v python3.12 >/dev/null 2>&1; then
    echo "Python 3.12 is required to set up SpiderFoot." >&2
    exit 1
fi

python3.12 -m venv "$VENV_PATH"
"$VENV_PATH/bin/python" -m pip install --upgrade pip
"$VENV_PATH/bin/python" -m pip install -r "$SPIDERFOOT_ROOT/requirements.txt"

echo "SpiderFoot is ready for Autherius."
