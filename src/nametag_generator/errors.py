class NametagError(Exception):
    """Base exception for nametag generation."""


class WorkbookValidationError(NametagError):
    """Raised when workbook structure does not match the expected schema."""


class FontResolutionError(NametagError):
    """Raised when no usable font can be found for rendering."""
