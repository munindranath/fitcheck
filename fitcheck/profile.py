"""Candidate profile loader."""

from pathlib import Path
from typing import Any
import yaml


def load_profile() -> dict[str, Any]:
    """Load the candidate profile.

    Prefers `profile.local.yaml` (gitignored, your real data) and falls back to
    `profile.yaml` (the fictional example that ships with the repo). This keeps a
    real compensation floor and a real banned-claim list out of version control
    while leaving the repo runnable for anyone who clones it.
    """
    root = Path(__file__).parent.parent
    for name in ("profile.local.yaml", "profile.yaml"):
        candidate = root / name
        if candidate.is_file():
            with open(candidate) as f:
                return yaml.safe_load(f)
    raise FileNotFoundError(
        f"no profile found in {root}: expected profile.local.yaml or profile.yaml"
    )


def format_evidence_for_prompt(profile: dict[str, Any]) -> str:
    """Format evidence section for tool context."""
    evidence = profile["candidate"]["evidence"]
    lines = ["CANDIDATE EVIDENCE:"]
    for exp in evidence:
        company = exp["company"]
        title = exp["title"]
        dates = exp.get("dates", "")
        team = exp.get("team", "")
        
        header = f"- {company}, {title}"
        if team:
            header += f", {team}"
        if dates:
            header += f", {dates}"
        lines.append(header)
        
        for bullet in exp.get("bullets", []):
            lines.append(f"  - {bullet}")
    
    return "\n".join(lines)


def format_banned_claims(profile: dict[str, Any]) -> list[str]:
    """Extract banned claims list."""
    return profile["candidate"]["banned_claims"]
