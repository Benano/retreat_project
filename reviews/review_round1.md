# Reviewer memo — round 1

**Reviewer:** reviewer agent
**Date:** 2026-06-02
**Scope:** Experiments 1 & 2 (H1 phase tuning, H2 causal disruption) at dev (200E/50I) and full (800E/200I) scales.

---

## 1. Reproducibility

**Per-trial metrics: yes.** Re-running `summarize_trial` on
`analysis/results/exp2_full/intact/trial_00000.pkl` reproduces every reported number
to ≥3 sig figs (sender_rate 17.68, gamma_coherence 0.896, granger_F_sr 789.7,
sender_gamma_power 6.66, transfer_entropy 0.221). The simulation→metric pipeline is
deterministic given the saved trial pickles.

**Synthetic channel tests: pass.** `python analysis/tests/test_channels.py` exits 0
with all assertions passing on synthetic gamma-modulated Poisson input
(block_shuffle: rate ratio 0.999, gamma power ratio 0.82, gamma coherence 0.138 vs
intact 1.00).

**Headline decoder accuracy from saved pickles: NOT directly reproducible.**
`exp2_causal_disruption.py` writes only one pickle per `n_stimuli` (`if k % n_stimuli == 0`),
so only stim 0 trials are on disk. Decoder accuracy depends on all four stimuli per
seed, so the 0.94 / 0.56 / 0.94 headline cannot be regenerated from the saved pickles
alone — it depends on in-memory trial objects produced during the run. Metrics are
preserved in `metrics_rows.json`, but the trial data underlying the decoder is not.

---

## 2. Issues

### BLOCKING

**B1. The manipulation check in `decisions.md` is measuring the wrong signal.**
`metrics.summarize_trial` computes `sender_rate_hz` and `sender_gamma_power` from
`trial["sender"]["spikes_E_t"]` — the *pre-channel* sender PING population. Across
conditions the sender simulation is identical (paired seeds), so these values are
trivially identical to 3 sig figs. They do not check whether the *delivered*
(post-channel) input to the receiver preserves rate and power. The actual delivered
statistics, computed from `trial["delivered_t"]` in the same pickles:

| Condition (full scale, 4 seeds × 4 stim, transient masked) | Delivered rate (Hz/cell) | Delivered γ power (a.u.) |
|---|---|---|
| intact   | 17.39 ± 0.26 | 6.65 ± 0.12 |
| scramble | **14.01 ± 2.28** | **3.05 ± 2.23** |
| poisson  | 17.33 ± 0.27 | 0.62 ± 0.03 |

Scramble loses ~20% of delivered spikes and ~55% of delivered gamma power relative to
intact at full scale; Poisson destroys gamma power ~10×. CLAUDE.md guardrail 4
requires that rate and power are preserved while coherence is changed. **At full
scale this is not the case.** The intact→scramble decode drop (0.94 → 0.56) is therefore
confounded with a substantial drop in delivered rate and gamma power, exactly the
confounds spec Section 9 warns about. The headline cannot be attributed solely to
coherence disruption from the current data.
**Fix:** (a) report rate/power computed on `delivered_t/i` (not sender) in every
condition table in `decisions.md`; (b) diagnose the spike loss in
`channels.apply_channel` (the per-cell `min_dt=0.11` deduplication loop and the
`(out_t >= 0) & (out_t < duration_ms)` window mask — block shuffle moves
end-of-window blocks earlier and any spike that lands ≥ duration_ms is dropped, and
the deduplication shifts collisions forward); (c) if the spike loss is structural to
block-shuffle, either re-tune (e.g. wrap blocks, raise dt floor in receiver) or add
a rate-matched control decoder (spec Section 9) that conditions on delivered rate
before claiming a causal coherence effect.

**B2. Reported decode-accuracy CIs are CV-fold SEs, not seed-level CIs.**
`decode_stimulus` returns `se_accuracy = std(folds)/√n_folds` across stratified
k-fold splits of the *same* trial set; folds share training data and are not
independent. The "0.94 ± 0.06" and "0.72 ± 0.05" in decisions.md are these
fold-SEs. With 4 seeds × 4 stim = 16 trials at full scale, k=4 folds → each test
fold has 4 trials → accuracies quantized to {0, 0.25, 0.5, 0.75, 1}. The 95% CI
implied by 1.96·SE is `intact=[0.81, 1.06]`, `scramble=[0.44, 0.69]` — these are
not seed-level uncertainty. The spec requires CIs across ≥20 random seeds, not
across CV folds (CLAUDE.md guardrail 5; spec Section 4.4).
**Fix:** compute per-seed decode accuracy (within each seed, decode across the
4 stim × any folding) and report mean ± 95% CI across seeds; or use stratified
group k-fold with groups=seed. With only n=4 seeds at full scale, also add a
paired test (e.g. Wilcoxon signed-rank) on the per-seed intact–scramble difference.

**B3. Full-scale n=4 seeds is below the spec's ≥20 (4.4) and below the locked
project decision D5 (≥20).** decisions.md notes this as an "Open issue" but the
headline 0.94 → 0.56 result rests on it. At n=4 the per-seed paired difference
distribution cannot reliably be characterised; a single bad seed flips the
headline. The compute-budget appeal does not discharge the guardrail.
**Fix:** add seeds (the dev run reached 8 in a similar wall time; the full run
should at minimum match it, ideally hit ≥20 for the H2 headline conditions).

### SHOULD-FIX

**S1. The Poisson-channel result is over-interpreted.** decisions.md D10 says at
full scale "Poisson channel matches intact decoding (0.94 each)" and concludes
"destruction of the *cross-areal temporal alignment* does [kill transmission]".
But the Poisson channel does **not** appreciably reduce γ-band coherence at
full scale (intact 0.72 vs Poisson 0.68; paired t/Wilcoxon would not separate
them), even though it destroys delivered γ power (0.66 vs intact 6.65). So
Poisson is not a "low-coherence" condition empirically — it is mostly a
low-delivered-γ-power condition that nevertheless preserves the coherence
metric (probably because the receiver's intrinsic γ phase-locks to the slow rate
envelope of the smoothed Poisson input). The current interpretation conflates
"coherence preserved → decoding preserved" with "fine timing destroyed".
**Fix:** state explicitly that the Poisson condition disrupts γ power but not γ
coherence as measured here, and adjust the H2 conclusion: the experiment provides
a clean test only of the block-shuffle case (with the B1 caveats), not a
double-dissociation across both scramble modes.

**S2. The "γ coherence is partly byproduct" caveat at dev scale (D9 caveat 1)
is glossed too quickly.** Dev-scale γ coherence is 0.347 (intact) vs 0.314
(scramble) — a 10% reduction, ANOVA across the 8 delays in Exp 1 yields
F=1.29, p=0.25 (i.e. coherence is flat across phase offsets at dev scale).
Decoding moves 0.72→0.47. A causal-CTC story requires that the manipulated
quantity (coherence) actually changes meaningfully. At dev scale it barely does,
yet the decoder responds strongly. This dissociation is interesting but means
the dev-scale Exp 2 is, mechanistically, not a coherence manipulation experiment
— it is a temporal-alignment manipulation experiment. The Discussion must not
conflate the two.
**Fix:** report this dissociation explicitly, and use the full-scale numbers
(where coherence does drop 0.72→0.42 paired-t p=1.4e-5) as the headline, with
B1 caveats addressed.

**S3. H1 phase-tuning evidence is weak.** Exp 1 dev decoding by delay (with
CV-fold SEs):

```
 2 ms 0.60 [0.49, 0.70]    8 ms 0.72 [0.61, 0.83]   14 ms 0.59 [0.42, 0.76]
 4 ms 0.60 [0.53, 0.66]   10 ms 0.66 [0.52, 0.80]   16 ms 0.50 [0.30, 0.69]
 6 ms 0.60 [0.46, 0.74]   12 ms 0.59 [0.51, 0.68]
```

These are CV-fold CIs (same B2 caveat) but even taken at face value, the curve
is not strikingly "peaked at 8 ms". Adjacent delays (10 ms, 0.66) overlap; the
2/4/6/12/14 cluster sits at 0.59-0.60. Calling this "weak but present phase
tuning" is reasonable for a caveat; using delay = 8 ms as "the optimal phase"
for Exp 2 rests on a noisy single-delay maximum.
**Fix:** either re-run Exp 1 at full scale to characterise the H1 curve, or
treat Exp 2 at 8 ms as "a delay near the apparent dev-scale maximum" rather
than "the optimal phase from Exp 1".

**S4. Calibration regime drifts at full scale.** `calibrated_ping.json` /
`figures/calibration/calibration_report.json` claim a 56 Hz γ peak at dev
scale. In the dev exp2 trials, mean sender peak is 62 Hz (close to calibration).
In the full-scale exp2_full trials, mean sender peak is 48.5 Hz (mostly 43.1 or
51.7 Hz, Welch quantised). At full scale the network oscillates ~8 Hz below the
calibrated value — still inside the 50-70 Hz target (most trials are at 51.7 Hz,
some at 43.1), but the calibration was not redone at full scale and decisions.md
does not flag the drift.
**Fix:** rerun the calibration check at 800E/200I and report the realised
γ peak; or note in Methods/Limitations that the full-scale realised γ peak
sits at the lower end of the calibration band, with 18/48 trials marginally
below 50 Hz.

### MINOR

**M1.** `exp1/run_config.json` records `n_stimuli: 3`, while the underlying
data has 4 stimuli per delay (and decisions.md says 4). The config write looks
like a stale CLI arg snapshot. Cosmetic, but harms reproducibility provenance.

**M2.** `exp2_causal_disruption.py` saves only trial 0 of each `n_stimuli` block,
so only stim=0 trials are on disk. Re-running the decoder from saved pickles
alone is impossible. Either save all trials (disk allowing) or save a per-trial
feature cache (`X, y` per condition) alongside `summary.json`.

**M3.** `decode_stimulus` reports `n_classes` and `chance` but the chance reported
in `summary.json` is recomputed from `1.0/n_stimuli`; with 4 stim that's 0.25 and
correct. Worth a one-line sanity assertion.

**M4.** `metrics.granger_causality` selects the lag with the *highest F* across
`max_lag=8`; this maximises over lags and inflates F. statsmodels'
`grangercausalitytests` is also known to be slow and noisy. Reported `granger_F_sr =
163.2 ± 199.0` (full scale intact) and `304 ± 703` (Poisson) — the SDs exceed
the means, so these point estimates are not informative. The current text
acknowledges Granger isn't the headline; fine, but consider dropping the lag-max
or reporting median + IQR.

**M5.** The dedup loop in `apply_channel` is O(N) Python-level per spike with a
running scalar; works but is the suspect for the scramble spike loss in B1.
Worth profiling/logging dropped-spike counts per call so the manipulation
check can quantify B1's source.

---

## 3. Verdict

**Back to analyst with the blocking list.**

The core experimental claim — that disrupting coherence while holding sender rate
and power fixed reduces transmission — is not currently supported by the saved
data because the rate/power manipulation check (CLAUDE.md guardrail 4) is being
applied to the wrong signal. When recomputed on the delivered (post-channel)
spike train, block-shuffle drops ~20% of spikes and ~55% of γ power at full
scale, which alone could account for the decoder drop. B2 (CV-fold CI mislabelled
as seed CI) and B3 (n=4 at full scale) are independent guardrail issues.

Once B1, B2, B3 are addressed the design and pipeline are otherwise sound:
synthetic channel tests pass cleanly, per-trial metrics reproduce exactly,
paired-seed design at the sender is correct, and the dev-scale qualitative
pattern (block-shuffle reduces decoding much more than Poisson does) is a
genuinely interesting finding worth keeping — once B1 is fixed and the
delivered-signal confounds are quantified.
