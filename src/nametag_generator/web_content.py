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
        "meta_title": "Nametag Generator | Create Print-Ready Event Name Tags from Excel",
        "meta_description": (
            "Generate print-ready event name tags from an Excel workbook, preview the first page in your browser, "
            "and export a PDF sized for real badge inserts."
        ),
        "meta_locale": "en_US",
        "site_name": "Nametag Generator",
        "eyebrow": "Ready to print",
        "hero_title": "Make name tags that fit the first time.",
        "lead": (
            "Upload a simple .xlsx file, preview the first page in your browser, "
            "and export a PDF that is already sized for your badge inserts."
        ),
        "stats": (
            {
                "title": "93 × 122 mm",
                "body": "Set to 93 × 122 mm by default, and easy to adjust. Print at 100% for a true-to-size fit.",
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
        "search_section_title": "Create printable event name tags from Excel",
        "search_section_body": (
            "This tool is built for event teams that need a fast path from a spreadsheet to a badge-sized PDF. "
            "It keeps the input simple, preserves physical dimensions in millimeters, and lets you preview before exporting."
        ),
        "howto_title": "How to make print-ready name tags",
        "howto_intro": (
            "Use the web app when you want a simple browser workflow without editing templates in a design tool."
        ),
        "howto_steps": (
            (
                "Prepare an .xlsx workbook",
                "Add the required columns `name` and `organization`, then add `role` or `title` only when you need them.",
            ),
            (
                "Adjust badge size and role styles",
                "Keep the default 93 × 122 mm size or enter a custom insert size, then edit role labels and colors if your event uses custom badge bars.",
            ),
            (
                "Preview and export",
                "Render the first page in your browser, verify the layout, and download the final PDF for printing at 100% or Actual Size.",
            ),
        ),
        "faq_title": "FAQ",
        "faq_intro": "These answers are written to help both visitors and search engines understand exactly what the app does.",
        "faq_items": (
            (
                "What file format does Nametag Generator use?",
                "Nametag Generator uses `.xlsx` Excel workbooks. The required columns are `name` and `organization`, while `role` and `title` are optional.",
            ),
            (
                "Can I create event badges without a design tool?",
                "Yes. The app turns spreadsheet data into a print-ready PDF, so event operators can create badges without opening layout software.",
            ),
            (
                "Can I preview badges before downloading the PDF?",
                "Yes. The web UI renders the first page in your browser so you can confirm names, spacing, and role bars before export.",
            ),
            (
                "How do I print the badges at the correct size?",
                "Export the PDF and print it at 100% or Actual Size. The default badge insert size is 93 × 122 mm, and you can change it if your inserts use another format.",
            ),
        ),
        "feature_list": (
            "Generate badge PDFs from `.xlsx` workbooks",
            "Preview the first page in the browser before export",
            "Customize role labels and colors",
            "Set physical badge size in millimeters",
            "Switch between English and Korean UI copy",
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
        "meta_title": "Nametag Generator | 엑셀로 출력용 행사 네임태그 PDF 만들기",
        "meta_description": (
            "엑셀 워크북으로 행사 네임태그를 만들고, 브라우저에서 첫 페이지를 미리 확인한 뒤 실제 배지 규격에 맞는 PDF로 바로 내보낼 수 있습니다."
        ),
        "meta_locale": "ko_KR",
        "site_name": "Nametag Generator",
        "eyebrow": "바로 출력 가능한 네임태그",
        "hero_title": "한 번에 맞는 네임태그를 바로 만드세요.",
        "lead": (
            "간단한 .xlsx 파일을 올리고 브라우저에서 첫 페이지를 확인한 뒤, "
            "실제 카드 규격에 맞는 PDF를 바로 내려받을 수 있습니다."
        ),
        "stats": (
            {
                "title": "93 × 122 mm",
                "body": "기본값은 93 × 122 mm이며 필요하면 조정할 수 있습니다. 100% 실제 사이즈로 출력하면 바로 사용할 수 있습니다.",
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
        "search_section_title": "엑셀에서 바로 출력 가능한 행사 네임태그 만들기",
        "search_section_body": (
            "이 도구는 행사 운영팀이 스프레드시트에서 배지용 PDF까지 빠르게 만들 수 있도록 설계되었습니다. "
            "입력은 단순하게 유지하고, 실제 규격은 mm 단위로 맞추며, 내보내기 전에 브라우저 미리보기도 제공합니다."
        ),
        "howto_title": "출력용 네임태그 만드는 방법",
        "howto_intro": "디자인 툴 없이 브라우저만으로 네임태그를 만들고 싶을 때 사용하는 흐름입니다.",
        "howto_steps": (
            (
                ".xlsx 워크북 준비",
                "필수 컬럼인 `name`, `organization`을 넣고, 필요할 때만 `role`, `title` 컬럼을 추가합니다.",
            ),
            (
                "카드 크기와 역할 바 설정",
                "기본 93 × 122 mm를 유지하거나 원하는 규격을 입력하고, 행사에 맞게 역할 라벨과 색상을 조정합니다.",
            ),
            (
                "미리보기 후 PDF 생성",
                "브라우저에서 첫 페이지를 확인한 뒤 최종 PDF를 내려받아 100% 또는 Actual Size로 출력합니다.",
            ),
        ),
        "faq_title": "자주 묻는 질문",
        "faq_intro": "방문자와 검색엔진이 이 앱의 용도를 바로 이해할 수 있도록 핵심 질문에 짧고 명확하게 답합니다.",
        "faq_items": (
            (
                "Nametag Generator는 어떤 파일 형식을 사용하나요?",
                "`.xlsx` 엑셀 워크북을 사용합니다. 필수 컬럼은 `name`, `organization`이며 `role`, `title`은 선택입니다.",
            ),
            (
                "디자인 툴 없이 행사 이름표를 만들 수 있나요?",
                "네. 스프레드시트 데이터를 바로 출력용 PDF로 바꿔 주기 때문에 별도의 레이아웃 툴 없이도 행사 배지를 만들 수 있습니다.",
            ),
            (
                "PDF를 받기 전에 미리보기를 볼 수 있나요?",
                "네. 웹 UI에서 첫 페이지를 브라우저로 렌더링해서 이름, 여백, 역할 바를 확인한 뒤 내보낼 수 있습니다.",
            ),
            (
                "실제 크기에 맞게 출력하려면 어떻게 해야 하나요?",
                "PDF를 생성한 뒤 프린터 설정에서 100% 또는 Actual Size로 출력하면 됩니다. 기본 카드 규격은 93 × 122 mm이며 필요하면 변경할 수 있습니다.",
            ),
        ),
        "feature_list": (
            "`.xlsx` 워크북으로 네임태그 PDF 생성",
            "브라우저에서 첫 페이지 미리보기",
            "역할 라벨과 색상 사용자 지정",
            "mm 단위 실제 카드 규격 설정",
            "영어와 한국어 UI 전환",
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
