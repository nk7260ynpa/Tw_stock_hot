# Tw_stock_hot

台股綜合熱度平台 -- Dashboard 式的台股熱度分析工具。

## 功能

- **漲跌停排行**：每日漲停板/跌停板股票清單（TWSE + TPEX）及產業分布統計
- **交易量 TOP 10**：當日成交量最大的 10 檔股票（合併 TWSE + TPEX）
- **交易金額 TOP 10**：當日成交金額最高的 10 檔股票（合併 TWSE + TPEX）
- **產業漲幅排行**：各產業平均漲跌幅前 10 名（僅 TWSE，TPEX 無產業分類）
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
│           └── hot.py        # 熱度 API 路由
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.jsx
│       ├── App.jsx           # Dashboard 首頁 + currentView 切換
│       ├── App.css
│       ├── api/
│       │   └── hot.js        # API 呼叫函數
│       └── components/
│           ├── HotDashboard.jsx   # 首頁卡片網格
│           ├── HotDashboard.css
│           ├── LimitStocks.jsx    # 漲跌停完整頁面
│           ├── LimitStocks.css
│           ├── LimitStockTable.jsx  # 漲跌停表格元件
│           ├── LimitStockTable.css
│           ├── IndustryStats.jsx    # 產業統計圖元件
│           ├── IndustryStats.css
│           ├── RankTable.jsx        # 通用排行表格（交易量/金額）
│           ├── RankTable.css
│           ├── IndustryRank.jsx     # 產業漲幅排行
│           └── IndustryRank.css
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
| `/api/hot/top-volume` | GET | 交易量前 10 名（`?date=YYYY-MM-DD`） |
| `/api/hot/top-value` | GET | 交易金額前 10 名（`?date=YYYY-MM-DD`） |
| `/api/hot/industry-change` | GET | 產業平均漲跌幅前 10 名（`?date=YYYY-MM-DD`） |
| `/api/hot/dates` | GET | 可查詢的交易日清單（`?limit=30`） |

### API 回應範例

#### `/api/hot/top-volume`

```json
{
  "date": "2026-03-02",
  "stocks": [
    {
      "code": "2330",
      "name": "台積電",
      "trade_volume": 50000000,
      "trade_value": 55000000000,
      "close_price": 1100.0,
      "price_change": 10.0,
      "change_pct": 0.92,
      "industry": "半導體業",
      "market": "TWSE"
    }
  ]
}
```

#### `/api/hot/industry-change`

```json
{
  "date": "2026-03-02",
  "industries": [
    {
      "industry": "半導體業",
      "stock_count": 30,
      "avg_change_pct": 2.15
    }
  ]
}
```

## 資料來源

- MySQL TWSE 資料庫：DailyPrice、StockName、CompanyInfo、IndustryMap
- MySQL TPEX 資料庫：DailyPrice、StockName
- 漲跌停判斷：漲跌幅 >= 9.5%（10% 限制留容差）
- 僅保留 4 位數股票代碼（排除權證等衍生商品）
- 產業別：TWSE 透過 CompanyInfo.IndustryCode 對應 IndustryMap.Industry；TPEX 無 IndustryMap 標為「未分類」

## 技術棧

- 後端：FastAPI + SQLAlchemy + PyMySQL
- 前端：React + Vite（Dashboard 式 SPA）
- 部署：Docker（multi-stage build），連接 `db_network`
- Docker Image：`nk7260ynpa/tw_stock_hot:latest`
- 服務端口：5050
