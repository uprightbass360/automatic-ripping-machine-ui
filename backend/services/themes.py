"""Theme loading and management service."""

import json
from pathlib import Path
from typing import Any

from backend.config import settings

# Built-in themes ship with the package
_BUILTIN_DIR = Path(__file__).parent.parent / "themes" / "builtin"


def _load_theme_file(path: Path) -> dict[str, Any] | None:
    """Load and validate a single theme JSON file."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not _validate_theme(data):
            return None
        return data
    except (json.JSONDecodeError, OSError):
        return None


def _validate_theme(data: Any) -> bool:
    """Check required fields are present."""
    if not isinstance(data, dict):
        return False
    required = {"id", "label", "tokens"}
    return required.issubset(data.keys()) and isinstance(data["tokens"], dict)


def _user_themes_dir() -> Path:
    """Return the user themes directory, creating it if needed."""
    p = Path(settings.arm_themes_path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _load_all() -> dict[str, dict[str, Any]]:
    """Load all themes, user themes override built-ins with same id."""
    themes: dict[str, dict[str, Any]] = {}

    # Built-in themes
    if _BUILTIN_DIR.is_dir():
        for f in sorted(_BUILTIN_DIR.glob("*.json")):
            t = _load_theme_file(f)
            if t:
                t["builtin"] = True
                themes[t["id"]] = t

    # User themes (override built-ins)
    user_dir = _user_themes_dir()
    if user_dir.is_dir():
        for f in sorted(user_dir.glob("*.json")):
            t = _load_theme_file(f)
            if t:
                t["builtin"] = False
                themes[t["id"]] = t

    return themes


def get_all_themes() -> list[dict[str, Any]]:
    """Return metadata for all themes (no CSS)."""
    themes = _load_all()
    result = []
    for t in themes.values():
        meta = {k: v for k, v in t.items() if k != "css"}
        result.append(meta)
    return result


def get_theme(theme_id: str) -> dict[str, Any] | None:
    """Return full theme data including CSS."""
    themes = _load_all()
    return themes.get(theme_id)


def save_user_theme(data: dict[str, Any]) -> dict[str, Any]:
    """Save a user theme to the themes directory. Returns the saved theme."""
    if not _validate_theme(data):
        raise ValueError("Invalid theme: missing required fields (id, label, tokens)")

    # Ensure standard fields
    data.setdefault("version", 1)
    data.setdefault("css", "")
    data.setdefault("swatch", "#888888")

    user_dir = _user_themes_dir()
    path = user_dir / f"{data['id']}.json"

    # Don't include runtime-only fields in saved file
    save_data = {k: v for k, v in data.items() if k != "builtin"}
    path.write_text(json.dumps(save_data, indent=2, ensure_ascii=False), encoding="utf-8")

    data["builtin"] = False
    return data


def delete_user_theme(theme_id: str) -> bool:
    """Delete a user theme. Returns False if it's a built-in or doesn't exist."""
    # Check if it's a built-in
    builtin_path = _BUILTIN_DIR / f"{theme_id}.json"
    if builtin_path.exists():
        return False

    user_dir = _user_themes_dir()
    path = user_dir / f"{theme_id}.json"
    if not path.exists():
        return False

    path.unlink()
    return True
