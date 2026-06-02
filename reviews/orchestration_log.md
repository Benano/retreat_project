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

## O3 — Reviewer round 2 (2026-06-02, task #22)

**Agent role:** reviewer (acting via general-purpose subagent), second pass.

**Brief I sent (verbatim summary):** asked the agent to verify whether all
round-1 items (B1/B2/B3 + S1–S4 + M1–M5) were adequately addressed by
re-inspecting `channels.py`, `metrics.py`, `exp2_causal_disruption.py`,
the n=12 paired-stats JSON, the full-scale Exp 1 summary, the coherence
ANOVA JSON, and the full-scale calibration JSON. Told it to re-derive at
least one independent check (e.g. recompute the paired Wilcoxon from
saved per-seed data) and to flag any new issues. Asked specifically about
(1) whether the n=6→n=12 flip is genuinely a power issue, (2) whether
the Poisson interpretation in D14 holds (γ power destroyed but coherence
preserved), (3) whether W=0 really means all paired differences are
positive given LeaveOneGroupOut produces quantized accuracies. Asked for
a round-1 item status table + new-issues section + verdict. Output to
`reviews/review_round2.md`.

**Returned (verbatim summary):**

> Verdict: ready with caveats.
> All three round-1 BLOCKERS substantively addressed:
> - B1 fixed: channel wrap-around preserves 100% of spikes; summarize_trial
>   reports delivered rate/power/coherence (full-scale scramble: rate −7%,
>   power −9%, coherence −66%).
> - B2 fixed for Exp 2: LeaveOneGroupOut + paired Wilcoxon. **Not** fixed
>   for Exp 1 (new issue N2).
> - B3 partially: n=12 still below locked ≥20, honestly flagged.
> All SHOULD-FIX and MINOR items addressed; ANOVA, Wilcoxon, and delivered-
> metric numbers reproduce from saved data.
>
> New caveats:
> - N1: D14's claim "all paired differences positive" is wrong — 9 positive,
>   3 ties (effective Wilcoxon n=9). p=0.0039 still correct.
> - N2: H1 decoding CIs at full scale are CV-fold, not seed-level.
> - N3: "n=6→n=12 flip is purely a power issue" is misleading — per-seed
>   values for seeds 0–5 differ between runs (likely fold-structure also
>   changed).
> - N4: trial pickles missing from headline merged dirs (code now saves
>   them; merged dir didn't inherit).
> - S4 acknowledged: full-scale γ peak 49 Hz, bimodal (43/63), below
>   target.

**Artifacts written:** `reviews/review_round2.md`.

**Reported cost:** ~81k subagent tokens; 27 tool calls; ~3.3 min duration.

**Orchestrator notes:**
- All caveats N1–N4 + S4 are now in `decisions.md` D15 with explicit table.
- N1 (paired-diffs typo) was a real mistake on my part — fixed in D14 of
  decisions.md; verified by re-loading paired_stats.json (9 positive, 3
  ties, 0 negative; W=0; p=0.0039).
- N2 (Exp 1 CIs still CV-fold) is not blocking — the H1 curve is supporting
  evidence, not the headline. Manuscript will describe it as qualitative.
- N3 is honest: I cannot fully attribute the n=6→n=12 flip to power alone;
  flagged in D15.
- N4 is provenance, not correctness: reviewer verified per-seed accuracies
  match between merged `_n12/` summary and source `_intsc/` pickles.
- **Round-2 verdict cleared the writer to start drafting**, with the
  caveats listed in D15 made explicit in Methods/Limitations.

---

---

## O4 — Reviewer round 3 (2026-06-02, task #25)

**Agent role:** reviewer (general-purpose subagent), third pass focused on
the new n=20 Exp 2 numbers and the H3 receiver-oscillation experiment.

**Brief I sent (summary, to be replaced with the actual prompt sent in the
next tool call):** verify the n=20 paired stats reproduce, verify the H3
implementation (disable_oscillation flag in PINGConfig zeroes the right
synapses), verify the H3 result direction (scramble > intact when receiver
oscillation disabled, p=0.011), check that the H3 hyperactive receiver
(60 Hz) interpretation is sound, and weigh in on the H1/H2/H3 synthesis
claim that the model supports the causal CTC reading.

**Returned (verbatim summary):**

> Verdict: READY FOR WRITING. All n=20 Wilcoxon tests reproduce exactly
> (intact-vs-scramble W=12 p=0.0070; scramble-vs-poisson W=0 p=0.00038;
> intact-vs-poisson W=3 p=0.18). H3 reproduces W=11 p=0.011 with 11
> negative diffs (scramble > intact). Delivered rate/power/coherence
> triple check holds. H3 implementation verified: disable_oscillation
> zeroes only g_EI/g_IE on the receiver; sender uses unchanged calibrated
> config. No remaining blocker.
>
> Framing constraints handed to the writer:
> 1. H1 is "plateau-then-drop," not sharp peak; lead with the coherence
>    ANOVA, not per-delay decoder CIs.
> 2. H2 headline = intact-vs-scramble (p=0.0070); scramble-vs-poisson
>    (p=0.00038) is the load-bearing CTC-vs-power dissociation and
>    deserves equal billing. Do NOT claim intact > poisson — both at
>    decoder ceiling, p=0.18.
> 3. H3: report W=11, p=0.011 AND the confound — receiver triples to
>    60 Hz, refractory saturation is a coexisting explanation. Honest
>    reading: "the effect requires an intact receiver E↔I loop; cannot
>    separate rhythmicity from saturation." Do NOT claim H3 proves
>    receiver oscillation is necessary for CTC.
> 4. Synthesis: "consistent with causal CTC, with the caveat that H3
>    does not isolate rhythmicity from saturation." No language
>    stronger than "consistent with."
> 5. Limitations must include, in order: H3 hyperactivity confound,
>    decoder quantization/ties, γ-peak bimodality at full scale, Exp 1
>    CV-fold CIs, skipped parameter sweep and H4.
> 6. Every citation must trace to a source the literature-scout pulled.
> 7. Canonical artifacts: exp2_full_n20/ and exp3_disabled/.
>
> New issues: N5 (H3 saturation confound), N6 (intact-vs-poisson ceiling
> effect), N7 (foreground scramble-vs-poisson), N8 (report effect size
> 0.15 alongside p in H3).

**Artifacts written:** `reviews/review_round3.md`.

**Reported cost:** ~63k subagent tokens; 11 tool calls; ~2.3 min duration.

**Orchestrator notes:** all framing constraints encoded into the writer's
brief below. The H3 saturation confound (N5) is the most important — the
writer must give the rhythmicity vs saturation alternatives equal weight,
not lead with rhythmicity.

---

## O5 — Final verification (2026-06-02, task #19)

**Agent role:** independent verifier (general-purpose subagent).

**Brief I sent (summary):** convert the .docx to markdown with pandoc, audit
every quantitative claim against the saved JSON files, verify every citation
DOI matches the annotated bibliography, verify figure files exist and match
captions, check that all 6 reviewer round-3 framing constraints are honored.
Output to `reviews/final_verification.md` with three tables (numerical claims;
citations; framing constraints) and a final verdict.

**Returned (verbatim summary):**

> Verdict: needs revision — three small mechanical fixes before sharing.
> All H1/H3/calibration/decoder/Wilcoxon numbers match the saved data, and
> all six round-3 framing constraints are honored. Issues found:
> 1. DOI mismatches against annotated bib (CLAUDE.md guardrail 1):
>    - Ref 13: manuscript 10.1016/j.neuron.2024.04.013 → should be .020
>    - Ref 14: manuscript 10.1016/j.tics.2024.07.005 → should be .09.013
> 2. H2 delivered γ-power numbers mis-rounded: 4.02/3.62/0.41 vs saved
>    4.07/3.68/0.43.
> 3. "Granger F dropped from 100 to 0.1" wrong — saved data 92→12.
> All figures exist and match captions; refs 1–12, 15 match exactly;
> manipulation-check rates, coherences, all decoder means/SEs, all paired
> Wilcoxon stats, H1 ANOVA, and calibration numbers all verify cleanly.

**Artifacts written:** `reviews/final_verification.md`.

**Reported cost:** ~54k subagent tokens; 12 tool calls; ~2.2 min duration.

**Orchestrator notes:** all three issues fixed in `drafts/build_manuscript.js`
and the .docx regenerated. Spot-check post-fix: refs 13/14 now show the
corrected DOIs, H2 powers print as 4.07 / 3.68 / 0.43, Granger sentence
reads "92 to 12". Manuscript revalidates clean.

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
