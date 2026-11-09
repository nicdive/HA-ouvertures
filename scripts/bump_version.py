#!/usr/bin/env python3
"""Synchronise la version semver dans manifest.json (+ affichage)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "custom_components" / "ouvertures" / "manifest.json"
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="Version semver, ex: 1.0.1 (sans préfixe v)")
    args = parser.parse_args()
    version = args.version.lstrip("v")
    if not SEMVER.match(version):
        print(f"Version invalide: {version}", file=sys.stderr)
        return 1

    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    previous = data.get("version")
    data["version"] = version
    MANIFEST.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"{MANIFEST.relative_to(ROOT)}: {previous} -> {version}")
    print("Ensuite:")
    print(f"  git commit -am 'chore: release {version}'")
    print(f"  git tag {version}")
    print(f"  git push && git push origin {version}")
    print(f"  gh release create {version} --title {version} --notes-file CHANGELOG.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
