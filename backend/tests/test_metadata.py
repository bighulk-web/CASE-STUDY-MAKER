from __future__ import annotations

from app.services.metadata.heuristic import heuristic_metadata, heuristic_year


def test_heuristic_extracts_industry_and_tech() -> None:
    text = (
        "Acme Manufacturing modernized its ERP with SAP S/4HANA in 2023. "
        "The challenge was fragmented supply chain data across EMEA. "
        "The solution delivered a 30% reduction in inventory costs over 6 months."
    )
    meta = heuristic_metadata(text)
    assert meta.industry == "Manufacturing"
    assert "SAP S/4HANA" in meta.technology
    assert meta.region == "EMEA"
    assert "Supply Chain" in meta.business_functions
    assert meta.implementation_duration == "6 months"
    assert any("30%" in b for b in meta.benefits)
    assert meta.customer.startswith("Acme")
    assert meta.confidence_score > 0
    assert heuristic_year(text) == 2023


def test_heuristic_empty_text() -> None:
    meta = heuristic_metadata("")
    assert meta.confidence_score == 0.0
    assert meta.industry == ""
