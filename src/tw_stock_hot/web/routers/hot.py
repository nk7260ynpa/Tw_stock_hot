"""漲跌停排行 API 路由。

提供今日漲停板、跌停板股票清單及產業別統計。
"""

import logging
import os
from datetime import date

from fastapi import APIRouter, Query
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/hot", tags=["hot"])

DB_HOST = os.environ.get("DB_HOST", "tw_stock_database")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASS = os.environ.get("DB_PASS", "stock")
DB_PORT = int(os.environ.get("DB_PORT", "3306"))

TWSE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/TWSE"
TPEX_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/TPEX"

twse_engine = create_engine(TWSE_URL, pool_pre_ping=True)
tpex_engine = create_engine(TPEX_URL, pool_pre_ping=True)

# 漲跌停門檻（10% 限制，留容差）
LIMIT_THRESHOLD = 9.5


def _query_twse_limit_stocks(target_date: date) -> list[dict]:
    """查詢 TWSE 漲跌停股票。"""
    sql = text("""
        SELECT
            dp.SecurityCode AS code,
            sn.StockName AS name,
            dp.ClosingPrice AS close_price,
            dp.Change AS price_change,
            ROUND(dp.Change / (dp.ClosingPrice - dp.Change) * 100, 2) AS change_pct,
            COALESCE(im.Industry, '') AS industry
        FROM DailyPrice dp
        LEFT JOIN StockName sn ON dp.SecurityCode = sn.SecurityCode
        LEFT JOIN CompanyInfo ci ON dp.SecurityCode = ci.SecurityCode
        LEFT JOIN IndustryMap im ON ci.IndustryCode = im.IndustryCode
        WHERE dp.Date = :target_date
            AND dp.SecurityCode REGEXP '^[0-9]{4}$'
            AND dp.ClosingPrice > 0
            AND (dp.ClosingPrice - dp.Change) > 0
    """)
    with twse_engine.connect() as conn:
        rows = conn.execute(sql, {"target_date": target_date}).mappings().all()
    return [dict(r) for r in rows]


def _query_tpex_limit_stocks(target_date: date) -> list[dict]:
    """查詢 TPEX 漲跌停股票。"""
    sql = text("""
        SELECT
            dp.Code AS code,
            sn.Name AS name,
            dp.Close AS close_price,
            dp.Change AS price_change,
            ROUND(dp.Change / (dp.Close - dp.Change) * 100, 2) AS change_pct,
            '' AS industry
        FROM DailyPrice dp
        LEFT JOIN StockName sn ON dp.Code = sn.Code
        WHERE dp.Date = :target_date
            AND dp.Code REGEXP '^[0-9]{4}$'
            AND dp.Close > 0
            AND (dp.Close - dp.Change) > 0
    """)
    with tpex_engine.connect() as conn:
        rows = conn.execute(sql, {"target_date": target_date}).mappings().all()
    return [dict(r) for r in rows]


def _classify_stocks(
    stocks: list[dict],
) -> tuple[list[dict], list[dict]]:
    """將股票分類為漲停板與跌停板。"""
    limit_up = []
    limit_down = []
    for s in stocks:
        pct = float(s["change_pct"]) if s["change_pct"] is not None else 0
        if pct >= LIMIT_THRESHOLD:
            limit_up.append(s)
        elif pct <= -LIMIT_THRESHOLD:
            limit_down.append(s)
    limit_up.sort(key=lambda x: float(x["change_pct"]), reverse=True)
    limit_down.sort(key=lambda x: float(x["change_pct"]))
    return limit_up, limit_down


def _industry_stats(stocks: list[dict]) -> list[dict]:
    """統計各產業出現次數並排序。"""
    counter: dict[str, int] = {}
    for s in stocks:
        industry = s.get("industry", "") or "未分類"
        counter[industry] = counter.get(industry, 0) + 1
    result = [{"industry": k, "count": v} for k, v in counter.items()]
    result.sort(key=lambda x: x["count"], reverse=True)
    return result


@router.get("/limit")
def get_limit_stocks(
    date_str: str | None = Query(None, alias="date", description="查詢日期 YYYY-MM-DD"),
) -> dict:
    """取得指定日期的漲停板與跌停板股票。"""
    target_date = date.fromisoformat(date_str) if date_str else date.today()
    logger.info("查詢漲跌停: %s", target_date)

    twse_stocks = _query_twse_limit_stocks(target_date)
    tpex_stocks = _query_tpex_limit_stocks(target_date)
    all_stocks = twse_stocks + tpex_stocks

    limit_up, limit_down = _classify_stocks(all_stocks)

    # 序列化 Decimal
    for lst in (limit_up, limit_down):
        for s in lst:
            s["close_price"] = float(s["close_price"]) if s["close_price"] else 0
            s["price_change"] = float(s["price_change"]) if s["price_change"] else 0
            s["change_pct"] = float(s["change_pct"]) if s["change_pct"] else 0

    return {
        "date": str(target_date),
        "limit_up": limit_up,
        "limit_up_count": len(limit_up),
        "limit_up_industry_stats": _industry_stats(limit_up),
        "limit_down": limit_down,
        "limit_down_count": len(limit_down),
        "limit_down_industry_stats": _industry_stats(limit_down),
    }


@router.get("/dates")
def get_available_dates(
    limit: int = Query(30, description="回傳筆數"),
) -> dict:
    """取得最近有交易資料的日期清單。"""
    sql = text("""
        SELECT DISTINCT Date
        FROM DailyPrice
        ORDER BY Date DESC
        LIMIT :limit
    """)
    with twse_engine.connect() as conn:
        rows = conn.execute(sql, {"limit": limit}).fetchall()
    dates = [str(r[0]) for r in rows]
    return {"dates": dates}
