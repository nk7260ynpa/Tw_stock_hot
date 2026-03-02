"""漲跌停 API 單元測試。"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from tw_stock_hot.web.app import app


@pytest.fixture
def client():
    """建立測試用 FastAPI client。"""
    return TestClient(app)


class TestGetLimitStocks:
    """測試 /api/hot/limit 端點。"""

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
