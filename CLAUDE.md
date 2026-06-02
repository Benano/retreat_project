# Project: [Your project / lab name]

## Purpose
This is a scientific research workspace. Work moves through a pipeline:
brainstorm → literature search → analysis code → review → figures → short paper.
The reviewer is a gate: the writer does not start until the reviewer clears the
analysis (or the analyst has resolved any blocking issues).
The orchestrating agent should decompose tasks and delegate to the specialist
agents in `.claude/agents/` rather than doing everything in one context.

## Field & context
- Field: [e.g. computational epidemiology / materials science / ecology]
- Audience for outputs: [e.g. domain peers, a preprint server, an internal report]
- Preferred citation style: [e.g. APA / Nature / IEEE]
- Preferred language & tone: precise, hedged appropriately, no overclaiming.

## Non-negotiable guardrails
1. **Never fabricate references.** Every citation must trace to a source that was
   actually retrieved in this session. Include a real, resolvable identifier
   (DOI, arXiv ID, or URL) for each. If a claim cannot be sourced, label it as
   unsupported rather than inventing a reference.
2. **Separate evidence from inference.** Distinguish what a source says from your
   interpretation of it. Flag extrapolation explicitly.
3. **Reproducibility first.** Any numeric result or figure must be backed by code
   that is saved to the repo and re-runnable. Do not report a number you cannot
   regenerate.
4. **Show uncertainty.** Report assumptions, parameter choices, and limitations
   alongside results — not buried at the end.
5. **Human checkpoint before "done".** Surface a short summary of decisions and
   open questions before producing the final paper draft; do not publish or send
   anything externally.

## File organization
- `/literature/`   — retrieved sources, extracted claims, annotated bib
- `/analysis/`     — code, data, intermediate outputs
- `/reviews/`      — reviewer memos for each analysis round
- `/figures/`      — generated plots (PNG/SVG) + the script that made each
- `/drafts/`       — paper drafts and the final document
Name figures so each maps to the script that produced it (e.g. `fig_sir_curve.png`
↔ `analysis/sir_model.py`).

## Working style
- Define end-states, then let agents work; prefer outcomes over step-by-step
  micromanagement.
- When delegating, pass each subagent only the context it needs.
- Keep a running `decisions.md` log of choices made and why.
