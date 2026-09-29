"""Guardrail: no hard-coded credentials anywhere in the repository.

This is the regression test for the exact class of problem GitGuardian flags:
literal passwords in connection strings, secret defaults in compose files, etc.
Sample "secrets" below are assembled from fragments so this file itself stays
clean and the scanner's finding output can be checked for value leakage.
"""

from pathlib import Path

from scripts.check_secrets import scan_text, scan_tree

REPO_ROOT = Path(__file__).resolve().parents[3]

# fragments -> never a literal secret in this source file
_USER = "svc" + "_user"
_PW = "Zx9" + "qLm2" + "Vt"


def _uri(password: str) -> str:
    return "postgresql+psycopg://" + _USER + ":" + password + "@db.internal:5432/app"


def test_repository_contains_no_hardcoded_secrets() -> None:
    findings = scan_tree(REPO_ROOT)
    assert findings == [], "Hard-coded secrets found:\n" + "\n".join(map(str, findings))


def test_detects_password_in_connection_uri() -> None:
    findings = scan_text(f'DATABASE_URL = "{_uri(_PW)}"')
    assert [f.rule for f in findings] == ["credentialed-uri"]


def test_detects_secret_default_in_compose_style_fallback() -> None:
    line = "  PASSWORD: ${DB_" + "PASSWORD:-" + _PW + "}"
    assert any(f.rule == "secret-default-fallback" for f in scan_text(line))


def test_detects_literal_secret_assignments() -> None:
    assert scan_text('api_key = "' + "abcd" + "1234efgh" + '"')
    assert scan_text("password: '" + _PW + "'")


def test_detects_vendor_key_formats_and_private_keys() -> None:
    assert scan_text("AK" + "IA" + "ABCDEFGHIJKLMNOP")
    assert scan_text("-----BEGIN " + "RSA PRIVATE KEY-----")
    assert scan_text("gh" + "p_" + "a" * 36)


def test_placeholders_and_env_references_are_allowed() -> None:
    placeholder_url = "DATABASE_URL=postgresql+psycopg://<user>:<password>@localhost:5432/<db>"
    assert scan_text(placeholder_url) == []
    assert scan_text("DATABASE_URL: postgresql+psycopg://${U}:${P}@postgres:5432/${D}") == []
    assert scan_text("POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?Set it in .env}") == []
    assert scan_text("password = os.environ['DB_PASSWORD']") == []
    assert scan_text("WATSONX_API_KEY=") == []


def test_findings_never_reveal_the_secret_value() -> None:
    (finding,) = scan_text(f'x = "{_uri(_PW)}"', "app/x.py")
    assert _PW not in str(finding)
    assert _USER not in str(finding)
    assert str(finding) == "app/x.py:1: possible hard-coded secret (credentialed-uri)"


def test_compose_file_has_no_default_for_any_secret() -> None:
    compose = (REPO_ROOT / "docker-compose.yml").read_text()
    assert "PASSWORD:-" not in compose
    assert "${POSTGRES_PASSWORD:?" in compose


def test_allowlist_marker_suppresses_a_matching_line() -> None:
    line = f'x = "{_uri(_PW)}"  # pragma: allowlist secret -- unit test fixture'
    assert scan_text(line) == []


def test_allowlist_marker_does_not_suppress_other_lines_in_the_file() -> None:
    text = (
        f'safe = "{_uri(_PW)}"  # pragma: allowlist secret -- fixture\n'
        f'unsafe = "{_uri(_PW)}"\n'
    )
    findings = scan_text(text)
    assert len(findings) == 1
    assert findings[0].line == 2
