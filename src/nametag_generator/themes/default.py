from __future__ import annotations

from pathlib import Path

from nametag_generator.models import RoleStyle


DEFAULT_FONT_CANDIDATES: tuple[Path, ...] = (
    Path("/System/Library/Fonts/AppleSDGothicNeo.ttc"),
    Path("/System/Library/Fonts/Supplemental/AppleGothic.ttf"),
    Path("/Library/Fonts/NanumGothic.ttf"),
    Path("/Library/Fonts/Noto Sans CJK KR.ttc"),
    Path("/usr/share/fonts/truetype/nanum/NanumGothic.ttf"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
)

DEFAULT_ROLE_STYLES: dict[str, RoleStyle] = {
    "HOST": RoleStyle(label="HOST", background_color="#000000"),
    "STAFF": RoleStyle(label="STAFF", background_color="#000000"),
    "SPEAKER": RoleStyle(label="SPEAKER", background_color="#4677D8"),
}


def normalize_role(role: str | None) -> str | None:
    if role is None:
        return None
    normalized = role.strip().upper()
    if not normalized or normalized in {"NONE", "ATTENDEE"}:
        return None
    return normalized


def resolve_role_style(
    role: str | None,
    role_styles: dict[str, RoleStyle],
) -> RoleStyle | None:
    normalized = normalize_role(role)
    if normalized is None:
        return None
    if normalized in role_styles:
        return role_styles[normalized]
    return RoleStyle(label=normalized, background_color="#2F2F2F")
