"""Lightweight, dependency-free secret scanner for this repository.

Purpose: stop hard-coded credentials before they reach git history (and
before GitGuardian flags them). It is a *guardrail*, not a replacement for a
full scanner -- ``.pre-commit-config.yaml`` also wires up gitleaks.

What it flags
-------------
* URIs with an embedded literal password (user, colon, password, at-sign,
  host). Placeholders such as angle-bracket or ``$``-brace forms are fine.
* Password/secret/token/api-key assignments with a literal value
* Compose/shell style fallbacks that give a secret variable a default value
* Well-known vendor key formats and private-key blocks

Suppressing a documented false positive: append ``# pragma: allowlist secret``
(or, in Markdown, place it anywhere on the same line) to a line that matches a
rule but is not a real secret -- a throwaway CI-only credential or a
documentation example of what the scanner looks for. Use sparingly and only
with a comment explaining *why* it is safe; this is an escape hatch for
genuine false positives, not a way to launder a real one.

Safety: findings report file, line and rule only -- **never the matched
value**, so CI logs cannot re-leak what we are trying to catch.

Usage:  python -m scripts.check_secrets [root]     (exit code 1 on findings)
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

_ALLOWLIST_MARKER = "pragma: allowlist secret"

SKIP_DIRS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache",
    ".ruff_cache", "dist", "build", ".idea", ".vscode", "pgdata",
}
SKIP_FILES = {"package-lock.json", ".env"}  # .env is git-ignored local config
SCAN_SUFFIXES = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".yml", ".yaml", ".toml",
    ".ini", ".cfg", ".sh", ".md", ".mjs", ".html", ".mako", "",
}

_PLACEHOLDER_HINTS = (
    "change", "your", "example", "placeholder", "xxxx", "****", "<", "${", "$(",
    "todo", "dummy", "redacted", "fake", "test-only",
)

# (rule name, compiled regex, group holding the secret value or None)
RULES: list[tuple[str, re.Pattern[str], int | None]] = [
    (
        "credentialed-uri",
        # password part excludes < > { } $ so <password> / ${VAR} never match
        re.compile(r"\b[a-z][a-z0-9+.\-]*://[^\s/:@'\"<>${}]+:([^\s/@'\"<>${}]+)@", re.I),
        1,
    ),
    (
        "secret-assignment",
        re.compile(
            r"(?i)\b(?:password|passwd|secret|api[_-]?key|access[_-]?key|token|private[_-]?key)"
            r"[\"']?\s*[:=]\s*[\"']([^\"'\s]{6,})[\"']"
        ),
        1,
    ),
    (
        "secret-default-fallback",
        re.compile(r"\$\{[A-Z0-9_]*(?:PASSWORD|SECRET|TOKEN|KEY)[A-Z0-9_]*:-([^}]+)\}"),
        1,
    ),
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b"), None),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"), None),
    ("openai-style-key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"), None),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b"), None),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"), None),
    ("private-key-block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), None),
    (
        "jwt",
        re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{5,}\b"),
        None,
    ),
]


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    rule: str

    def __str__(self) -> str:  # value intentionally omitted
        return f"{self.path}:{self.line}: possible hard-coded secret ({self.rule})"


def _is_placeholder(value: str) -> bool:
    lowered = value.lower()
    return any(hint in lowered for hint in _PLACEHOLDER_HINTS)


def scan_text(text: str, path: str = "<memory>") -> list[Finding]:
    """Scan a string; return findings (never the secret values)."""
    findings: list[Finding] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if _ALLOWLIST_MARKER in line:
            continue
        for rule, pattern, group in RULES:
            for match in pattern.finditer(line):
                if group is not None and _is_placeholder(match.group(group)):
                    continue
                findings.append(Finding(path, lineno, rule))
    return findings


def scan_tree(root: Path) -> list[Finding]:
    """Scan every text file under ``root`` (skipping vendored/generated dirs)."""
    findings: list[Finding] = []
    for file in sorted(root.rglob("*")):
        if not file.is_file():
            continue
        if any(part in SKIP_DIRS for part in file.relative_to(root).parts):
            continue
        if file.name in SKIP_FILES:
            continue
        if file.suffix not in SCAN_SUFFIXES and not file.name.startswith(".env"):
            continue
        try:
            text = file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        findings.extend(scan_text(text, str(file.relative_to(root))))
    return findings


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    root = Path(args[0]) if args else Path(__file__).resolve().parents[2]
    findings = scan_tree(root)
    for finding in findings:
        print(finding)
    if findings:
        print(f"\n{len(findings)} finding(s). Move secrets to environment variables.")
        return 1
    print("No hard-coded secrets found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
