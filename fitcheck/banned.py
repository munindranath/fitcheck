"""The banned-claim gate.

Deliberately dependency-free: no langchain, no pydantic, no network, no model. The
honesty check is the one part of this system that must never be probabilistic, so it
is also the one part you can run and test with nothing installed:

    python3 -m pytest evals/test_tools.py

A banned claim is a number the candidate must never state — wrong, stale, or not theirs
to disclose. On a violation the gate returns the offending string verbatim rather than
paraphrasing it, so the caller can see exactly what tripped and where.

`tools.py` wraps this for the agent. Nothing here knows an agent exists.
"""

from pathlib import Path
from typing import NamedTuple

_STRIP = ("$", "~", ",")
_FILLER = ("approximately", "around", "roughly", "about")


class BannedClaimResult(NamedTuple):
    clean: bool
    violations: list[str]


def _normalize(text: str) -> str:
    """Lowercase and drop the decoration that lets a claim slip past an exact match."""
    out = text.lower()
    for ch in _STRIP:
        out = out.replace(ch, "")
    for word in _FILLER:
        out = out.replace(word, "")
    return out


def check(text: str, banned: list[str]) -> BannedClaimResult:
    """Return the banned claims present in `text`, quoted exactly as configured.

    Matches exactly first, then again with currency symbols, tildes, commas, and
    approximator words removed — so "approximately $180M" still trips "~$180M".
    """
    violations: list[str] = []
    lowered = text.lower()
    normalized_text = _normalize(text)

    for claim in banned:
        if claim in violations:
            continue
        if claim.lower() in lowered or _normalize(claim).strip() in normalized_text:
            violations.append(claim)

    return BannedClaimResult(clean=not violations, violations=violations)


def load_banned_claims(root: Path | None = None) -> list[str]:
    """Read `banned_claims` from the active profile without importing the loader.

    Prefers profile.local.yaml, same as `profile.load_profile`. Uses PyYAML when it is
    available and falls back to a minimal list parser so this module keeps its promise
    of running with nothing installed.
    """
    root = root or Path(__file__).parent.parent
    for name in ("profile.local.yaml", "profile.yaml"):
        path = root / name
        if not path.is_file():
            continue
        try:
            import yaml

            return yaml.safe_load(path.read_text())["candidate"]["banned_claims"]
        except ImportError:
            return _parse_banned_claims(path.read_text())
    raise FileNotFoundError(f"no profile found in {root}")


def _parse_banned_claims(source: str) -> list[str]:
    """Minimal fallback: read the `banned_claims:` block's list items."""
    claims, inside, indent = [], False, 0
    for raw in source.splitlines():
        stripped = raw.strip()
        if not inside:
            if stripped.startswith("banned_claims:"):
                inside, indent = True, len(raw) - len(raw.lstrip())
            continue
        if not stripped or stripped.startswith("#"):
            continue
        if not stripped.startswith("-") or (len(raw) - len(raw.lstrip())) <= indent:
            break
        claims.append(stripped[1:].strip().strip('"').strip("'"))
    return claims
