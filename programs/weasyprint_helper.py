"""Helper to import WeasyPrint safely.

This module centralizes the WeasyPrint import so other modules can
depend on `HTML` being `None` when native dependencies are missing.
"""

try:
    from weasyprint import HTML  # type: ignore
except Exception:
    HTML = None

__all__ = ("HTML",)
