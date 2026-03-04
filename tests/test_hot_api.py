"""台股熱度 API 單元測試。"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from tw_stock_hot.web.app import app


@pytest.fixture
def client():
    """建立測試用 FastAPI client。"""
    return TestClient(app)


# ============================================================
# /api/hot/limit
# ============================================================

class TestGetLimitStocks:
    """測試 /api/hot/limit 端點（僅 TWSE 上市股票）。"""

    @patch("tw_stock_hot.web.routers.hot._query_twse_limit_stocks")
    def test_response_format(self, mock_twse, client):
        """回應應包含漲停與跌停清單。"""
        mock_twse.return_value = [
            {
                "code": "2330",
                "name": "台積電",
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

    @patch("tw_stock_hot.web.routers.hot._query_twse_limit_stocks")
    def test_industry_stats(self, mock_twse, client):
        """產業統計應正確計算。"""
        mock_twse.return_value = [
            {"code": "2330", "name": "台積電", "close_price": 1100.00,
             "price_change": 100.00, "change_pct": 10.0, "industry": "半導體業"},
            {"code": "3711", "name": "日月光", "close_price": 220.00,
             "price_change": 20.00, "change_pct": 10.0, "industry": "半導體業"},
            {"code": "2317", "name": "鴻海", "close_price": 165.00,
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
        """回應應包含 stocks 清單與 date。"""
        mock_twse_conn = MagicMock()
        mock_twse_eng.connect.return_value.__enter__ = lambda _: mock_twse_conn
        mock_twse_eng.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_twse_conn.execute.return_value.mappings.return_value.all.return_value = [
            {
                "code": "2330", "name": "台積電",
                "trade_volume": 50000000, "trade_value": 55000000000,
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
        """回應應包含 stocks 清單與 date。"""
        mock_twse_conn = MagicMock()
        mock_twse_eng.connect.return_value.__enter__ = lambda _: mock_twse_conn
        mock_twse_eng.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_twse_conn.execute.return_value.mappings.return_value.all.return_value = [
            {
                "code": "2330", "name": "台積電",
                "trade_volume": 50000000, "trade_value": 55000000000,
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
# 路由註冊
# ============================================================

class TestRouteRegistered:
    """測試路由是否正確註冊。"""

    def test_hot_limit_route_exists(self, client):
        """漲跌停路由應存在。"""
        routes = [r.path for r in app.routes]
        assert "/api/hot/limit" in routes

    def test_hot_dates_route_exists(self, client):
        """日期路由應存在。"""
        routes = [r.path for r in app.routes]
        assert "/api/hot/dates" in routes

    def test_hot_top_volume_route_exists(self, client):
        """交易量排行路由應存在。"""
        routes = [r.path for r in app.routes]
        assert "/api/hot/top-volume" in routes

    def test_hot_top_value_route_exists(self, client):
        """交易金額排行路由應存在。"""
        routes = [r.path for r in app.routes]
        assert "/api/hot/top-value" in routes

    def test_hot_industry_change_route_exists(self, client):
        """產業漲幅排行路由應存在。"""
        routes = [r.path for r in app.routes]
        assert "/api/hot/industry-change" in routes

    def test_hot_industry_ratio_route_exists(self, client):
        """產業漲幅佔比排行路由應存在。"""
        routes = [r.path for r in app.routes]
        assert "/api/hot/industry-ratio" in routes
