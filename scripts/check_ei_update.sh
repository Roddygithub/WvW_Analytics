#!/usr/bin/env bash
set -e

# Adjust paths if needed
cd /home/roddy/WvW_Analytics

# Activate venv if present
if [ -f "venv/bin/activate" ]; then
  source venv/bin/activate
elif [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
fi

PYTHONPATH=$(pwd) python -m scripts.check_ei_update
