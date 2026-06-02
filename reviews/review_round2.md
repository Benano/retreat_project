# Reviewer memo — round 2

**Reviewer:** reviewer agent
**Date:** 2026-06-02
**Scope:** Verifying remediation of round-1 items (3 BLOCKING, 4 SHOULD-FIX, 5 MINOR) against the analyst's claims in `decisions.md` D13/D14.

---

## 1. Reproducibility

- **Headline Wilcoxon W=0, p=0.00390625 reproduces** from
  `analysis/results/exp2_full_n12/paired_stats.json` (`scipy.stats.wilcoxon`,
  default `zero_method='wilcox'`).
- **Per-seed decoder accuracies reproduce** from the saved trial pickles in
  `analysis/results/exp2_full_intsc/{intact,scramble}/` (48 pickles each).
  Running LeaveOneGroupOut + LogisticRegression on the saved features yields
  exactly the published per-seed vectors `intact=[1,1,1,0.75,1,1,1,1,0.75,1,1,1]`,
  `scramble=[0.25,1,0.75,0.75,0.75,0.75,0.75,1,0.5,0.75,0.5,0.75]`.
- **Delivered-signal manipulation check reproduces** from `metrics_rows.json`:
  intact d_rate=14.35, d_gpow=4.02, d_coh=0.89; scramble d_rate=13.28 (−7%),
  d_gpow=3.67 (−9%), d_coh=0.30 (−66%); poisson d_rate=14.25, d_gpow=0.43 (−89%),
  d_coh=0.71 (−20%). Sender rate/power identical to 3 sig figs across conditions.
- **ANOVA reproduces:** `coherence_anova.json` dev F=1.29 p=0.25; full F=68.2,
  p=8.6×10⁻⁴⁸.
- **Calibration full-scale:** peak_hz_per_seed=[42.9, 62.9, 42.9], mean=49.5,
  bimodal, as claimed.
- **Channel test suite passes** (`analysis/tests/test_channels.py`); synthetic
  block_shuffle now preserves 100% of spikes (was ~80% before fix).

**Reproducibility caveat:** the headline directory `exp2_full_n12/` does **not**
contain trial pickles (only `metrics_rows.json`, `summary.json`,
`paired_stats.json`, `run_config.json`). I reproduced the decoder from the parallel
intact+scramble-only directory `exp2_full_intsc/`, which is a separate run
producing identical per-seed accuracies. `exp1_full/` also lacks trial pickles.
The code in `exp2_causal_disruption.py` does now write all pickles (lines 156–162),
so the missing pickles in the headline run reflect what was committed, not a code
defect.

---

## 2. Round-1 item status

| Item | Status | Evidence |
|---|---|---|
| **B1** delivered rate/power not measured | **addressed** | `metrics.summarize_trial` (lines 254–358) adds `delivered_rate_hz`, `delivered_gamma_power`, `delivered_coherence`. At full scale, scramble loses only 7%/9% rate/power vs 66% coherence — clean dissociation. Channel wrap-around in `channels._phase_scramble` (lines 154–183) confirmed to preserve 100% of spikes in synthetic test. |
| **B2** CV-fold SE mislabelled as seed CI | **addressed** | `exp2_causal_disruption.py` (lines 183–203) uses `LeaveOneGroupOut(groups=seed)`; per-seed accuracies are now reported and a paired Wilcoxon is added. (Note: Exp 1 `exp1_phase_tuning.py` lines 174–186 still uses `decode_stimulus` with `StratifiedKFold` — the H1 phase-tuning curve in `exp1_full/summary.json` still has CV-fold SDs, not seed-level. See new issue N2.) |
| **B3** n=4 below spec ≥20 | **partially addressed** | Bumped to n=12. Still below locked ≥20 (D5); analyst flags this as remaining limitation. The effect is significant at p=0.0039 but n=12 is the analyst's compute-budget compromise. |
| **S1** Poisson over-interpretation | **addressed** | D13/D14 now state explicitly that Poisson destroys delivered γ POWER (−89%) but not γ COHERENCE (−20%). Confirmed in metrics_rows. |
| **S2** dev-scale coherence flat across delays | **addressed** | `coherence_anova.json` reports dev F=1.29, p=0.25 (flat) vs full F=68, p≈0 (strong tuning). D13 frames the experiment as only meaningful at full scale. |
| **S3** H1 phase-tuning curve weak at dev | **addressed** | `exp1_full/summary.json` characterises a clean monotonic coherence curve (0.89 → 0.32 across 2–16 ms) and a "plateau then drop" decoding curve. D13 honestly reframes "optimal phase" as "high-decoding plateau". |
| **S4** calibration drift at full scale | **addressed** | `figures/calibration/calibration_full_scale.json` shows peak 49.5 Hz (SD 11.6, bimodal 43/63 Hz). D13 flags as a remaining honest limitation. |
| **M1** stale `n_stimuli: 3` in run_config | **partially addressed** | New runs (`exp2_full_n12/run_config.json`) correctly record `"n_stimuli": 4`. The old `exp1/run_config.json` was not back-corrected (cosmetic). |
| **M2** save ALL trials | **partially addressed (code yes, headline data no)** | Both `exp1_phase_tuning.py:142` and `exp2_causal_disruption.py:157` now save every trial. However the headline directories `exp2_full_n12/` and `exp1_full/` ship **no trial pickles** — decoder is only re-runnable via the parallel `exp2_full_intsc/` directory. Should re-emit pickles for the n=12 headline run, or document that `exp2_full_intsc` is the canonical decoder-source. |
| **M3** chance sanity assertion | **addressed** | `exp2_causal_disruption.py:164` adds the assertion. |
| **M4** Granger max-F over lags | **addressed** | `metrics.granger_causality` (lines 110–146) now uses fixed `lag=5`; `summarize_trial` calls it with `lag=5`. F SDs are now smaller than means in `summary.json` (intact F_sr=100±71, was 163±199). |
| **M5** dedup loop dropped spikes | **addressed** | The wrap-around fix removes the root cause: B1 verifies delivered rate now drops <9% (was ~20%). Dedup loop refactored to push collisions back but no longer the dominant loss mechanism. |

---

## 3. New issues found in round 2

- **N1 (SHOULD-FIX). D14 misstates "every paired difference is positive".**
  In fact the per-seed diff vector is `[0.75, 0, 0.25, 0, 0.25, 0.25, 0.25, 0, 0.25, 0.25, 0.5, 0.25]`: 9 strictly positive, **3 ties**, 0 negative. Wilcoxon's default `zero_method='wilcox'` drops ties, so the effective sample size for the rank test is n=9, not 12. The W=0, p=0.0039 is still correct but the verbal description in D14 ("per-seed difference distribution = {0.50, 0.25, 0.25, 0.50, 0.25, 0.50, ...}, all positive") is inaccurate and should be corrected before the writer quotes it. Per-seed decoder quantization to 0.25 means the 3 ties are at the ceiling (intact=scramble=1.0 or 0.75), which is also informative about the test's resolution.
- **N2 (SHOULD-FIX). H1 (Exp 1) full-scale decoding CIs are still CV-fold SDs, not seed-level.** `exp1_phase_tuning.py` lines 174–186 still call `decode_stimulus` (StratifiedKFold). `decode_acc_n=5` in `exp1_full/summary.json` is folds, not seeds. The H1 figure CIs are not the per-seed quantity B2 demanded. Coherence/ANOVA are seed-level so the headline ANOVA result is fine, but the Exp-1 decoding panel of the headline figure still has the round-1 B2 issue at full scale.
- **N3 (MINOR). The "n=6 → n=12 flip is a power issue" claim is over-interpreted.** Per-seed accuracies for seeds 0–5 in the n=12 run produce mean diff = 0.25, which would have been a strong directional signal at n=6 too. The n=6 result reported in D12 has different per-seed values entirely (intact `[1,1,1,0.75,0.75,0.75]` vs n=12's `[1,1,1,0.75,1,1]` for seeds 0–5). So the n=6 run is not a strict subset of the n=12 run — something else also changed (likely the channel wrap-around fix, or recompute-from-scratch). D14 should say "after the channel fix and rerun, the n=12 result is significant" rather than framing this as a pure-power flip.
- **N4 (MINOR). Headline `exp2_full_n12/` has no trial pickles.** Re-running the decoder from the canonical headline directory alone is impossible. Cleanest fix is to point readers to `exp2_full_intsc/` as the artifact-of-record for decoder re-derivation, or re-emit pickles for the n=12 run.

---

## 4. Verdict

**Ready with caveats.**

The three round-1 BLOCKERS are addressed: B1 is fixed at the channel level
(wrap-around) and the manipulation check is now computed on delivered signals
(rate/power preserved within 9%, coherence collapsed by 66%); B2 is fixed for
the Exp 2 headline (LeaveOneGroupOut + paired Wilcoxon); B3 is partially
addressed (n=12, still under the locked ≥20, but honestly flagged). All
SHOULD-FIX items have substantive responses. The headline numbers
(W=0, p=0.0039; the rate/power/coherence triple check; the full-scale H1 ANOVA
F=68) all reproduce from saved data.

Caveats to carry into the writing phase:

1. **N1**: writer must say "9 of 12 seeds positive, 3 ties, none negative",
   not "all positive". Wilcoxon-with-zeros has effective n=9.
2. **N2**: writer must not quote per-delay CIs on the H1 decoding curve as
   seed-level; either rerun with LOGO or report only ANOVA-on-coherence
   (which is seed-level and clean).
3. **B3 / N3**: n=12 is below the locked ≥20; the "underpowered n=6" framing
   in D14 is a partial explanation only — confounded by the channel fix
   between runs. Limitations section should state both.
4. **M2 / N4**: headline directory missing trial pickles; document
   `exp2_full_intsc/` as the canonical decoder artifact.
5. **S4**: full-scale γ peak is bimodal (43/63 Hz) and 8 Hz below the
   calibration target. Limitations.

The science is sound enough to write; these are presentational fixes the
writer can apply without further analysis work. Not "back to analyst" — there
is no remaining blocker, only honesty edits and one re-emit of pickles if the
analyst wants to fully discharge M2.
