# Fitcheck

**Interview-ready first agent: skills before autonomy.**

Fitcheck evaluates job descriptions against a hardcoded candidate profile and returns APPLY or SKIP with evidence-backed scoring.

**Skill docs:** [`skills/job-fit/DOCUMENTATION.md`](skills/job-fit/DOCUMENTATION.md)

## Why Skills First?

Traditional agents are black boxes. Fitcheck inverts this:

1. **Four typed tools** (Pydantic schemas) define the skill:
   - `extract_role` — parse JD into structured fields + 5 must-haves
   - `map_evidence` — match each must-have to candidate bullets (or mark as `gap`)
   - `check_banned_claims` — catch inflated metrics in any output
   - `score_fit` — 1-5 score + APPLY/SKIP decision

2. **One agent** orchestrates the tools using LangGraph

3. **Inspectability**: every tool I/O is logged, Pydantic-validated, and separately testable

This means you can debug the skill (tools) independently from the orchestrator (agent).

## Quick Start

```bash
# Clone and install
git clone https://github.com/munindranath/fitcheck
cd fitcheck
pip install -e .

# Set up API keys
cp .env.example .env
# Edit .env: add OPENAI_API_KEY or ANTHROPIC_API_KEY
# (Optional: LANGSMITH_API_KEY for tracing)

# Run on a job description
python -m fitcheck "Senior PM, AI Observability @ Arize, $240k base, requires ML platform experience..."

# Or from a file
python -m fitcheck @examples/langsmith_pm.txt

# Run evals
pytest evals/

# Unit-test the banned-claim gate with no LLM and no API key at all
pytest evals/test_tools.py -v
```

## Project Structure

```
fitcheck/
├── profile.yaml          # Hardcoded candidate profile
├── fitcheck/
│   ├── tools.py          # Four Pydantic-typed tools
│   ├── agent.py          # LangGraph agent (create_react_agent)
│   ├── profile.py        # Profile loader
│   └── __main__.py       # CLI entry point
├── evals/
│   ├── test_agent.py     # ~20 JD test cases
│   └── test_tools.py     # Unit tests (no LLM)
├── skills/
│   └── job-fit/
│       └── SKILL.md      # Skill documentation
└── README.md             # This file
```

## Running it against yourself

The `profile.yaml` in this repo is a **fictional candidate**, so the demo and the evals
run for anyone who clones it. To use your own:

```bash
cp profile.yaml profile.local.yaml   # gitignored
$EDITOR profile.local.yaml
```

The loader prefers `profile.local.yaml` and falls back to the example. Your real
compensation floor and your real banned-claim list never enter version control.

That separation is deliberate, and it is the part most worth copying. A banned-claim
list is a record of numbers you must not state — figures that are wrong, stale, or not
yours to disclose. It only works if you write it candidly, and candid is not the same
as publishable.

## How It Works

### 1. Extract Role
Parse the JD into structured fields:
- title, level, company, location, compensation
- exactly 5 "must-have" requirements (not nice-to-haves)

### 2. Map Evidence
For each must-have, find ONE specific bullet from the candidate's `profile.yaml`:
```yaml
evidence:
  - company: Meridian Software
    bullets:
      - "internal API gateway used by 40+ engineering teams"
      - "migrated 30 services onto OpenTelemetry"
```

If no match: mark as `gap` and assess if trainable in 30 days.

### 3. Check Banned Claims
Scan all outputs for prohibited metrics:
- ~500 customers
- ~$180M
- ~9% churn  
- $4M ARR for Meridian

**Why?** Prevents the agent from inflating metrics even if the LLM "wants to help."

### 4. Score Fit
```
5: Strong match, all must-haves covered → APPLY
4: Good match, minor gaps → APPLY
3: Moderate, 1-2 trainable gaps → APPLY (if trainable)
2: Weak, multiple gaps → SKIP
1: Poor fit → SKIP

Additional rules:
- Listed base < $200k → SKIP
- Banned claims → SKIP
```

## Viewing Traces

If `LANGSMITH_API_KEY` is set in `.env`:

```bash
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_PROJECT=fitcheck
python -m fitcheck "paste JD here"
```

Visit [smith.langchain.com](https://smith.langchain.com) → Projects → fitcheck to see:
- Agent graph execution
- Tool calls with inputs/outputs
- Token usage and latency

**Offline mode**: Works without LangSmith (prints structured logs to console).

## Running Evals

```bash
# Unit tests (no API key required - tests tool logic directly)
pytest evals/test_tools.py -v

# Agent integration tests (requires OPENAI_API_KEY or ANTHROPIC_API_KEY)
pytest evals/test_agent.py -v

# All tests
pytest evals/ -v
```

**Note**: Unit tests pass without any API keys. Integration tests require an API key to run the full agent. Set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` in `.env` before running integration tests.

Test dataset includes:
- **APPLY cases**: LangSmith PM, Arize Principal PM, observability roles at/above $200k floor
- **SKIP cases**: comp below floor, wrong domain (consumer PM), location mismatches
- **Banned claim traps**: JDs that tempt inflated Meridian Software metrics
- **Edge cases**: score=3 with trainable gaps, contract roles, adjacent data-plane positions

## Example Output

```
$ python -m fitcheck "Senior PM, AI Observability @ LangSmith, $230k, requires ML observability experience..."

Evaluating job description...

============================================================
DECISION: APPLY
SCORE: 5/5
RATIONALE: Strong match across all requirements with proven AI platform experience
============================================================

ROLE INFO:
  Title: Senior PM, AI Observability
  Level: Senior
  Company: LangSmith
  Location: Remote
  Comp: $230k - $260k base + equity

EVIDENCE MAPPING:
  1. 5+ years PM in data platforms or observability
     → Meridian Software, Senior PM, Platform, Mar 2022 – Nov 2024
  2. Shipped high-scale data ingestion products
     → polling 30s vs 15min (30x improvement)
  3. Enterprise B2B with $1M+ deals
     → time-to-first-API-call 11 days to under 4 hours
  4. AI/ML operational challenges
     → migrated 30 services onto OpenTelemetry
  5. 0→1 product velocity
     → install to insight under 15 minutes

NEXT ACTION:
  Draft cover letter emphasizing LangSmith alignment with platform observability work
```

## Design Philosophy

**Inspectability over autonomy.**  
Each tool is separately testable. Scoring rules are explicit. The agent doesn't "decide" — it orchestrates typed tools that implement the skill.

**Typed tools prevent drift.**  
Pydantic schemas enforce structure. The agent can't invent new output formats or skip steps.

**Baked-in skepticism.**  
Banned claims detection prevents inflated metrics. Gaps are marked explicitly (no generic claims allowed).

**Skills first, then agent.**  
The skill (`skills/job-fit/SKILL.md`) is the inspectable unit. The agent (`fitcheck/agent.py`) is the implementation.

## Interview Walkthrough

1. **Show the skill** (`skills/job-fit/SKILL.md`) — explain the 4 tools and scoring rules
2. **Show the profile** (`profile.yaml`) — hardcoded candidate data
3. **Run one JD** — `python -m fitcheck @examples/langsmith_pm.txt`
4. **Show a trace** — LangSmith dashboard (tool calls, I/O, reasoning)
5. **Run evals** — `pytest evals/ -v` (show pass/fail on 20 JDs)
6. **Show banned claims working** — run a JD that tempts ~500 customers, watch it get caught

## Limitations (v1)

- **One candidate**: profile is hardcoded in `profile.yaml` (no multi-candidate comparison)
- **No job board integration**: paste JDs manually
- **No cover letters**: returns APPLY/SKIP only (no outreach text generation)
- **No interview prep**: doesn't generate interview stories or prep materials
- **Single agent**: no handoffs, no multi-agent orchestration

## Future Extensions (Not in v1)

- **Dynamic profiles**: load candidate data from resume/LinkedIn API
- **Job board connectors**: poll Indeed/LinkedIn/Ashby for new postings
- **Cover letter generation**: conditional on APPLY decision
- **Interview prep**: generate stories for each evidence bullet
- **Multi-candidate**: compare multiple profiles against one JD

## License

MIT

---

**Built with**: LangGraph • LangSmith • Pydantic • pytest
