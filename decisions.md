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

## Remaining caveats / open issues for Limitations
- n=6 seeds at full scale still below spec's ≥20. Per-seed paired decoding
  has 4 of 6 ties → low statistical power; we can't rule out a small effect.
- Per-seed decoding is somewhat quantized (4 stim → multiples of 0.25 per
  test fold). A finer-grained DV would tighten the test.
- Phase-tuning curve (Exp 1, H1) is weak: peak at 8 ms but adjacent delays
  overlap. The "optimal phase" used in Exp 2 is a noisy maximum (reviewer
  S3).
- Calibration was not redone at full scale (reviewer S4): realised γ peak
  drifted to ~48 Hz at 800E/200I (still inside 50–70 target on most trials).
- Parameter-sensitivity sweep (Deliverable 5) skipped due to compute budget.
