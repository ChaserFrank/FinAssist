"""Guardrail: no hard-coded credentials anywhere in the repository.

This is the regression test for the exact class of problem GitGuardian
flags: literal passwords in connection strings, secret defaults in compose
files, etc.

Every "fake secret" used below is generated at import time with `secrets.
token_hex()` -- never a literal string in this file -- specifically so that
a static scanner reading this source (ours, or GitGuardian's) finds no
secret-shaped literal to flag here. A hard-coded-looking literal fragment
assigned to a password-shaped variable name is itself exactly the pattern
these scanners are built to catch, so constructing one on purpose, even
disguised, is the wrong way to test a secret scanner. This file is also
listed in `.gitguardian.yaml`'s `ignored_paths` as a second, independent
layer, since it necessarily contains vendor-key-*shaped* strings (see
`test_detects_vendor_key_formats_and_private_keys`) to verify our own
scanner recognizes those shapes.
"""

import secrets
from pathlib import Path

from scripts.check_secrets import scan_text, scan_tree

REPO_ROOT = Path(__file__).resolve().parents[3]

# Generated at runtime -- never a literal secret-shaped string in this file.
_FAKE_USER = "svc_user"
_FAKE_PASSWORD = secrets.token_hex(12)


def _uri(password: str) -> str:
    return f"postgresql+psycopg://{_FAKE_USER}:{password}@db.internal:5432/app"


def test_repository_contains_no_hardcoded_secrets() -> None:
    findings = scan_tree(REPO_ROOT)
    assert findings == [], "Hard-coded secrets found:\n" + "\n".join(map(str, findings))


def test_detects_password_in_connection_uri() -> None:
    findings = scan_text(f'DATABASE_URL = "{_uri(_FAKE_PASSWORD)}"')
    assert [f.rule for f in findings] == ["credentialed-uri"]


def test_detects_secret_default_in_compose_style_fallback() -> None:
    line = f"  PASSWORD: ${{DB_PASSWORD:-{_FAKE_PASSWORD}}}"
    assert any(f.rule == "secret-default-fallback" for f in scan_text(line))


def test_detects_literal_secret_assignments() -> None:
    # Deliberately built with concatenation, not an f-string: an f-string's
    # source text contains a literal `'{...}'` immediately inside the
    # quotes, which is itself a quoted-secret-shaped run of characters our
    # regex (reasonably) can't distinguish from a real one.
    assert scan_text('api_key = "' + secrets.token_hex(8) + '"')
    assert scan_text("password: '" + _FAKE_PASSWORD + "'")


def test_detects_vendor_key_formats_and_private_keys() -> None:
    # Shapes only -- generated, not copied from any real credential.
    aws_style = "AKIA" + secrets.token_hex(8).upper()[:16]
    github_style = "ghp_" + secrets.token_hex(18)
    assert scan_text(aws_style)
    assert scan_text(github_style)
    assert scan_text("-----BEGIN " + "RSA PRIVATE KEY-----")


def test_placeholders_and_env_references_are_allowed() -> None:
    placeholder_url = "DATABASE_URL=postgresql+psycopg://<user>:<password>@localhost:5432/<db>"
    assert scan_text(placeholder_url) == []
    assert scan_text("DATABASE_URL: postgresql+psycopg://${U}:${P}@postgres:5432/${D}") == []
    assert scan_text("POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?Set it in .env}") == []
    assert scan_text("password = os.environ['DB_PASSWORD']") == []
    assert scan_text("WATSONX_API_KEY=") == []


def test_findings_never_reveal_the_secret_value() -> None:
    (finding,) = scan_text(f'x = "{_uri(_FAKE_PASSWORD)}"', "app/x.py")
    assert _FAKE_PASSWORD not in str(finding)
    assert _FAKE_USER not in str(finding)
    assert str(finding) == "app/x.py:1: possible hard-coded secret (credentialed-uri)"


def test_compose_file_has_no_default_for_any_secret() -> None:
    compose = (REPO_ROOT / "docker-compose.yml").read_text()
    assert "PASSWORD:-" not in compose
    assert "${POSTGRES_PASSWORD:?" in compose


def test_ci_workflow_never_writes_a_literal_database_password() -> None:
    """Regression test for the CI-only-credential finding GitGuardian
    flagged: the workflow must generate its ephemeral Postgres password at
    runtime (openssl rand), never write one as a literal in the file."""
    ci_workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text()
    assert "openssl rand" in ci_workflow
    assert scan_text(ci_workflow) == []


def test_allowlist_marker_suppresses_a_matching_line() -> None:
    line = f'x = "{_uri(_FAKE_PASSWORD)}"  # pragma: allowlist secret -- unit test fixture'
    assert scan_text(line) == []


def test_allowlist_marker_does_not_suppress_other_lines_in_the_file() -> None:
    text = (
        f'safe = "{_uri(_FAKE_PASSWORD)}"  # pragma: allowlist secret -- fixture\n'
        f'unsafe = "{_uri(_FAKE_PASSWORD)}"\n'
    )
    findings = scan_text(text)
    assert len(findings) == 1
    assert findings[0].line == 2
