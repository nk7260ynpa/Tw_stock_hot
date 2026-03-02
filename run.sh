#!/bin/bash
# 啟動 Tw_stock_hot 容器

set -euo pipefail

CONTAINER_NAME="tw_stock_hot"
IMAGE_NAME="nk7260ynpa/tw_stock_hot:latest"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 停止並移除舊容器
docker rm -f "$CONTAINER_NAME" 2>/dev/null || true

docker run -d \
  --name "$CONTAINER_NAME" \
  --network db_network \
  -p 5050:5050 \
  -v "$SCRIPT_DIR/logs:/app/logs" \
  "$IMAGE_NAME"

echo "服務已啟動: http://localhost:5050"
