#!/bin/bash
# 建立 Tw_stock_hot Docker image

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

docker build \
  -t nk7260ynpa/tw_stock_hot:latest \
  -f "$SCRIPT_DIR/Dockerfile" \
  "$PROJECT_DIR"
