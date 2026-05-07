# Tw_stock_hot — 台股熱度平台

## 概述

台股熱度分析平台，提供漲跌停排行、交易量/金額 TOP 10、產業漲幅排行等功能。

## 技術架構

- **後端**：FastAPI (Python 3.12)
- **前端**：React + Vite
- **部署**：Docker 單一容器（multi-stage build），透過 `db_network` 連接 MySQL
- **存取方式**：僅透過 Dashboard 反向代理（`localhost:8002/app/hot/`）

## 服務端口

- 容器內部：5050
- 對外存取：透過 Dashboard 反向代理 `/app/hot/`
