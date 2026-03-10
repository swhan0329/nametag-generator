from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from nametag_generator.web import create_app


def test_home_page_shows_schema_and_preview_help() -> None:
    client = TestClient(create_app())
    response = client.get("/")
    assert response.status_code == 200
    body = response.text
    assert "<title>Nametag Generator | Create Print-Ready Event Name Tags from Excel</title>" in body
    assert (
        '<meta name="description" content="Generate print-ready event name tags from an Excel workbook, preview the first page in your browser, and export a PDF sized for real badge inserts." />'
        in body
    )
    assert '<link rel="canonical" href="http://testserver/en"' in body
    assert 'type="application/ld+json"' in body
    assert "FAQPage" in body
    assert "SoftwareApplication" in body
    assert "Need to know" in body
    assert "Production workflow" in body
    assert "Sample workbook columns" in body
    assert "Role examples" in body
    assert "Set to 93 × 122 mm by default, and easy to adjust. Print at 100% for a true-to-size fit." in body
    assert "/sample-workbook" in body
    assert "Role style settings" in body
    assert 'name="role_key"' in body
    assert 'value="SPEAKER"' in body
    assert 'value="STAFF"' in body
    assert 'name="role_color"' in body
    assert "Preview in browser" in body
    assert "fetch('/preview'" in body
    assert 'href="/ko"' in body
    assert "Add role" in body
    assert 'href="/favicon.ico"' in body


def test_korean_language_toggle_renders_full_page_copy() -> None:
    client = TestClient(create_app())
    response = client.get("/?lang=ko")
    assert response.status_code == 200
    body = response.text
    assert "<title>Nametag Generator | 엑셀로 출력용 행사 네임태그 PDF 만들기</title>" in body
    assert '<link rel="canonical" href="http://testserver/ko"' in body
    assert "빠른 안내" in body
    assert "작업 흐름" in body
    assert "행사 네임태그를 깔끔하게 바로 만드세요." in body
    assert "기본 규격은 93 × 122 mm입니다. 필요하면 수정하고, 출력할 때는 100% 실제 크기로 맞춰 주세요." in body
    assert "역할 바 설정" in body
    assert "브라우저에서 미리보기" in body
    assert 'href="/en"' in body


def test_language_shortcuts_render_without_404() -> None:
    client = TestClient(create_app())
    ko_response = client.get("/ko")
    en_response = client.get("/en")
    assert ko_response.status_code == 200
    assert en_response.status_code == 200
    assert "역할 추가" in ko_response.text


def test_sample_assets_are_downloadable() -> None:
    client = TestClient(create_app())
    workbook_response = client.get("/sample-workbook")
    assert workbook_response.status_code == 200
    assert (
        workbook_response.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def test_favicon_is_served() -> None:
    client = TestClient(create_app())
    response = client.get("/favicon.ico")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/x-icon"
    assert len(response.content) > 0


def test_robots_txt_and_sitemap_are_served() -> None:
    client = TestClient(create_app())

    robots_response = client.get("/robots.txt")
    assert robots_response.status_code == 200
    assert robots_response.text == "User-agent: *\nAllow: /\nSitemap: http://testserver/sitemap.xml\n"

    sitemap_response = client.get("/sitemap.xml")
    assert sitemap_response.status_code == 200
    assert sitemap_response.headers["content-type"].startswith("application/xml")
    assert "<loc>http://testserver/en</loc>" in sitemap_response.text
    assert "<loc>http://testserver/ko</loc>" in sitemap_response.text
    assert 'hreflang="x-default"' in sitemap_response.text


def test_preview_endpoint_returns_preview_data_url() -> None:
    client = TestClient(create_app())
    workbook = Path("sample/attendees.sample.xlsx")
    with workbook.open("rb") as handle:
        response = client.post(
            "/preview",
            files={
                "workbook": (
                    workbook.name,
                    handle,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
            data={
                "card_width_mm": "93",
                "card_height_mm": "122",
                "lang": "ko",
                "role_key": ["SPEAKER", "STAFF"],
                "role_label": ["SPEAKER", "STAFF"],
                "role_color": ["#4677D8", "#000000"],
            },
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["preview_data_url"].startswith("data:image/png;base64,")
    assert payload["attendee_count"] == 6


def test_upload_applies_role_style_overrides(monkeypatch: Any) -> None:
    captured: dict[str, Any] = {}

    def fake_generate_pdf(attendees: Any, config: Any, output_path: Any = None) -> Any:
        captured["attendees"] = attendees
        captured["config"] = config

        class Result:
            pdf_bytes = b"%PDF-1.4 sample"

        return Result()

    monkeypatch.setattr("nametag_generator.web.generate_pdf", fake_generate_pdf)
    client = TestClient(create_app())
    workbook = Path("sample/attendees.sample.xlsx")
    with workbook.open("rb") as handle:
        response = client.post(
            "/generate",
            files={
                "workbook": (
                    workbook.name,
                    handle,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
            data={
                "card_width_mm": "93",
                "card_height_mm": "122",
                "lang": "en",
                "role_key": ["SPEAKER", "STAFF", "HOST"],
                "role_label": ["TALK", "CREW", "ORGANIZER"],
                "role_color": ["#445566", "#778899", "#112233"],
            },
        )
    assert response.status_code == 200
    theme = captured["config"].theme.role_styles
    assert theme["HOST"].label == "ORGANIZER"
    assert theme["HOST"].background_color == "#112233"
    assert theme["SPEAKER"].label == "TALK"
    assert theme["STAFF"].label == "CREW"


def test_upload_generates_pdf() -> None:
    client = TestClient(create_app())
    workbook = Path("sample/attendees.sample.xlsx")
    with workbook.open("rb") as handle:
        response = client.post(
            "/generate",
            files={
                "workbook": (
                    workbook.name,
                    handle,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
            data={
                "card_width_mm": "93",
                "card_height_mm": "122",
                "lang": "en",
                "role_key": ["SPEAKER", "STAFF"],
                "role_label": ["SPEAKER", "STAFF"],
                "role_color": ["#4677D8", "#000000"],
            },
        )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


def test_default_role_rows_are_speaker_and_staff_only() -> None:
    client = TestClient(create_app())
    response = client.get("/")
    assert response.status_code == 200
    body = response.text
    assert 'value="SPEAKER"' in body
    assert 'value="STAFF"' in body
    assert 'value="HOST"' not in body
