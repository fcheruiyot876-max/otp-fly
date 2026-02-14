#!/bin/sh
set -e
while true; do
    python -m src.bypass
    echo "Bot exited – restarting in 5s…"
    sleep 5
done
