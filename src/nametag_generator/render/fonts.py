from __future__ import annotations

from pathlib import Path
from typing import Sequence

from nametag_generator.errors import FontResolutionError


def resolve_font_path(candidates: Sequence[Path | str]) -> Path:
    for candidate in candidates:
        path = Path(candidate).expanduser()
        if path.exists():
            return path
    searched = ", ".join(str(Path(candidate).expanduser()) for candidate in candidates)
    raise FontResolutionError(
        "No usable font was found. Tried: "
        f"{searched}. Configure font_candidates to a font that supports your text."
    )
