# Job-Fit Evaluation Skill

**Purpose**: Evaluate job descriptions against a candidate profile to determine fit and make APPLY/SKIP decisions.

**Domain**: Recruitment, job search automation, career management

## Skill Definition

This skill evaluates whether a job posting matches a candidate's profile by:

1. **Extracting role structure** — title, level, company, location, compensation, and critical requirements
2. **Mapping evidence** — connecting each requirement to specific achievements from the candidate's history
3. **Enforcing quality gates** — detecting banned claims (inflated metrics) in any output
4. **Scoring fit** — 1-5 scale with explicit APPLY/SKIP decision rules

## Key Capabilities

### 1. Structured Extraction (`extract_role`)
- Parse unstructured job descriptions into 5 required fields
- Identify exactly 5 "must-have" requirements (not nice-to-haves)
- Extract compensation when present

### 2. Evidence Mapping (`map_evidence`)
- For each must-have, find ONE specific bullet from candidate evidence
- Mark as `gap` if no match (no generic claims allowed)
- For gaps, assess if trainable in 30 days

### 3. Quality Control (`check_banned_claims`)
- Scan all agent output for prohibited metrics
- Exact and fuzzy matching (handles quotes, dollar signs, etc.)
- Hard fail if violations detected

### 4. Fit Scoring (`score_fit`)
- 5: Strong match, all must-haves covered
- 4: Good match, minor gaps
- 3: Moderate, 1-2 trainable gaps → APPLY only if trainable
- 2: Weak, multiple gaps → SKIP
- 1: Poor fit → SKIP

**Additional rules:**
- Listed base < $200k → SKIP
- Banned claims → SKIP

## Guardrails

### Inspection Over Autonomy
- Each tool is separately testable (Pydantic schemas)
- Agent must call all 4 tools in sequence (no shortcuts)
- Decisions are deterministic given tool outputs

### No Hallucination Zone
- Evidence must be exact quotes from `profile.yaml`
- "Generic experience" or vague claims are forbidden
- Gaps acknowledged explicitly rather than papered over

### Hard Compensation Floor
- $200k base is non-negotiable
- Agent cannot rationalize exceptions

## Example Flow

**Input:** Job description for "Senior PM, AI Observability @ Datadog, $200k base"

1. `extract_role` → title="Senior PM, AI Observability", comp="$200k base", 5 must-haves
2. `map_evidence` → map each must-have to candidate bullets or `gap`
3. `check_banned_claims` → scan all tool outputs for violations
4. `score_fit` → score=4 but **decision=SKIP** (comp below floor)

**Output:** "SKIP — base below $200k floor despite strong technical fit"

## When to Use This Skill

✅ **Use when:**
- Automating job screening for a defined candidate profile
- Need explainable APPLY/SKIP decisions
- Compensation floors and quality gates are critical
- Interview/demo scenario where inspectability matters

❌ **Don't use when:**
- Candidate profile is dynamic or changes per query
- Need multi-candidate comparison
- Decision requires human judgment on soft factors (culture fit, growth potential)

## Integration Pattern

```python
from fitcheck.agent import evaluate_job

result = evaluate_job(job_description_text)
# Returns: decision, score, rationale, evidence_map, next_action
```

Trace with LangSmith when `LANGSMITH_API_KEY` is set. Offline mode degrades gracefully (prints structured logs).

## Testing

Evals in `evals/test_agent.py`:
- Strong matches → APPLY
- Comp below floor → SKIP
- Banned claims → SKIP (fails eval)
- 1-2 trainable gaps with score=3 → APPLY

Run: `pytest evals/`

## Design Philosophy

**Skills before agent.** The agent is a thin orchestrator over four inspectable tools. This makes the system:
- Easier to debug (tool I/O is logged)
- Safer to modify (change scoring rules without retraining)
- Interview-ready (show the skill, then show the agent that implements it)

**Typed tools prevent drift.** Pydantic schemas enforce structure. The agent cannot invent new output formats or skip steps.

**Baked-in skepticism.** Banned claims detection prevents the agent from inflating metrics even if the LLM "wants to help" by making the candidate look better.

---

**Skill status:** Production-ready for demo/interview. Not connected to live job boards or candidate databases.
