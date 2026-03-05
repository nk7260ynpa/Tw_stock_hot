"""台股熱度 API 路由。

提供漲跌停排行、交易量/交易金額 TOP 10、產業漲幅排行等功能。
"""

import logging
import os
from datetime import date
from decimal import Decimal

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


def _to_float(val) -> float:
    """將 Decimal 或其他數值安全轉為 float。"""
    if val is None:
        return 0.0
    if isinstance(val, Decimal):
        return float(val)
    return float(val)


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
    """取得指定日期的漲停板與跌停板股票。

    僅查詢 TWSE 上市股票（TPEX 無產業對照資料，不納入漲跌停排行）。
    """
    target_date = date.fromisoformat(date_str) if date_str else date.today()
    logger.info("查詢漲跌停: %s", target_date)

    all_stocks = _query_twse_limit_stocks(target_date)

    limit_up, limit_down = _classify_stocks(all_stocks)

    # 序列化 Decimal
    for lst in (limit_up, limit_down):
        for s in lst:
            s["close_price"] = _to_float(s["close_price"])
            s["price_change"] = _to_float(s["price_change"])
            s["change_pct"] = _to_float(s["change_pct"])

    return {
        "date": str(target_date),
        "limit_up": limit_up,
        "limit_up_count": len(limit_up),
        "limit_up_industry_stats": _industry_stats(limit_up),
        "limit_down": limit_down,
        "limit_down_count": len(limit_down),
        "limit_down_industry_stats": _industry_stats(limit_down),
    }


@router.get("/top-volume")
def get_top_volume(
    date_str: str | None = Query(None, alias="date", description="查詢日期 YYYY-MM-DD"),
) -> dict:
    """取得指定日期交易量前 10 名股票。

    合併 TWSE 與 TPEX 資料，依交易量降冪排序取前 10 名。
    """
    target_date = date.fromisoformat(date_str) if date_str else date.today()
    logger.info("查詢交易量 TOP 10: %s", target_date)

    twse_sql = text("""
        SELECT
            dp.SecurityCode AS code,
            sn.StockName AS name,
            dp.TradeVolume AS trade_volume,
            dp.TradeValue AS trade_value,
            ROUND(dp.ClosingPrice - dp.Change, 2) AS prev_close,
            dp.OpeningPrice AS open_price,
            dp.ClosingPrice AS close_price,
            dp.Change AS price_change,
            ROUND(dp.Change / (dp.ClosingPrice - dp.Change) * 100, 2) AS change_pct,
            COALESCE(im.Industry, '') AS industry,
            'TWSE' AS market
        FROM DailyPrice dp
        LEFT JOIN StockName sn ON dp.SecurityCode = sn.SecurityCode
        LEFT JOIN CompanyInfo ci ON dp.SecurityCode = ci.SecurityCode
        LEFT JOIN IndustryMap im ON ci.IndustryCode = im.IndustryCode
        WHERE dp.Date = :target_date
            AND dp.SecurityCode REGEXP '^[0-9]{4}$'
            AND dp.ClosingPrice > 0
            AND (dp.ClosingPrice - dp.Change) > 0
        ORDER BY dp.TradeVolume DESC
        LIMIT 10
    """)

    tpex_sql = text("""
        SELECT
            dp.Code AS code,
            sn.Name AS name,
            dp.TradeVolume AS trade_volume,
            dp.TradeAmount AS trade_value,
            ROUND(dp.Close - dp.Change, 2) AS prev_close,
            dp.Open AS open_price,
            dp.Close AS close_price,
            dp.Change AS price_change,
            ROUND(dp.Change / (dp.Close - dp.Change) * 100, 2) AS change_pct,
            '未分類' AS industry,
            'TPEX' AS market
        FROM DailyPrice dp
        LEFT JOIN StockName sn ON dp.Code = sn.Code
        WHERE dp.Date = :target_date
            AND dp.Code REGEXP '^[0-9]{4}$'
            AND dp.Close > 0
            AND (dp.Close - dp.Change) > 0
        ORDER BY dp.TradeVolume DESC
        LIMIT 10
    """)

    with twse_engine.connect() as conn:
        twse_rows = conn.execute(twse_sql, {"target_date": target_date}).mappings().all()
    with tpex_engine.connect() as conn:
        tpex_rows = conn.execute(tpex_sql, {"target_date": target_date}).mappings().all()

    combined = [dict(r) for r in twse_rows] + [dict(r) for r in tpex_rows]
    combined.sort(key=lambda x: _to_float(x["trade_volume"]), reverse=True)
    top10 = combined[:10]

    for s in top10:
        s["trade_volume"] = _to_float(s["trade_volume"])
        s["trade_value"] = _to_float(s["trade_value"])
        s["prev_close"] = _to_float(s["prev_close"])
        s["open_price"] = _to_float(s["open_price"])
        s["close_price"] = _to_float(s["close_price"])
        s["price_change"] = _to_float(s["price_change"])
        s["change_pct"] = _to_float(s["change_pct"])

    return {"date": str(target_date), "stocks": top10}


@router.get("/top-value")
def get_top_value(
    date_str: str | None = Query(None, alias="date", description="查詢日期 YYYY-MM-DD"),
) -> dict:
    """取得指定日期交易金額前 10 名股票。

    合併 TWSE 與 TPEX 資料，依交易金額降冪排序取前 10 名。
    """
    target_date = date.fromisoformat(date_str) if date_str else date.today()
    logger.info("查詢交易金額 TOP 10: %s", target_date)

    twse_sql = text("""
        SELECT
            dp.SecurityCode AS code,
            sn.StockName AS name,
            dp.TradeVolume AS trade_volume,
            dp.TradeValue AS trade_value,
            ROUND(dp.ClosingPrice - dp.Change, 2) AS prev_close,
            dp.OpeningPrice AS open_price,
            dp.ClosingPrice AS close_price,
            dp.Change AS price_change,
            ROUND(dp.Change / (dp.ClosingPrice - dp.Change) * 100, 2) AS change_pct,
            COALESCE(im.Industry, '') AS industry,
            'TWSE' AS market
        FROM DailyPrice dp
        LEFT JOIN StockName sn ON dp.SecurityCode = sn.SecurityCode
        LEFT JOIN CompanyInfo ci ON dp.SecurityCode = ci.SecurityCode
        LEFT JOIN IndustryMap im ON ci.IndustryCode = im.IndustryCode
        WHERE dp.Date = :target_date
            AND dp.SecurityCode REGEXP '^[0-9]{4}$'
            AND dp.ClosingPrice > 0
            AND (dp.ClosingPrice - dp.Change) > 0
        ORDER BY dp.TradeValue DESC
        LIMIT 10
    """)

    tpex_sql = text("""
        SELECT
            dp.Code AS code,
            sn.Name AS name,
            dp.TradeVolume AS trade_volume,
            dp.TradeAmount AS trade_value,
            ROUND(dp.Close - dp.Change, 2) AS prev_close,
            dp.Open AS open_price,
            dp.Close AS close_price,
            dp.Change AS price_change,
            ROUND(dp.Change / (dp.Close - dp.Change) * 100, 2) AS change_pct,
            '未分類' AS industry,
            'TPEX' AS market
        FROM DailyPrice dp
        LEFT JOIN StockName sn ON dp.Code = sn.Code
        WHERE dp.Date = :target_date
            AND dp.Code REGEXP '^[0-9]{4}$'
            AND dp.Close > 0
            AND (dp.Close - dp.Change) > 0
        ORDER BY dp.TradeAmount DESC
        LIMIT 10
    """)

    with twse_engine.connect() as conn:
        twse_rows = conn.execute(twse_sql, {"target_date": target_date}).mappings().all()
    with tpex_engine.connect() as conn:
        tpex_rows = conn.execute(tpex_sql, {"target_date": target_date}).mappings().all()

    combined = [dict(r) for r in twse_rows] + [dict(r) for r in tpex_rows]
    combined.sort(key=lambda x: _to_float(x["trade_value"]), reverse=True)
    top10 = combined[:10]

    for s in top10:
        s["trade_volume"] = _to_float(s["trade_volume"])
        s["trade_value"] = _to_float(s["trade_value"])
        s["prev_close"] = _to_float(s["prev_close"])
        s["open_price"] = _to_float(s["open_price"])
        s["close_price"] = _to_float(s["close_price"])
        s["price_change"] = _to_float(s["price_change"])
        s["change_pct"] = _to_float(s["change_pct"])

    return {"date": str(target_date), "stocks": top10}


@router.get("/industry-change")
def get_industry_change(
    date_str: str | None = Query(None, alias="date", description="查詢日期 YYYY-MM-DD"),
) -> dict:
    """取得指定日期各產業平均漲跌幅排行（前 10 名）。

    僅使用 TWSE 資料（TPEX 無產業分類）。
    依各產業平均漲跌幅降冪排序，取前 10 名。
    """
    target_date = date.fromisoformat(date_str) if date_str else date.today()
    logger.info("查詢產業漲幅排行: %s", target_date)

    sql = text("""
        SELECT
            im.Industry AS industry,
            COUNT(*) AS stock_count,
            ROUND(AVG(dp.Change / (dp.ClosingPrice - dp.Change) * 100), 2) AS avg_change_pct
        FROM DailyPrice dp
        INNER JOIN CompanyInfo ci ON dp.SecurityCode = ci.SecurityCode
        INNER JOIN IndustryMap im ON ci.IndustryCode = im.IndustryCode
        WHERE dp.Date = :target_date
            AND dp.SecurityCode REGEXP '^[0-9]{4}$'
            AND dp.ClosingPrice > 0
            AND (dp.ClosingPrice - dp.Change) > 0
        GROUP BY im.Industry
        ORDER BY avg_change_pct DESC
        LIMIT 10
    """)

    with twse_engine.connect() as conn:
        rows = conn.execute(sql, {"target_date": target_date}).mappings().all()

    industries = []
    for r in rows:
        industries.append({
            "industry": r["industry"],
            "stock_count": int(r["stock_count"]),
            "avg_change_pct": _to_float(r["avg_change_pct"]),
        })

    return {"date": str(target_date), "industries": industries}


@router.get("/industry-ratio")
def get_industry_ratio(
    date_str: str | None = Query(None, alias="date", description="查詢日期 YYYY-MM-DD"),
) -> dict:
    """取得指定日期各產業漲幅佔比排行。

    僅使用 TWSE 資料（TPEX 無產業分類）。
    漲幅佔比公式：(漲的公司數 - 跌的公司數) / 該產業總公司數 * 100。
    依漲幅佔比降冪排序。
    """
    target_date = date.fromisoformat(date_str) if date_str else date.today()
    logger.info("查詢產業漲幅佔比排行: %s", target_date)

    sql = text("""
        SELECT
            im.Industry AS industry,
            COUNT(*) AS total_count,
            SUM(CASE WHEN dp.Change > 0 THEN 1 ELSE 0 END) AS up_count,
            SUM(CASE WHEN dp.Change < 0 THEN 1 ELSE 0 END) AS down_count,
            ROUND(
                (SUM(CASE WHEN dp.Change > 0 THEN 1 ELSE 0 END)
                 - SUM(CASE WHEN dp.Change < 0 THEN 1 ELSE 0 END))
                / COUNT(*) * 100, 2
            ) AS ratio_pct
        FROM DailyPrice dp
        INNER JOIN CompanyInfo ci ON dp.SecurityCode = ci.SecurityCode
        INNER JOIN IndustryMap im ON ci.IndustryCode = im.IndustryCode
        WHERE dp.Date = :target_date
            AND dp.SecurityCode REGEXP '^[0-9]{4}$'
            AND dp.ClosingPrice > 0
            AND (dp.ClosingPrice - dp.Change) > 0
        GROUP BY im.Industry
        ORDER BY ratio_pct DESC
    """)

    with twse_engine.connect() as conn:
        rows = conn.execute(sql, {"target_date": target_date}).mappings().all()

    industries = []
    for r in rows:
        industries.append({
            "industry": r["industry"],
            "ratio_pct": _to_float(r["ratio_pct"]),
            "up_count": int(r["up_count"]),
            "down_count": int(r["down_count"]),
            "total_count": int(r["total_count"]),
        })

    return {"date": str(target_date), "industries": industries}


@router.get("/industry-stocks")
def get_industry_stocks(
    date_str: str | None = Query(None, alias="date", description="查詢日期 YYYY-MM-DD"),
    industry: str = Query(..., description="產業名稱"),
) -> dict:
    """取得指定日期、指定產業的個股明細。

    僅查詢 TWSE 上市股票，回傳該產業所有股票的交易資訊。
    """
    target_date = date.fromisoformat(date_str) if date_str else date.today()
    logger.info("查詢產業股票明細: %s, 產業=%s", target_date, industry)

    sql = text("""
        SELECT
            dp.SecurityCode AS code,
            sn.StockName AS name,
            ROUND(dp.ClosingPrice - dp.Change, 2) AS prev_close,
            dp.OpeningPrice AS open_price,
            dp.ClosingPrice AS close_price,
            dp.Change AS price_change,
            ROUND(dp.Change / (dp.ClosingPrice - dp.Change) * 100, 2) AS change_pct,
            dp.TradeVolume AS trade_volume,
            dp.TradeValue AS trade_value,
            im.Industry AS industry
        FROM DailyPrice dp
        LEFT JOIN StockName sn ON dp.SecurityCode = sn.SecurityCode
        INNER JOIN CompanyInfo ci ON dp.SecurityCode = ci.SecurityCode
        INNER JOIN IndustryMap im ON ci.IndustryCode = im.IndustryCode
        WHERE dp.Date = :target_date
            AND dp.SecurityCode REGEXP '^[0-9]{4}$'
            AND dp.ClosingPrice > 0
            AND (dp.ClosingPrice - dp.Change) > 0
            AND im.Industry = :industry
        ORDER BY change_pct DESC
    """)

    with twse_engine.connect() as conn:
        rows = conn.execute(
            sql, {"target_date": target_date, "industry": industry}
        ).mappings().all()

    stocks = []
    for r in rows:
        stocks.append({
            "code": r["code"],
            "name": r["name"],
            "prev_close": _to_float(r["prev_close"]),
            "open_price": _to_float(r["open_price"]),
            "close_price": _to_float(r["close_price"]),
            "price_change": _to_float(r["price_change"]),
            "change_pct": _to_float(r["change_pct"]),
            "trade_volume": _to_float(r["trade_volume"]),
            "trade_value": _to_float(r["trade_value"]),
            "industry": r["industry"],
        })

    return {
        "date": str(target_date),
        "industry": industry,
        "stock_count": len(stocks),
        "stocks": stocks,
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
