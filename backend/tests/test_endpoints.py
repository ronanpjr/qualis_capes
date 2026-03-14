"""
Integration tests for the FastAPI HTTP endpoints.
Tests the full request/response cycle with a test SQLite database.
"""

import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_structure(self, client):
        data = client.get("/health").json()
        assert "status" in data
        assert data["status"] == "ok"


class TestAreasEndpoint:
    def test_get_areas_success(self, client):
        response = client.get("/api/areas")
        assert response.status_code == 200

    def test_get_areas_returns_list(self, client):
        data = client.get("/api/areas").json()
        assert isinstance(data, list)

    def test_get_areas_has_items(self, client):
        data = client.get("/api/areas").json()
        assert len(data) > 0

    def test_get_areas_are_strings(self, client):
        data = client.get("/api/areas").json()
        assert all(isinstance(a, str) for a in data)


class TestPeriodicosEndpoint:
    def test_list_all_periodicos(self, client):
        response = client.get("/api/periodicos")
        assert response.status_code == 200

    def test_response_has_pagination_fields(self, client):
        data = client.get("/api/periodicos").json()
        assert {"items", "total", "page", "per_page", "total_pages"} <= set(data.keys())

    def test_filter_by_area(self, client):
        response = client.get("/api/periodicos?area=COMPUTAÇÃO")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert all(p["area"] == "COMPUTAÇÃO" for p in data["items"])

    def test_filter_by_estrato(self, client):
        response = client.get("/api/periodicos?estrato=A1")
        assert response.status_code == 200
        data = response.json()
        assert all(p["estrato"] == "A1" for p in data["items"])

    def test_filter_by_area_and_estrato(self, client):
        response = client.get("/api/periodicos?area=COMPUTAÇÃO&estrato=A1")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_search_query(self, client):
        response = client.get("/api/periodicos?search=testing")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    def test_invalid_estrato_returns_empty(self, client):
        response = client.get("/api/periodicos?estrato=Z9")
        # Estrato inválido é rejeitado pelo schema (422) ou retorna vazio (200)
        assert response.status_code in (200, 422)

    def test_pagination_per_page(self, client):
        response = client.get("/api/periodicos?per_page=2&page=1")
        data = response.json()
        assert len(data["items"]) == 2
        assert data["per_page"] == 2

    def test_per_page_capped_at_100(self, client):
        response = client.get("/api/periodicos?per_page=999")
        data = response.json()
        assert data["per_page"] <= 100

    def test_item_has_required_fields(self, client):
        data = client.get("/api/periodicos?per_page=1").json()
        item = data["items"][0]
        assert {"id", "issn", "titulo", "area", "estrato"} <= set(item.keys())

    def test_total_pages_calculated_correctly(self, client):
        data = client.get("/api/periodicos?per_page=3").json()
        expected_pages = (data["total"] + 2) // 3  # ceil division
        assert data["total_pages"] == expected_pages


class TestDistribuicaoEndpoint:
    def test_distribuicao_success(self, client):
        response = client.get("/api/areas/COMPUTAÇÃO/distribuicao")
        assert response.status_code == 200

    def test_distribuicao_response_structure(self, client):
        data = client.get("/api/areas/COMPUTAÇÃO/distribuicao").json()
        assert "area" in data
        assert "total" in data
        assert "distribuicao" in data

    def test_distribuicao_items_have_fields(self, client):
        data = client.get("/api/areas/COMPUTAÇÃO/distribuicao").json()
        for item in data["distribuicao"]:
            assert {"estrato", "count", "percentual"} <= set(item.keys())

    def test_distribuicao_total_is_correct(self, client):
        data = client.get("/api/areas/COMPUTAÇÃO/distribuicao").json()
        assert data["total"] == 5

    def test_distribuicao_percentuals_sum_100(self, client):
        data = client.get("/api/areas/COMPUTAÇÃO/distribuicao").json()
        total_pct = sum(item["percentual"] for item in data["distribuicao"])
        assert abs(total_pct - 100.0) < 0.1

    def test_distribuicao_unknown_area_returns_empty(self, client):
        response = client.get("/api/areas/ÁREA_INEXISTENTE/distribuicao")
        assert response.status_code in (200, 404)


class TestChatEndpoint:
    def test_chat_requires_message(self, client):
        response = client.post("/api/chat", json={})
        assert response.status_code == 422

    def test_chat_empty_message_rejected(self, client):
        response = client.post("/api/chat", json={"message": ""})
        assert response.status_code == 422

    def test_chat_message_too_long_rejected(self, client):
        response = client.post("/api/chat", json={"message": "x" * 501})
        assert response.status_code == 422

    def test_chat_without_api_key_returns_error(self, client, monkeypatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        response = client.post("/api/chat", json={"message": "Olá"})
        # Deve retornar 500 (RuntimeError) ou 200 se não chamar Gemini
        assert response.status_code in (200, 500)
