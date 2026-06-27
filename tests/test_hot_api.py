"""台股熱度 API 單元測試。"""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from tw_stock_hot.web.app import app
from tw_stock_hot.web.routers import hot as hot_module

# 在 autouse fixture 介入前擷取真實 helper 參照，供直接測試底層查詢函式使用。
_real_query_latest_date = hot_module._query_latest_date_on_or_before
_resolve_trading_date = hot_module._resolve_trading_date


@pytest.fixture
def client():
    """建立測試用 FastAPI client。"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def _trading_date_has_data(monkeypatch):
    """預設情境：請求日期當天即有資料（退回邏輯不觸發）。

    讓既有測試維持「回應 date == 請求日期」的行為；
    需要驗證退回行為的測試會自行覆寫 `_query_latest_date_on_or_before`。
    """
    monkeypatch.setattr(
        "tw_stock_hot.web.routers.hot._query_latest_date_on_or_before",
        lambda target_date: target_date,
    )


# ============================================================
# /api/hot/limit
# ============================================================

class TestGetLimitStocks:
    """測試 /api/hot/limit 端點（僅 TWSE 上市股票）。"""

    @patch("tw_stock_hot.web.routers.hot._query_twse_limit_stocks")
    def test_response_format(self, mock_twse, client):
        """回應應包含漲停與跌停清單，且含 prev_close 與 open_price 欄位。"""
        mock_twse.return_value = [
            {
                "code": "2330",
                "name": "台積電",
                "prev_close": 1000.00,
                "open_price": 1005.00,
                "close_price": 1100.00,
                "price_change": 100.00,
                "change_pct": 10.0,
                "industry": "半導體業",
            }
        ]

        res = client.get("/api/hot/limit?date=2026-03-02")
        assert res.status_code == 200

        data = res.json()
        assert "limit_up" in data
        assert "limit_down" in data
        assert "limit_up_count" in data
        assert "limit_down_count" in data
        assert "limit_up_industry_stats" in data
        assert "limit_down_industry_stats" in data
        assert data["limit_up_count"] == 1
        assert data["limit_up"][0]["code"] == "2330"
        assert data["limit_up"][0]["industry"] == "半導體業"
        assert data["limit_up"][0]["prev_close"] == 1000.00
        assert data["limit_up"][0]["open_price"] == 1005.00

    @patch("tw_stock_hot.web.routers.hot._query_twse_limit_stocks")
    def test_industry_stats(self, mock_twse, client):
        """產業統計應正確計算。"""
        mock_twse.return_value = [
            {"code": "2330", "name": "台積電", "prev_close": 1000.00,
             "open_price": 1005.00, "close_price": 1100.00,
             "price_change": 100.00, "change_pct": 10.0, "industry": "半導體業"},
            {"code": "3711", "name": "日月光", "prev_close": 200.00,
             "open_price": 202.00, "close_price": 220.00,
             "price_change": 20.00, "change_pct": 10.0, "industry": "半導體業"},
            {"code": "2317", "name": "鴻海", "prev_close": 150.00,
             "open_price": 152.00, "close_price": 165.00,
             "price_change": 15.00, "change_pct": 10.0, "industry": "其他電子業"},
        ]

        res = client.get("/api/hot/limit?date=2026-03-02")
        data = res.json()
        stats = data["limit_up_industry_stats"]
        assert stats[0]["industry"] == "半導體業"
        assert stats[0]["count"] == 2
        assert stats[1]["industry"] == "其他電子業"
        assert stats[1]["count"] == 1

    @patch("tw_stock_hot.web.routers.hot._query_twse_limit_stocks")
    def test_sorted_by_industry_rank(self, mock_twse, client):
        """股票應依產業分布排名排序：數量多的產業排前面，同產業內按漲跌幅排。"""
        mock_twse.return_value = [
            {"code": "2317", "name": "鴻海", "prev_close": 150.00,
             "open_price": 152.00, "close_price": 165.00,
             "price_change": 15.00, "change_pct": 10.0, "industry": "其他電子業"},
            {"code": "2330", "name": "台積電", "prev_close": 1000.00,
             "open_price": 1005.00, "close_price": 1100.00,
             "price_change": 100.00, "change_pct": 10.0, "industry": "半導體業"},
            {"code": "3711", "name": "日月光", "prev_close": 200.00,
             "open_price": 202.00, "close_price": 220.00,
             "price_change": 20.00, "change_pct": 10.0, "industry": "半導體業"},
            {"code": "2454", "name": "聯發科", "prev_close": 800.00,
             "open_price": 805.00, "close_price": 880.00,
             "price_change": 80.00, "change_pct": 10.0, "industry": "半導體業"},
        ]

        res = client.get("/api/hot/limit?date=2026-03-02")
        data = res.json()

        # 半導體業有 3 檔，其他電子業有 1 檔
        # 半導體業的股票應排在前面
        stocks = data["limit_up"]
        assert len(stocks) == 4
        assert stocks[0]["industry"] == "半導體業"
        assert stocks[1]["industry"] == "半導體業"
        assert stocks[2]["industry"] == "半導體業"
        assert stocks[3]["industry"] == "其他電子業"
        assert stocks[3]["code"] == "2317"

    @patch("tw_stock_hot.web.routers.hot._query_twse_limit_stocks")
    def test_sorted_by_industry_rank_limit_down(self, mock_twse, client):
        """跌停股票也應依產業分布排名排序，同產業內按漲跌幅升冪排。"""
        mock_twse.return_value = [
            {"code": "1101", "name": "台泥", "prev_close": 50.00,
             "open_price": 49.00, "close_price": 45.00,
             "price_change": -5.00, "change_pct": -10.0, "industry": "水泥工業"},
            {"code": "1102", "name": "亞泥", "prev_close": 40.00,
             "open_price": 39.00, "close_price": 36.00,
             "price_change": -4.00, "change_pct": -10.0, "industry": "水泥工業"},
            {"code": "2002", "name": "中鋼", "prev_close": 30.00,
             "open_price": 29.00, "close_price": 27.00,
             "price_change": -3.00, "change_pct": -10.0, "industry": "鋼鐵工業"},
        ]

        res = client.get("/api/hot/limit?date=2026-03-02")
        data = res.json()

        # 水泥工業有 2 檔，鋼鐵工業有 1 檔
        stocks = data["limit_down"]
        assert len(stocks) == 3
        assert stocks[0]["industry"] == "水泥工業"
        assert stocks[1]["industry"] == "水泥工業"
        assert stocks[2]["industry"] == "鋼鐵工業"
        assert stocks[2]["code"] == "2002"

    @patch("tw_stock_hot.web.routers.hot._query_twse_limit_stocks")
    def test_empty_result(self, mock_twse, client):
        """無資料時應回傳空清單。"""
        mock_twse.return_value = []

        res = client.get("/api/hot/limit?date=2026-01-01")
        data = res.json()
        assert data["limit_up"] == []
        assert data["limit_down"] == []
        assert data["limit_up_count"] == 0
        assert data["limit_down_count"] == 0

    @patch("tw_stock_hot.web.routers.hot._query_twse_limit_stocks")
    def test_missing_industry_shows_unclassified(self, mock_twse, client):
        """TWSE 股票缺少 CompanyInfo 或 IndustryMap 時產業應為「未分類」。"""
        mock_twse.return_value = [
            {
                "code": "9999",
                "name": "測試股",
                "prev_close": 100.00,
                "open_price": 101.00,
                "close_price": 110.00,
                "price_change": 10.00,
                "change_pct": 10.0,
                "industry": "",
            }
        ]

        res = client.get("/api/hot/limit?date=2026-03-02")
        data = res.json()
        assert data["limit_up_count"] == 1
        stats = data["limit_up_industry_stats"]
        assert stats[0]["industry"] == "未分類"


# ============================================================
# /api/hot/top-volume
# ============================================================

class TestGetTopVolume:
    """測試 /api/hot/top-volume 端點。"""

    @patch("tw_stock_hot.web.routers.hot.tpex_engine")
    @patch("tw_stock_hot.web.routers.hot.twse_engine")
    def test_response_format(self, mock_twse_eng, mock_tpex_eng, client):
        """回應應包含 stocks 清單與 date，且包含 open_price 欄位。"""
        mock_twse_conn = MagicMock()
        mock_twse_eng.connect.return_value.__enter__ = lambda _: mock_twse_conn
        mock_twse_eng.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_twse_conn.execute.return_value.mappings.return_value.all.return_value = [
            {
                "code": "2330", "name": "台積電",
                "trade_volume": 50000000, "trade_value": 55000000000,
                "prev_close": 1090.00,
                "open_price": 1090.00,
                "close_price": 1100.00, "price_change": 10.00,
                "change_pct": 0.92, "industry": "半導體業", "market": "TWSE",
            }
        ]

        mock_tpex_conn = MagicMock()
        mock_tpex_eng.connect.return_value.__enter__ = lambda _: mock_tpex_conn
        mock_tpex_eng.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_tpex_conn.execute.return_value.mappings.return_value.all.return_value = []

        res = client.get("/api/hot/top-volume?date=2026-03-02")
        assert res.status_code == 200

        data = res.json()
        assert "date" in data
        assert "stocks" in data
        assert len(data["stocks"]) == 1
        assert data["stocks"][0]["code"] == "2330"
        assert data["stocks"][0]["trade_volume"] == 50000000
        assert data["stocks"][0]["prev_close"] == 1090.00
        assert data["stocks"][0]["open_price"] == 1090.00

    @patch("tw_stock_hot.web.routers.hot.tpex_engine")
    @patch("tw_stock_hot.web.routers.hot.twse_engine")
    def test_combined_sorted_by_volume(self, mock_twse_eng, mock_tpex_eng, client):
        """TWSE 與 TPEX 合併後應依交易量降冪排序。"""
        mock_twse_conn = MagicMock()
        mock_twse_eng.connect.return_value.__enter__ = lambda _: mock_twse_conn
        mock_twse_eng.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_twse_conn.execute.return_value.mappings.return_value.all.return_value = [
            {
                "code": "2330", "name": "台積電",
                "trade_volume": 30000000, "trade_value": 33000000000,
                "prev_close": 1090.00,
                "open_price": 1090.00,
                "close_price": 1100.00, "price_change": 10.00,
                "change_pct": 0.92, "industry": "半導體業", "market": "TWSE",
            }
        ]

        mock_tpex_conn = MagicMock()
        mock_tpex_eng.connect.return_value.__enter__ = lambda _: mock_tpex_conn
        mock_tpex_eng.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_tpex_conn.execute.return_value.mappings.return_value.all.return_value = [
            {
                "code": "6547", "name": "高端疫苗",
                "trade_volume": 80000000, "trade_value": 17600000000,
                "prev_close": 215.00,
                "open_price": 215.00,
                "close_price": 220.00, "price_change": 5.00,
                "change_pct": 2.33, "industry": "未分類", "market": "TPEX",
            }
        ]

        res = client.get("/api/hot/top-volume?date=2026-03-02")
        data = res.json()
        assert data["stocks"][0]["code"] == "6547"
        assert data["stocks"][1]["code"] == "2330"


# ============================================================
# /api/hot/top-value
# ============================================================

class TestGetTopValue:
    """測試 /api/hot/top-value 端點。"""

    @patch("tw_stock_hot.web.routers.hot.tpex_engine")
    @patch("tw_stock_hot.web.routers.hot.twse_engine")
    def test_response_format(self, mock_twse_eng, mock_tpex_eng, client):
        """回應應包含 stocks 清單與 date，且包含 prev_close 與 open_price 欄位。"""
        mock_twse_conn = MagicMock()
        mock_twse_eng.connect.return_value.__enter__ = lambda _: mock_twse_conn
        mock_twse_eng.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_twse_conn.execute.return_value.mappings.return_value.all.return_value = [
            {
                "code": "2330", "name": "台積電",
                "trade_volume": 50000000, "trade_value": 55000000000,
                "prev_close": 1090.00,
                "open_price": 1090.00,
                "close_price": 1100.00, "price_change": 10.00,
                "change_pct": 0.92, "industry": "半導體業", "market": "TWSE",
            }
        ]

        mock_tpex_conn = MagicMock()
        mock_tpex_eng.connect.return_value.__enter__ = lambda _: mock_tpex_conn
        mock_tpex_eng.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_tpex_conn.execute.return_value.mappings.return_value.all.return_value = []

        res = client.get("/api/hot/top-value?date=2026-03-02")
        assert res.status_code == 200

        data = res.json()
        assert "date" in data
        assert "stocks" in data
        assert len(data["stocks"]) == 1
        assert data["stocks"][0]["trade_value"] == 55000000000
        assert data["stocks"][0]["prev_close"] == 1090.00
        assert data["stocks"][0]["open_price"] == 1090.00

    @patch("tw_stock_hot.web.routers.hot.tpex_engine")
    @patch("tw_stock_hot.web.routers.hot.twse_engine")
    def test_combined_sorted_by_value(self, mock_twse_eng, mock_tpex_eng, client):
        """TWSE 與 TPEX 合併後應依交易金額降冪排序。"""
        mock_twse_conn = MagicMock()
        mock_twse_eng.connect.return_value.__enter__ = lambda _: mock_twse_conn
        mock_twse_eng.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_twse_conn.execute.return_value.mappings.return_value.all.return_value = [
            {
                "code": "2330", "name": "台積電",
                "trade_volume": 50000000, "trade_value": 55000000000,
                "prev_close": 1090.00,
                "open_price": 1090.00,
                "close_price": 1100.00, "price_change": 10.00,
                "change_pct": 0.92, "industry": "半導體業", "market": "TWSE",
            }
        ]

        mock_tpex_conn = MagicMock()
        mock_tpex_eng.connect.return_value.__enter__ = lambda _: mock_tpex_conn
        mock_tpex_eng.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_tpex_conn.execute.return_value.mappings.return_value.all.return_value = [
            {
                "code": "6547", "name": "高端疫苗",
                "trade_volume": 80000000, "trade_value": 17600000000,
                "prev_close": 215.00,
                "open_price": 215.00,
                "close_price": 220.00, "price_change": 5.00,
                "change_pct": 2.33, "industry": "未分類", "market": "TPEX",
            }
        ]

        res = client.get("/api/hot/top-value?date=2026-03-02")
        data = res.json()
        # 台積電交易金額 55B > 高端 17.6B
        assert data["stocks"][0]["code"] == "2330"
        assert data["stocks"][1]["code"] == "6547"


# ============================================================
# /api/hot/industry-change
# ============================================================

class TestGetIndustryChange:
    """測試 /api/hot/industry-change 端點。"""

    @patch("tw_stock_hot.web.routers.hot.twse_engine")
    def test_response_format(self, mock_twse_eng, client):
        """回應應包含 industries 清單與 date。"""
        mock_conn = MagicMock()
        mock_twse_eng.connect.return_value.__enter__ = lambda _: mock_conn
        mock_twse_eng.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.mappings.return_value.all.return_value = [
            {"industry": "半導體業", "stock_count": 30, "avg_change_pct": 2.15},
            {"industry": "金融保險業", "stock_count": 25, "avg_change_pct": 1.05},
        ]

        res = client.get("/api/hot/industry-change?date=2026-03-02")
        assert res.status_code == 200

        data = res.json()
        assert "date" in data
        assert "industries" in data
        assert len(data["industries"]) == 2
        assert data["industries"][0]["industry"] == "半導體業"
        assert data["industries"][0]["stock_count"] == 30
        assert data["industries"][0]["avg_change_pct"] == 2.15

    @patch("tw_stock_hot.web.routers.hot.twse_engine")
    def test_empty_result(self, mock_twse_eng, client):
        """無資料時應回傳空清單。"""
        mock_conn = MagicMock()
        mock_twse_eng.connect.return_value.__enter__ = lambda _: mock_conn
        mock_twse_eng.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.mappings.return_value.all.return_value = []

        res = client.get("/api/hot/industry-change?date=2026-01-01")
        data = res.json()
        assert data["industries"] == []


# ============================================================
# /api/hot/industry-ratio
# ============================================================

class TestGetIndustryRatio:
    """測試 /api/hot/industry-ratio 端點。"""

    @patch("tw_stock_hot.web.routers.hot.twse_engine")
    def test_response_format(self, mock_twse_eng, client):
        """回應應包含 industries 清單與完整欄位。"""
        mock_conn = MagicMock()
        mock_twse_eng.connect.return_value.__enter__ = lambda _: mock_conn
        mock_twse_eng.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.mappings.return_value.all.return_value = [
            {
                "industry": "半導體業",
                "total_count": 30,
                "up_count": 20,
                "down_count": 5,
                "ratio_pct": 50.0,
            },
            {
                "industry": "金融保險業",
                "total_count": 25,
                "up_count": 10,
                "down_count": 12,
                "ratio_pct": -8.0,
            },
        ]

        res = client.get("/api/hot/industry-ratio?date=2026-03-02")
        assert res.status_code == 200

        data = res.json()
        assert "date" in data
        assert "industries" in data
        assert len(data["industries"]) == 2

        first = data["industries"][0]
        assert first["industry"] == "半導體業"
        assert first["ratio_pct"] == 50.0
        assert first["up_count"] == 20
        assert first["down_count"] == 5
        assert first["total_count"] == 30

    @patch("tw_stock_hot.web.routers.hot.twse_engine")
    def test_negative_ratio(self, mock_twse_eng, client):
        """跌多於漲的產業應有負的 ratio_pct。"""
        mock_conn = MagicMock()
        mock_twse_eng.connect.return_value.__enter__ = lambda _: mock_conn
        mock_twse_eng.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.mappings.return_value.all.return_value = [
            {
                "industry": "航運業",
                "total_count": 10,
                "up_count": 2,
                "down_count": 7,
                "ratio_pct": -50.0,
            },
        ]

        res = client.get("/api/hot/industry-ratio?date=2026-03-02")
        data = res.json()
        assert data["industries"][0]["ratio_pct"] == -50.0
        assert data["industries"][0]["up_count"] == 2
        assert data["industries"][0]["down_count"] == 7

    @patch("tw_stock_hot.web.routers.hot.twse_engine")
    def test_empty_result(self, mock_twse_eng, client):
        """無資料時應回傳空清單。"""
        mock_conn = MagicMock()
        mock_twse_eng.connect.return_value.__enter__ = lambda _: mock_conn
        mock_twse_eng.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.mappings.return_value.all.return_value = []

        res = client.get("/api/hot/industry-ratio?date=2026-01-01")
        data = res.json()
        assert data["industries"] == []


# ============================================================
# /api/hot/industry-stocks
# ============================================================

class TestGetIndustryStocks:
    """測試 /api/hot/industry-stocks 端點。"""

    @patch("tw_stock_hot.web.routers.hot.twse_engine")
    def test_response_format(self, mock_twse_eng, client):
        """回應應包含 date、industry、stock_count、stocks 清單。"""
        mock_conn = MagicMock()
        mock_twse_eng.connect.return_value.__enter__ = lambda _: mock_conn
        mock_twse_eng.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.mappings.return_value.all.return_value = [
            {
                "code": "2330", "name": "台積電",
                "prev_close": 1090.00,
                "open_price": 1090.00, "close_price": 1100.00,
                "price_change": 10.00, "change_pct": 0.92,
                "trade_volume": 50000000, "trade_value": 55000000000,
                "industry": "半導體業",
            },
            {
                "code": "2303", "name": "聯電",
                "prev_close": 55.00,
                "open_price": 55.00, "close_price": 56.00,
                "price_change": 1.00, "change_pct": 1.82,
                "trade_volume": 30000000, "trade_value": 1680000000,
                "industry": "半導體業",
            },
        ]

        res = client.get(
            "/api/hot/industry-stocks?date=2026-03-02&industry=半導體業"
        )
        assert res.status_code == 200

        data = res.json()
        assert data["date"] == "2026-03-02"
        assert data["industry"] == "半導體業"
        assert data["stock_count"] == 2
        assert len(data["stocks"]) == 2
        assert data["stocks"][0]["code"] == "2330"
        assert data["stocks"][0]["prev_close"] == 1090.00
        assert data["stocks"][0]["open_price"] == 1090.00
        assert data["stocks"][0]["close_price"] == 1100.00
        assert data["stocks"][0]["trade_volume"] == 50000000
        assert data["stocks"][1]["code"] == "2303"

    @patch("tw_stock_hot.web.routers.hot.twse_engine")
    def test_empty_result(self, mock_twse_eng, client):
        """無資料時應回傳空 stocks 清單與 stock_count 為 0。"""
        mock_conn = MagicMock()
        mock_twse_eng.connect.return_value.__enter__ = lambda _: mock_conn
        mock_twse_eng.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.mappings.return_value.all.return_value = []

        res = client.get(
            "/api/hot/industry-stocks?date=2026-01-01&industry=不存在的產業"
        )
        assert res.status_code == 200

        data = res.json()
        assert data["stocks"] == []
        assert data["stock_count"] == 0

    def test_missing_industry_param(self, client):
        """缺少必要的 industry 參數應回傳 422。"""
        res = client.get("/api/hot/industry-stocks?date=2026-03-02")
        assert res.status_code == 422


# ============================================================
# /api/hot/dates
# ============================================================

class TestGetAvailableDates:
    """測試 /api/hot/dates 端點。"""

    @patch("tw_stock_hot.web.routers.hot.twse_engine")
    def test_dates_response_format(self, mock_engine, client):
        """回應應包含日期清單。"""
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__ = lambda _: mock_conn
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.fetchall.return_value = [
            ("2026-03-02",), ("2026-03-01",),
        ]

        res = client.get("/api/hot/dates")
        assert res.status_code == 200
        data = res.json()
        assert "dates" in data


# ============================================================
# 日期退回邏輯（最新日無資料 → 退回最近有資料日）
# ============================================================

class TestQueryLatestDate:
    """測試 _query_latest_date_on_or_before 底層查詢函式。"""

    @patch("tw_stock_hot.web.routers.hot.twse_engine")
    def test_returns_date_when_present(self, mock_eng):
        """資料庫有 <= 目標日期的資料時應回傳該最大日期。"""
        mock_conn = MagicMock()
        mock_eng.connect.return_value.__enter__ = lambda _: mock_conn
        mock_eng.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.scalar.return_value = date(2026, 3, 2)

        result = _real_query_latest_date(date(2026, 3, 5))
        assert result == date(2026, 3, 2)

    @patch("tw_stock_hot.web.routers.hot.twse_engine")
    def test_returns_none_when_no_data(self, mock_eng):
        """查無資料（scalar 為 None）時應回傳 None。"""
        mock_conn = MagicMock()
        mock_eng.connect.return_value.__enter__ = lambda _: mock_conn
        mock_eng.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.scalar.return_value = None

        result = _real_query_latest_date(date(2026, 3, 5))
        assert result is None

    @patch("tw_stock_hot.web.routers.hot.twse_engine")
    def test_ignores_non_date_value(self, mock_eng):
        """scalar 回傳非 date 型別（髒資料）時應視為查無資料回傳 None。"""
        mock_conn = MagicMock()
        mock_eng.connect.return_value.__enter__ = lambda _: mock_conn
        mock_eng.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.scalar.return_value = "not-a-date"

        result = _real_query_latest_date(date(2026, 3, 5))
        assert result is None


class TestResolveTradingDate:
    """測試 _resolve_trading_date 退回解析邏輯。"""

    @patch("tw_stock_hot.web.routers.hot._query_latest_date_on_or_before")
    def test_default_returns_latest_available(self, mock_latest):
        """不帶日期時，requested 為今天、actual 為資料庫最新有資料日。"""
        mock_latest.return_value = date(2026, 3, 2)
        requested, actual = _resolve_trading_date(None)
        assert requested == date.today()
        assert actual == date(2026, 3, 2)
        mock_latest.assert_called_once_with(date.today())

    @patch("tw_stock_hot.web.routers.hot._query_latest_date_on_or_before")
    def test_specified_date_with_data(self, mock_latest):
        """指定有資料日期時，requested 與 actual 應一致。"""
        mock_latest.return_value = date(2026, 3, 2)
        requested, actual = _resolve_trading_date("2026-03-02")
        assert requested == date(2026, 3, 2)
        assert actual == date(2026, 3, 2)

    @patch("tw_stock_hot.web.routers.hot._query_latest_date_on_or_before")
    def test_specified_nodata_falls_back(self, mock_latest):
        """指定無資料日期時，actual 應退回到最近有資料日。"""
        mock_latest.return_value = date(2026, 3, 2)
        requested, actual = _resolve_trading_date("2026-03-05")
        assert requested == date(2026, 3, 5)
        assert actual == date(2026, 3, 2)

    @patch("tw_stock_hot.web.routers.hot._query_latest_date_on_or_before")
    def test_no_data_in_db_keeps_requested(self, mock_latest):
        """資料庫完全無資料時，actual 退回為請求日本身。"""
        mock_latest.return_value = None
        requested, actual = _resolve_trading_date("2026-03-05")
        assert requested == date(2026, 3, 5)
        assert actual == date(2026, 3, 5)


class TestDateFallbackEndpoints:
    """測試各 API 在「最新日無資料」情境下會退回並標示實際日期。"""

    @patch("tw_stock_hot.web.routers.hot._query_twse_limit_stocks")
    @patch("tw_stock_hot.web.routers.hot._query_latest_date_on_or_before")
    def test_limit_default_uses_latest_available_date(
        self, mock_latest, mock_query, client
    ):
        """預設（不帶 date）開啟漲跌停應顯示最後一個有資料日的資料，不空白。"""
        # 模擬今天尚無資料，資料庫最新有資料日為 2026-03-02
        mock_latest.return_value = date(2026, 3, 2)
        mock_query.return_value = [
            {"code": "2330", "name": "台積電", "prev_close": 1000.0,
             "open_price": 1005.0, "close_price": 1100.0,
             "price_change": 100.0, "change_pct": 10.0, "industry": "半導體業"},
        ]

        res = client.get("/api/hot/limit")
        assert res.status_code == 200
        data = res.json()
        # 標題顯示的 date 為退回後實際採用日期
        assert data["date"] == "2026-03-02"
        # requested_date 為預設的今天
        assert data["requested_date"] == date.today().isoformat()
        # 畫面不再空白
        assert data["limit_up_count"] == 1
        # 以退回後日期實際查詢
        mock_query.assert_called_once_with(date(2026, 3, 2))

    @patch("tw_stock_hot.web.routers.hot._query_twse_limit_stocks")
    @patch("tw_stock_hot.web.routers.hot._query_latest_date_on_or_before")
    def test_limit_specified_nodata_falls_back(
        self, mock_latest, mock_query, client
    ):
        """指定一個無資料日期查詢，應退回最近有資料日並於回應標示。"""
        # 使用者指定 2026-03-05（無資料），最近有資料日為 2026-03-02
        mock_latest.return_value = date(2026, 3, 2)
        mock_query.return_value = []

        res = client.get("/api/hot/limit?date=2026-03-05")
        data = res.json()
        assert data["requested_date"] == "2026-03-05"
        assert data["date"] == "2026-03-02"
        mock_latest.assert_called_once_with(date(2026, 3, 5))
        mock_query.assert_called_once_with(date(2026, 3, 2))

    @patch("tw_stock_hot.web.routers.hot._query_twse_limit_stocks")
    @patch("tw_stock_hot.web.routers.hot._query_latest_date_on_or_before")
    def test_limit_no_data_in_db_keeps_requested(
        self, mock_latest, mock_query, client
    ):
        """資料庫完全無資料時，date 退回為請求日本身且結果為空。"""
        mock_latest.return_value = None
        mock_query.return_value = []

        res = client.get("/api/hot/limit?date=2026-03-05")
        data = res.json()
        assert data["date"] == "2026-03-05"
        assert data["requested_date"] == "2026-03-05"
        assert data["limit_up_count"] == 0
        assert data["limit_down_count"] == 0

    @patch("tw_stock_hot.web.routers.hot.tpex_engine")
    @patch("tw_stock_hot.web.routers.hot.twse_engine")
    @patch("tw_stock_hot.web.routers.hot._query_latest_date_on_or_before")
    def test_top_volume_default_uses_latest_available_date(
        self, mock_latest, mock_twse_eng, mock_tpex_eng, client
    ):
        """交易量 TOP 10 預設開啟應退回到最新有資料日並標示。"""
        mock_latest.return_value = date(2026, 3, 2)

        mock_twse_conn = MagicMock()
        mock_twse_eng.connect.return_value.__enter__ = lambda _: mock_twse_conn
        mock_twse_eng.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_twse_conn.execute.return_value.mappings.return_value.all.return_value = [
            {
                "code": "2330", "name": "台積電",
                "trade_volume": 50000000, "trade_value": 55000000000,
                "prev_close": 1090.00, "open_price": 1090.00,
                "close_price": 1100.00, "price_change": 10.00,
                "change_pct": 0.92, "industry": "半導體業", "market": "TWSE",
            }
        ]

        mock_tpex_conn = MagicMock()
        mock_tpex_eng.connect.return_value.__enter__ = lambda _: mock_tpex_conn
        mock_tpex_eng.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_tpex_conn.execute.return_value.mappings.return_value.all.return_value = []

        res = client.get("/api/hot/top-volume")
        data = res.json()
        assert data["date"] == "2026-03-02"
        assert data["requested_date"] == date.today().isoformat()
        assert len(data["stocks"]) == 1

    @patch("tw_stock_hot.web.routers.hot.twse_engine")
    @patch("tw_stock_hot.web.routers.hot._query_latest_date_on_or_before")
    def test_industry_change_specified_nodata_falls_back(
        self, mock_latest, mock_twse_eng, client
    ):
        """產業漲幅排行指定無資料日時應退回並標示 requested_date。"""
        mock_latest.return_value = date(2026, 3, 2)
        mock_conn = MagicMock()
        mock_twse_eng.connect.return_value.__enter__ = lambda _: mock_conn
        mock_twse_eng.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.mappings.return_value.all.return_value = [
            {"industry": "半導體業", "stock_count": 30, "avg_change_pct": 2.15},
        ]

        res = client.get("/api/hot/industry-change?date=2026-03-05")
        data = res.json()
        assert data["date"] == "2026-03-02"
        assert data["requested_date"] == "2026-03-05"
        assert len(data["industries"]) == 1


# ============================================================
# 路由註冊
# ============================================================

class TestRouteRegistered:
    """測試路由是否正確註冊。

    以 ``app.openapi()['paths']`` 列舉已註冊路由，避免新版 FastAPI
    （include_router 改為延遲包含、``app.routes`` 含 ``_IncludedRouter``
    佔位物件）導致直接走訪 ``app.routes`` 取不到路徑。
    """

    @staticmethod
    def _registered_paths() -> set[str]:
        """取得目前已註冊的 API 路徑集合。"""
        return set(app.openapi()["paths"].keys())

    def test_hot_limit_route_exists(self, client):
        """漲跌停路由應存在。"""
        assert "/api/hot/limit" in self._registered_paths()

    def test_hot_dates_route_exists(self, client):
        """日期路由應存在。"""
        assert "/api/hot/dates" in self._registered_paths()

    def test_hot_top_volume_route_exists(self, client):
        """交易量排行路由應存在。"""
        assert "/api/hot/top-volume" in self._registered_paths()

    def test_hot_top_value_route_exists(self, client):
        """交易金額排行路由應存在。"""
        assert "/api/hot/top-value" in self._registered_paths()

    def test_hot_industry_change_route_exists(self, client):
        """產業漲幅排行路由應存在。"""
        assert "/api/hot/industry-change" in self._registered_paths()

    def test_hot_industry_ratio_route_exists(self, client):
        """產業漲幅佔比排行路由應存在。"""
        assert "/api/hot/industry-ratio" in self._registered_paths()

    def test_hot_industry_stocks_route_exists(self, client):
        """產業股票明細路由應存在。"""
        assert "/api/hot/industry-stocks" in self._registered_paths()
