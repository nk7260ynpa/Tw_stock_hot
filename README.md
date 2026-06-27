# Tw_stock_hot

台股綜合熱度平台 -- Dashboard 式的台股熱度分析工具。

## 版本

目前版本：`1.2.0`

## 功能

- **漲跌停排行**：每日漲停板/跌停板股票清單（僅 TWSE 上市股票），含昨收、開盤價及產業分布統計；股票依產業分布排名排序（數量多的產業排前面，同產業內按漲跌幅排序）
- **交易量 TOP 10**：當日成交量最大的 10 檔股票（合併 TWSE + TPEX），含昨收、開盤價
- **交易金額 TOP 10**：當日成交金額最高的 10 檔股票（合併 TWSE + TPEX），含昨收、開盤價
- **產業漲幅排行**：各產業平均漲跌幅前 10 名（僅 TWSE，TPEX 無產業分類），產業名稱可點擊查看個股明細
- **產業漲幅佔比排行**：各產業漲跌公司數佔比分析（僅 TWSE），公式為 (漲的公司數 - 跌的公司數) / 產業總公司數，產業名稱可點擊查看個股明細
- **產業股票明細**：指定產業的所有股票交易資訊（僅 TWSE），含昨收、開盤價、收盤價、漲跌、漲跌幅、成交量、成交金額
- 歷史交易日切換
- **自動退回最新有資料日**：開啟平台或查詢「最新交易日」時，若當天資料尚未上傳，會自動退回到「資料庫中最後一個真正有資料的交易日」並顯示其資料，畫面不再空白；指定一個無資料的日期查詢時，亦會退回到「該日期(含)以前最近一個有資料的日期」並於畫面標示實際採用日期

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

> **日期退回行為**：除 `/api/hot/dates` 外，所有 API 在未帶 `date` 參數時，會以
> 「資料庫中最後一個真正有資料的交易日」作為查詢日期（而非單純取今天）；帶入的
> `date` 當天若無資料，則退回「該日期(含)以前最近一個有資料的日期」。回應的 `date`
> 欄位即為實際採用的日期，另新增 `requested_date` 欄位標示使用者原本請求的日期，
> 兩者不同即代表發生退回（前端會提示使用者）。

### API 回應範例

#### `/api/hot/top-volume`

```json
{
  "date": "2026-03-02",
  "requested_date": "2026-03-02",
  "stocks": [
    {
      "code": "2330",
      "name": "台積電",
      "trade_volume": 50000000,
      "trade_value": 55000000000,
      "prev_close": 1090.0,
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
      "prev_close": 1090.0,
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

開發主線在自架 GitLab，`.gitlab-ci.yml` 在推送 `vX.Y.Z` 版本 tag 時觸發管線，
管線含 **deploy** 與 **mirror** 兩個並行 stage（兩個 job 各自 `needs: []`，互不阻擋）。

```text
在 main 打上 vX.Y.Z tag
        │
        ├──> deploy（並行）：於 GitLab Runner 的 host daemon 本地 build 並重啟容器
        └──> mirror（並行）：把 main 與該 tag 推送到 GitHub（再由 GitHub Actions 推映像）
```

### deploy（tag 觸發、host 本地重新部署）

- **觸發條件**：在 `main` 打上 `vX.Y.Z` 版本 tag 並推送（**合併進 `main` 當下不部署**）
- **執行環境**：GitLab Runner 為 docker executor 且掛載 `/var/run/docker.sock`（socket 綁定），
  故 job 內的 `docker` 指令直接作用在 **host daemon**——build 出的映像、run 起的容器都落在主機，
  等同手動執行 `docker/build.sh` + `run.sh`。
- **步驟（嚴格順序，關鍵安全性質）**：`docker build` → `docker rm -f` → `docker run`。
  先 build 新映像，**build 失敗即中止、舊容器完全不動、服務不中斷**；只有 build 成功後才會
  移除舊容器並以新映像重啟。切勿調換此順序。
- **容器設定**：`--restart=always`、`--network db_network`，log 以**具名 volume
  `tw_stock_hot_logs`** 掛載到容器內 `/app/logs`。
- **映像標籤**：同時打上 `nk7260ynpa/tw_stock_hot:<版本>` 與 `:latest`。

> **查 log 的位置（重要）**：經 CI 部署的容器，log 落在**具名 volume `tw_stock_hot_logs`**，
> **不再**寫入 repo 的 `logs/` 目錄。請改用 `docker logs tw_stock_hot`，或直接讀具名 volume
> （`docker run --rm -v tw_stock_hot_logs:/logs alpine cat /logs/hot.log`）。repo 內 `logs/` 僅在
> 以 `run.sh` 手動啟動（bind mount）時才會有內容。

### mirror（GitLab → GitHub 鏡像）

GitHub 為對外鏡像（`origin` → GitLab、`github` → GitHub）。

- **觸發條件**：在 `main` 打上 `vX.Y.Z` 版本 tag 並推送（**合併進 `main` 當下不鏡像**）
- **行為**：`.gitlab-ci.yml` 的 `mirror-to-github` job 以 GitLab Runner 注入的 SSH
  金鑰（`GITHUB_SSH_KEY`）把 `main` 與該版本 tag 一併推送到 GitHub
- **後續**：GitHub 收到 tag 後，由 `.github/workflows/docker-publish.yml`（GitHub Actions）
  另行建置並推送 `nk7260ynpa/tw_stock_hot:{版本}` 與 `:latest` 到 DockerHub

### 流程

```text
feature 分支 → 開 MR → 合併進 main → 在 main 打 vX.Y.Z tag → 觸發 deploy + mirror 並行
```

### 發布新版本

```bash
# 1. 更新 pyproject.toml 中的版本號
# 2. Commit 所有變更並合併進 main
# 3. 在 main 建立 annotated tag 並僅推送到 origin（GitLab）
git tag -a v1.3.0 -m "版本說明"
git push origin v1.3.0   # 觸發 deploy（host 重新部署）+ mirror（推送到 GitHub）
```

> 只需 `git push origin <tag>`；**不要**手動推送到 `github`，GitHub 由 `mirror-to-github`
> job 自動鏡像。tag 推送後即觸發 deploy 重新部署本機容器。

### 必要的 CI 變數 / Secrets

| 來源 | 變數 | 說明 |
|------|------|------|
| GitLab Runner | `GITHUB_SSH_KEY` | mirror job 推送到 GitHub 用的 SSH 私鑰（路徑或內容皆可） |
| GitHub Actions | `DOCKER_USERNAME` | DockerHub 帳號 |
| GitHub Actions | `DOCKER_PASSWORD` | DockerHub 密碼或 Access Token |
