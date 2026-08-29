import json
import sys

import yaml

from feature_map.errors import CliError, FeaturesNotFoundError


def emit(data, as_json=False, stream=None):
    stream = stream or sys.stdout
    if as_json:
        json.dump(data, stream, indent=2, default=str)
        stream.write("\n")
    elif isinstance(data, str):
        stream.write(data)
        if not data.endswith("\n"):
            stream.write("\n")
    elif isinstance(data, dict) and "features" in data and len(data) == 1:
        yaml.dump(data, stream, default_flow_style=False)
    else:
        yaml.dump(data, stream, default_flow_style=False, sort_keys=False)


def emit_error(error, as_json=False, stream=None):
    stream = stream or (sys.stdout if as_json else sys.stderr)
    if isinstance(error, CliError):
        message = error.message
        suggestion = error.suggestion
        exit_code = error.exit_code
    elif isinstance(error, FeaturesNotFoundError):
        message = error.message
        suggestion = error.suggestion
        exit_code = 1
    else:
        message = str(error)
        suggestion = None
        exit_code = 1

    if as_json:
        payload = {
            "ok": False,
            "error": message,
            "exit_code": exit_code,
        }
        if suggestion:
            payload["suggestion"] = suggestion
        json.dump(payload, stream, indent=2)
        stream.write("\n")
    else:
        stream.write(f"Error: {message}\n")
        if suggestion:
            stream.write(f"Suggestion: {suggestion}\n")
    return exit_code

