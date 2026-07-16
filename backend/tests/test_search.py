from __future__ import annotations

from pathlib import Path

from tests import fixtures


def _seed(client, tmp_path: Path) -> None:
    docs = {
        "acme.txt": "Acme Manufacturing modernized its ERP with SAP S/4HANA in 2023, "
        "cutting inventory costs 30% across EMEA supply chain operations.",
        "globex.txt": "Globex Healthcare deployed an AI diagnostics platform in APAC, "
        "reducing patient wait times by 40%.",
        "initech.txt": "Initech Bank implemented Oracle ERP for finance transformation "
        "in North America, improving financial close by 25%.",
        "umbrella.txt": "Umbrella Manufacturing adopted Microsoft Azure IoT for smart "
        "factory analytics, boosting production uptime.",
    }
    for name, text in docs.items():
        p = fixtures.make_txt(tmp_path / name, text=text)
        with p.open("rb") as fh:
            r = client.post("/api/documents", files=[("files", (name, fh.read()))])
        assert r.status_code == 200


def test_structured_search_industry_filter(client, tmp_path: Path) -> None:
    _seed(client, tmp_path)
    resp = client.post("/api/search", json={"industries": ["Manufacturing"]})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 2
    assert all(i["industry"] == "Manufacturing" for i in items)


def test_semantic_keyword_search_ranks_sap(client, tmp_path: Path) -> None:
    _seed(client, tmp_path)
    resp = client.post("/api/search", json={"query": "SAP manufacturing ERP inventory"})
    items = resp.json()["items"]
    assert items, "expected results"
    assert "Acme" in items[0]["customer"]
    assert any(s in items[0]["signals"] for s in ("semantic", "keyword"))


def test_facets(client, tmp_path: Path) -> None:
    _seed(client, tmp_path)
    facets = client.get("/api/search/facets").json()
    assert "Manufacturing" in facets["industries"]
    assert "Healthcare" in facets["industries"]
    assert 2023 in facets["years"]


def test_intent_search(client, tmp_path: Path) -> None:
    _seed(client, tmp_path)
    resp = client.post(
        "/api/search/intent",
        json={"prompt": "Create a manufacturing presentation showing our SAP projects, top 3 case studies"},
    )
    body = resp.json()
    assert body["intent"]["industries"] == ["Manufacturing"]
    assert "SAP" in body["intent"]["technologies"]
    assert body["intent"]["max_case_studies"] == 3
    # Only manufacturing case studies returned.
    assert all(i["industry"] == "Manufacturing" for i in body["items"])


def test_parse_intent_slides_and_layout(client) -> None:
    resp = client.post(
        "/api/search/parse",
        json={"prompt": "Create a healthcare AI deck with 8 slides, two per slide, recent first"},
    )
    intent = resp.json()["intent"]
    assert intent["num_slides"] == 8
    assert intent["layout"] == "two_per_slide"
    assert intent["sort_order"] == "recent"
    assert "Healthcare" in intent["industries"]
