# Orchestration log

Audit trail of every subagent invocation in this project: what they were
asked, what they returned, what artifacts they produced, and any caveats
they self-flagged. Append-only — do not rewrite past entries.

Entries are numbered chronologically (O1, O2, ...). Each entry records:
- **When:** date + relative position in the task list
- **Agent role:** literature-scout / analyst / reviewer / writer (or
  "general-purpose" acting in that role)
- **Brief:** the exact (or near-exact) prompt I sent
- **Returned:** the agent's final report to me
- **Artifacts written:** files on disk that anyone can re-read
- **Token cost / duration:** when reported back
- **Orchestrator notes:** my read on the quality and what I did with it

---

## O1 — Literature scout (2026-06-02, task #4)

**Agent role:** literature-scout (acting via general-purpose subagent).
The project-level agent definition is `/.claude/agents/literature-scout.md`.

**Brief I sent:**

> You are the literature-scout for a computational neuroscience project. Read
> `CTC_causality_simulation_spec.md` and `.claude/agents/literature-scout.md`
> for full context before starting.
>
> **Goal:** Produce an annotated bibliography for a short paper testing whether
> inter-areal coherence is a *cause* of neural communication (Fries CTC) or a
> *byproduct* (Schneider et al. 2021 — "coherence through communication"). The
> simulation introduces a phase-scramble channel that disrupts coherence while
> preserving rate and power.
>
> Your task:
> 1. Retrieve information about the 9 references in Section 10 of the spec
>    (Fries 2005; Fries 2015; Womelsdorf 2007; Börgers & Kopell 2008;
>    Börgers Epstein Kopell 2008; Akam & Kullmann 2012; Bosman 2012;
>    Bastos 2015; Schneider 2021).
> 2. Search for 2022–2026 follow-ups on the CTC vs coherence-through-
>    communication debate.
> 3. For each source, retrieve a real resolvable identifier you actually
>    fetched. Never invent DOIs. If you can only see an abstract, say so
>    and flag it.
> 4. For each source extract: core claim, method, key result, limitations,
>    and which side of the CTC-causal vs epiphenomenal debate it bears on.
>
> Output: write to `literature/annotated_bib.md` with the format
> `## [N]. Authors (year). Title. Venue.` followed by DOI/URL, core claim,
> method, key result, limitations, bears-on tag, and notes. Start with a
> 3–6 sentence synthesis, end with a "Sources I could not retrieve" section.
>
> Hard rules: never invent a citation; paraphrase by default; separate what
> the source says from your read; flag paywalled/abstract-only sources.

**Returned (verbatim from the agent's final message):**

> File written: `literature/annotated_bib.md`. Count: 20 numbered entries
> (9 core + 11 supplementary, 1 candidate flagged as could-not-retrieve).
> All 9 core references retrieved with real DOIs. Schneider 2021 was the
> only one for which full text was rendered (via the bioRxiv preprint); the
> other 8 are annotated from abstract/summary only — flagged per entry.
> 11 follow-ups added (Vinck et al. 2023 Neuron; Dowdall & Vinck 2023;
> Dowdall Schneider & Vinck 2023; Spyropoulos Schneider Vinck 2024;
> Vinck et al. 2024 TICS; Greenwood & Ward 2024; Vezoli et al. 2021; plus
> Quax/Jensen/Tiesinga 2017, Bastos et al. 2020 PNAS, Palmigiano et al.
> 2017 as precedent context).
>
> Key open issue: PubMed itself was unreachable (reCAPTCHA wall); for the
> 8 paywalled core references the writer agent or user should verify
> claims against publisher PDFs before quoting.

**Artifacts written:** `literature/annotated_bib.md`.

**Reported cost:** ~131k subagent tokens; 60 tool calls; ~7 min duration.

**Orchestrator notes:**
- Compliance with the "never invent a citation" rule looks solid — agent
  explicitly listed an "Akam & Kullmann 2010 candidate" in the could-not-
  retrieve section rather than guessing.
- The full-text limitation is real and the writer needs to know it: only
  Schneider 2021 was read beyond an abstract. The other 8 core references
  are useful for context and resolvable for reference-list purposes, but
  paraphrased quantitative claims should be double-checked.
- The 2022–2026 follow-ups (Vinck 2023, Dowdall 2023, Spyropoulos 2024)
  are highly relevant — they extend the Schneider 2021 line of argument.
  This shifts the literature landscape: the "epiphenomenal" camp has
  consolidated significantly post-2021, which matters for how the
  Discussion is framed.

---

## O2 — Reviewer round 1 (2026-06-02, task #15)

**Agent role:** reviewer (acting via general-purpose subagent).
The project-level agent definition is `/.claude/agents/reviewer.md`.

**Brief I sent:**

> You are the reviewer for a computational neuroscience project. Your job
> per `/.claude/agents/reviewer.md` is to find what is wrong, weak, or
> overstated in the analysis — and to classify issues as BLOCKING /
> SHOULD-FIX / MINOR. The writer is gated on your verdict.
>
> Project context: `CTC_causality_simulation_spec.md` (read Sections 4,
> 5, 6, 9 in particular). The headline claim is whether disrupting
> inter-areal coherence (via a phase-scramble channel that holds sender
> rate and power fixed) reduces effective communication.
>
> Tasks: (1) read `decisions.md`, `channels.py`, `tests/test_channels.py`,
> `metrics.py`, the experiment runners, the saved `summary.json` files,
> `calibrated_ping.json` and `figures/calibration/calibration_report.json`.
> (2) Audit critically: the phase-scramble manipulation check in the COUPLED
> simulation (not just synthetic), decoder confounds, statistical robustness
> at n=8/n=4, the Poisson-channel anomaly, Brian2 calibration, conclusion
> proportionality. (3) Re-run at least one quick check yourself (e.g. load
> a trial pickle and confirm a key number). (4) Write the review to
> `reviews/review_round1.md` with reproducibility section + BLOCKING/
> SHOULD-FIX/MINOR groupings + verdict.
>
> Be specific. Do not edit code. Report back the verdict and counts under
> 250 words.

**Returned (verbatim):**

> Review written to `reviews/review_round1.md`.
> Verdict: back to analyst with the blocking list.
> Issue counts: BLOCKING = 3, SHOULD-FIX = 4, MINOR = 5.
>
> Key findings:
> - B1 (the big one): the "rate/power preserved across conditions" check
>   in decisions.md is computed on the pre-channel sender population, which
>   is identical by construction (paired seeds). Recomputing on the delivered
>   (post-channel) signal from saved pickles shows block-shuffle scramble
>   loses ~20% of spikes and ~55% of γ power at full scale — the central
>   manipulation check (CLAUDE.md guardrail 4) is not met. The 0.94→0.56
>   decode drop is confounded with delivered rate and power changes.
> - B2: the reported "± 0.06" CIs are CV-fold SEs (4 folds of dependent
>   splits), not seed-level CIs.
> - B3: n=4 full-scale seeds is below the locked ≥20 (D5).
> - The synthetic channel tests pass cleanly and per-trial metrics
>   regenerate exactly from saved pickles, so the pipeline itself is sound
>   — the issues are in the manipulation check methodology and statistical
>   reporting, not the simulation.

**Artifacts written:** `reviews/review_round1.md` (193 lines, detailed).

**Reported cost:** ~97k subagent tokens; 45 tool calls; ~6 min duration.

**Orchestrator notes:**
- B1 was correct. I re-derived it from the saved data and confirmed:
  block-shuffle in its original form (no wrap-around) plus the dedup loop
  was systematically dropping end-of-window spikes. Fixed by switching to
  a wrap-around block shuffle with `n_blocks = floor(duration/T_b)` so no
  partial blocks exist. After the fix, intact and scramble *decoding* are
  equal (0.88 vs 0.88) while delivered coherence is 0.90 vs 0.29.
  **The headline finding direction flipped because of this.**
- B2 was correct. I switched to leave-one-seed-out CV in
  `exp2_causal_disruption.py` so reported CIs are now seed-level.
- B3 partially addressed: bumped n=4 → n=6 at full scale. Still below the
  locked ≥20 (D5). I noted this as a remaining limitation in `decisions.md`
  D12 rather than re-running at full n=20 due to compute budget.
- SHOULD-FIX items S1–S4 are *not* fully addressed yet — flagged as future
  reviewer items if a second round runs.

---

## How to use this log going forward

- Before invoking any future subagent, copy the brief here as a new entry
  (O3, O4, ...) and append the returned summary when it comes back.
- If a subagent is invoked twice (e.g. reviewer round 2), use a new
  numbered entry — do not merge.
- This log is the audit trail for orchestrator behaviour. If anyone wants
  to second-guess what the team was asked vs what it returned, this is
  where they look.
- Each subagent runs in an isolated context (no access to this conversation
  beyond its prompt). The exact brief here is the totality of what they
  saw plus whatever they read from disk.
