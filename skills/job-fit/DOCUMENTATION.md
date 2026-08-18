# Job-Fit Skill Documentation

**Operator documentation for the Fitcheck job-fit evaluation skill.**

## What This Is

One job description → APPLY or SKIP decision backed by evidence.

The skill evaluates a JD against a hardcoded Production AI Reliability PM profile, maps requirements to specific candidate achievements, enforces quality gates (compensation floor, banned claims), and returns a scored verdict.

## When to Use

✅ Use when:
- Screening job postings for a defined candidate profile
- Need explainable APPLY/SKIP with evidence
- Compensation floors and quality gates matter
- Demonstrating inspectable agent design

❌ Don't use when:
- Profile changes per query (this is hardcoded)
- Need multi-candidate comparison
- Decision requires soft judgment (culture fit, growth potential)
- Want cover letters or interview prep (v1 scope: verdict only)

## Input / Output Contract

**Input:**
- Job description (paste or file)

**Output:**
- `decision`: "APPLY" or "SKIP"
- `score`: 1-5
- `rationale`: one-sentence explanation
- `evidence_map`: 5 must-haves → specific candidate bullets or `gap`
- `banned_check`: clean=true/false, violations list
- `next_action`: one next step if APPLY, decline message if SKIP

## Scoring Table

| Score | Meaning | Decision Logic |
|-------|---------|----------------|
| 5 | Strong match, all must-haves covered | APPLY |
| 4 | Good match, minor gaps | APPLY |
| 3 | Moderate fit, 1-2 trainable gaps | APPLY if trainable in 30d |
| 2 | Weak fit, multiple gaps | SKIP |
| 1 | Poor fit | SKIP |

**Additional rules:**
- Listed base < **$200k** → SKIP (hard floor)
- Banned claims detected → SKIP

## Canonical Facts vs Banned Claims

**Canonical facts** (from `profile.yaml`):
- time-to-first-API-call 11 days to under 4 hours (Meridian Software)
- migrated 30 services onto OpenTelemetry
- Team scaled 1 to 5
- Polling latency: 30s (from 15min baseline = 30x improvement)
- Install to insight under 15 minutes

**Banned claims** (agent must never output these):
- ~500 customers ❌
- ~$180M ❌
- ~9% churn ❌
- $4M ARR for Meridian ❌
- $4M ARR for Meridian ❌

The skill's `check_banned_claims` tool scans all output and fails if violations detected.

## How to Run

### CLI

```bash
# Set API key
export ANTHROPIC_API_KEY=sk-ant-...
# or
export OPENAI_API_KEY=sk-...

# Evaluate a JD
python -m fitcheck "Senior PM, AI Observability @ Arize, $240k..."

# Or from file
python -m fitcheck @examples/langsmith_pm.txt
```

### Tests (No LLM Required)

```bash
# Unit tests for banned claims detection
pytest evals/test_tools.py -v

# 6 tests, all pass, no API key needed
```

Integration tests (`evals/test_agent.py`) require an API key and test the full agent on ~20 JDs.

## Interview 60-Second Walk

1. **Show SKILL.md** — "Four typed tools define the skill: extract_role, map_evidence, check_banned_claims, score_fit"
2. **Show profile.yaml** — "Example candidate: Developer Platform PM, $200k floor, Meridian Software — API gateway for 40+ teams"
3. **Run one JD** — `python -m fitcheck @examples/langsmith_pm.txt` → APPLY, score 5, evidence mapped
4. **Show banned-claim tests** — `pytest evals/test_tools.py -v` → 6 passing, catches ~500 customers, ~$180M, etc.

Done. Agent orchestrates tools; tools are separately testable.

## What This Will Not Do

- ❌ Cover letter generation
- ❌ Outreach or interview story generation
- ❌ "Idea Finder" or exploration agents
- ❌ Second agent / handoffs / multi-agent orchestration
- ❌ Career OS / Thrive / Prescient integrations
- ❌ Dynamic profiles (one hardcoded profile only)
- ❌ Job board connectors (manual paste only)

**Scope:** One agent, four tools, one profile. Inspectability first.

## Architecture

```
User pastes JD
    ↓
Agent calls extract_role → 5 must-haves
    ↓
Agent calls map_evidence → must-have → candidate bullet or gap
    ↓
Agent calls check_banned_claims → scan for violations
    ↓
Agent calls score_fit → 1-5 + APPLY/SKIP
    ↓
CLI prints verdict, evidence, next action
```

Each tool has explicit Pydantic schemas. Agent cannot skip steps or invent formats.

## Files

- `fitcheck/tools.py` — four typed tools
- `fitcheck/agent.py` — LangGraph orchestrator
- `fitcheck/__main__.py` — CLI
- `profile.yaml` — candidate data
- `evals/test_tools.py` — unit tests (no LLM)
- `evals/test_agent.py` — integration tests (~20 JDs)
- `skills/job-fit/SKILL.md` — inspectable spec
- `README.md` — interview walkthrough

---

**For implementation details**, see `SKILL.md`.  
**For quickstart**, see `README.md`.
