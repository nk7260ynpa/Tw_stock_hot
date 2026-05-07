# fix: 修正股票超連結改用 Dashboard 反向代理路徑

- **Date:** 2026-05-07
- **Author:** nk7260ynpa
- **Related commit:** 961ba48

## Summary

將熱門話題前端三個元件中的股票名稱超連結從 `http://localhost:7938/?code=` 改為 `/app/webpage/?code=`，修正因 Tw_stock_webpage 容器未對外暴露 port 7938 導致連結無法開啟的問題。

## Motivation / context

Tw_stock_webpage 的 `run.sh` 刻意不做 port mapping（無 `-p 7938:8000`），僅透過 `db_network` 內部通訊，再由 Dashboard（port 8002）反向代理提供 `/app/webpage/` 路徑。但 Tw_stock_hot 前端元件硬寫了 `http://localhost:7938`，瀏覽器無法連線到該 port。

## Key changes

- `frontend/src/components/LimitStockTable.jsx`: 漲跌停排行股票連結改為 `/app/webpage/?code=`
- `frontend/src/components/RankTable.jsx`: 交易量/金額排行股票連結改為 `/app/webpage/?code=`
- `frontend/src/components/IndustryStocks.jsx`: 產業個股明細股票連結改為 `/app/webpage/?code=`

## Impact

所有從熱門話題點擊股票名稱的超連結現在可正確透過 Dashboard 反向代理導向台股網頁。

## Verification

- Docker image 重建成功
- 容器重啟後，確認 build 產物中三處連結均為 `/app/webpage/?code=`，無殘留 `localhost:7938`
