# Tw_stock_hot

台股綜合熱度平台 -- Dashboard 式的台股熱度分析工具。

## 版本

目前版本：`1.0.0`

## 功能

- **漲跌停排行**：每日漲停板/跌停板股票清單（僅 TWSE 上市股票）及產業分布統計
- **交易量 TOP 10**：當日成交量最大的 10 檔股票（合併 TWSE + TPEX），含開盤價
- **交易金額 TOP 10**：當日成交金額最高的 10 檔股票（合併 TWSE + TPEX），含開盤價
- **產業漲幅排行**：各產業平均漲跌幅前 10 名（僅 TWSE，TPEX 無產業分類），產業名稱可點擊查看個股明細
- **產業漲幅佔比排行**：各產業漲跌公司數佔比分析（僅 TWSE），公式為 (漲的公司數 - 跌的公司數) / 產業總公司數，產業名稱可點擊查看個股明細
- **產業股票明細**：指定產業的所有股票交易資訊（僅 TWSE），含開盤價、收盤價、漲跌、漲跌幅、成交量、成交金額
- 歷史交易日切換

## 專案架構

```
Tw_stock_hot/
├── .github/
│   └── workflows/
│       └── docker-publish.yml  # GitHub Actions CI/CD
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
│           ├── IndustryRank.css
│           ├── IndustryRatioRank.jsx  # 產業漲幅佔比排行
│           ├── IndustryRatioRank.css
│           ├── IndustryStocks.jsx     # 產業股票明細
│           └── IndustryStocks.css
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
| `/api/hot/industry-ratio` | GET | 產業漲幅佔比排行（`?date=YYYY-MM-DD`） |
| `/api/hot/industry-stocks` | GET | 產業股票明細（`?date=YYYY-MM-DD&industry=xxx`） |
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
      "open_price": 1090.0,
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

#### `/api/hot/industry-ratio`

```json
{
  "date": "2026-03-02",
  "industries": [
    {
      "industry": "半導體業",
      "ratio_pct": 50.0,
      "up_count": 20,
      "down_count": 5,
      "total_count": 30
    }
  ]
}
```

#### `/api/hot/industry-stocks`

```json
{
  "date": "2026-03-02",
  "industry": "半導體業",
  "stock_count": 2,
  "stocks": [
    {
      "code": "2330",
      "name": "台積電",
      "open_price": 1090.0,
      "close_price": 1100.0,
      "price_change": 10.0,
      "change_pct": 0.92,
      "trade_volume": 50000000,
      "trade_value": 55000000000,
      "industry": "半導體業"
    }
  ]
}
```

## 資料來源

- MySQL TWSE 資料庫：DailyPrice、StockName、CompanyInfo、IndustryMap
- MySQL TPEX 資料庫：DailyPrice、StockName
- 漲跌停判斷：漲跌幅 >= 9.5%（10% 限制留容差）
- 僅保留 4 位數股票代碼（排除權證等衍生商品）
- 漲跌停排行僅查詢 TWSE 上市股票（TPEX 無產業對照資料，不納入漲跌停排行）
- 產業別：TWSE 透過 CompanyInfo.IndustryCode 對應 IndustryMap.Industry；缺少對應資料時標為「未分類」

## 技術棧

- 後端：FastAPI + SQLAlchemy + PyMySQL
- 前端：React + Vite（Dashboard 式 SPA）
- 部署：Docker（multi-stage build），連接 `db_network`
- Docker Image：`nk7260ynpa/tw_stock_hot:latest`
- 服務端口：5050

## CI/CD

使用 GitHub Actions 自動建置並推送 Docker image 至 DockerHub。

- **觸發條件**：推送符合 `v*.*.*` 格式的 Git tag
- **產出**：同時推送版本號 tag（如 `1.0.0`）與 `latest` tag
- **Workflow 檔案**：`.github/workflows/docker-publish.yml`

### 發布新版本

```bash
# 1. 更新 pyproject.toml 中的版本號
# 2. Commit 所有變更
# 3. 建立 tag 並推送
git tag v1.0.0
git push origin v1.0.0
```

### 必要的 GitHub Secrets

| Secret | 說明 |
|--------|------|
| `DOCKER_USERNAME` | DockerHub 帳號 |
| `DOCKER_PASSWORD` | DockerHub 密碼或 Access Token |
