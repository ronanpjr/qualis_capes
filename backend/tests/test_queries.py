"""
Unit tests for queries.py — testam a lógica SQL isolada do HTTP layer.
Cada teste recebe uma sessão SQLite limpa via fixture.
"""

import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import queries


class TestGetAreas:
    def test_returns_list_of_strings(self, db):
        result = queries.get_areas(db)
        assert isinstance(result, list)
        assert all(isinstance(a, str) for a in result)

    def test_returns_distinct_areas(self, db):
        result = queries.get_areas(db)
        assert len(result) == len(set(result)), "Áreas devem ser únicas"

    def test_areas_are_sorted(self, db):
        result = queries.get_areas(db)
        assert result == sorted(result)

    def test_includes_seeded_areas(self, db):
        result = queries.get_areas(db)
        assert "COMPUTAÇÃO" in result
        assert "MEDICINA I" in result
        assert "ENGENHARIAS I" in result


class TestSearchPeriodicos:
    def test_returns_all_without_filters(self, db):
        items, total = queries.search_periodicos(db)
        assert total == 9
        assert len(items) == 9

    def test_filter_by_area(self, db):
        items, total = queries.search_periodicos(db, area="COMPUTAÇÃO")
        assert total == 5
        assert all(p["area"] == "COMPUTAÇÃO" for p in items)

    def test_filter_by_estrato(self, db):
        items, total = queries.search_periodicos(db, estrato="A1")
        assert total == 3
        assert all(p["estrato"] == "A1" for p in items)

    def test_combined_filter_area_and_estrato(self, db):
        items, total = queries.search_periodicos(db, area="COMPUTAÇÃO", estrato="A1")
        assert total == 1
        assert items[0]["titulo"] == "Journal of Testing A1"

    def test_search_by_title(self, db):
        items, total = queries.search_periodicos(db, search="testing")
        # "Journal of Testing A1/A2/B1/C" + "Journal of Testing A3" + "Testing ISSN Search" = 6
        assert total >= 1
        assert all("testing" in p["titulo"].lower() for p in items)

    def test_search_by_issn(self, db):
        items, total = queries.search_periodicos(db, search="1234-5678")
        assert total == 1
        assert items[0]["issn"] == "1234-5678"

    def test_pagination_first_page(self, db):
        items, total = queries.search_periodicos(db, per_page=3, page=1)
        assert total == 9
        assert len(items) == 3

    def test_pagination_second_page(self, db):
        items_p1, _ = queries.search_periodicos(db, per_page=3, page=1)
        items_p2, _ = queries.search_periodicos(db, per_page=3, page=2)
        titles_p1 = {p["titulo"] for p in items_p1}
        titles_p2 = {p["titulo"] for p in items_p2}
        assert titles_p1.isdisjoint(titles_p2), "Páginas não devem se sobrepor"

    def test_empty_result_for_unknown_area(self, db):
        items, total = queries.search_periodicos(db, area="ÁREA INEXISTENTE")
        assert total == 0
        assert items == []

    def test_result_items_have_required_fields(self, db):
        items, _ = queries.search_periodicos(db, per_page=1)
        assert {"id", "issn", "titulo", "area", "estrato"} <= set(items[0].keys())

    def test_invalid_estrato_returns_empty(self, db):
        items, total = queries.search_periodicos(db, estrato="Z9")
        assert total == 0


class TestGetDistribuicao:
    def test_returns_list_of_dicts(self, db):
        result = queries.get_distribuicao(db, area="COMPUTAÇÃO")
        assert isinstance(result, list)
        assert all(isinstance(r, dict) for r in result)

    def test_has_expected_keys(self, db):
        result = queries.get_distribuicao(db, area="COMPUTAÇÃO")
        for item in result:
            assert {"estrato", "count", "percentual"} <= set(item.keys())

    def test_count_is_correct(self, db):
        result = queries.get_distribuicao(db, area="COMPUTAÇÃO")
        total = sum(r["count"] for r in result)
        assert total == 5  # 5 periódicos na área COMPUTAÇÃO

    def test_percentual_sums_to_100(self, db):
        result = queries.get_distribuicao(db, area="COMPUTAÇÃO")
        total_pct = sum(r["percentual"] for r in result)
        assert abs(total_pct - 100.0) < 0.1

    def test_estratos_are_ordered(self, db):
        result = queries.get_distribuicao(db, area="COMPUTAÇÃO")
        estratos = [r["estrato"] for r in result]
        order = {"A1": 1, "A2": 2, "A3": 3, "A4": 4, "B1": 5, "B2": 6, "B3": 7, "B4": 8, "C": 9}
        positions = [order.get(e, 99) for e in estratos]
        assert positions == sorted(positions)

    def test_empty_for_unknown_area(self, db):
        result = queries.get_distribuicao(db, area="ÁREA INEXISTENTE")
        assert result == []
