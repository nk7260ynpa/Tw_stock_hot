# Tw_stock_hot

台股綜合熱度平台 — 漲跌停排行與產業熱度分析。

## 功能

- 每日漲停板/跌停板股票清單（TWSE + TPEX）
- 各股產業別顯示
- 產業分布統計圖（哪個產業漲跌停最多）
- 歷史交易日切換

## 專案架構

```
Tw_stock_hot/
├── docker/
│   ├── build.sh              # 建立 Docker image
│   └── Dockerfile            # Multi-stage build（Node + Python）
├── src/tw_stock_hot/
│   ├── __init__.py
│   ├── main.py               # 主程式入口
│   └── web/
│       ├── app.py            # FastAPI 應用
│       └── routers/
│           └── hot.py        # 漲跌停 API 路由
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.jsx
│       ├── App.jsx           # 主頁面
│       ├── api/
│       │   └── hot.js        # API 呼叫
│       └── components/
│           ├── LimitStockTable.jsx  # 漲跌停表格
│           └── IndustryStats.jsx    # 產業統計圖
├── tests/
│   └── test_hot_api.py
├── logs/
├── run.sh                    # 啟動容器
├── pyproject.toml
├── requirements.txt
└── README.md
```

## 快速開始

```bash
# 建置 Docker image
bash docker/build.sh

# 啟動服務
bash run.sh

# 開啟 http://localhost:5050
```

## API

| Endpoint | 方法 | 功能 |
|----------|------|------|
| `/api/hot/limit` | GET | 漲跌停股票清單（`?date=YYYY-MM-DD`） |
| `/api/hot/dates` | GET | 可查詢的交易日清單（`?limit=30`） |

## 資料來源

- MySQL TWSE 資料庫：DailyPrice、StockName、CompanyInfo、IndustryMap
- MySQL TPEX 資料庫：DailyPrice、StockName
- 漲跌停判斷：漲跌幅 >= 9.5%（10% 限制留容差）
- 僅保留 4 位數股票代碼（排除權證等衍生商品）

## 技術棧

- 後端：FastAPI + SQLAlchemy + PyMySQL
- 前端：React + Vite
- 部署：Docker（multi-stage build），連接 `db_network`
