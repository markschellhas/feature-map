"""Bounded YAML loading for untrusted repo files.

Feature maps and `.feature-map.yaml` are attacker-controlled when an agent
runs this CLI in a cloned repo. PyYAML's SafeLoader still expands aliases
into recursive object graphs that flatteners (`search`, `check`, …) walk
until they overflow.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from yaml.composer import ComposerError
from yaml.events import AliasEvent
from yaml.loader import SafeLoader

MAX_YAML_BYTES = 512_000
MAX_YAML_NODES = 10_000
MAX_YAML_DEPTH = 40


class BoundedLoader(SafeLoader):
    """SafeLoader that rejects aliases and caps graph size/depth."""

    def __init__(self, stream):
        super().__init__(stream)
        self._node_count = 0
        self._depth = 0

    def compose_node(self, parent, index):
        if self.check_event(AliasEvent):
            event = self.peek_event()
            raise ComposerError(
                None,
                None,
                "YAML aliases are not allowed",
                event.start_mark if event is not None else None,
            )
        if self._node_count >= MAX_YAML_NODES:
            raise ComposerError(None, None, "YAML exceeds complexity limit", None)
        self._node_count += 1
        self._depth += 1
        if self._depth > MAX_YAML_DEPTH:
            raise ComposerError(None, None, "YAML nesting is too deep", None)
        try:
            return super().compose_node(parent, index)
        finally:
            self._depth -= 1


def safe_load(source):
    """Parse YAML with BoundedLoader. Raises yaml.YAMLError on abuse."""
    return yaml.load(source, Loader=BoundedLoader)


def read_text_bounded(path: Path, limit: int = MAX_YAML_BYTES) -> str:
    data = path.read_bytes()
    if len(data) > limit:
        raise yaml.YAMLError(
            "{0} exceeds the {1} byte YAML size limit".format(path.name, limit)
        )
    return data.decode("utf-8")


def read_yaml_file(path: Path, limit: int = MAX_YAML_BYTES):
    """Read a YAML file with a byte cap, then parse it."""
    return safe_load(read_text_bounded(path, limit=limit))
