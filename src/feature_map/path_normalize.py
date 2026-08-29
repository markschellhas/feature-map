import re
from typing import Optional

HTTP_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS")
PATH_EXTENSIONS = (".rb", ".js", ".erb", ".svelte", ".ts", ".tsx", ".py", ".go", ".yaml", ".yml")
PATH_PREFIXES = ("app/", "src/", "lib/", "config/", "pkg/", "internal/", "rails/")
EXT_PATTERN = r"\.(?:rb|js|erb|svelte|ts|tsx|py|go|yaml|yml)"
LINE_RANGE_RE = re.compile(r":\d+(?:-\d+)?$")


def looks_like_file_path(value: str) -> bool:
    if not value or " " in value:
        return False
    if LINE_RANGE_RE.search(value):
        return False
    if ":" in value and not value.startswith(("rails/", "app/", "src/", "config/", "lib/")):
        # reject stray colon annotations (e.g. line ranges not yet stripped)
        if re.search(r":\d", value):
            return False
    if value.endswith(PATH_EXTENSIONS):
        return True
    if any(value.startswith(prefix) for prefix in PATH_PREFIXES):
        return True
    if "/" in value:
        last = value.rsplit("/", 1)[-1]
        if "." in last and not last.endswith("."):
            return True
    return False


def passes_normalized_invariants(path: str) -> bool:
    if not path or " " in path:
        return False
    if re.search(r":\d", path):
        return False
    if "—" in path or "–" in path:
        return False
    if "mounts" in path.lower():
        return False
    return looks_like_file_path(path)


def strip_line_range(value: str) -> str:
    return LINE_RANGE_RE.sub("", value).strip()


def normalize_path_candidate(value: str) -> Optional[str]:
    if not isinstance(value, str):
        return None

    value = value.strip().strip('"').strip("'")
    if not value or value.startswith("("):
        return None
    if value.lower().startswith("see "):
        return None
    if value.startswith(HTTP_METHODS):
        return None

    if ": " in value:
        left, _right = value.split(": ", 1)
        left = left.strip()
        if "/" in left or left.endswith(PATH_EXTENSIONS):
            value = left

    for sep in (" — ", " – ", " - ", " (", "("):
        if sep in value:
            value = value.split(sep, 1)[0].strip()

    if "#" in value:
        value = value.split("#", 1)[0].strip()

    value = strip_line_range(value)

    value = value.rstrip("/")
    if not value:
        return None
    if value.startswith("config/") and " " in value:
        return None
    if "," in value:
        return None

    ext_match = re.match(rf"^(\S+{EXT_PATTERN})(?:\s|$)", value)
    if ext_match:
        value = ext_match.group(1)
        value = strip_line_range(value)
    elif " " in value:
        first = value.split(" ", 1)[0].strip()
        first = strip_line_range(first)
        if looks_like_file_path(first):
            value = first
        else:
            return None

    value = strip_line_range(value)
    if not looks_like_file_path(value):
        return None
    if re.match(r"^[A-Za-z_]+Controller$", value):
        return None

    return value