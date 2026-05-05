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
  --restart=always \
  --network db_network \
  -v "$SCRIPT_DIR/logs:/app/logs" \
  "$IMAGE_NAME"

echo "服務已啟動 (僅限 db_network 內部存取): http://tw_stock_hot:5050"
