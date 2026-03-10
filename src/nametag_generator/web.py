from __future__ import annotations

import base64
import html
import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response

from nametag_generator.config import GeneratorConfig, LayoutConfig, ThemeConfig
from nametag_generator.errors import FontResolutionError, WorkbookValidationError
from nametag_generator.loaders.xlsx import load_attendees_from_xlsx
from nametag_generator.models import RoleStyle
from nametag_generator.service import generate_pdf, generate_preview_png
from nametag_generator.themes.default import DEFAULT_ROLE_STYLES
from nametag_generator.web_content import SAMPLE_ROWS, UI_COPY, resolve_language


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_WORKBOOK = PROJECT_ROOT / "sample/attendees.sample.xlsx"
SAMPLE_PDF = PROJECT_ROOT / "sample/badges.sample.pdf"
FAVICON_ICO = PROJECT_ROOT / "ui/favicon.ico"
FALLBACK_FAVICON_ICO = base64.b64decode(
    "AAABAAEAEBAAAAAAIABdAAAAFgAAAIlQTkcNChoKAAAADUlIRFIAAAAQAAAAEAgGAAAAH/P/YQAAACRJREFUeJxjFIm8+Z+BAsBEieZRA0YNgAGWrUIBA+uCUQMYGAAhBQN+o9XGkAAAAABJRU5ErkJggg=="
)
MAX_ROLE_ROWS = 6
MIN_ROLE_ROWS = 2


def _escape(value: str) -> str:
    return html.escape(value, quote=True)


def _default_role_rows() -> list[dict[str, str]]:
    return [
        {
            "key": "SPEAKER",
            "label": DEFAULT_ROLE_STYLES["SPEAKER"].label,
            "color": DEFAULT_ROLE_STYLES["SPEAKER"].background_color,
        },
        {
            "key": "STAFF",
            "label": DEFAULT_ROLE_STYLES["STAFF"].label,
            "color": DEFAULT_ROLE_STYLES["STAFF"].background_color,
        },
    ]


def _normalize_role_rows(role_rows: list[dict[str, str]] | None = None) -> list[dict[str, str]]:
    rows = role_rows or _default_role_rows()
    normalized: list[dict[str, str]] = []
    for row in rows[:MAX_ROLE_ROWS]:
        role_key = row.get("key", "").strip().upper()
        if not role_key:
            continue
        fallback = DEFAULT_ROLE_STYLES.get(role_key)
        normalized.append(
            {
                "key": role_key,
                "label": row.get("label", "").strip()
                or (fallback.label if fallback else role_key),
                "color": row.get("color", "").strip()
                or (fallback.background_color if fallback else "#2F2F2F"),
            }
        )
    if len(normalized) < MIN_ROLE_ROWS:
        defaults = _default_role_rows()
        for row in defaults:
            if len(normalized) >= MIN_ROLE_ROWS:
                break
            if not any(existing["key"] == row["key"] for existing in normalized):
                normalized.append(row)
    return normalized[:MAX_ROLE_ROWS]


def _build_theme_config(role_rows: list[dict[str, str]] | None = None) -> ThemeConfig:
    return ThemeConfig(
        role_styles={
            row["key"]: RoleStyle(label=row["label"], background_color=row["color"])
            for row in _normalize_role_rows(role_rows)
        }
    )


def _build_generator_config(
    card_width_mm: float,
    card_height_mm: float,
    role_rows: list[dict[str, str]] | None = None,
) -> GeneratorConfig:
    return GeneratorConfig(
        layout=LayoutConfig(
            card_width_mm=card_width_mm,
            card_height_mm=card_height_mm,
        ),
        theme=_build_theme_config(role_rows),
    )


def _table_rows_html(copy: dict[str, Any]) -> str:
    rows: list[str] = []
    for column, required, example, description in copy["sample_table_rows"]:
        rows.append(
            f"""
            <tr>
              <td><code>{_escape(column)}</code></td>
              <td>{_escape(required)}</td>
              <td>{_escape(example)}</td>
              <td>{_escape(description)}</td>
            </tr>
            """
        )
    return "".join(rows)


def _workflow_hints_html(copy: dict[str, Any]) -> str:
    return "".join(
        f"""
        <div class="hint">
          <strong>{_escape(label)}</strong>
          <span><code>{_escape(value)}</code></span>
        </div>
        """
        for label, value in copy["workflow_hints"]
    )


def _guide_items_html(copy: dict[str, Any]) -> str:
    return "".join(f"<li>{_escape(item)}</li>" for item in copy["guide_items"])


def _howto_steps_html(copy: dict[str, Any]) -> str:
    return "".join(
        f"""
        <li class="step-item">
          <strong>{_escape(title)}</strong>
          <p>{_escape(body)}</p>
        </li>
        """
        for title, body in copy["howto_steps"]
    )


def _faq_items_html(copy: dict[str, Any]) -> str:
    return "".join(
        f"""
        <article class="faq-item">
          <h3>{_escape(question)}</h3>
          <p>{_escape(answer)}</p>
        </article>
        """
        for question, answer in copy["faq_items"]
    )


def _quick_notes_html(copy: dict[str, Any]) -> str:
    return "".join(
        f"""
        <article class="note-card">
          <strong>{_escape(title)}</strong>
          <p>{_escape(body)}</p>
        </article>
        """
        for title, body in copy["quick_notes"]
    )


def _role_settings_html(copy: dict[str, Any], role_rows: list[dict[str, str]]) -> str:
    blocks: list[str] = []
    for index, row in enumerate(role_rows):
        remove_disabled = "disabled" if index < MIN_ROLE_ROWS else ""
        blocks.append(
            f"""
            <div class="role-row" data-role-row>
              <strong class="role-row-title">{_escape(copy["role_key_field"])} {index + 1}</strong>
              <div class="role-fields">
                <label class="role-field role-field-key">
                  {_escape(copy["role_key_field"])}
                  <input type="text" name="role_key" value="{_escape(row["key"])}" />
                </label>
                <label class="role-field">
                  {_escape(copy["label_field"])}
                  <input type="text" name="role_label" value="{_escape(row["label"])}" />
                </label>
                <label class="role-field role-field-color">
                  {_escape(copy["color_field"])}
                  <input type="color" name="role_color" value="{_escape(row["color"])}" />
                </label>
                <button type="button" class="button-secondary role-remove" data-role-remove {remove_disabled}>
                  {_escape(copy["remove_role_button"])}
                </button>
              </div>
              <small class="role-help">{_escape(copy["role_key_help"])}</small>
            </div>
            """
        )
    return "".join(blocks)


def _sample_cards_html(copy: dict[str, Any], role_rows: list[dict[str, str]]) -> str:
    sample_people = list(SAMPLE_ROWS)
    while len(sample_people) < len(role_rows):
        sample_people.extend(SAMPLE_ROWS)

    cards: list[str] = []
    for role_row, sample in zip(role_rows, sample_people, strict=False):
        name, organization, _, title = sample
        cards.append(
            f"""
            <article class="sample-card">
              <span class="sample-label">{_escape(role_row["key"])}</span>
              <strong class="name">{_escape(name)}</strong>
              <div class="meta">
                <div>{_escape(title or "")}</div>
                <div>@{_escape(organization)}</div>
              </div>
              <div class="bar" style="background:{_escape(role_row["color"])};">{_escape(role_row["label"])}</div>
            </article>
            """
        )

    plain_name, plain_org, _, plain_title = SAMPLE_ROWS[1]
    cards.append(
        f"""
        <article class="sample-card no-role">
          <span class="sample-label">{_escape(copy["sample_card_labels"]["plain"])}</span>
          <strong class="name">{_escape(plain_name)}</strong>
          <div class="meta">
            <div>{_escape(plain_title or "")}</div>
            <div>@{_escape(plain_org)}</div>
          </div>
        </article>
        """
    )
    return "".join(cards)


def _language_toggle_html(language: str) -> str:
    return "".join(
        f'<a class="{"lang-link active" if code == language else "lang-link"}" href="/{code}">{_escape(UI_COPY[language]["language_toggle"][code])}</a>'
        for code in ("en", "ko")
    )


def _absolute_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def _structured_data_json(
    *,
    copy: dict[str, Any],
    language: str,
    canonical_url: str,
) -> str:
    data = [
        {
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": copy["site_name"],
            "applicationCategory": "BusinessApplication",
            "operatingSystem": "Web",
            "url": canonical_url,
            "inLanguage": language,
            "description": copy["meta_description"],
            "featureList": list(copy["feature_list"]),
        },
        {
            "@context": "https://schema.org",
            "@type": "HowTo",
            "name": copy["howto_title"],
            "description": copy["howto_intro"],
            "inLanguage": language,
            "step": [
                {
                    "@type": "HowToStep",
                    "name": title,
                    "text": body,
                }
                for title, body in copy["howto_steps"]
            ],
        },
        {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "inLanguage": language,
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": question,
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": answer,
                    },
                }
                for question, answer in copy["faq_items"]
            ],
        },
    ]
    return json.dumps(data, ensure_ascii=False)


def _sitemap_xml(base_url: str) -> str:
    english_url = _absolute_url(base_url, "/en")
    korean_url = _absolute_url(base_url, "/ko")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">
  <url>
    <loc>{_escape(english_url)}</loc>
    <xhtml:link rel="alternate" hreflang="en" href="{_escape(english_url)}" />
    <xhtml:link rel="alternate" hreflang="ko" href="{_escape(korean_url)}" />
    <xhtml:link rel="alternate" hreflang="x-default" href="{_escape(english_url)}" />
  </url>
  <url>
    <loc>{_escape(korean_url)}</loc>
    <xhtml:link rel="alternate" hreflang="en" href="{_escape(english_url)}" />
    <xhtml:link rel="alternate" hreflang="ko" href="{_escape(korean_url)}" />
    <xhtml:link rel="alternate" hreflang="x-default" href="{_escape(english_url)}" />
  </url>
</urlset>
"""


def _parse_role_rows_from_form(form: Any) -> list[dict[str, str]]:
    return _normalize_role_rows(
        [
            {"key": key, "label": label, "color": color}
            for key, label, color in zip(
                form.getlist("role_key"),
                form.getlist("role_label"),
                form.getlist("role_color"),
                strict=False,
            )
        ]
    )


def _render_page(
    *,
    language: str,
    base_url: str,
    canonical_path: str,
    error: str | None = None,
    role_rows: list[dict[str, str]] | None = None,
) -> str:
    resolved_language = resolve_language(language)
    copy = UI_COPY[resolved_language]
    normalized_role_rows = _normalize_role_rows(role_rows)
    preview_messages = json.dumps(copy["preview_messages"], ensure_ascii=False)
    initial_role_rows = json.dumps(normalized_role_rows, ensure_ascii=False)
    sample_people = json.dumps(SAMPLE_ROWS, ensure_ascii=False)
    canonical_url = _absolute_url(base_url, canonical_path)
    english_url = _absolute_url(base_url, "/en")
    korean_url = _absolute_url(base_url, "/ko")
    structured_data = _structured_data_json(
        copy=copy,
        language=resolved_language,
        canonical_url=canonical_url,
    )
    message_html = (
        f"<div class='flash flash-error'>{_escape(error)}</div>" if error else ""
    )
    return f"""<!doctype html>
<html lang="{_escape(resolved_language)}">
  <head>
    <meta charset="utf-8" />
    <title>{_escape(copy["meta_title"])}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="description" content="{_escape(copy["meta_description"])}" />
    <meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large,max-video-preview:-1" />
    <link rel="canonical" href="{_escape(canonical_url)}" />
    <link rel="alternate" hreflang="en" href="{_escape(english_url)}" />
    <link rel="alternate" hreflang="ko" href="{_escape(korean_url)}" />
    <link rel="alternate" hreflang="x-default" href="{_escape(english_url)}" />
    <meta property="og:type" content="website" />
    <meta property="og:site_name" content="{_escape(copy["site_name"])}" />
    <meta property="og:title" content="{_escape(copy["meta_title"])}" />
    <meta property="og:description" content="{_escape(copy["meta_description"])}" />
    <meta property="og:url" content="{_escape(canonical_url)}" />
    <meta property="og:locale" content="{_escape(copy["meta_locale"])}" />
    <meta name="twitter:card" content="summary" />
    <meta name="twitter:title" content="{_escape(copy["meta_title"])}" />
    <meta name="twitter:description" content="{_escape(copy["meta_description"])}" />
    <link rel="icon" href="/favicon.ico" sizes="any" />
    <script type="application/ld+json">{structured_data}</script>
    <style>
      :root {{
        --bg: #eef1f5;
        --bg-accent: #f7f2e9;
        --panel: rgba(252, 248, 241, 0.92);
        --panel-strong: #ffffff;
        --panel-muted: #f4ede2;
        --ink: #1a1d25;
        --muted: #5d6573;
        --line: rgba(26, 29, 37, 0.12);
        --accent: #2057d6;
        --accent-strong: #13307f;
        --accent-soft: rgba(32, 87, 214, 0.12);
        --accent-grid: rgba(32, 87, 214, 0.08);
        --warm: #a85c31;
        --shadow: 0 30px 80px rgba(25, 32, 54, 0.12);
        --radius-xl: 30px;
        --radius-lg: 22px;
        --radius-md: 18px;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        font-family: "Avenir Next", "SUIT", "Pretendard", "Helvetica Neue", sans-serif;
        background:
          radial-gradient(circle at top left, rgba(32, 87, 214, 0.12), transparent 26%),
          radial-gradient(circle at top right, rgba(168, 92, 49, 0.10), transparent 22%),
          linear-gradient(180deg, var(--bg), var(--bg-accent));
        color: var(--ink);
      }}
      main {{
        max-width: 1300px;
        margin: 0 auto;
        padding: 26px 20px 48px;
      }}
      .masthead {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 18px;
        margin-bottom: 20px;
      }}
      .brand-lockup {{
        display: inline-flex;
        align-items: center;
        gap: 14px;
      }}
      .brand-mark {{
        display: grid;
        place-items: center;
        width: 48px;
        height: 48px;
        border-radius: 16px;
        background: linear-gradient(135deg, var(--accent), var(--accent-strong));
        color: white;
        font-size: 15px;
        font-weight: 800;
        letter-spacing: 0.08em;
        box-shadow: 0 18px 30px rgba(32, 87, 214, 0.22);
      }}
      .brand-copy {{
        display: grid;
        gap: 2px;
      }}
      .brand-copy strong {{
        font-size: 15px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }}
      .brand-copy span {{
        color: var(--muted);
        font-size: 13px;
      }}
      .lang-switch {{
        display: inline-flex;
        gap: 6px;
        padding: 6px;
        border-radius: 999px;
        border: 1px solid var(--line);
        background: rgba(255, 255, 255, 0.82);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
      }}
      .lang-link {{
        padding: 9px 14px;
        border-radius: 999px;
        color: var(--muted);
        text-decoration: none;
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
      }}
      .lang-link.active {{
        background: var(--ink);
        color: white;
      }}
      .hero-shell {{
        display: grid;
        grid-template-columns: minmax(0, 1.08fr) minmax(320px, 0.92fr);
        gap: 24px;
        margin-bottom: 24px;
      }}
      .shell {{
        display: grid;
        grid-template-columns: minmax(0, 1.04fr) minmax(300px, 0.96fr);
        gap: 24px;
        align-items: start;
      }}
      .panel {{
        border-radius: var(--radius-xl);
        border: 1px solid var(--line);
        background: linear-gradient(180deg, var(--panel), rgba(255, 255, 255, 0.98));
        backdrop-filter: blur(10px);
        overflow: hidden;
        border: 1px solid var(--line);
        box-shadow: var(--shadow);
      }}
      .hero-copy {{
        position: relative;
        min-height: 100%;
      }}
      .hero-copy::before,
      .hero-rail::before {{
        content: "";
        position: absolute;
        inset: 0;
        background:
          linear-gradient(90deg, transparent 0, transparent calc(100% - 1px), var(--accent-grid) calc(100% - 1px)),
          linear-gradient(180deg, transparent 0, transparent calc(100% - 1px), var(--accent-grid) calc(100% - 1px));
        background-size: 28px 28px;
        mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.28), transparent 78%);
        pointer-events: none;
      }}
      .hero-copy-inner,
      .hero-rail,
      .workspace,
      .sidebar,
      .knowledge-panel {{
        position: relative;
        z-index: 1;
      }}
      .hero-copy-inner {{
        padding: 34px;
      }}
      .workspace {{
        padding: 30px;
      }}
      .sidebar {{
        position: sticky;
        top: 20px;
        padding: 22px;
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.97), rgba(244, 237, 226, 0.95));
      }}
      .eyebrow {{
        display: inline-flex;
        padding: 7px 12px;
        border-radius: 999px;
        background: var(--accent-soft);
        color: var(--accent);
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }}
      h1 {{
        margin: 18px 0 10px;
        font-family: "Iowan Old Style", "Palatino Linotype", "Noto Serif KR", serif;
        font-size: clamp(42px, 7vw, 68px);
        line-height: 0.98;
        letter-spacing: -0.05em;
        max-width: 11ch;
      }}
      .lead {{
        margin: 0;
        max-width: 60ch;
        color: var(--muted);
        font-size: 18px;
        line-height: 1.6;
      }}
      .hero-note-grid {{
        display: grid;
        grid-template-columns: minmax(0, 1.1fr) minmax(260px, 0.9fr);
        gap: 18px;
        margin-top: 26px;
      }}
      .stat-card {{
        min-height: 178px;
        padding: 24px;
        border-radius: var(--radius-lg);
        border: 1px solid var(--line);
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.94), var(--panel-muted));
        transition: transform 180ms ease, box-shadow 180ms ease;
      }}
      .stat-card:hover,
      .panel-block:hover,
      .sample-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 16px 40px rgba(26, 29, 37, 0.10);
      }}
      .stat-card-primary {{
        background:
          radial-gradient(circle at top right, rgba(32, 87, 214, 0.16), transparent 28%),
          linear-gradient(180deg, rgba(255, 255, 255, 0.97), rgba(235, 241, 255, 0.92));
      }}
      .stat-card strong {{
        display: block;
        margin-bottom: 8px;
        font-size: clamp(28px, 5vw, 36px);
        line-height: 1;
      }}
      .stat-card p {{
        margin: 0;
        color: var(--muted);
        line-height: 1.55;
      }}
      .flash {{
        margin-top: 18px;
        padding: 14px 16px;
        border-radius: var(--radius-md);
        border: 1px solid #e5b5a7;
        background: #fff0ea;
        font-weight: 600;
      }}
      .hero-rail {{
        position: relative;
        padding: 28px;
        background:
          radial-gradient(circle at top right, rgba(32, 87, 214, 0.18), transparent 24%),
          linear-gradient(180deg, rgba(247, 250, 255, 0.98), rgba(240, 233, 223, 0.98));
      }}
      .rail-top,
      .section-header,
      .block-head,
      .role-toolbar {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 16px;
      }}
      .section-tag,
      .block-eyebrow {{
        margin: 0 0 8px;
        color: var(--accent);
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }}
      h2,
      h3 {{
        font-family: "Iowan Old Style", "Palatino Linotype", "Noto Serif KR", serif;
      }}
      html[lang="ko"] h1,
      html[lang="ko"] h2,
      html[lang="ko"] h3 {{
        font-family: "SUIT", "Pretendard", "Apple SD Gothic Neo", sans-serif;
        letter-spacing: -0.04em;
        word-break: keep-all;
      }}
      html[lang="ko"] h1 {{
        font-size: clamp(38px, 6.4vw, 60px);
        line-height: 1.12;
        max-width: 8.5ch;
      }}
      html[lang="ko"] .lead,
      html[lang="ko"] .rail-body,
      html[lang="ko"] .section-body,
      html[lang="ko"] .block-body,
      html[lang="ko"] .note-card p {{
        word-break: keep-all;
      }}
      .hero-rail h2,
      .section-header h2 {{
        margin: 0;
        font-size: clamp(28px, 4vw, 36px);
        line-height: 1.08;
      }}
      .section-body,
      .rail-body,
      .block-body {{
        margin: 0;
        color: var(--muted);
        line-height: 1.6;
      }}
      .metric-pill {{
        display: grid;
        min-width: 92px;
        padding: 12px 14px;
        border-radius: 18px;
        border: 1px solid rgba(32, 87, 214, 0.18);
        background: rgba(255, 255, 255, 0.78);
        text-align: right;
      }}
      .metric-pill strong {{
        font-size: 28px;
        line-height: 1;
      }}
      .metric-pill span {{
        color: var(--muted);
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
      }}
      .hero-actions {{
        margin-top: 20px;
      }}
      form {{
        display: grid;
        gap: 16px;
        margin-top: 24px;
      }}
      .panel-block {{
        padding: 22px;
        border-radius: var(--radius-lg);
        border: 1px solid var(--line);
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(244, 237, 226, 0.92));
        transition: transform 180ms ease, box-shadow 180ms ease;
      }}
      .block-title {{
        margin: 0;
        font-size: 24px;
        line-height: 1.15;
      }}
      .block-head {{
        margin-bottom: 16px;
      }}
      label {{
        display: grid;
        gap: 8px;
        font-weight: 600;
      }}
      input[type=file], input[type=number], input[type=text], input[type=color] {{
        width: 100%;
        padding: 13px 14px;
        border-radius: 16px;
        border: 1px solid var(--line);
        background: rgba(255, 255, 255, 0.96);
        font: inherit;
      }}
      input[type=file]:focus,
      input[type=number]:focus,
      input[type=text]:focus,
      input[type=color]:focus {{
        outline: 2px solid rgba(32, 87, 214, 0.14);
        border-color: rgba(32, 87, 214, 0.32);
      }}
      input[type=color] {{
        min-height: 52px;
        padding: 8px;
      }}
      .split {{
        display: grid;
        grid-template-columns: minmax(0, 1fr) 240px;
        gap: 16px;
      }}
      .grid {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 16px;
      }}
      .hint-grid {{
        display: grid;
        gap: 10px;
      }}
      .hint {{
        padding: 14px 16px;
        border-radius: 16px;
        border: 1px solid var(--line);
        background: rgba(255, 255, 255, 0.82);
      }}
      .hint strong {{
        display: block;
        margin-bottom: 4px;
        font-size: 13px;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        color: var(--warm);
      }}
      .button-row {{
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
      }}
      button {{
        padding: 14px 20px;
        border-radius: 16px;
        border: 0;
        background: linear-gradient(135deg, var(--accent), var(--accent-strong));
        color: white;
        font-weight: 700;
        cursor: pointer;
        transition: transform 140ms ease, box-shadow 140ms ease, filter 140ms ease;
      }}
      .button-secondary {{
        background: rgba(255, 255, 255, 0.95);
        color: var(--ink);
        border: 1px solid var(--line);
      }}
      button:hover {{
        transform: translateY(-2px);
        filter: saturate(1.06);
        box-shadow: 0 14px 28px rgba(20, 89, 217, 0.24);
      }}
      .button-secondary:hover {{
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.06);
      }}
      .role-note {{
        color: var(--muted);
        font-size: 13px;
      }}
      .role-settings {{
        display: grid;
        gap: 12px;
      }}
      .role-row {{
        display: grid;
        gap: 10px;
        padding: 16px;
        border-radius: 18px;
        border: 1px solid var(--line);
        background: rgba(255, 255, 255, 0.76);
      }}
      .role-row-title {{
        display: block;
        font-size: 13px;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: var(--muted);
      }}
      .role-fields {{
        display: grid;
        grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr) 120px auto;
        gap: 12px;
        align-items: end;
      }}
      .role-field {{
        display: grid;
        gap: 8px;
      }}
      .role-field-color input {{
        padding: 8px;
      }}
      .role-help {{
        display: block;
        color: var(--muted);
        font-size: 12px;
      }}
      .role-remove[disabled] {{
        visibility: hidden;
        pointer-events: none;
      }}
      .help {{
        padding: 18px;
        border-radius: var(--radius-lg);
        border: 1px solid var(--line);
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(244, 237, 226, 0.92));
      }}
      .help + .help {{
        margin-top: 16px;
      }}
      .help h2 {{
        margin: 0 0 10px;
        font-size: 22px;
        line-height: 1.18;
      }}
      .help p {{
        margin: 0 0 10px;
        color: var(--muted);
        line-height: 1.6;
      }}
      .help ul {{
        margin: 0;
        padding-left: 20px;
      }}
      .help li + li {{ margin-top: 6px; }}
      .help code {{
        background: rgba(0, 0, 0, 0.05);
        padding: 1px 4px;
      }}
      .actions {{
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-top: 12px;
      }}
      .action-link {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 11px 16px;
        border-radius: 14px;
        border: 1px solid var(--line);
        background: rgba(255, 255, 255, 0.92);
        color: var(--ink);
        text-decoration: none;
        font-weight: 700;
        transition: transform 140ms ease, box-shadow 140ms ease;
      }}
      .action-link:hover {{
        transform: translateY(-2px);
        box-shadow: 0 10px 18px rgba(26, 29, 37, 0.08);
      }}
      .table-shell {{
        overflow-x: auto;
      }}
      .schema-table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
        font-size: 14px;
      }}
      .schema-table th,
      .schema-table td {{
        text-align: left;
        padding: 10px 12px;
        border-top: 1px solid var(--line);
        vertical-align: top;
      }}
      .schema-table th {{
        font-size: 12px;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: var(--muted);
      }}
      .examples {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 16px;
        margin-top: 14px;
        justify-items: center;
      }}
      .hero-examples {{
        margin-top: 18px;
      }}
      .sample-card {{
        position: relative;
        width: min(100%, 220px);
        aspect-ratio: 93 / 122;
        min-height: unset;
        padding: 18px 16px 16px;
        border-radius: 26px;
        border: 1px solid rgba(26, 29, 37, 0.14);
        background: linear-gradient(180deg, #fffefb, #f6f1e8);
        overflow: hidden;
        box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.54);
        transition: transform 180ms ease, box-shadow 180ms ease;
      }}
      .sample-card::before {{
        content: "";
        position: absolute;
        inset: 10px;
        border-radius: 18px;
        border: 1px solid rgba(26, 29, 37, 0.08);
        pointer-events: none;
      }}
      .sample-card.no-role {{
        aspect-ratio: 93 / 122;
      }}
      .sample-card .name {{
        display: block;
        margin-top: 18px;
        font-size: clamp(24px, 2.4vw, 28px);
        font-weight: 700;
        text-align: center;
        letter-spacing: -0.03em;
        position: relative;
        z-index: 1;
      }}
      .sample-card .meta {{
        margin-top: 14px;
        text-align: center;
        line-height: 1.25;
        font-size: 13px;
        position: relative;
        z-index: 1;
      }}
      .sample-card .bar {{
        position: absolute;
        left: 0;
        right: 0;
        bottom: 0;
        padding: 12px 8px;
        text-align: center;
        color: white;
        font-size: 16px;
        font-weight: 800;
        letter-spacing: 0.04em;
      }}
      .sample-label {{
        display: inline-block;
        padding: 4px 8px;
        border-radius: 999px;
        background: rgba(20, 89, 217, 0.08);
        color: var(--accent);
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        position: relative;
        z-index: 1;
      }}
      p {{ line-height: 1.5; }}
      .note-strip {{
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 16px;
        margin-top: 24px;
      }}
      .note-card {{
        padding: 18px 20px;
        border-radius: var(--radius-lg);
        border: 1px solid var(--line);
        background: rgba(255, 255, 255, 0.76);
        box-shadow: 0 12px 28px rgba(26, 29, 37, 0.06);
      }}
      .note-card strong {{
        display: block;
        margin-bottom: 8px;
        font-size: 13px;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--accent);
      }}
      .note-card p {{
        margin: 0;
        color: var(--muted);
      }}
      @keyframes rise-in {{
        from {{
          opacity: 0;
          transform: translateY(12px);
        }}
        to {{
          opacity: 1;
          transform: translateY(0);
        }}
      }}
      .hero-copy,
      .hero-rail,
      .workspace,
      .sidebar,
      .note-strip {{
        animation: rise-in 420ms ease both;
      }}
      .hero-rail {{
        animation-delay: 80ms;
      }}
      .sidebar {{
        animation-delay: 120ms;
      }}
      .note-strip {{
        animation-delay: 160ms;
      }}
      @media (max-width: 1100px) {{
        .hero-shell,
        .shell {{
          grid-template-columns: 1fr;
        }}
        .sidebar {{ position: static; }}
      }}
      @media (max-width: 900px) {{
        .hero-note-grid,
        .split {{
          grid-template-columns: 1fr;
        }}
      }}
      @media (max-width: 860px) {{
        .role-fields {{
          grid-template-columns: 1fr;
        }}
      }}
      @media (max-width: 760px) {{
        main {{ padding: 16px; }}
        .hero-copy-inner,
        .workspace,
        .sidebar,
        .hero-rail,
        .note-card {{
          padding: 20px;
        }}
        .grid,
        .examples {{
          grid-template-columns: 1fr;
        }}
        .note-strip {{
          grid-template-columns: 1fr;
        }}
        .masthead,
        .section-header,
        .block-head,
        .rail-top,
        .role-toolbar {{
          flex-direction: column;
        }}
        .metric-pill {{
          text-align: left;
        }}
      }}
    </style>
  </head>
  <body>
    <main>
      <header class="masthead">
        <div class="brand-lockup">
          <span class="brand-mark">NG</span>
          <div class="brand-copy">
            <strong>{_escape(copy["site_name"])}</strong>
            <span>{_escape(copy["eyebrow"])}</span>
          </div>
        </div>
        <div class="lang-switch" aria-label="{_escape(copy["language_label"])}">
          {_language_toggle_html(language)}
        </div>
      </header>
      <section class="hero-shell">
        <section class="panel hero-copy">
          <div class="hero-copy-inner">
            <span class="eyebrow">{_escape(copy["eyebrow"])}</span>
            <h1>{_escape(copy["hero_title"])}</h1>
            <p class="lead">{_escape(copy["lead"])}</p>
            <div class="hero-note-grid">
              <article class="stat-card stat-card-primary">
                <strong>{_escape(copy["stats"][0]["title"])}</strong>
                <p>{_escape(copy["stats"][0]["body"])}</p>
              </article>
              <article class="stat-card">
                <strong>{_escape(copy["stats"][1]["title"])}</strong>
                <p>{_escape(copy["stats"][1]["body"])}</p>
                <div class="hint-grid" style="margin-top:16px;">
                  {_workflow_hints_html(copy)}
                </div>
              </article>
            </div>
            {message_html}
          </div>
        </section>
        <aside class="panel hero-rail">
          <div class="rail-top">
            <div>
              <p class="section-tag">{_escape(copy["rail_title"])}</p>
              <h2>{_escape(copy["preview_section_title"])}</h2>
            </div>
            <div class="metric-pill">
              <strong data-role-count aria-live="polite">{len(normalized_role_rows)}</strong>
              <span>{_escape(copy["role_settings_title"])}</span>
            </div>
          </div>
          <p class="rail-body">{_escape(copy["rail_body"])}</p>
          <div class="examples hero-examples">{_sample_cards_html(copy, normalized_role_rows)}</div>
          <div class="actions hero-actions">
            <a class="action-link" href="/sample-workbook">{_escape(copy["download_workbook"])}</a>
            <a class="action-link" href="/sample-pdf">{_escape(copy["download_pdf"])}</a>
          </div>
        </aside>
      </section>
      <div class="shell">
        <section class="panel workspace">
          <div class="section-header">
            <div>
              <p class="section-tag">{_escape(copy["workflow_title"])}</p>
              <h2>{_escape(copy["generate_button"])}</h2>
            </div>
            <p class="section-body">{_escape(copy["workflow_body"])}</p>
          </div>
          <form action="/generate" method="post" enctype="multipart/form-data">
            <input type="hidden" name="lang" value="{_escape(language)}" />
            <section class="panel-block">
              <div class="block-head">
                <div>
                  <p class="block-eyebrow">{_escape(copy["upload_section_title"])}</p>
                  <h3 class="block-title">{_escape(copy["workbook_label"])}</h3>
                </div>
                <p class="block-body">{_escape(copy["upload_section_body"])}</p>
              </div>
              <div class="split">
                <label>
                  {_escape(copy["workbook_label"])}
                  <input type="file" name="workbook" accept=".xlsx" required />
                </label>
                <div class="hint-grid">
                  {_workflow_hints_html(copy)}
                </div>
              </div>
            </section>
            <section class="panel-block">
              <div class="block-head">
                <div>
                  <p class="block-eyebrow">{_escape(copy["size_section_title"])}</p>
                  <h3 class="block-title">{_escape(copy["stats"][0]["title"])}</h3>
                </div>
                <p class="block-body">{_escape(copy["size_section_body"])}</p>
              </div>
              <div class="grid">
                <label>
                  {_escape(copy["card_width_label"])}
                  <input type="number" step="0.1" name="card_width_mm" value="93" required />
                </label>
                <label>
                  {_escape(copy["card_height_label"])}
                  <input type="number" step="0.1" name="card_height_mm" value="122" required />
                </label>
              </div>
            </section>
            <section class="panel-block">
              <div class="block-head">
                <div>
                  <p class="block-eyebrow">{_escape(copy["role_section_title"])}</p>
                  <h3 class="block-title">{_escape(copy["role_settings_title"])}</h3>
                </div>
                <p class="block-body">{_escape(copy["role_settings_body"])}</p>
              </div>
              <div class="role-toolbar">
                <span class="role-note">{_escape(copy["max_roles_note"])}</span>
                <button type="button" class="button-secondary" id="add-role-button">{_escape(copy["add_role_button"])}</button>
              </div>
              <div class="role-settings">
                {_role_settings_html(copy, normalized_role_rows)}
              </div>
            </section>
            <section class="panel-block">
              <div class="block-head">
                <div>
                  <p class="block-eyebrow">{_escape(copy["action_section_title"])}</p>
                  <h3 class="block-title">{_escape(copy["generate_button"])}</h3>
                </div>
                <p class="block-body">{_escape(copy["action_section_body"])}</p>
              </div>
              <div class="button-row">
                <button type="button" class="button-secondary" id="preview-button">{_escape(copy["preview_button"])}</button>
                <button type="submit">{_escape(copy["generate_button"])}</button>
              </div>
            </section>
          </form>
        </section>
        <aside class="panel sidebar">
          <section class="help">
            <h2>{_escape(copy["sample_section_title"])}</h2>
            <p>{_escape(copy["sample_section_body"])}</p>
            <div class="table-shell">
              <table class="schema-table">
                <thead>
                  <tr>
                    <th>{_escape(copy["sample_table_headers"][0])}</th>
                    <th>{_escape(copy["sample_table_headers"][1])}</th>
                    <th>{_escape(copy["sample_table_headers"][2])}</th>
                    <th>{_escape(copy["sample_table_headers"][3])}</th>
                  </tr>
                </thead>
                <tbody>{_table_rows_html(copy)}</tbody>
              </table>
            </div>
          </section>
          <section class="help">
            <h2>{_escape(copy["guide_title"])}</h2>
            <ul>{_guide_items_html(copy)}</ul>
          </section>
        </aside>
      </div>
      <section class="note-strip" aria-label="{_escape(copy["quick_notes_title"])}">
        {_quick_notes_html(copy)}
      </section>
    </main>
    <script>
      const uiText = {preview_messages};
      const form = document.querySelector('form[action="/generate"]');
      const previewButton = document.getElementById('preview-button');
      const roleSettings = document.querySelector('.role-settings');
      const addRoleButton = document.getElementById('add-role-button');
      const exampleContainer = document.querySelector('.examples');
      const roleCountIndicators = document.querySelectorAll('[data-role-count]');
      const maxRoleRows = {MAX_ROLE_ROWS};
      const minRoleRows = {MIN_ROLE_ROWS};
      const initialRoleRows = {initial_role_rows};
      const samplePeople = {sample_people};

      function collectRoleRows() {{
        const rows = [];
        for (const row of roleSettings.querySelectorAll('[data-role-row]')) {{
          const key = row.querySelector('input[name="role_key"]').value.trim().toUpperCase();
          const label = row.querySelector('input[name="role_label"]').value.trim();
          const color = row.querySelector('input[name="role_color"]').value;
          if (!key) continue;
          rows.push({{ key, label: label || key, color }});
        }}
        return rows;
      }}

      function createRoleRow(role, index) {{
        const row = document.createElement('div');
        row.className = 'role-row';
        row.setAttribute('data-role-row', 'true');
        row.innerHTML = `
          <strong class="role-row-title">{_escape(copy["role_key_field"])} ${'{'}index + 1{'}'}</strong>
          <div class="role-fields">
            <label class="role-field role-field-key">
              {_escape(copy["role_key_field"])}
              <input type="text" name="role_key" value="${'{'}role.key{'}'}" />
            </label>
            <label class="role-field">
              {_escape(copy["label_field"])}
              <input type="text" name="role_label" value="${'{'}role.label{'}'}" />
            </label>
            <label class="role-field role-field-color">
              {_escape(copy["color_field"])}
              <input type="color" name="role_color" value="${'{'}role.color{'}'}" />
            </label>
            <button type="button" class="button-secondary role-remove" data-role-remove>{_escape(copy["remove_role_button"])}</button>
          </div>
          <small class="role-help">{_escape(copy["role_key_help"])}</small>
        `;
        return row;
      }}

      function renderExampleCards() {{
        const roles = collectRoleRows();
        const sourceRoles = roles.length ? roles : initialRoleRows.slice(0, minRoleRows);
        let html = '';
        sourceRoles.forEach((role, index) => {{
          const sample = samplePeople[index % samplePeople.length];
          html += `
            <article class="sample-card">
              <span class="sample-label">${'{'}role.key{'}'}</span>
              <strong class="name">${'{'}sample[0]{'}'}</strong>
              <div class="meta">
                <div>${'{'}sample[3] || ''{'}'}</div>
                <div>@${'{'}sample[1]{'}'}</div>
              </div>
              <div class="bar" style="background:${'{'}role.color{'}'};">${'{'}role.label{'}'}</div>
            </article>
          `;
        }});
        const plain = samplePeople[1];
        html += `
          <article class="sample-card no-role">
            <span class="sample-label">{_escape(copy["sample_card_labels"]["plain"])}</span>
            <strong class="name">${'{'}plain[0]{'}'}</strong>
            <div class="meta">
              <div>${'{'}plain[3] || ''{'}'}</div>
              <div>@${'{'}plain[1]{'}'}</div>
            </div>
          </article>
        `;
        exampleContainer.innerHTML = html;
      }}

      function syncRoleRows() {{
        const rows = [...roleSettings.querySelectorAll('[data-role-row]')];
        rows.forEach((row, index) => {{
          const title = row.querySelector('.role-row-title');
          if (title) title.textContent = `{_escape(copy["role_key_field"])} ${'{'}index + 1{'}'}`;
          const removeButton = row.querySelector('[data-role-remove]');
          if (removeButton) {{
            removeButton.disabled = index < minRoleRows;
          }}
        }});
        if (addRoleButton) {{
          addRoleButton.disabled = rows.length >= maxRoleRows;
        }}
        roleCountIndicators.forEach((indicator) => {{
          indicator.textContent = String(rows.length);
        }});
        renderExampleCards();
      }}

      async function renderPreview() {{
        if (!form) return;
        const workbookInput = form.querySelector('input[name="workbook"]');
        if (!workbookInput || !workbookInput.files || workbookInput.files.length === 0) {{
          window.alert(uiText.choose_file);
          return;
        }}
        const formData = new FormData(form);
        try {{
          const response = await fetch('/preview', {{ method: 'POST', body: formData }});
          const payload = await response.json();
          if (!response.ok) {{
            window.alert(payload.error || uiText.failed);
            return;
          }}
          const previewWindow = window.open(payload.preview_data_url, '_blank');
          if (!previewWindow) {{
            window.alert(uiText.ready.replace('__COUNT__', String(payload.attendee_count)));
          }}
        }} catch (error) {{
          window.alert(uiText.failed);
        }}
      }}

      if (addRoleButton && roleSettings) {{
        addRoleButton.addEventListener('click', () => {{
          const rows = roleSettings.querySelectorAll('[data-role-row]');
          if (rows.length >= maxRoleRows) return;
          roleSettings.appendChild(
            createRoleRow(
              {{ key: `ROLE_${'{'}rows.length + 1{'}'}`, label: `ROLE ${'{'}rows.length + 1{'}'}`, color: '#2F2F2F' }},
              rows.length
            )
          );
          syncRoleRows();
        }});

        roleSettings.addEventListener('click', (event) => {{
          const target = event.target;
          if (!(target instanceof HTMLElement)) return;
          const button = target.closest('[data-role-remove]');
          if (!button) return;
          const rows = roleSettings.querySelectorAll('[data-role-row]');
          if (rows.length <= minRoleRows) return;
          button.closest('[data-role-row]')?.remove();
          syncRoleRows();
        }});

        roleSettings.addEventListener('input', () => {{
          syncRoleRows();
        }});
      }}

      if (previewButton) {{
        previewButton.addEventListener('click', renderPreview);
      }}

      syncRoleRows();
    </script>
  </body>
</html>"""


def create_app() -> FastAPI:
    app = FastAPI(title="Nametag Generator")

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> str:
        language = resolve_language(request.query_params.get("lang"))
        return _render_page(
            language=language,
            base_url=str(request.base_url).rstrip("/"),
            canonical_path=f"/{language}",
        )

    @app.get("/en", response_class=HTMLResponse)
    async def english_page(request: Request) -> str:
        return _render_page(
            language="en",
            base_url=str(request.base_url).rstrip("/"),
            canonical_path="/en",
        )

    @app.get("/ko", response_class=HTMLResponse)
    async def korean_page(request: Request) -> str:
        return _render_page(
            language="ko",
            base_url=str(request.base_url).rstrip("/"),
            canonical_path="/ko",
        )

    @app.get("/robots.txt")
    async def robots(request: Request) -> Response:
        base_url = str(request.base_url).rstrip("/")
        return Response(
            content=f"User-agent: *\nAllow: /\nSitemap: {base_url}/sitemap.xml\n",
            media_type="text/plain",
        )

    @app.get("/sitemap.xml")
    async def sitemap(request: Request) -> Response:
        return Response(
            content=_sitemap_xml(str(request.base_url).rstrip("/")),
            media_type="application/xml",
        )

    @app.get("/sample-workbook")
    async def sample_workbook() -> FileResponse:
        return FileResponse(
            SAMPLE_WORKBOOK,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=SAMPLE_WORKBOOK.name,
        )

    @app.get("/sample-pdf")
    async def sample_pdf() -> FileResponse:
        return FileResponse(
            SAMPLE_PDF,
            media_type="application/pdf",
            filename=SAMPLE_PDF.name,
        )

    @app.get("/favicon.ico")
    async def favicon() -> Response:
        if not FAVICON_ICO.exists():
            return Response(content=FALLBACK_FAVICON_ICO, media_type="image/x-icon")
        return FileResponse(FAVICON_ICO, media_type="image/x-icon")

    @app.post("/preview")
    async def preview(request: Request) -> JSONResponse:
        form = await request.form()
        workbook = form["workbook"]
        card_width_mm = float(form.get("card_width_mm", 93.0))
        card_height_mm = float(form.get("card_height_mm", 122.0))
        role_rows = _parse_role_rows_from_form(form)
        suffix = Path(workbook.filename or "preview.xlsx").suffix or ".xlsx"
        with NamedTemporaryFile(suffix=suffix) as temp_file:
            temp_file.write(await workbook.read())
            temp_file.flush()
            try:
                attendees = load_attendees_from_xlsx(Path(temp_file.name))
                config = _build_generator_config(
                    card_width_mm=card_width_mm,
                    card_height_mm=card_height_mm,
                    role_rows=role_rows,
                )
                preview_png = generate_preview_png(attendees, config=config)
            except (WorkbookValidationError, FontResolutionError, ValueError) as exc:
                return JSONResponse(
                    {"error": str(exc), "attendee_count": 0},
                    status_code=400,
                )
        encoded = base64.b64encode(preview_png).decode("ascii")
        return JSONResponse(
            {
                "preview_data_url": f"data:image/png;base64,{encoded}",
                "attendee_count": len(attendees),
            }
        )

    @app.post("/generate")
    async def generate(request: Request) -> Response:
        form = await request.form()
        workbook = form["workbook"]
        language = resolve_language(str(form.get("lang", "en")))
        card_width_mm = float(form.get("card_width_mm", 93.0))
        card_height_mm = float(form.get("card_height_mm", 122.0))
        role_rows = _parse_role_rows_from_form(form)
        suffix = Path(workbook.filename or "upload.xlsx").suffix or ".xlsx"
        with NamedTemporaryFile(suffix=suffix) as temp_file:
            temp_file.write(await workbook.read())
            temp_file.flush()
            try:
                attendees = load_attendees_from_xlsx(Path(temp_file.name))
                config = _build_generator_config(
                    card_width_mm=card_width_mm,
                    card_height_mm=card_height_mm,
                    role_rows=role_rows,
                )
                result = generate_pdf(attendees, config=config)
            except (WorkbookValidationError, FontResolutionError, ValueError) as exc:
                return HTMLResponse(
                    _render_page(
                        language=language,
                        base_url=str(request.base_url).rstrip("/"),
                        canonical_path=f"/{language}",
                        error=str(exc),
                        role_rows=role_rows,
                    ),
                    status_code=400,
                )
        return Response(
            content=result.pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="nametags.pdf"'},
        )

    return app
