# Project: Testing the Causal Direction of Communication-Through-Coherence (CTC)

The full project brief lives in `CTC_causality_simulation_spec.md` at the repo
root. Read it before doing anything substantive. This file gives the orchestrating
agent the working rules; the spec gives the science.

## Purpose
A computational neuroscience simulation that asks whether inter-areal coherence
is a *cause* of effective communication (CTC, Fries 2005/2015) or a *byproduct*
of it (Schneider et al., 2021). The novelty is a controllable "phase-scramble
channel" between sender and receiver that disrupts coherence while holding
firing rate and oscillatory power statistically fixed.

Work moves through a pipeline:
brainstorm → literature search → analysis code → review → figures → short paper.
The reviewer is a gate: the writer does not start until the reviewer clears the
analysis (or the analyst has resolved any blocking issues).
The orchestrating agent should decompose tasks and delegate to the specialist
agents in `.claude/agents/` rather than doing everything in one context.

## Field & context
- Field: computational / systems neuroscience (gamma oscillations, inter-areal
  communication).
- Audience for outputs: systems neuroscience peers; a short Nature-style paper
  is the headline deliverable.
- Preferred citation style: Nature (numbered references).
- Preferred language & tone: precise, hedged appropriately, no overclaiming.
  Conclusions are stated as "consistent with / inconsistent with" specific
  manipulations, never as proof about the brain.

## Scope decisions (agreed up-front)
- **Simulator:** Brian2 (Python). The custom phase-scramble channel must be
  insertable as an explicit intermediary between groups.
- **Network size:** develop and iterate at 200 E / 50 I per group; rerun the
  headline conditions at the spec default 800 E / 200 I before the final figures.
- **Experiments in scope:** H1 (phase-tuning curve) and H2 (intact vs
  phase-scramble vs rate-matched Poisson). H3 and H4 are out of scope for this
  pass; note them as future work in Discussion.
- **Manuscript:** `.docx`, Nature-style numbered references, produced via the
  `docx` skill.

## Non-negotiable guardrails
1. **Never fabricate references.** Every citation must trace to a source that was
   actually retrieved in this session by the literature-scout. Include a real,
   resolvable identifier (DOI, arXiv ID, or URL) for each. If a claim cannot be
   sourced, label it as unsupported rather than inventing a reference.
2. **Separate evidence from inference.** Distinguish what a source says from your
   interpretation of it. Flag extrapolation explicitly.
3. **Reproducibility first.** Any numeric result or figure must be backed by code
   that is saved to the repo and re-runnable. Do not report a number you cannot
   regenerate. Fix and log every random seed.
4. **The phase-scramble channel is the experiment.** Its manipulation check
   (rate preserved, power preserved, coherence reduced) must pass unit tests on
   synthetic input before it is wired into the full model, and must be reported
   for every experimental condition. If the triple-check fails, that is the
   result — do not paper over it.
5. **Show uncertainty.** Report assumptions, parameter choices, and limitations
   alongside results — not buried at the end. Use confidence intervals across
   ≥20 random seeds, not point estimates.
6. **Human checkpoint before "done".** Before the writer drafts the paper,
   surface a short summary of decisions, the headline figures, and open
   questions for human sign-off.

## File organization
- `/literature/`   — retrieved sources, extracted claims, annotated bibliography
- `/analysis/`     — simulation code, channels, analysis pipeline, raw results
- `/analysis/results/` — per-experiment outputs (one subfolder per experiment)
- `/reviews/`      — reviewer memos for each analysis round
- `/figures/`      — generated plots (PNG/SVG) plus the script that made each
- `/drafts/`       — paper drafts and the final `.docx`
- `decisions.md`   — running log of choices and why (at repo root)

Name figures so each maps to the script that produced it
(e.g. `fig_phase_tuning.png` ↔ `analysis/exp1_phase_tuning.py`).

## Working style
- Define end-states, then let agents work; prefer outcomes over step-by-step
  micromanagement.
- When delegating, pass each subagent only the context it needs plus a pointer
  to `CTC_causality_simulation_spec.md`.
- Keep a running `decisions.md` log of choices made and why.
- Develop at small scale, validate, then rerun headline conditions at full scale.
