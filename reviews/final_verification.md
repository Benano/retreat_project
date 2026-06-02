# Final independent verification — CTC_causality_paper.docx

Verifier pass on `drafts/CTC_causality_paper.docx` (extracted via
`pandoc --track-changes=all` to `/tmp/manuscript.md`, copied into
`drafts/_manuscript_extracted.md` for inspection). All paths below are
relative to the repo root.

## 1. Numerical claims

| Claim | Manuscript value | Saved value (source) | Status |
|---|---|---|---|
| H2 delivered rate, intact | 14.36 Hz | 14.3626 Hz (`exp2_full_n20/summary.json`) | match |
| H2 delivered rate, scramble | 13.12 Hz | 13.1194 Hz | match |
| H2 delivered rate, poisson | 14.24 Hz | 14.2401 Hz | match |
| H2 delivered γ-power, intact | 4.02 a.u. | 4.0664 a.u. | MISMATCH (paper rounds wrong; should be 4.07) |
| H2 delivered γ-power, scramble | 3.62 a.u. | 3.6836 a.u. | MISMATCH (should be 3.68) |
| H2 delivered γ-power, poisson | 0.41 a.u. | 0.4272 a.u. | MISMATCH (should be 0.43) |
| H2 delivered coherence, intact | 0.89 | 0.8924 | match |
| H2 delivered coherence, scramble | 0.30 | 0.3008 | match |
| H2 delivered coherence, poisson | 0.71 | 0.7103 | match |
| H2 intact decoder | 0.94 ± 0.025 | 0.9375 ± 0.0248 | match (rounded) |
| H2 scramble decoder | 0.78 ± 0.036 | 0.7750 ± 0.0358 | match (rounded) |
| H2 poisson decoder | 0.98 ± 0.017 | 0.9750 ± 0.0172 | match (rounded) |
| H2 intact vs scramble Wilcoxon | W=12, p=0.0070 | W=12.0, p=0.007028 (`paired_stats.json`) | match |
| H2 scramble vs poisson Wilcoxon | W=0, p=0.0004 | W=0.0, p=0.000375 | match |
| H2 intact vs poisson Wilcoxon | W=3, p=0.18 | W=3.0, p=0.17971 | match |
| H2 Granger F drop | "from 100 to 0.1" | intact 92.27 → scramble 11.96 | MISMATCH (should read "from ~92 to ~12", not "to 0.1") |
| H3 intact decoder | 0.74 ± 0.038 | 0.7375 ± 0.0384 (`exp3_disabled/summary.json`) | match |
| H3 scramble decoder | 0.89 ± 0.042 | 0.8875 ± 0.0424 | match |
| H3 paired Wilcoxon | W=11, p=0.011 | W=11.0, p=0.01090 (`exp3_disabled/paired_stats.json`) | match |
| H3 receiver rate | ~60 Hz | intact 60.45, scramble 60.20 | match |
| H1 full-scale ANOVA | F(7,184)=68.2, p<10⁻⁴⁷ | F=68.215, p=8.58e-48 (`exp1_full/coherence_anova.json`) | match |
| H1 dev ANOVA | F=1.29, p=0.25 | F=1.293, p=0.2544 | match |
| H1 coherence sweep range | 0.89 → 0.32 | 0.8927 (2 ms) → 0.3191 (16 ms) | match |
| Calibration dev γ peak | 56 Hz | 56.0 Hz (`calibration_report.json`) | match |
| Calibration dev E→I lag | 3.1 ms | 3.1 ms | match |
| Calibration full peaks | 43, 63, 43 (mean 49.5 ± 11.6) | 42.86, 62.86, 42.86, mean 49.52, sd 11.55 (`calibration_full_scale.json`) | match |
| Calibration full lag | 1.7 ms | 1.7 ms | match |

Three substantive numerical issues:
- **Delivered γ-power triple (4.02 / 3.62 / 0.41)** does not match the saved
  summary (4.07 / 3.68 / 0.43). Two-decimal rounding is off by ~0.02–0.05 a.u.
  in all three conditions and in the same direction; this is consistent with
  the paper having been written against an earlier results file. The
  qualitative claims (±10% rate, ±10% γ-power, 10× γ-power drop in poisson)
  remain correct, but the printed numbers should be regenerated from the
  canonical `exp2_full_n20/summary.json`.
- **"Granger F dropped from 100 to 0.1"** (line 165 of extracted markdown):
  the saved data show 92.27 → 11.96. "0.1" is almost certainly a typo for
  "10". Easy fix.
- All other quantitative claims match the saved data within reported sig figs.

## 2. Citations

DOIs in the manuscript reference list cross-checked against
`literature/annotated_bib.md`.

| Ref # | Manuscript DOI | Bib DOI | Status |
|---|---|---|---|
| 1 | 10.1016/j.tics.2005.08.011 | 10.1016/j.tics.2005.08.011 | match |
| 2 | 10.1016/j.neuron.2015.09.034 | 10.1016/j.neuron.2015.09.034 | match |
| 3 | 10.1126/science.1139597 | 10.1126/science.1139597 | match |
| 4 | 10.1162/neco.2007.07-06-289 | 10.1162/neco.2007.07-06-289 | match |
| 5 | 10.1073/pnas.0809511105 | 10.1073/pnas.0809511105 | match |
| 6 | 10.1371/journal.pcbi.1002760 | 10.1371/journal.pcbi.1002760 | match |
| 7 | 10.1016/j.neuron.2012.06.037 | 10.1016/j.neuron.2012.06.037 | match |
| 8 | 10.1016/j.neuron.2014.12.018 | 10.1016/j.neuron.2014.12.018 | match |
| 9 | 10.1016/j.neuron.2021.09.037 | 10.1016/j.neuron.2021.09.037 | match |
| 10 | 10.1016/j.neuron.2023.03.015 | 10.1016/j.neuron.2023.03.015 | match |
| 11 | 10.1016/j.neuroimage.2023.119998 | 10.1016/j.neuroimage.2023.119998 | match |
| 12 | 10.1016/j.neuroimage.2023.120256 | 10.1016/j.neuroimage.2023.120256 | match |
| 13 | 10.1016/j.neuron.2024.04.013 | 10.1016/j.neuron.2024.04.020 | MISMATCH |
| 14 | 10.1016/j.tics.2024.07.005 | 10.1016/j.tics.2024.09.013 | MISMATCH |
| 15 | 10.1371/journal.pcbi.1011431 | 10.1371/journal.pcbi.1011431 | match |

Two DOI mismatches. Ref 13 (Spyropoulos et al. 2024) and ref 14 (Vinck et
al. 2024 TiCS) have month/page-suffix errors in the manuscript DOI strings.
The bibliography DOIs (`...2024.04.020` and `...2024.09.013`) are the ones
the literature-scout retrieved and recorded; the manuscript values
(`...2024.04.013`, `...2024.07.005`) are not resolvable to those records.
Both need to be corrected against the annotated bib before submission
(CLAUDE.md guardrail 1 explicitly forbids unsourced DOIs).

All four figure callouts (Fig. 1 through Fig. 4) resolve to existing files:
- `figures/fig1_phase_tuning.png` (H1 phase tuning — decoding, coherence, Granger)
- `figures/fig2_causal_test.png` (H2 decoding + coherence)
- `figures/fig3_manipulation_check.png` (delivered rate / γ-power / coherence)
- `figures/fig4_h3.png` (H3 decoding by-condition + receiver rate)

Each filename matches the figure described in-text.

## 3. Framing constraints (reviewer round 3)

| Constraint | Status | Evidence |
|---|---|---|
| H1 leads with ANOVA, not per-delay decoder CIs | honored | Results §H1 opens with "sender↔delivered γ-coherence from 0.89 to 0.32, with a one-way ANOVA … F(7,184)=68.2, p<10⁻⁴⁷"; the decoder curve is described second and explicitly downgraded as "qualitative" in Limitation 4. |
| H2 reports intact-vs-scramble AND scramble-vs-poisson with equal billing | honored | Both contrasts appear with full Wilcoxon stats in the same paragraph; the manuscript explicitly states "the load-bearing test is scramble-vs-Poisson". |
| Does NOT claim intact > poisson (ceiling, not difference) | honored | Manuscript: "statistically indistinguishable from intact (W=3, p=0.18) … The intact-vs-Poisson non-difference reflects ceiling decoding under both conditions and is not interpreted as a positive finding". |
| H3 reports saturation confound with equal weight to rhythmicity reading | honored | H3 contains a dedicated paragraph headed "Important confound." that documents the 60 Hz receiver rate, attributes the reversal to saturation, and concludes "we therefore cannot, from this experiment alone, separate 'rhythm is required for gating' from 'rhythm controls the receiver's dynamic range'". Limitation 1 and Discussion both reiterate. |
| Synthesis uses "consistent with" rather than stronger language | honored | Abstract, Results, and Discussion all use "consistent with"; no instance of "proves", "demonstrates that the brain", "establishes causation" in the text. The Discussion explicitly says "consistent with a causal role … in line with the original CTC proposal" — phrased as compatibility, not proof. |
| Limitations in order: H3 hyperactivity → decoder quantization → γ peak bimodality → Exp 1 CIs → parameter sweep → H4 | honored | Limitations section lists items 1–6 in exactly that order. |

All six framing constraints are honored.

## Final verdict

**Needs revision** — minor edits required before sharing. Blocking issues:

1. **Correct two DOIs.** Ref 13 → `10.1016/j.neuron.2024.04.020`; Ref 14 →
   `10.1016/j.tics.2024.09.013`. Both must match `literature/annotated_bib.md`
   per CLAUDE.md guardrail 1 (no unsourced references).
2. **Re-round three γ-power numbers in H2.** Replace "4.02 → 3.62" with
   "4.07 → 3.68" and "4.02 to 0.41" with "4.07 to 0.43" so the printed
   manipulation-check values match `analysis/results/exp2_full_n20/summary.json`.
3. **Fix the Granger F sentence in H2.** "Granger F dropped from 100 to 0.1"
   should read "Granger F dropped from ~92 to ~12" (or "from 100 to ~10"
   if the author prefers one sig fig).

Non-blocking observations: all other numerical claims, the figure-text
correspondence, and all six round-3 framing constraints are clean. After
the three edits above, the manuscript is ready to share.
