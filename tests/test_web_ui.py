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
    assert "Sample workbook columns" in body
    assert "Role examples" in body
    assert "Built for this insert size. Print at 100% and you are ready to go." in body
    assert "/sample-workbook" in body
    assert "Role style settings" in body
    assert 'name="role_key"' in body
    assert 'value="SPEAKER"' in body
    assert 'value="STAFF"' in body
    assert 'name="role_color"' in body
    assert "Preview in browser" in body
    assert "fetch('/preview'" in body
    assert 'href="/?lang=ko"' in body
    assert "Add role" in body


def test_korean_language_toggle_renders_full_page_copy() -> None:
    client = TestClient(create_app())
    response = client.get("/?lang=ko")
    assert response.status_code == 200
    body = response.text
    assert "한 번에 맞는 네임태그를 바로 만드세요." in body
    assert "이 규격에 맞춰 만들었습니다. 100% 실제 사이즈로 출력하면 바로 사용할 수 있습니다." in body
    assert "역할 바 설정" in body
    assert "브라우저에서 미리보기" in body
    assert 'href="/?lang=en"' in body


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
