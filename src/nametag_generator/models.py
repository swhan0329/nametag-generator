from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Attendee:
    name: str
    organization: str | None = None
    role: str | None = None
    title: str | None = None


@dataclass(slots=True)
class RoleStyle:
    label: str
    background_color: str
    text_color: str = "#FFFFFF"
    show_bar: bool = True
