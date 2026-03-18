from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from hatchling.version.source.plugin.interface import VersionSourceInterface


_DEFAULT_DESCRIBE: List[str] = [
    "git",
    "describe",
    "--tags",
    "--long",
    "--always",
    "--abbrev=7",
    "--dirty",
    "--match",
    "*[0-9]*",
]

_DEFAULT_TAG_REGEX = r"^(?:v)?(?P<version>\d+(?:\.\d+)*)$"


@dataclass(frozen=True)
class _Describe:
    tag: str
    distance: int
    sha: str
    dirty: bool


_DESCRIBE_RE = re.compile(
    r"^(?P<tag>.+?)-(?P<distance>\d+)-g(?P<sha>[0-9a-f]+)(?P<dirty>-dirty)?$"
)


def _run_git_describe(root: str, argv: List[str]) -> str:
    proc = subprocess.run(
        argv,
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip()


def _parse_describe(output: str) -> _Describe:
    # With --long we expect TAG-N-gSHA[-dirty]
    m = _DESCRIBE_RE.match(output)
    if m:
        return _Describe(
            tag=m.group("tag"),
            distance=int(m.group("distance")),
            sha=m.group("sha"),
            dirty=bool(m.group("dirty")),
        )

    # Fallback: exact tag without --long (or unusual describe output)
    return _Describe(tag=output, distance=0, sha="", dirty=False)


def _extract_version(tag: str, tag_regex: str) -> str:
    m = re.match(tag_regex, tag)
    if not m:
        raise ValueError(f"Tag '{tag}' does not match tag_regex '{tag_regex}'")
    version = m.groupdict().get("version")
    if not version:
        # if user provided a single capture group instead
        if m.groups():
            version = m.group(1)
        else:
            raise ValueError(f"tag_regex '{tag_regex}' must capture a version")
    return version


def _split_semverish(version: str) -> Tuple[str, str, str]:
    parts = version.split(".")
    while len(parts) < 3:
        parts.append("0")
    return parts[0], parts[1], parts[2]


def _format_version(desc: _Describe, tag_regex: str) -> str:
    base = _extract_version(desc.tag, tag_regex)
    major, minor, patch = _split_semverish(base)

    # Keep exact tag on clean checkout.
    if desc.distance == 0 and not desc.dirty:
        return base

    local_parts: List[str] = []
    if desc.sha:
        local_parts.append(f"g{desc.sha[:7]}")
    if desc.dirty:
        local_parts.append("dirty")
    local = f"+{'.'.join(local_parts)}" if local_parts else ""

    if desc.distance == 0:
        # Dirty tag: keep base and append local info.
        return f"{base}{local}"

    # Main rule: if patch is 0, replace it with distance.
    if patch == "0":
        return f"{major}.{minor}.{desc.distance}{local}"

    # Fallback: bump patch by distance to preserve ordering.
    try:
        patch_i = int(patch)
    except ValueError:
        patch_i = 0
    return f"{major}.{minor}.{patch_i + desc.distance}{local}"


class MptGitDescribeVersionSource(VersionSourceInterface):
    """
    Hatchling version source: `source = "mpt-git-describe"`.

    Options (under `[tool.hatch.version]`):
    - `tag_regex`: regex with group `version` to extract base version from tag.
    - `git_describe_args`: list of args for `git describe` (defaults to a safe `--long` form).
    """

    PLUGIN_NAME = "mpt-git-describe"

    def get_version_data(self) -> Dict[str, Any]:
        tag_regex = self.config.get("tag_regex") or _DEFAULT_TAG_REGEX
        argv = self.config.get("git_describe_args") or _DEFAULT_DESCRIBE

        if not isinstance(argv, list) or not all(isinstance(x, str) for x in argv):
            raise TypeError("git_describe_args must be a list of strings")

        output = _run_git_describe(self.root, argv)
        desc = _parse_describe(output)
        version = _format_version(desc, tag_regex)
        return {"version": version, "describe": output}

