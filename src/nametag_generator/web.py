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
        f'<a class="{"lang-link active" if code == language else "lang-link"}" href="/?lang={code}">{_escape(UI_COPY[language]["language_toggle"][code])}</a>'
        for code in ("en", "ko")
    )


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
    error: str | None = None,
    role_rows: list[dict[str, str]] | None = None,
) -> str:
    copy = UI_COPY[resolve_language(language)]
    normalized_role_rows = _normalize_role_rows(role_rows)
    preview_messages = json.dumps(copy["preview_messages"], ensure_ascii=False)
    initial_role_rows = json.dumps(normalized_role_rows, ensure_ascii=False)
    sample_people = json.dumps(SAMPLE_ROWS, ensure_ascii=False)
    message_html = (
        f"<div class='flash flash-error'>{_escape(error)}</div>" if error else ""
    )
    return f"""<!doctype html>
<html lang="{_escape(language)}">
  <head>
    <meta charset="utf-8" />
    <title>Nametag Generator</title>
    <link rel="icon" href="/favicon.ico" sizes="any" />
    <style>
      :root {{
        --bg: #efe7da;
        --panel: #fffaf2;
        --panel-strong: #f6eee1;
        --ink: #1d1b18;
        --muted: #6a6258;
        --line: #d9ccbb;
        --accent: #1459d9;
        --accent-soft: rgba(20, 89, 217, 0.10);
        --warm: #c96b29;
        --shadow: 0 24px 70px rgba(0, 0, 0, 0.10);
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        font-family: "Avenir Next", "Helvetica Neue", "Pretendard", sans-serif;
        background:
          radial-gradient(circle at top left, rgba(20, 89, 217, 0.10), transparent 24%),
          radial-gradient(circle at top right, rgba(201, 107, 41, 0.12), transparent 20%),
          linear-gradient(180deg, var(--bg), #e8dece);
        color: var(--ink);
      }}
      main {{
        max-width: 1240px;
        margin: 0 auto;
        padding: 28px 20px 40px;
      }}
      .topbar {{
        display: flex;
        justify-content: flex-end;
        margin-bottom: 14px;
      }}
      .lang-switch {{
        display: inline-flex;
        gap: 6px;
        padding: 6px;
        border: 1px solid var(--line);
        background: rgba(255, 255, 255, 0.72);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
      }}
      .lang-link {{
        padding: 8px 12px;
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
      .shell {{
        display: grid;
        grid-template-columns: minmax(0, 1.1fr) minmax(320px, 0.9fr);
        gap: 24px;
        align-items: start;
      }}
      .panel {{
        background: color-mix(in srgb, var(--panel) 88%, white);
        border: 1px solid var(--line);
        box-shadow: var(--shadow);
      }}
      .workspace {{ padding: 32px; }}
      .sidebar {{
        position: sticky;
        top: 20px;
        padding: 22px;
        background:
          linear-gradient(180deg, rgba(255, 255, 255, 0.97), rgba(245, 236, 223, 0.95));
      }}
      .eyebrow {{
        display: inline-flex;
        padding: 6px 12px;
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
        font-size: clamp(42px, 7vw, 68px);
        line-height: 0.94;
        letter-spacing: -0.05em;
        max-width: 10ch;
      }}
      .lead {{
        margin: 0;
        max-width: 58ch;
        color: var(--muted);
        font-size: 18px;
      }}
      .stats {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 16px;
        margin-top: 26px;
      }}
      .stat-card {{
        min-height: 162px;
        padding: 20px;
        border: 1px solid var(--line);
        background: linear-gradient(180deg, white, var(--panel-strong));
      }}
      .stat-card strong {{
        display: block;
        margin-bottom: 8px;
        font-size: clamp(28px, 5vw, 36px);
        line-height: 1;
      }}
      .stat-card p {{ margin: 0; color: var(--muted); }}
      .flash {{
        margin-top: 18px;
        padding: 14px 16px;
        border: 1px solid #e5b5a7;
        background: #fff0ea;
        font-weight: 600;
      }}
      form {{
        display: grid;
        gap: 18px;
        margin-top: 28px;
      }}
      .panel-block {{
        padding: 18px;
        border: 1px solid var(--line);
        background: linear-gradient(180deg, #fffdf9, #f6eee2);
      }}
      .panel-block h2 {{
        margin: 0 0 8px;
        font-size: 18px;
      }}
      .panel-block p {{
        margin: 0 0 10px;
        color: var(--muted);
      }}
      label {{
        display: grid;
        gap: 8px;
        font-weight: 600;
      }}
      input[type=file], input[type=number], input[type=text], input[type=color] {{
        width: 100%;
        padding: 12px;
        border: 1px solid var(--line);
        background: white;
        font: inherit;
      }}
      input[type=color] {{ min-height: 48px; }}
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
        border: 1px solid var(--line);
        background: rgba(255, 255, 255, 0.74);
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
        padding: 14px 18px;
        border: 0;
        background: var(--accent);
        color: white;
        font-weight: 700;
        cursor: pointer;
        transition: transform 120ms ease, box-shadow 120ms ease;
      }}
      .button-secondary {{
        background: white;
        color: var(--ink);
        border: 1px solid var(--line);
      }}
      button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 10px 24px rgba(20, 89, 217, 0.24);
      }}
      .button-secondary:hover {{
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.06);
      }}
      .role-toolbar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
        margin-bottom: 12px;
      }}
      .role-note {{ color: var(--muted); font-size: 13px; }}
      .role-settings {{
        display: grid;
        gap: 12px;
      }}
      .role-row {{
        display: grid;
        gap: 10px;
        padding: 16px;
        border: 1px solid var(--line);
        background: rgba(255, 255, 255, 0.52);
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
        border: 1px solid var(--line);
        background: linear-gradient(180deg, #fffdf9, #f6eee2);
      }}
      .help + .help {{
        margin-top: 16px;
      }}
      .help h2 {{
        margin: 0 0 10px;
        font-size: 18px;
      }}
      .help p {{
        margin: 0 0 10px;
        color: var(--muted);
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
        border: 1px solid var(--line);
        background: white;
        color: var(--ink);
        text-decoration: none;
        font-weight: 700;
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
      .sample-card {{
        position: relative;
        width: min(100%, 220px);
        aspect-ratio: 93 / 122;
        min-height: unset;
        padding: 18px 16px 16px;
        border: 1px solid #b9b1a3;
        background: linear-gradient(180deg, #fffefb, #f6f1e8);
        overflow: hidden;
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
      }}
      .sample-card .meta {{
        margin-top: 14px;
        text-align: center;
        line-height: 1.25;
        font-size: 13px;
      }}
      .sample-card .bar {{
        position: absolute;
        left: 0;
        right: 0;
        bottom: 0;
        padding: 10px 8px;
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
      }}
      p {{ line-height: 1.5; }}
      @media (max-width: 1020px) {{
        .shell {{ grid-template-columns: 1fr; }}
        .sidebar {{ position: static; }}
      }}
      @media (max-width: 860px) {{
        .role-fields {{
          grid-template-columns: 1fr;
        }}
      }}
      @media (max-width: 760px) {{
        main {{ padding: 16px; }}
        .workspace, .sidebar {{ padding: 20px; }}
        .stats, .grid, .split {{ grid-template-columns: 1fr; }}
      }}
    </style>
  </head>
  <body>
    <main>
      <div class="topbar">
        <div class="lang-switch" aria-label="{_escape(copy["language_label"])}">
          {_language_toggle_html(language)}
        </div>
      </div>
      <div class="shell">
        <section class="panel workspace">
          <span class="eyebrow">{_escape(copy["eyebrow"])}</span>
          <h1>{_escape(copy["hero_title"])}</h1>
          <p class="lead">{_escape(copy["lead"])}</p>
          <div class="stats">
            <div class="stat-card">
              <strong>{_escape(copy["stats"][0]["title"])}</strong>
              <p>{_escape(copy["stats"][0]["body"])}</p>
            </div>
            <div class="stat-card">
              <strong>{_escape(copy["stats"][1]["title"])}</strong>
              <p>{_escape(copy["stats"][1]["body"])}</p>
            </div>
          </div>
          {message_html}
          <form action="/generate" method="post" enctype="multipart/form-data">
            <input type="hidden" name="lang" value="{_escape(language)}" />
            <div class="split">
              <label>
                {_escape(copy["workbook_label"])}
                <input type="file" name="workbook" accept=".xlsx" required />
              </label>
              <div class="hint-grid">
                {_workflow_hints_html(copy)}
              </div>
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
            <section class="panel-block">
              <h2>{_escape(copy["role_settings_title"])}</h2>
              <p>{_escape(copy["role_settings_body"])}</p>
              <div class="role-toolbar">
                <span class="role-note">{_escape(copy["max_roles_note"])}</span>
                <button type="button" class="button-secondary" id="add-role-button">{_escape(copy["add_role_button"])}</button>
              </div>
              <div class="role-settings">
                {_role_settings_html(copy, normalized_role_rows)}
              </div>
            </section>
            <div class="button-row">
              <button type="button" class="button-secondary" id="preview-button">{_escape(copy["preview_button"])}</button>
              <button type="submit">{_escape(copy["generate_button"])}</button>
            </div>
          </form>
        </section>
        <aside class="panel sidebar">
          <section class="help">
            <h2>{_escape(copy["sample_section_title"])}</h2>
            <p>{_escape(copy["sample_section_body"])}</p>
            <div class="actions">
              <a class="action-link" href="/sample-workbook">{_escape(copy["download_workbook"])}</a>
              <a class="action-link" href="/sample-pdf">{_escape(copy["download_pdf"])}</a>
            </div>
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
          </section>
          <section class="help">
            <h2>{_escape(copy["preview_section_title"])}</h2>
            <p>{_escape(copy["preview_section_body"])}</p>
            <div class="examples">{_sample_cards_html(copy, normalized_role_rows)}</div>
          </section>
          <section class="help">
            <h2>{_escape(copy["guide_title"])}</h2>
            <ul>{_guide_items_html(copy)}</ul>
          </section>
        </aside>
      </div>
    </main>
    <script>
      const uiText = {preview_messages};
      const form = document.querySelector('form[action="/generate"]');
      const previewButton = document.getElementById('preview-button');
      const roleSettings = document.querySelector('.role-settings');
      const addRoleButton = document.getElementById('add-role-button');
      const exampleContainer = document.querySelector('.examples');
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
        return _render_page(language=language)

    @app.get("/en", response_class=HTMLResponse)
    async def english_page() -> str:
        return _render_page(language="en")

    @app.get("/ko", response_class=HTMLResponse)
    async def korean_page() -> str:
        return _render_page(language="ko")

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
            return Response(status_code=204)
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
