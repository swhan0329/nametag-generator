from __future__ import annotations

from typing import Any


SAMPLE_ROWS: tuple[tuple[str, str, str | None, str | None], ...] = (
    ("Ethan Carter", "Northstar Labs", "HOST", "Engineering Lead"),
    ("Olivia Bennett", "Harbor AI", None, "Product Designer"),
    ("Mason Reed", "Blue Mesa Systems", "SPEAKER", "Founder & CEO"),
)


UI_COPY: dict[str, dict[str, Any]] = {
    "en": {
        "language_name": "English",
        "eyebrow": "Ready to print",
        "hero_title": "Make name tags that fit the first time.",
        "lead": (
            "Upload a simple .xlsx file, preview the first page in your browser, "
            "and export a PDF that is already sized for your badge inserts."
        ),
        "stats": (
            {
                "title": "93 × 122 mm",
                "body": "Built for this insert size. Print at 100% and you are ready to go.",
            },
            {
                "title": "Preview before export",
                "body": (
                    "See the first page in your browser before you download the final PDF."
                ),
            },
        ),
        "required_label": "Required",
        "optional_label": "Optional",
        "workbook_label": "Workbook",
        "card_width_label": "Card width (mm)",
        "card_height_label": "Card height (mm)",
        "generate_button": "Generate PDF",
        "preview_button": "Preview in browser",
        "language_label": "Language",
        "language_toggle": {"en": "English", "ko": "한국어"},
        "role_settings_title": "Role style settings",
        "role_settings_body": (
            "Start with SPEAKER and STAFF, then add more roles only when you need them."
        ),
        "role_names": {"host": "Host", "speaker": "Speaker", "staff": "Staff"},
        "role_key_field": "Role value",
        "role_key_help": "Use the same value that appears in the workbook, such as SPEAKER.",
        "label_field": "Label",
        "color_field": "Color",
        "add_role_button": "Add role",
        "remove_role_button": "Remove",
        "max_roles_note": "Only 2 rows are shown at first. Add more if you need them, up to 6 total.",
        "sample_section_title": "Sample workbook columns",
        "sample_section_body": (
            "The sample file uses fictional U.S. names and companies so it is safe to share."
        ),
        "download_workbook": "Download sample .xlsx",
        "download_pdf": "Download sample PDF",
        "sample_table_headers": ("Column", "Required", "Example", "Use"),
        "sample_table_rows": (
            ("name", "Yes", "Ethan Carter", "Large name text on the badge"),
            (
                "organization",
                "Yes",
                "Northstar Labs",
                "Shown as @Northstar Labs",
            ),
            (
                "role",
                "No",
                "SPEAKER",
                "Adds a role bar. Leave it blank, or remove the column, for a plain badge. The panel starts with SPEAKER and STAFF.",
            ),
            (
                "title",
                "No",
                "Engineering Lead",
                "Small subtitle line above the organization",
            ),
        ),
        "workflow_hints": (
            ("Required", "name, organization"),
            ("Optional", "role, title"),
        ),
        "preview_section_title": "Role examples",
        "preview_section_body": (
            "These sample cards show how the configured role rows will look."
        ),
        "guide_title": "Workbook guide",
        "guide_items": (
            "If role is blank, or the column is missing, the nametag is generated without a role bar.",
            "Typical role values include ATTENDEE, HOST, SPEAKER, and STAFF.",
            "For the right physical size, print at 100% or Actual Size.",
        ),
        "sample_card_labels": {"host": "Host", "speaker": "Speaker", "plain": "No Role"},
        "preview_messages": {
            "choose_file": "Choose an .xlsx file first.",
            "rendering": "Rendering your preview...",
            "failed": "Preview failed. Check the workbook format and try again.",
            "ready": "Preview ready for __COUNT__ attendee(s). This is the first page only.",
        },
    },
    "ko": {
        "language_name": "한국어",
        "eyebrow": "바로 출력 가능한 네임태그",
        "hero_title": "한 번에 맞는 네임태그를 바로 만드세요.",
        "lead": (
            "간단한 .xlsx 파일을 올리고 브라우저에서 첫 페이지를 확인한 뒤, "
            "실제 카드 규격에 맞는 PDF를 바로 내려받을 수 있습니다."
        ),
        "stats": (
            {
                "title": "93 × 122 mm",
                "body": "이 규격에 맞춰 만들었습니다. 100% 실제 사이즈로 출력하면 바로 사용할 수 있습니다.",
            },
            {
                "title": "미리보기 후 출력",
                "body": "최종 PDF를 받기 전에 브라우저에서 첫 페이지를 먼저 확인할 수 있습니다.",
            },
        ),
        "required_label": "필수",
        "optional_label": "선택",
        "workbook_label": "워크북",
        "card_width_label": "카드 가로 (mm)",
        "card_height_label": "카드 세로 (mm)",
        "generate_button": "PDF 생성",
        "preview_button": "브라우저에서 미리보기",
        "language_label": "언어",
        "language_toggle": {"en": "English", "ko": "한국어"},
        "role_settings_title": "역할 바 설정",
        "role_settings_body": "기본은 SPEAKER와 STAFF 두 줄만 보이고, 필요한 경우에만 더 추가할 수 있습니다.",
        "role_names": {"host": "호스트", "speaker": "연사", "staff": "스태프"},
        "role_key_field": "역할 값",
        "role_key_help": "워크북에 들어 있는 role 값과 맞춰 주세요. 예: SPEAKER",
        "label_field": "라벨",
        "color_field": "색상",
        "add_role_button": "역할 추가",
        "remove_role_button": "삭제",
        "max_roles_note": "처음에는 2개만 보이고, 필요하면 추가해서 최대 6개까지 설정할 수 있습니다.",
        "sample_section_title": "샘플 워크북 컬럼",
        "sample_section_body": "공개 저장소에서도 안전하게 쓸 수 있도록 가상의 미국식 이름과 회사명을 사용합니다.",
        "download_workbook": "샘플 .xlsx 다운로드",
        "download_pdf": "샘플 PDF 다운로드",
        "sample_table_headers": ("컬럼", "필수", "예시", "설명"),
        "sample_table_rows": (
            ("name", "예", "Ethan Carter", "이름표에 크게 표시되는 이름"),
            (
                "organization",
                "예",
                "Northstar Labs",
                "@Northstar Labs 형식으로 표시되는 소속",
            ),
            (
                "role",
                "아니오",
                "SPEAKER",
                "역할 바를 추가합니다. 비워 두거나 컬럼이 없으면 일반 이름표로 출력됩니다. 설정 패널은 SPEAKER와 STAFF로 시작합니다.",
            ),
            (
                "title",
                "아니오",
                "Engineering Lead",
                "소속 위에 들어가는 작은 직함/부제목",
            ),
        ),
        "workflow_hints": (
            ("필수", "name, organization"),
            ("선택", "role, title"),
        ),
        "preview_section_title": "역할 예시",
        "preview_section_body": "현재 설정한 역할 행이 카드에서 어떻게 보이는지 예시로 보여줍니다.",
        "guide_title": "워크북 안내",
        "guide_items": (
            "role 값이 비어 있거나 컬럼이 없으면 역할 바 없이 일반 이름표가 생성됩니다.",
            "주로 쓰는 역할 값은 ATTENDEE, HOST, SPEAKER, STAFF 입니다.",
            "실측을 맞추려면 100% 또는 Actual Size로 출력하세요.",
        ),
        "sample_card_labels": {"host": "호스트", "speaker": "연사", "plain": "일반"},
        "preview_messages": {
            "choose_file": ".xlsx 파일을 먼저 선택해 주세요.",
            "rendering": "미리보기를 만드는 중입니다...",
            "failed": "미리보기에 실패했습니다. 워크북 형식을 다시 확인해 주세요.",
            "ready": "__COUNT__명 기준 첫 페이지 미리보기가 준비되었습니다.",
        },
    },
}


def resolve_language(language: str | None) -> str:
    if language in UI_COPY:
        return language
    return "en"
