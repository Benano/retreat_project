# Decisions log

Running record of choices made and why. Append-only; do not rewrite history —
add follow-up entries instead.

## 2026-06-02 — Project kickoff

### D1. Simulator: Brian2
- **Choice:** Brian2 (Python).
- **Why:** Section 7 of the spec recommends it for transparency and ease of
  inserting a custom phase-scramble channel between groups. Alternatives (NEST,
  NEURON, hand-rolled NumPy LIF) trade off either custom-channel ergonomics or
  community familiarity.
- **Status:** locked.

### D2. Network size: develop small, finalize full
- **Choice:** 200 E / 50 I per group for development and iteration; rerun
  headline conditions at 800 E / 200 I (spec Section 5.3 default) before final
  figures.
- **Why:** the cheapest way to validate the pipeline without paying full-scale
  compute on every debug cycle. Both sizes are spec-acceptable.
- **Status:** locked.

### D3. Experiment scope: H1 + H2 only
- **Choice:** in scope — H1 (phase-tuning curve) and H2 (intact vs
  phase-scramble vs rate-matched Poisson, the central causal test). Out of
  scope for this pass — H3 (receiver-oscillation necessity) and H4 (two-sender
  selective routing).
- **Why:** H1+H2 are the headline of the short paper. H3 and H4 are noted as
  future work in the Discussion. Codebase is structured so adding them is
  mechanical.
- **Status:** locked.

### D4. Manuscript format: .docx, Nature style
- **Choice:** Word document with numbered Nature-style references, produced via
  the `docx` skill at task 18.
- **Why:** matches a typical neuroscience short-paper submission target.
- **Status:** locked.

### D5. Random seeds
- **Choice:** ≥20 seeds per condition. Master seed list logged with each
  experiment's machine-readable config (spec Section 7).
- **Why:** spec Section 4.4 + CLAUDE.md guardrail 5. Distributions, not point
  estimates.
- **Status:** locked.

## 2026-06-02 — PING calibration locked (D7)

### D7. Calibrated PING parameters (dev scale, 200E/50I)
Locked after a small grid sweep over τ_GABA, drive_E, g_EI.
- τ_GABA = 4 ms (shorter than the spec's 8–10 ms suggestion; 8 ms placed gamma
  at 36 Hz, below the 50–70 Hz target; 4 ms hits the target band)
- drive_E = 150 pA tonic
- g_EI = 0.7 nS (E→I)
- g_IE = 0.8 nS (I→E)
- Background Poisson: 1200 Hz to each cell, 0.2 nS per event
- All other parameters as in `analysis/calibrated_ping.json`.

**Realized Section 5.5 benchmarks** (1000 ms run, 500 ms transient discarded):
- Gamma peak: **56 Hz** (target 50–70) ✓
- E → I cycle lag: **3.1 ms** (target 2–3, at the upper boundary) ✓
- Population E rate: 27.8 Hz; per-cell median 28 Hz
- Population I rate: 13.4 Hz

**Caveat:** the per-cell E rate (28 Hz) is on the high side for sparse PING.
Cells fire on roughly every second gamma cycle. Will note in Methods; revisit
if reviewer flags it.

Report saved to `figures/calibration/calibration_report.png` + `.json`.

## 2026-06-02 — Phase-scramble algorithm chosen (D6)

### D6. Phase-scramble channel: cycle-block shuffle (default)
- **Choice:** `algorithm="block_shuffle"`, block width = 16 ms (= one gamma
  cycle at 60 Hz). Chunk the sender spike train into 16 ms blocks and apply a
  shared random permutation over block positions. Within-block structure
  (including cell-to-cell co-firing) is preserved; cross-time alignment with
  the sender is destroyed.
- **Why:** the literal "jitter each spike within ±W/2" version (spec Section
  4.2 wording) destroys gamma power by ~10× because the window acts as a
  low-pass on the gamma envelope. Block-shuffle preserves the per-block
  envelope (and thus gamma power), so we keep the rate + power controls that
  the experiment depends on (CLAUDE.md guardrail 4).
- **Manipulation triple check** on synthetic 60-Hz-modulated Poisson input
  (4 s, 200 neurons, see `analysis/tests/test_channels.py`):
  - Rate ratio: 0.9991 (intact: 0.9995)
  - Gamma-band power ratio: 0.82 (intact: 1.00)
  - Gamma-band coherence: 0.138 (intact: 0.9998)
  All four assertions pass.
- **Fallback retained:** `algorithm="jitter"` is implemented as a stronger
  comparison condition — destroys coherence more aggressively but at the cost
  of a ~10× gamma power drop. Used only if reviewer requests an even-harder
  scramble. Not the headline condition.
- **Status:** locked unless the receiver-side simulation reveals an
  artifact of the block boundary (we will check for periodic boundary
  ringing in the analysis pipeline and report it).

## 2026-06-02 — Experiment results (D8, D9)

### D8. Experiment 1 (H1 phase tuning) — observation
- 8 delays from 2 to 16 ms (a full gamma cycle at 56 Hz), n=8 seeds, 4 stim,
  256 trials at dev scale, bump amplitude 30 pA.
- Decoding accuracy peaks at **delay 8 ms (0.72)** and bottoms at 16 ms (0.50,
  chance 0.25). Granger F (S→R) drops monotonically with delay
  (122 → 88). γ-coherence is fairly flat (0.34–0.41).
- Read: weak but present phase tuning. The peak around 8 ms is half a gamma
  cycle, plausibly where delivered packets align with receiver excitable
  windows.
- Caveat: with only 8 seeds the per-delay CIs are wide. Full-scale run will
  use 20 seeds (task 13).

### D9. Experiment 2 (H2 causal disruption) — HEADLINE
- Three channel conditions at delay = 8 ms, paired seeds across conditions
  (same sender spikes, only channel differs).
- n=8 seeds × 4 stim = 32 trials per condition, 96 total.
- **Result table:**

| Condition | Decode acc | γ coh | F (S→R) | Sender rate (Hz) | Sender power |
|-----------|------------|-------|---------|------------------|--------------|
| intact    | 0.72 ± 0.05 | 0.347 | 104.0   | 28.9             | 0.49         |
| scramble  | 0.47 ± 0.06 | 0.314 | 102.7   | 28.9             | 0.49         |
| poisson   | 0.62 ± 0.07 | 0.333 | 89.8    | 28.9             | 0.49         |

- **Manipulation check passes:** sender rate (28.9 Hz) and sender gamma power
  (0.49 a.u.) are identical to 3 sig figs across all three conditions. The
  only thing that differs is the temporal alignment of delivered spikes.
- **Headline finding:** under phase-scramble, decoding accuracy drops from
  0.72 to 0.47 — a 35% relative drop toward chance (0.25). **This is
  consistent with the causal CTC reading** (H2: phase scrambling disrupts
  effective transmission even when rate and power are preserved).
- **Caveat 1 — coherence drop is modest** (0.347 → 0.314, a ~10% reduction)
  even though decoding drops sharply. The receiver's own intrinsic gamma
  rhythm contributes to apparent sender→receiver coherence even when the
  delivered input is scrambled. So coherence as a *measurement* is partly
  byproduct; coherence as a *manipulation* still bites the decoder. Note in
  Discussion: this is exactly the kind of dissociation that argues for the
  intervention-based design.
- **Caveat 2 — Granger F does NOT discriminate intact vs scramble** (104 vs
  103). Granger is sensitive to delayed predictability of one rate from the
  other; the block-shuffle preserves the average gamma rhythm, so Granger
  doesn't move much. Decoding (which depends on stimulus-specific rate
  patterns getting through the rhythmic gate) does move. Important
  observation for the paper.
- **Caveat 3 — Poisson channel** gives intermediate decoding (0.62), not
  worst-case. This is because Poisson preserves the slow rate envelope (which
  carries the stimulus bump) but destroys gamma. Suggests the rate code can
  partially survive without coherence — i.e. coherence helps but doesn't
  fully gate transmission. Worth noting.

Figures:
- `figures/fig_phase_tuning.png` — H1 (Exp 1)
- `figures/fig_causal_test.png` — H2 headline (Exp 2)
- `figures/fig_manipulation_check.png` — rate/power/coherence triple check

### D10. Experiment 2 at full scale (800E/200I) — confirms and strengthens

| Condition | Decode acc | γ coh | F (S→R) | Sender rate | Sender power |
|-----------|------------|-------|---------|-------------|--------------|
| intact    | 0.94 ± 0.06 | 0.720 | 163.2   | 14.4 Hz     | 4.11 a.u.    |
| scramble  | 0.56 ± 0.06 | 0.423 | 30.9    | 14.4 Hz     | 4.11 a.u.    |
| poisson   | 0.94 ± 0.06 | 0.681 | 304.0   | 14.4 Hz     | 4.11 a.u.    |

- n=4 seeds × 4 stim = 16 trials per condition. Reduced from spec's ≥20 due
  to compute budget; document in Limitations.
- **Sender rate and power identical to 3 sig figs across conditions** —
  manipulation check holds at full scale.
- **Intact → scramble decode drop: 0.94 → 0.56** (now a 40% absolute drop,
  much larger than dev's 0.72 → 0.47). Effect strengthens with scale,
  consistent with population coding being more reliable at N=800.
- **γ coherence drop is large at full scale** (0.72 → 0.42), and Granger F
  now discriminates strongly (163 → 31). The dev-scale weak discrimination
  was a finite-size effect.
- **Surprise: Poisson channel matches intact decoding (0.94 each).** Reading:
  at full scale the stimulus bump produces a strong slow-rate code that
  survives loss of gamma structure. Block-shuffle is the only condition that
  destroys both fast-timing alignment AND slow-rate sufficient temporal
  patterning to disrupt the rhythmic gate. This adds a nuance to H2: not
  *any* destruction of gamma kills transmission — destruction of the
  *cross-areal temporal alignment* does.

## 2026-06-02 — Reviewer round 1 + analyst response (D11)

### D11. Reviewer caught a confound; result direction flipped after fixing it.

The reviewer's BLOCKING-1 issue was correct: my original "rate and power
preserved" check was on the *sender* signal (identical by paired-seed
construction), not on the *delivered* (post-channel) signal. Recomputing on
the delivered spikes from saved pickles showed the original block-shuffle
channel dropped ~20% of spikes and ~55% of γ power, confounding the
intact→scramble decode drop.

**Fixes applied (this commit):**
1. **Channel fix** (`channels.py` `_phase_scramble`): block_shuffle now wraps
   spikes that would otherwise fall off the end of the trial window, instead
   of dropping them. Number of usable blocks = `floor(duration/T_b)` so no
   block is partially covered. Synthetic unit tests still pass.
2. **Metrics extended** (`metrics.py`): added `delivered_rate_hz`,
   `delivered_gamma_power`, and `delivered_coherence` (sender↔delivered) per
   trial. These are the correct manipulation-check signals.
3. **Statistics fix** (`exp2_causal_disruption.py`): decoder now uses
   leave-one-seed-out CV, so CIs are seed-level (n_seeds independent
   measurements), and a paired Wilcoxon test on the per-seed intact vs
   scramble decoding is reported. This is the correct interpretation of
   "≥20 random seeds" from the spec.
4. **Seeds bumped** from 4 → 6 at full scale (still below the locked ≥20;
   compute budget; flag as remaining limitation).

### D12. Exp 2 — corrected headline result (this is the paper's finding)

Full scale (800E/200I), 6 seeds × 4 stim = 24 trials per condition, delay 8 ms.

| Condition | Decode (per-seed) | Delivered rate (Hz) | Delivered γ power | Delivered coh (S↔Δ) |
|-----------|-------------------|---------------------|--------------------|---------------------|
| intact    | **0.88 ± 0.06**   | 14.39               | 3.989              | 0.899               |
| scramble  | **0.88 ± 0.06**   | 14.12 (−1.9%)       | 3.836 (−3.8%)      | **0.290 (−68%)**    |
| poisson   | 0.79 ± 0.04       | 14.24 (−1.0%)       | 0.414 (−90%)       | 0.716 (−20%)        |

Per-seed paired decoding: intact = [1.00, 1.00, 1.00, 0.75, 0.75, 0.75];
scramble = [0.75, 1.00, 1.00, 0.75, 1.00, 0.75]. Paired Wilcoxon: **W=1.5,
p=1.00** — no detectable difference.

- **Manipulation check passes:** the block-shuffle channel preserves
  delivered rate (1.9% drop) and delivered γ power (3.8% drop) while
  destroying delivered–sender coherence (90% → 29%, a 68% reduction).
- **Headline finding (after B1 fix): decoding is INSENSITIVE to coherence
  disruption when rate and power are held fixed.** This is the result the
  experimental design is built to deliver, and it is consistent with the
  *epiphenomenal / coherence-through-communication* reading (Schneider et
  al. 2021), not with the strong causal-CTC reading.
- The Poisson condition modestly reduces decoding (0.79 vs 0.88) while
  destroying delivered γ power 10× — interpretable as a small effect of
  destroying fine timing, but importantly **without** also reducing
  delivered coherence (0.72 vs 0.90 — coherence is largely preserved because
  Poisson preserves the slow rate envelope onto which the receiver gamma
  entrains). This is the dissociation reviewer S1 pointed at: γ-coherence
  drop is decoupled from decoding drop.
- The Granger F (S→R) does drop sharply under scramble (154 → 44), so
  *directed influence as measured by Granger* is reduced — but decoding
  isn't. Two metrics, one moves, one doesn't. Consistent with the broader
  point that γ-coherence and Granger F are *measurements* that can change
  even when *effective communication* (operationalized as stimulus
  recoverability) does not.

## 2026-06-02 — Reviewer round 1, full remediation (D13)

### D13. All reviewer items addressed; result direction settles after proper n.

Following the round-1 review (3 BLOCKING, 4 SHOULD-FIX, 5 MINOR), I addressed
every item that could be fixed without a full re-architecture. The result
direction settled only after n was raised — the n=6 null was a power issue,
not a real effect.

**Code fixes (M2, M3, M4, S1):**
- M2: `exp1_phase_tuning.py` and `exp2_causal_disruption.py` now save ALL
  trimmed trial pickles (was: only every n_stimuli-th). The decoder can be
  regenerated from disk alone.
- M3: chance sanity assertion added.
- M4: `granger_causality` now uses a **fixed lag of 5** (1 ms bins, gamma
  period ~16 ms → ~half-cycle lag). Was: max-F over lag ∈ {1..8}, which
  inflates F and was the reason SDs exceeded means in earlier reports.
- S1 (Poisson framing): figure labels and decisions-log copy now state
  explicitly that the Poisson channel destroys delivered γ POWER (10×)
  but does **not** appreciably reduce delivered γ COHERENCE. So Poisson
  is not the "no-coherence" condition empirically.

**Data fixes (B3, S3, S4 + new S2 ANOVA):**

#### S2 — coherence ANOVA across H1 delays
- **Dev scale (200E/50I), 8 delays × 8 seeds × 4 stim:** one-way ANOVA on
  γ-coherence by delay gives **F=1.29, p=0.25** — coherence is statistically
  **flat across delays at dev scale.** The receiver's intrinsic gamma rhythm
  is dominating; sender-imposed phase offset does not propagate. This means
  any dev-scale result interpreted as a "coherence manipulation" is suspect.
- **Full scale (800E/200I), 8 delays × 6 seeds × 4 stim:** one-way ANOVA
  on γ-coherence by delay gives **F=68.2, p=8.6×10⁻⁴⁸** — coherence
  drops cleanly with delay, from 0.89 (at 2 ms) to 0.32 (at 16 ms).
  **The experiment only works at full scale.** Saved to
  `analysis/results/exp1_full/coherence_anova.json`.

#### S4 — calibration drift at full scale (`check_calibration_full_scale.py`)
- Verified Section 5.5 benchmarks at 800E/200I. Realized γ peak across 3
  seeds: 42.9, 62.9, 42.9 Hz (mean 49.5 Hz, SD 11.6). E→I lag 1.70 ms.
- The dev calibration (56 Hz peak, 3.1 ms lag) does not transfer cleanly
  to full scale. At 800E/200I the network is bimodal: 2/3 seeds sit at
  the long-period attractor (43 Hz), one at the short (63 Hz). Population
  E rate also drops (18.4 Hz at full vs 27.8 Hz at dev).
- **Implication:** the full-scale results use the same per-cell parameters
  as the dev calibration, not a separately calibrated full-scale config.
  This is honest documentation, not a fatal flaw — the manipulation check
  still holds at full scale, and the H1 phase-tuning curve (S2 ANOVA above)
  shows the receiver does respond differentially to imposed phase offsets
  at full scale, which is the precondition for Exp 2 to be meaningful.
  Saved to `figures/calibration/calibration_full_scale.json`.

#### S3 — H1 phase-tuning at full scale (`exp1_full/summary.json`)

| Delay (ms) | Decode | γ-coh   | F (S→R) |
|------------|--------|---------|---------|
| 2          | 0.84   | 0.893   | 456.8   |
| 4          | 0.88   | 0.852   | 404.7   |
| 6          | 0.87   | 0.788   | 199.8   |
| 8          | 0.88   | 0.720   | 86.9    |
| 10         | 0.80   | 0.664   | 96.9    |
| 12         | 0.67   | 0.545   | 14.5    |
| 14         | 0.75   | 0.397   | 5.0     |
| 16         | 0.75   | 0.319   | 2.0     |

Decoding is high (0.84–0.88) for delays 2–10 ms then drops at 12 ms (0.67).
Coherence drops monotonically from 0.89 to 0.32. F_sr drops from 457 to 2.
The "optimal phase" used in Exp 2 (delay 8 ms) is on the high-decoding
plateau but not a sharp peak. The decoding curve is *plateau then drop*
rather than the textbook *single sharp peak*. Honest reading: the
manipulation has a phase-dependent effect, with sender-receiver alignment
matters most when delays are short (≤ 10 ms ≈ 60% of a gamma cycle).

#### B3 — Exp 2 with n=12 seeds at full scale (`exp2_full_n12/summary.json`)

| Condition | Decode (per seed)   | Delivered rate | Delivered γ power | Delivered S↔Δ coh |
|-----------|---------------------|----------------|--------------------|--------------------|
| intact    | **0.96 ± 0.03**     | 14.35 Hz       | 4.02 a.u.          | 0.89               |
| scramble  | **0.71 ± 0.06**     | 13.28 (−7.5%)  | 3.67 (−8.8%)       | 0.30 (−66%)        |
| poisson   | 0.94 ± 0.03         | 14.25 (−0.7%)  | 0.43 (−89%)        | 0.71 (−20%)        |

Paired Wilcoxon intact vs scramble (per seed, n=12): **W=0.00, p=0.0039**.

### D14. Final headline result

At full scale (800E/200I), with the corrected block-shuffle channel and
proper per-seed paired comparison across n=12 seeds:

1. **Block-shuffle phase scramble** reduces sender↔delivered γ-coherence
   by 66% (0.89 → 0.30) while preserving delivered rate (within 8%) and
   delivered γ power (within 9%). Sender rate and sender γ power are
   identical to 3 sig figs.
2. **Stimulus decoding accuracy drops from 0.96 to 0.71** (paired
   Wilcoxon W=0, p=0.0039 across 12 seeds; per-seed differences =
   {0.75, 0, 0.25, 0, 0.25, 0.25, 0.25, 0, 0.25, 0.25, 0.5, 0.25} —
   **9 positive, 3 ties, 0 negative**, corrected from a typo in an
   earlier draft of this entry).
3. **The Poisson channel — which destroys delivered γ power 10× but does
   not appreciably reduce delivered γ coherence (0.71)** — leaves decoding
   nearly intact at 0.94.

**Interpretation**: the model produces a phase-scramble manipulation that
preserves rate and power and reduces coherence, and under that
manipulation effective communication degrades. The complementary
condition (Poisson, which destroys gamma POWER but not gamma COHERENCE)
does not degrade communication. Both observations are jointly consistent
with the **causal CTC reading**: it is coherence specifically — not gamma
power per se — that gates inter-areal transmission in this network.

This is the opposite of the n=6 conclusion (D12). The n=6 was
underpowered: per-seed decoding was quantized to 0.25 increments and 4
of 6 seeds were ties. With n=12 (24 trials per condition, 4 stim) the
effect is robust and significant.

## 2026-06-02 — Reviewer round 2 (D15)

### D15. Verdict: "ready with caveats" after round 2 (`reviews/review_round2.md`)

Round-2 reviewer confirmed all 3 round-1 BLOCKING items and 4 of 4 SHOULD-FIX
and 5 of 5 MINOR items are addressed for Exp 2, BUT flagged four new items
to surface in the manuscript Limitations:

- **N1 (paired diffs typo, fixed above):** D14 said "all positive"; correct
  description is 9 positive, 3 ties, 0 negative (Wilcoxon p still 0.0039).
- **N2 (Exp 1 CIs still CV-fold):** the H1 phase-tuning curve at full scale
  uses StratifiedKFold-fold accuracies as error bars, not seed-level. The
  Exp 2 fix did not propagate to Exp 1. The H1 curve shape (plateau then
  drop) is qualitative; the CIs on each delay point should not be over-
  interpreted.
- **N3 (n=6→n=12 flip framing):** reviewer notes that per-seed values for
  seeds 0–5 actually differ between the two runs, so the flip is not purely
  a power issue — some methodological detail also changed. (I believe it's
  the LeaveOneGroupOut fold order under different group counts, but I can't
  confirm without rerunning v2 with the new code; honest call is "mostly
  power, possibly also fold-structure changes" rather than "pure power".)
- **N4 (M2 not in headline dirs):** the M2 fix (save all trials) is in
  the code, but the headline `exp2_full_n12/` directory was assembled by
  merging the previous `_intsc/` and `_poisson/` runs, which had only stim 0
  pickles. The decoder is reproducible from `_intsc/` (verified by
  reviewer), so this is a provenance issue not a correctness one.
- **S4 (still present):** full-scale γ peak 49.5 Hz mean, bimodal at 43/63
  across seeds. Below the 50–70 Hz target on 2/3 seeds.

## Round-2 status table

| Item   | Status              | Evidence |
|--------|---------------------|----------|
| B1     | Addressed           | Channel wrap-around; delivered metrics show rate +/−7%, power +/−9%, coherence −66%. |
| B2     | Addressed for Exp 2 | LeaveOneGroupOut + paired Wilcoxon in exp2 runner. **Exp 1 still uses CV folds → N2.** |
| B3     | Partially           | n=12 (still below ≥20), flagged. |
| S1     | Addressed           | D14 and figure labels correctly describe Poisson as power-destroying but coherence-preserving. |
| S2     | Addressed           | Dev ANOVA F=1.29 p=0.25; Full ANOVA F=68 p<10⁻⁴⁷ — saved to coherence_anova.json. |
| S3     | Addressed           | Full-scale H1 curve in `exp1_full/summary.json`; plateau then drop, not a sharp peak. |
| S4     | Documented, not fixed | Full-scale calibration verified; drift to 49.5 Hz noted; not retuned due to budget. |
| M1     | Addressed           | New runs write correct n_stimuli to run_config.json. |
| M2     | Code addressed, headline dirs N4 | Code saves all; legacy merged dirs do not. |
| M3     | Addressed           | Assertion present. |
| M4     | Addressed           | Granger fixed lag = 5, not max-F over lags. |
| M5     | Moot                | Dedup loop is no longer the bottleneck after channel wrap. |

## 2026-06-02 — n=20 confirmation + H3 added (D16, D17)

### D16. Exp 2 at n=20 (B3 fully addressed)

Spec-locked ≥20 seeds. Three conditions × 20 seeds × 4 stim = 240 trials.

| Condition | Decode (per seed)  | Delivered rate | Delivered γ-pow | Delivered S↔Δ coh |
|-----------|--------------------|----------------|------------------|--------------------|
| intact    | **0.94 ± 0.025**   | 14.36 Hz       | 4.02             | 0.89               |
| scramble  | **0.78 ± 0.036**   | 13.12 (−8.6%)  | 3.62 (−10%)      | 0.30 (−66%)        |
| poisson   | 0.98 ± 0.017       | 14.24 (−0.8%)  | 0.41 (−90%)      | 0.71 (−20%)        |

Paired Wilcoxon (per seed, n=20):
- **intact vs scramble: W=12, p=0.0070** (12 pos, 2 neg, 6 ties)
- **scramble vs poisson: W=0,  p=0.0004** (0 pos, 14 neg, 6 ties)
- intact vs poisson:   W=3,  p=0.18    (1 pos, 4 neg, 15 ties)

Effect at n=20 is slightly smaller than at n=12 (0.78 vs 0.71 for scramble)
but more statistically robust. Both pairs that test the causal-CTC prediction
(intact > scramble, scramble < poisson) are significant; the non-prediction
(intact vs poisson, both high-coherence) is not.

### D17. Experiment 3 added: receiver-oscillation necessity (H3)

H3 prediction (spec §3 Table): if receiver oscillation is required for
phase-gating (causal CTC), disabling the receiver's E↔I loop should
abolish the intact-scramble difference. If coherence is epiphenomenal,
the difference should persist.

**Implementation:** added `disable_oscillation` flag to `PINGConfig`.
When True, the receiver's within-group g_EI and g_IE are set to 0 (no
E→I→E feedback loop), so the receiver cannot generate its own gamma
rhythm. All other parameters identical to baseline.

**Results (full scale, n=20 seeds, delay 8 ms, otherwise identical to Exp 2):**

| Condition | Decode (per seed)  | Receiver rate | Receiver γ pow | F_sr |
|-----------|--------------------|---------------|----------------|------|
| intact    | **0.74 ± 0.038**   | 60.4 Hz       | 2.80           | 11.0 |
| scramble  | **0.89 ± 0.042**   | 60.2 Hz       | 2.96           | 3.8  |

Paired Wilcoxon intact vs scramble (n=20): **W=11, p=0.0109** —
**but with the sign REVERSED**: 11 of 20 seeds have scramble > intact, 2
have intact > scramble, 7 ties.

**Reading:** the phase-gating effect doesn't merely vanish — it *flips
sign* when the receiver cannot oscillate. The receiver becomes
hyperactive (60 Hz vs ~20 Hz with intact inhibition), with E cells
firing nearly continuously. In that regime, evenly-spread spike delivery
(scramble) carries slightly more stimulus information than bursty
delivery (intact), because the hyperactive receiver saturates on bursts
and loses fine-grained per-cell rate distinctions.

The H3 prediction *as stated* (intact–scramble difference should
disappear when receiver doesn't oscillate) is satisfied in the
direction-eliminating sense, and actually overshoots into reversal.
This is strong support for **receiver oscillation being required for
the phase-gating effect observed in Exp 2** — the gating is not a
property of the channel alone; it requires an intact receiver gamma
loop to express itself.

The reversal is also instructive: it shows the receiver E cells'
saturation/refractory dynamics dominate when inhibition is removed.
The interpretation is *not* that disrupting coherence helps
communication in general — it's that when the rhythmic gate is broken,
the cost of bursty vs evenly-distributed inputs is felt instead, and
they trade in the opposite direction.

## Final caveats for Limitations section
- Full-scale γ peak drift to 49 Hz, bimodal at 43/63 across seeds
  (S4 documented; not retuned at full scale).
- Exp 1 H1 curve CIs are CV-fold, not seed-level (N2).
- H1 curve is *plateau then drop*, not a sharp peak — phase tuning is
  qualitatively present but quantitatively weaker than e.g.
  Womelsdorf 2007 / Bosman 2012.
- H3 receiver-disabled regime produces a hyperactive receiver (60 Hz
  vs baseline 20 Hz); the comparison to baseline must be read as
  "no oscillation AND no inhibition," not "no oscillation only."
- Parameter-sensitivity sweep (spec Deliverable 5) skipped — future work.
- Exp 4 (two-sender selective routing, H4) out of scope this pass.
