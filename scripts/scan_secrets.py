"""Fail if tracked files contain AWS-style credentials or private keys, or a tracked .env.

    python scripts/scan_secrets.py     # used by CI and by a test
Heuristic: it catches the common shapes; it is not a substitute for a dedicated scanner.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    "AWS access key id": re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    "AWS secret key assignment": re.compile(
        r"(?i)aws_secret_access_key\s*[=:]\s*['\"]?[A-Za-z0-9/+=]{40}\b"
    ),
    "private key block": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}
SKIP_SUFFIX = {".png", ".jpg", ".jpeg", ".webp", ".ico", ".zip", ".woff", ".woff2", ".lock"}


def tracked_files() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True
    ).stdout.decode()
    return [ROOT / p for p in out.split("\0") if p]


def scan(files: list[Path]) -> list[str]:
    problems: list[str] = []
    for f in files:
        rel = f.relative_to(ROOT).as_posix()
        if f.name == ".env" or (f.name.startswith(".env.") and f.name != ".env.example"):
            problems.append(f"{rel}: environment file is tracked")
        if f.suffix in SKIP_SUFFIX or not f.is_file() or f.name == "scan_secrets.py":
            continue
        text = f.read_text(errors="ignore")
        for label, pat in PATTERNS.items():
            if pat.search(text):
                problems.append(f"{rel}: looks like {label}")
    return problems


if __name__ == "__main__":
    files = tracked_files()
    found = scan(files)
    for p in found:
        print(p, file=sys.stderr)
    print("secret scan:", "FAILED" if found else "clean", f"({len(files)} files)")
    raise SystemExit(1 if found else 0)
