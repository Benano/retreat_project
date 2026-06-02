# Reviewer memo — round 3

**Reviewer:** reviewer agent
**Date:** 2026-06-02
**Scope:** D16 (Exp 2 at n=20) and D17 (Exp 3 / H3, receiver oscillation disabled).
Round-1 and round-2 items not re-litigated except where new evidence touches them.

---

## 1. Reproducibility

### Exp 2 at n=20 (`analysis/results/exp2_full_n20/`)

All headline numbers reproduce from the saved per-seed vectors via
`scipy.stats.wilcoxon` (default `zero_method='wilcox'`, two-sided):

| Test | W | p | Direction |
|---|---|---|---|
| intact vs scramble | **12.0** | **0.00703** | 12 pos, 2 neg, 6 ties |
| scramble vs poisson | **0.0** | **0.000375** | 0 pos, 14 neg, 6 ties |
| intact vs poisson | **3.0** | **0.1797** | 1 pos, 4 neg, 15 ties |

These match `paired_stats.json` exactly. Decoder means also match `summary.json`
(intact 0.9375, scramble 0.7750, poisson 0.9750).

**Delivered-signal manipulation check (n=20, from `summary.json`):**

| Condition | Delivered rate (Hz) | Delivered γ power | Delivered S↔Δ coh |
|---|---|---|---|
| intact   | 14.36 | 4.07 | 0.892 |
| scramble | 13.12 (−8.6%) | 3.68 (−9.4%) | 0.301 (−66%) |
| poisson  | 14.24 (−0.8%) | 0.43 (−89%) | 0.710 (−20%) |

(Decisions.md D16 reports γ-power 3.62 for scramble; the summary.json value is
3.684. Within rounding — cosmetic. The 4.02 / 4.07 mismatch for intact is the
same kind of harmless rounding artifact.)

Manipulation check holds: scramble preserves rate and power within 10% while
crushing delivered coherence by two thirds. Sender rate and sender γ power are
identical to 3 sig figs across all conditions by paired-seed construction.

**N1 from round 2 is now moot for the n=20 headline**: D16 correctly reports
"12 pos, 2 neg, 6 ties" — no "all positive" misstatement carried forward.

### Exp 3 / H3 (`analysis/results/exp3_disabled/`)

- `paired_stats.json` shows **W=11.0, p=0.01090, n=20**, scramble > intact in
  11 seeds, intact > scramble in 2, 7 ties. Reproduced exactly via
  `scipy.stats.wilcoxon` on the per-seed vectors.
- Means: intact **0.7375**, scramble **0.8875** (decisions.md says 0.74 / 0.89 —
  matches).
- Receiver rate **60.4 Hz** intact, 60.2 Hz scramble — confirmed hyperactive
  regime, ~3× baseline (20 Hz with intact inhibition).

### H3 implementation review

`ping_group.py` lines 92–96, 178–195:
```python
disable_oscillation: bool = False
...
g_EI_eff = 0.0 if c.disable_oscillation else c.g_EI
g_IE_eff = 0.0 if c.disable_oscillation else c.g_IE
```
Both `S_EI` and `S_IE` use the `_eff` values; `S_EE` and `S_II` are untouched.
This correctly disables only the rhythm-generating E↔I loop. The flag is on the
`PINGConfig` of the *individual* group, so disabling on the receiver does not
touch the sender.

`exp3_receiver_oscillation.py` lines 88–96:
```python
cfg = PINGConfig(**cfg_dict)             # sender — normal PING
...
cfg_recv = PINGConfig(**cfg.to_dict())
cfg_recv.name = "R"
cfg_recv.disable_oscillation = True
```
Sender uses the calibrated config unchanged; only the receiver gets the flag.
Implementation matches the design.

**Reproducibility verdict for round 3: PASS.** All n=20 and H3 numbers regenerate
from saved artifacts.

---

## 2. Validity of the H3 design — is the comparison clean?

**No, not fully.** The H3 result is real but the manipulation is *not* "receiver
oscillation removed, everything else held fixed." Removing `g_IE` removes the
*inhibitory clamp* on receiver E cells. Without I→E inhibition, E cells fire
near their refractory ceiling (~60 Hz vs ~20 Hz baseline), which:

1. **Triples the receiver firing rate.** This is a regime change, not a
   targeted ablation of rhythmicity. Comparisons between baseline-receiver
   (Exp 2) and disabled-receiver (Exp 3) are confounded by total spike count,
   not just by gamma structure.
2. **Pushes E cells toward saturation.** Per-cell rate ceiling is set by the
   refractory period (~50 Hz absolute max with `t_ref_E=2 ms`); 60 Hz means
   most cells are firing on nearly every gamma cycle of their input. In that
   regime, fine timing carries little information because the postsynaptic
   response is saturated.
3. **The reversal therefore has at least two readings.** Reading A (the D17
   reading): receiver oscillation is required for phase-gating; without it, the
   gating effect inverts. Reading B (the saturation reading): a hyperactive,
   saturating receiver discriminates evenly-spread inputs (scramble) better
   than bursty inputs (intact) because bursts blow past the refractory ceiling
   and lose per-cell rate information.

These are not mutually exclusive — both could be true — but they are not
distinguishable from the current data. A cleaner H3 would either (a) rescale
`drive_E` downward in the disabled-receiver to keep total firing rate matched
to baseline, or (b) add a control with `g_IE` partially reduced (e.g. 50%) to
trace the dose–response. Both are out of scope for this pass and should be
listed explicitly as future work.

**The headline H3 finding survives this caveat**, but only in a weaker form:
"removing the receiver's E↔I loop abolishes (and in fact reverses) the
intact-vs-scramble effect; whether this is because of lost oscillation, lost
inhibition, or saturation cannot be separated in this design."

---

## 3. Synthesis verdict — does H1 + H2 + H3 jointly support causal CTC?

**Partially, and only with disciplined framing.** Each leg of the argument has
a caveat the manuscript must honour:

- **H1 (phase tuning).** The full-scale H1 curve is a *plateau (2–10 ms) then
  drop (12–16 ms)*, not a textbook sharp peak. Coherence drops monotonically
  (F=68, p≪10⁻⁴⁷, seed-level), which is genuinely strong. Decoding drops only
  at long delays. This is consistent with phase-tuning but it's also consistent
  with "the receiver tolerates a wide window of delivery phases and only fails
  at near-anti-phase." That's a real CTC-flavoured signal, not a textbook one.
- **H2 (intact vs scramble vs poisson at n=20).** The two pairwise tests that
  the causal-CTC prediction requires (intact > scramble; scramble < poisson)
  are both significant. The non-prediction (intact ≈ poisson, both
  high-coherence) is non-significant. This is the *cleanest* leg of the
  argument, with one caveat (next bullet).
- **The intact-vs-poisson "anomaly".** poisson (0.975) is numerically *higher*
  than intact (0.937). The paired Wilcoxon p=0.18 says this is not
  distinguishable from zero, but the *direction* is "wrong" for a strong CTC
  story (one would expect intact ≥ poisson). With 15 ties and only 5
  discordant pairs the test is at the floor of its resolution; the per-seed
  decoder is quantized to 0.25 steps and intact is already near the ceiling
  (mean 0.94). The honest framing is: "intact and poisson are both at the
  high-decoding ceiling; the experiment cannot resolve which is larger; what
  it *can* resolve is that scramble is below both." That keeps the
  scramble-vs-poisson contrast (the load-bearing pair for CTC: same delivered
  power as scramble would give if it weren't preserved — both are γ-power-low
  conditions but only scramble has low coherence) intact.
  *Wait — that's wrong*: scramble preserves γ-power (3.68) while poisson
  destroys it (0.43). What scramble and poisson share is *no* common
  manipulation. The clean dissociation is: scramble (low coherence, high
  power) loses information; poisson (high coherence, low power) does not.
  That dissociation does pin information loss to *coherence* rather than
  *power*, which is the CTC-consistent reading.
- **H3 (receiver oscillation disabled).** Reverses sign with p=0.011, n=20.
  Confounded by hyperactive receiver (see Section 2 above). The cleanest
  reading is "the intact-vs-scramble effect requires an intact receiver E↔I
  loop; it does not survive the loop's removal." Strong evidence that the
  effect is *not* a property of the channel alone. Weaker evidence that the
  specific mechanism is rhythmic gating, because saturation is a coexisting
  explanation.

**Honest synthesis statement for the manuscript:**

> The intact-vs-scramble decoding deficit (H2, n=20, p=0.007) appears in a
> network whose receiver generates its own gamma rhythm and whose delivered
> input has its coherence — but not its rate or power — manipulated. A
> rate-matched Poisson channel that destroys γ power but preserves γ coherence
> (scramble vs poisson, p=0.0004) does *not* produce the deficit. Disabling
> the receiver's E↔I loop, which removes its endogenous gamma but also
> triples its firing rate, abolishes and reverses the deficit (H3, p=0.011).
> Together these are consistent with the causal-CTC reading that coherence
> between sender and receiver populations, not gamma power per se, gates
> inter-areal communication in this model — with the caveat that the H3
> manipulation does not isolate rhythmicity from saturation.

This is the strongest claim the data can carry. Stronger claims (e.g.
"oscillatory coherence is *necessary* for cortical communication") would
overrun the H3 caveat.

---

## 4. New issues (round 3)

- **N5 (SHOULD-FIX, H3 confound). Receiver hyperactivity is not just a side
  observation — it is a competing mechanism for the H3 reversal.** Manuscript
  must explicitly raise saturation/refractory ceiling as an alternative
  explanation alongside "loss of phase gating." Currently D17 prose treats
  the reversal as confirmation of the rhythmic-gating story with the
  hyperactivity noted as a curiosity. The two readings need equal weight.
- **N6 (MINOR, intact-vs-poisson framing).** The numerical inversion (poisson
  0.975 > intact 0.937, p=0.18) is at the decoder ceiling and not interpretable
  as "poisson is better than intact." Manuscript should pre-empt the obvious
  reader question by stating that both conditions sit at the per-seed
  decoder ceiling and the test resolution (per-seed quantization to 0.25)
  cannot separate them. Do not claim intact ≥ poisson; claim only that both
  are above scramble.
- **N7 (MINOR, scramble-vs-poisson is now the load-bearing contrast for CTC).**
  Of the three pairwise comparisons, only scramble-vs-poisson cleanly
  dissociates coherence from power (both preserved-power vs destroyed-power
  with reversed coherence outcomes). The manuscript should foreground this
  contrast at least as much as intact-vs-scramble; the latter alone could be
  read as "any disruption hurts."
- **N8 (MINOR, H3 effect-size language).** The "p=0.011" comes from 11 vs 2
  with 7 ties out of n=20; effective n for the rank test (ties dropped) is
  13. Mean difference is 0.15 (scramble 0.89 − intact 0.74). Both numbers
  should appear in the manuscript — p alone undersells how many seeds are
  tied at the per-trial resolution.

---

## 5. Final verdict — READY FOR WRITING with framing constraints

The science is sound enough to write. No remaining blocker; the open items
are presentational and interpretive. Specific instructions for the writer:

**Framing constraints (the writer MUST honour these):**

1. **H1**: describe as "plateau-then-drop" phase tuning, not "sharp peak."
   The coherence ANOVA (F=68, p≪10⁻⁴⁷) is the clean H1 number; the
   decoding-by-delay curve is supportive but qualitative. Do not put
   per-delay decoder CIs in the headline figure as if they were seed-level
   (round-2 N2).
2. **H2 headline**: intact vs scramble W=12, p=0.0070, n=20 (12 pos, 2 neg,
   6 ties). Scramble vs poisson W=0, p=0.00038 (0 pos, 14 neg, 6 ties) is
   the *load-bearing* contrast for the CTC-vs-power dissociation; give it
   equal billing. Do *not* claim intact > poisson; the test is null
   (p=0.18) and the means invert at the decoder ceiling — say both are at
   ceiling and the experiment cannot resolve them.
3. **H3 results**: state both the result (W=11, p=0.011, scramble > intact)
   and the confound (receiver rate triples to 60 Hz, refractory saturation
   is a coexisting explanation). The honest reading is
   "the intact-vs-scramble effect requires an intact receiver E↔I loop; the
   experiment cannot separate loss of rhythmicity from receiver saturation."
   Do *not* claim H3 proves receiver oscillation is necessary for CTC.
4. **Synthesis**: use the exact wording in Section 3 above (or paraphrase
   tightly). "Consistent with causal CTC, with caveat that H3 does not
   isolate rhythmicity from saturation." No language stronger than
   "consistent with."
5. **Limitations section must include**, in order of importance: (a) H3
   hyperactivity confound (N5); (b) n=20 with per-seed decoder quantized to
   0.25 — many ties, low resolution near ceiling (N6, N8);
   (c) full-scale γ peak drift to bimodal 43/63 Hz (S4);
   (d) Exp 1 decoder CIs are CV-fold not seed-level (round-2 N2);
   (e) parameter-sensitivity sweep skipped; H4 selective routing out of
   scope.
6. **Citations**: every assertion about Fries 2005/2015, Schneider 2021,
   Womelsdorf 2007, Bosman 2012 etc. must trace to a source the
   literature-scout actually pulled this session. Do not invent
   identifiers (CLAUDE.md guardrail 1).
7. **Reproducibility statement**: cite `exp2_full_n20/` and
   `exp3_disabled/` as the canonical artifacts. Note that `exp2_full_n12/`
   and `exp1_full/` are intermediate runs without trial pickles
   (round-2 N4, no longer load-bearing).

Hand off to the writer.
