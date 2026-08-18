"""Typed tools for job-fit agent."""

from typing import Literal, Annotated
from pydantic import BaseModel, Field
from langchain_core.tools import tool, StructuredTool

from .profile import load_profile, format_banned_claims


class ExtractRoleOutput(BaseModel):
    """Extracted role information from job description."""
    title: str = Field(description="Job title")
    level: str = Field(description="Seniority level (e.g., Senior, Principal, Director)")
    company: str = Field(description="Company name")
    location: str = Field(description="Location or remote policy")
    listed_comp: str | None = Field(description="Listed compensation if present, otherwise null")
    must_haves: list[str] = Field(
        description="Exactly 5 critical requirements (skills, experience, domain)",
        min_length=5,
        max_length=5
    )


class EvidenceBullet(BaseModel):
    """One mapped evidence bullet."""
    must_have: str = Field(description="The requirement from the JD")
    evidence: str | Literal["gap"] = Field(
        description="One specific bullet from candidate evidence, or 'gap' if no match"
    )
    trainable_30d: bool | None = Field(
        description="If gap, can it be learned in 30 days? Otherwise null",
        default=None
    )


class MapEvidenceOutput(BaseModel):
    """Mapping of must-haves to evidence."""
    mappings: list[EvidenceBullet] = Field(
        description="One mapping per must-have",
        min_length=5,
        max_length=5
    )


class CheckBannedClaimsOutput(BaseModel):
    """Result of checking for banned claims."""
    clean: bool = Field(description="True if no banned claims detected")
    violations: list[str] = Field(
        description="List of banned claims found in the text (quote exact string)",
        default_factory=list
    )


class ScoreFitOutput(BaseModel):
    """Final fit score and decision."""
    score: Literal[1, 2, 3, 4, 5] = Field(description="Fit score 1-5")
    decision: Literal["APPLY", "SKIP"] = Field(description="Final decision")
    rationale: str = Field(description="One-sentence explanation")
    next_action: str = Field(description="One next step if APPLY, otherwise decline message")


class ExtractRoleInput(BaseModel):
    """Input schema for extract_role tool."""
    job_description: str = Field(description="Full text of the job description")


class MapEvidenceInput(BaseModel):
    """Input schema for map_evidence tool."""
    must_haves: list[str] = Field(description="List of 5 must-have requirements from the JD")
    context: str = Field(default="", description="Additional context if needed")


class ScoreFitInput(BaseModel):
    """Input schema for score_fit tool."""
    role_info: dict = Field(description="Extracted role information")
    evidence_map: list[dict] = Field(description="Evidence mappings")
    banned_check: dict = Field(description="Banned claims check result")


class CheckBannedClaimsInput(BaseModel):
    """Input schema for check_banned_claims tool."""
    text: str = Field(description="Text to check for banned claims")


# Structured tools with explicit schemas

def extract_role_fn(job_description: str) -> str:
    """Extract structured role information from job description.
    
    Parse the JD and return title, level, company, location, compensation,
    and exactly 5 critical must-haves as a structured JSON object.
    """
    # This is implemented by the LLM via tool calling
    return "Tool not implemented - should be called by LLM"


def map_evidence_fn(must_haves: list[str], context: str = "") -> str:
    """Map each must-have requirement to candidate evidence.
    
    For each must-have, return one specific evidence bullet from the candidate
    profile, or 'gap' if no match exists. If gap, assess if trainable in 30 days.
    
    Candidate evidence is provided in the system context.
    """
    # This is implemented by the LLM via tool calling
    return "Tool not implemented - should be called by LLM"


def check_banned_claims_fn(text: str) -> CheckBannedClaimsOutput:
    """Check if text contains any banned claims.
    
    Scans the text for exact or near-exact matches to banned metrics.
    Returns violations list if found.
    
    The banned list is loaded from the active profile's `banned_claims`, never
    hardcoded here — the whole point of the list is that it holds numbers you do not
    want written down in a repo.
    """
    profile = load_profile()
    banned = format_banned_claims(profile)
    
    violations = []
    text_lower = text.lower()
    
    for claim in banned:
        claim_lower = claim.lower()
        # Check for exact or near-exact matches (handle quotes, spaces)
        if claim_lower in text_lower:
            violations.append(claim)
            continue
        
        # Check for approximate matches without special chars
        cleaned_claim = claim_lower.replace("$", "").replace("~", "").replace(",", "").strip()
        cleaned_text = text_lower.replace("$", "").replace("~", "").replace(",", "").replace("approximately", "").replace("around", "")
        
        if cleaned_claim in cleaned_text and claim not in violations:
            violations.append(claim)
    
    return CheckBannedClaimsOutput(
        clean=len(violations) == 0,
        violations=violations
    )


def score_fit_fn(
    role_info: dict,
    evidence_map: list[dict],
    banned_check: dict
) -> str:
    """Score overall fit and make APPLY/SKIP decision.
    
    Scoring rules:
    - 5: Strong match, all must-haves covered
    - 4: Good match, minor gaps
    - 3: Moderate fit, 1-2 trainable gaps
    - 2: Weak fit, multiple gaps
    - 1: Poor fit
    
    Decision rules:
    - 4-5: APPLY
    - 3: APPLY only if gaps are trainable in 30 days
    - 1-2: SKIP
    - Listed base below the profile's compensation.base_floor: SKIP
    - Banned claims present: SKIP
    """
    # This is implemented by the LLM via tool calling
    return "Tool not implemented - should be called by LLM"


# Create structured tools with schemas
extract_role = StructuredTool.from_function(
    func=extract_role_fn,
    name="extract_role",
    description="Extract structured role information from job description including title, level, company, location, compensation, and exactly 5 critical must-haves.",
    args_schema=ExtractRoleInput,
)

map_evidence = StructuredTool.from_function(
    func=map_evidence_fn,
    name="map_evidence",
    description="Map each must-have requirement to candidate evidence. Return one specific evidence bullet from the candidate profile, or 'gap' if no match exists.",
    args_schema=MapEvidenceInput,
)

check_banned_claims = StructuredTool.from_function(
    func=check_banned_claims_fn,
    name="check_banned_claims",
    description="Check if text contains any claim on the candidate's banned-claims list (loaded from their profile). Returns clean=true/false and the violations, quoted exactly.",
    args_schema=CheckBannedClaimsInput,
)

score_fit = StructuredTool.from_function(
    func=score_fit_fn,
    name="score_fit",
    description="Score overall fit (1-5) and make APPLY/SKIP decision based on role info, evidence mapping, and banned claims check.",
    args_schema=ScoreFitInput,
)

# Tool list for agent
TOOLS = [extract_role, map_evidence, check_banned_claims, score_fit]
