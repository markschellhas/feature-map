import json
import shlex
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path
from typing import List, Optional

from feature_map._version import __version__
from feature_map.errors import CliError

PIP_PACKAGE = "feature-map-cli"
NPM_PACKAGE = "feature-map-cli"
BREW_FORMULA = "markschellhas/tap/feature-map"
PYPI_JSON_URL = "https://pypi.org/pypi/feature-map-cli/json"
NPM_JSON_URL = "https://registry.npmjs.org/feature-map-cli/latest"
SKILL_HINT = "In each repo that uses Feature Map, run: feature-map init --upgrade-skill"


@dataclass
class InstallOrigin:
    kind: str
    command: List[str] = field(default_factory=list)
    package: str = PIP_PACKAGE
    cwd: Optional[str] = None


def version_key(value):
    text = str(value).strip()
    if text[:1] in ("v", "V"):
        text = text[1:]
    parts = []
    for chunk in text.split("."):
        digits = []
        for ch in chunk:
            if ch.isdigit():
                digits.append(ch)
            else:
                break
        parts.append(int("".join(digits) or "0"))
    return tuple(parts)


def compare_versions(left, right):
    left_key = version_key(left)
    right_key = version_key(right)
    size = max(len(left_key), len(right_key))
    left_key = left_key + (0,) * (size - len(left_key))
    right_key = right_key + (0,) * (size - len(right_key))
    if left_key < right_key:
        return -1
    if left_key > right_key:
        return 1
    return 0


def _normalize(path: Path) -> str:
    return path.as_posix().replace("\\", "/").lower()


def _resolve(path) -> Path:
    try:
        return Path(path).resolve()
    except (OSError, RuntimeError):
        return Path(path)


def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def _npm_root(path: Path) -> Optional[Path]:
    current = path if path.is_dir() else path.parent
    for candidate in [current, *current.parents]:
        pkg_file = candidate / "package.json"
        if not pkg_file.is_file():
            continue
        data = _read_json(pkg_file)
        if not isinstance(data, dict):
            continue
        if data.get("name") == NPM_PACKAGE and candidate.parent.name == "node_modules":
            return candidate
    return None


def _npm_origin(root: Path) -> InstallOrigin:
    node_modules = root.parent
    parent = node_modules.parent
    is_global = parent.name in {"lib", "npm"}
    if is_global:
        return InstallOrigin(
            kind="npm",
            command=["npm", "install", "-g", NPM_PACKAGE + "@latest"],
            package=NPM_PACKAGE,
        )
    cwd = str(_resolve(parent) if node_modules.name == "node_modules" else _resolve(root))
    return InstallOrigin(
        kind="npm",
        command=["npm", "install", NPM_PACKAGE + "@latest"],
        package=NPM_PACKAGE,
        cwd=cwd,
    )


def _from_path(path: Path) -> Optional[InstallOrigin]:
    normalized = _normalize(path)

    if (
        "/cellar/feature-map/" in normalized
        or "/cellar/feature-map-cli/" in normalized
        or "/opt/feature-map/" in normalized
    ):
        return InstallOrigin(
            kind="brew",
            command=["brew", "upgrade", BREW_FORMULA],
            package="feature-map",
        )

    if "/pipx/venvs/" in normalized and "feature-map" in normalized:
        return InstallOrigin(
            kind="pipx",
            command=["pipx", "upgrade", PIP_PACKAGE],
        )

    if "/uv/tools/" in normalized and "feature-map" in normalized:
        return InstallOrigin(
            kind="uv",
            command=["uv", "tool", "upgrade", PIP_PACKAGE],
        )

    npm_root = _npm_root(path)
    if npm_root is not None:
        return _npm_origin(npm_root)
    return None


def _direct_url_is_editable(text: Optional[str]) -> bool:
    if not text:
        return False
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return False
    return bool(data.get("dir_info", {}).get("editable"))


def _distribution():
    try:
        return distribution(PIP_PACKAGE)
    except PackageNotFoundError:
        return None


def detect_installer(
    executable=None,
    script=None,
    dist_direct_url=None,
    dist_present=None,
) -> InstallOrigin:
    exe = _resolve(executable or sys.executable)
    raw_script = script if script is not None else (sys.argv[0] if sys.argv else exe)
    script_path = _resolve(raw_script)

    for path in (exe, script_path):
        origin = _from_path(path)
        if origin is not None:
            return origin

    if dist_direct_url is None and dist_present is None:
        dist = _distribution()
        if dist is not None:
            dist_present = True
            try:
                dist_direct_url = dist.read_text("direct_url.json")
            except Exception:
                dist_direct_url = None
        else:
            dist_present = False

    if _direct_url_is_editable(dist_direct_url):
        return InstallOrigin(kind="source")

    if dist_present:
        python = str(exe) if executable else sys.executable
        return InstallOrigin(
            kind="pip",
            command=[python, "-m", "pip", "install", "--upgrade", PIP_PACKAGE],
        )

    return InstallOrigin(kind="unknown")


def _urlopen(url: str, timeout=15):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "feature-map-cli/" + __version__},
    )
    return urllib.request.urlopen(request, timeout=timeout)


def _http_json(url, urlopen_fn):
    try:
        with urlopen_fn(url) as response:
            return json.load(response)
    except (urllib.error.URLError, OSError, json.JSONDecodeError, TimeoutError, ValueError) as exc:
        raise CliError(
            "Could not look up the latest version: {0}".format(exc),
            suggestion="Check your network and try again.",
        )


def _default_brew_info_runner(command, cwd=None):
    return subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True)


def _brew_latest(runner):
    try:
        result = runner(["brew", "info", "--json=v2", BREW_FORMULA], cwd=None)
    except FileNotFoundError:
        raise CliError(
            "This CLI was installed with Homebrew, but brew is not on PATH.",
            suggestion="Install Homebrew, or reinstall with pip or npm.",
        )
    code = getattr(result, "returncode", 0)
    stdout = getattr(result, "stdout", None) or ""
    if code != 0:
        stderr = (getattr(result, "stderr", None) or "").strip()
        detail = stderr or "brew info failed"
        raise CliError(
            "Could not ask Homebrew for the latest feature-map version: {0}".format(detail),
            suggestion="Try: brew update && brew info {0}".format(BREW_FORMULA),
        )
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise CliError("Homebrew returned invalid JSON: {0}".format(exc))
    formulae = data.get("formulae") or []
    if not formulae:
        raise CliError("Homebrew did not return formula info for {0}.".format(BREW_FORMULA))
    version = (formulae[0].get("versions") or {}).get("stable")
    if not version:
        raise CliError("Homebrew formula has no stable version.")
    return str(version)


def fetch_latest(kind, urlopen_fn=None, brew_runner=None):
    urlopen_fn = urlopen_fn or _urlopen
    if kind == "brew":
        return _brew_latest(brew_runner or _default_brew_info_runner)
    if kind == "npm":
        data = _http_json(NPM_JSON_URL, urlopen_fn)
        version = data.get("version")
    else:
        data = _http_json(PYPI_JSON_URL, urlopen_fn)
        version = (data.get("info") or {}).get("version")
    if not version:
        raise CliError("Latest version was missing from the registry response.")
    return str(version)


def _default_runner(command, cwd=None):
    return subprocess.run(command, cwd=cwd, check=False)


def _payload(origin: InstallOrigin, current, latest, already_latest, updated, message, suggestion=None):
    data = {
        "ok": True,
        "installer": origin.kind,
        "package": origin.package,
        "current_version": current,
        "latest_version": latest,
        "already_latest": already_latest,
        "updated": updated,
        "command": origin.command,
        "message": message,
    }
    if suggestion:
        data["suggestion"] = suggestion
    if origin.cwd:
        data["cwd"] = origin.cwd
    return data


def run_update(
    as_json=False,
    current_version=None,
    origin=None,
    latest_version=None,
    fetch_latest_fn=None,
    runner=None,
    urlopen_fn=None,
):
    current = current_version or __version__
    origin = origin or detect_installer()

    if origin.kind == "unknown":
        raise CliError(
            "Could not detect how feature-map was installed.",
            suggestion=(
                "Reinstall with pip install feature-map-cli, "
                "npm install -g feature-map-cli, or "
                "brew install markschellhas/tap/feature-map."
            ),
        )
    if origin.kind == "source":
        raise CliError(
            "This copy is a source/editable install ({0}); "
            "package managers cannot update it.".format(current),
            suggestion=(
                "pip install feature-map-cli, "
                "npm install -g feature-map-cli, or "
                "brew install markschellhas/tap/feature-map"
            ),
        )

    if latest_version is None:
        fetch = fetch_latest_fn or fetch_latest
        if fetch is fetch_latest:
            latest = fetch(origin.kind, urlopen_fn=urlopen_fn)
        else:
            latest = fetch(origin.kind)
    else:
        latest = latest_version

    comparison = compare_versions(current, latest)
    if comparison >= 0:
        if comparison == 0:
            message = "Already on the latest version ({0}), installed via {1}.".format(
                current, origin.kind
            )
            already = True
        else:
            message = (
                "Installed version {0} is newer than {1} ({2}); nothing to update.".format(
                    current, latest, origin.kind
                )
            )
            already = False
        payload = _payload(origin, current, latest, already, False, message)
        if not as_json:
            sys.stdout.write(payload["message"] + "\n")
        return payload

    if not as_json:
        sys.stdout.write(
            "Updating feature-map from {0} to {1} via {2}...\n".format(
                current, latest, origin.kind
            )
        )
        sys.stdout.write(shlex.join(origin.command) + "\n")
        sys.stdout.flush()

    run = runner or _default_runner
    try:
        result = run(origin.command, cwd=origin.cwd)
    except FileNotFoundError:
        raise CliError(
            "{0} is not on PATH.".format(origin.command[0]),
            suggestion="Install {0} or reinstall feature-map with a different package manager.".format(
                origin.kind
            ),
        )

    code = getattr(result, "returncode", 0)
    if code not in (0, None):
        raise CliError(
            "{0} update failed (exit {1}).".format(origin.kind, code),
            suggestion=shlex.join(origin.command),
        )

    payload = _payload(
        origin,
        current,
        latest,
        False,
        True,
        "Updated from {0} to {1} via {2}.".format(current, latest, origin.kind),
        suggestion=SKILL_HINT,
    )
    if not as_json:
        sys.stdout.write(payload["message"] + "\n")
        sys.stdout.write(payload["suggestion"] + "\n")
    return payload
