# Project Specification: Testing the Causal Direction of Communication-Through-Coherence

**Project type:** Computational neuroscience simulation
**Audience:** An AI agent (or research assistant) implementing the project end-to-end
**Status:** Ready for implementation
**Version:** 1.0

---

## 0. How to use this document

This is a self-contained brief. It gives you (the implementer) the scientific context, the precise question, the model to build, the parameters to use, the experimental manipulation that is the heart of the project, the analyses to run, and the deliverables expected. Where a parameter is given, use it as a default but expose it as a configurable variable. Where a choice is left open, make a reasonable decision, document it, and flag it. Do not silently deviate from the core experimental logic in Section 4 — that logic is the whole point of the project.

---

## 1. Background and scientific context

### 1.1 The Communication-Through-Coherence (CTC) hypothesis

CTC (Fries, 2005; Fries, 2015) proposes that anatomically connected neuronal groups communicate effectively only when their rhythmic activity is appropriately phase-aligned ("coherent"). The mechanism, in brief:

- An active neuronal group engages in rhythmic synchronization, prominently in the gamma band (~30–90 Hz), produced by a fast excitation–inhibition (E–I) loop.
- Each gamma cycle has a short window of high excitability (excitation has fired, inhibition has not yet clamped down) followed by a longer window of low excitability (inhibition dominant).
- A receiving group is sensitive to input only during its own high-excitability windows.
- Therefore a sending group transmits effectively **only if its spikes arrive during the receiver's excitable windows** — i.e. only if sender and receiver are coherent at the right phase.
- Selective attention is proposed to bias this competition by strengthening and slightly increasing the gamma frequency of the attended representation, giving it a competitive advantage in entraining the downstream group.

### 1.2 The controversy this project addresses

CTC's central and contested claim is **causal**: that coherence is a *cause* of (or precondition for) effective communication.

A prominent alternative — most forcefully argued by Schneider et al. (2021, *Neuron*) — holds that the causal arrow runs the other way: coherence is a **byproduct** of communication ("coherence through communication"). On this view, simply having anatomical connectivity plus oscillatory power in the sending area produces inter-areal coherence and frequency-specific Granger causality as epiphenomena, without coherence doing any causal work. Schneider et al. supported this with a spiking network and an analytical "stochastic/spiking model" showing inter-areal LFP coherence can arise even when the receiver does not oscillate in that band.

The problem: most existing simulations are built to demonstrate one position or the other. PING-based models (Börgers & Kopell, 2008) presuppose a mechanistic role for the rhythm; the Schneider models are constructed to show coherence without that role. **No widely used simulation cleanly dissociates the two by manipulating coherence as an independent variable while holding everything else (firing rate, connectivity, oscillatory power) fixed.** That dissociation is what this project builds.

### 1.3 Why a simulation can decide something experiments cannot (yet)

In a real brain you cannot change phase relationships between two areas without also perturbing firing rates, synaptic drive, or power. In a model you can. This project exploits that: we build the ability to *surgically scramble or impose phase* on the channel between two areas, leaving rate and power statistically unchanged, and ask whether transmission survives.

---

## 2. The research question

**Primary question.** When inter-areal coherence is reduced (or its phase mis-set) *without* changing the sender's firing rate, the sender's oscillatory power, or the anatomical connectivity, does effective information transfer from sender to receiver degrade?

- If **yes** (transmission degrades when only coherence is disrupted) → evidence consistent with the *causal* CTC reading.
- If **no** (transmission is preserved despite disrupted coherence) → evidence consistent with the *epiphenomenal* / coherence-through-communication reading.

**Secondary questions.**

1. Is there an *optimal phase offset* for transmission, and how sharply tuned is it? (Replicates/extends Womelsdorf et al., 2007 in silico.)
2. How does the result depend on the receiver's own intrinsic rhythmicity — i.e. does the receiver need to oscillate for coherence to matter? (Directly engages the Schneider observation that coherence appeared without receiver oscillation.)
3. How does the dissociation behave as a function of connection strength and conduction delay?

---

## 3. Hypotheses and falsifiable predictions

| # | Hypothesis | Prediction if CTC is *causal* | Prediction if coherence is *epiphenomenal* |
|---|---|---|---|
| H1 | Phase relation gates transmission | Information transfer is a strong, non-monotonic (peaked) function of imposed phase offset | Information transfer is flat (or only weakly dependent) across phase offset, set by power/connectivity |
| H2 | Coherence disruption impairs transmission | Phase-scrambling the channel (rate/power preserved) sharply reduces transfer | Phase-scrambling leaves transfer largely intact |
| H3 | Receiver oscillation is required for the gating | Disabling the receiver's E–I loop abolishes the phase-gating effect | Coherence (as measured) and transfer persist even with a non-oscillating receiver |
| H4 | Selective routing via coherence | Of two equal-rate senders, the one phase-matched to the receiver dominates the receiver's output | Both senders contribute in proportion to connectivity/power, regardless of phase |

The value of the project is that **the same model produces different, measurable outcomes under the two interpretations**, so the result discriminates between them rather than illustrating a prior commitment.

---

## 4. Core experimental design (the heart of the project)

This is the part that must not be compromised. The novelty is the **causal intervention on coherence as an independent variable**.

### 4.1 Base architecture

Three neuronal groups, each a local E–I (PING) microcircuit that generates a gamma rhythm endogenously:

- **Sender A** (a presynaptic group encoding stimulus A)
- **Sender B** (a presynaptic group encoding stimulus B) — used for the selective-routing experiments (H4); can be omitted for the single-sender experiments (H1–H3)
- **Receiver R** (a postsynaptic group receiving feedforward input from A and/or B)

Connectivity is feedforward (A→R, B→R) via excitatory synapses with a conduction delay. The receiver does **not** project back in the baseline condition (add reciprocal coupling only as an explicit variant).

### 4.2 The independent variable: an interposed "phase channel"

Between each sender and the receiver, route the sender's spike train through a controllable channel that can manipulate phase/coherence **without altering the marginal firing-rate statistics or the power spectrum of what is delivered**. Implement and compare at least these channel modes:

1. **`intact`** — spikes delivered with a fixed conduction delay (control; coherence preserved). Sweep the delay to realize a controlled, deterministic phase offset (this gives the H1 phase-tuning curve).
2. **`phase_scramble`** — the *timing* of delivered spikes is randomized within a sliding window so that the inter-areal phase relationship is destroyed, **while preserving the per-window spike count** (rate matched) and the overall rate spectrum as closely as possible. This is the critical manipulation for H2.
3. **`rate_matched_poisson`** — replace the sender's spike train with an inhomogeneous Poisson process whose instantaneous rate equals the sender's smoothed rate (destroys fine temporal/oscillatory structure but matches rate). A stronger destruction of coherence; useful as an extreme of `phase_scramble`.

**Critical requirement:** for `phase_scramble`, verify and report that (a) total and time-resolved firing rate, and (b) sender oscillatory power, are statistically unchanged from `intact`, while (c) sender–receiver coherence is reduced. The validity of the whole experiment rests on this triple check. If you cannot hold (a) and (b) fixed while changing (c), document exactly where the trade-off appears.

### 4.3 The conditions to run

- **Experiment 1 (H1 — phase tuning):** channel = `intact`, sweep conduction delay across a full gamma cycle (e.g. 0 to ~16 ms in ~1 ms steps for a 60 Hz rhythm). Measure transfer vs. phase offset. Expect a peaked curve under CTC.
- **Experiment 2 (H2 — causal disruption):** compare `intact` (at the optimal phase from Exp 1) vs `phase_scramble` vs `rate_matched_poisson`. Measure transfer in each. This is the central test.
- **Experiment 3 (H3 — receiver oscillation necessity):** repeat Exp 1 and 2 with the receiver's I-population disabled or its E→I/I→E coupling set to zero so the receiver cannot generate its own gamma. Ask whether phase still matters.
- **Experiment 4 (H4 — selective routing):** two senders A and B with **matched firing rates and power**, differing only in their phase relationship to R (e.g. A phase-matched, B anti-phase, via channel delays). Measure each sender's contribution to R's output (and R's stimulus selectivity). CTC predicts A dominates.

### 4.4 What to randomize and replicate

Run each condition over many random seeds (≥ 20; more if cheap) to get distributions, not point estimates. Vary the random seed for: background noise, connection instantiation (if probabilistic), and the scrambling. Report effect sizes with confidence intervals, not just significance.

---

## 5. The model: equations, parameters, "data"

This section is the concrete material the implementer needs. Treat these as defaults; expose them as parameters.

### 5.1 Neuron model

Use conductance-based or current-based spiking neurons. Two acceptable choices:

- **Option A (recommended, simple & standard): leaky integrate-and-fire (LIF)** for both E and I cells. Fast to simulate, adequate for PING.
- **Option B (more biophysical): reduced Hodgkin–Huxley** — e.g. regular-spiking (RTM/reduced Traub-Miles) E cells and Wang–Buzsáki (WB) fast-spiking I cells, as used in the canonical PING literature. Use this if you want closer contact with Börgers & Kopell.

LIF defaults (per cell):

| Parameter | E cells | I cells |
|---|---|---|
| Membrane time constant τ_m | 20 ms | 10 ms |
| Resting potential V_rest | −65 mV | −65 mV |
| Threshold V_th | −50 mV | −50 mV |
| Reset V_reset | −65 mV | −65 mV |
| Refractory period | 2 ms | 1 ms |

### 5.2 Synapses

- Excitatory: AMPA-like, fast. Rise ~0.5 ms, decay τ ≈ 2–3 ms. Reversal 0 mV.
- Inhibitory: GABA_A-like. Decay τ ≈ 8–10 ms (this longer inhibitory time constant is what sets the gamma period and the duty cycle — do not shorten it casually). Reversal −70 to −80 mV.
- The E→I→E loop must be tuned so the network oscillates in the gamma band (target ~50–70 Hz; report the realized peak frequency).

### 5.3 Network size and connectivity (per group)

- E cells: 800; I cells: 200 (the standard 4:1 ratio). Smaller (e.g. 200 E / 50 I) is acceptable for development; report what you use.
- Within-group connectivity: sparse random, ~10–20% connection probability, sufficient to produce a clean PING rhythm.
- Feedforward (sender→receiver): excitatory, onto receiver E cells (and optionally a fraction onto receiver I cells). Connection probability and weight are key variables — sweep them in Section 4 secondary questions.
- Conduction delay (sender→receiver): default ~3–5 ms; this is the knob used to set phase offset in Experiment 1.

### 5.4 Drive and the "stimulus representation"

- Drive each sender with an external input encoding a "stimulus" as a *spatial pattern of target firing rates* across its E cells (e.g. a tuning curve). The thing to be transmitted is this pattern. The receiver's job is to reconstruct it.
- Background: independent noise (e.g. Poisson background or current noise) to every cell to desynchronize trivially and force the rhythm to be emergent, not clock-driven.
- For attention/salience variants, the attended sender gets slightly stronger drive and/or a small gamma-frequency increase (~3–5 Hz, per Bosman et al., 2012) — relevant if you extend to the attentional-advantage question.

### 5.5 Calibration targets (so the model is in a biologically sensible regime)

Before running experiments, confirm the baseline model reproduces these qualitative benchmarks:

- Emergent gamma peak in the sender LFP/rate spectrum at ~50–70 Hz.
- E→I lag of roughly 2–3 ms within a cycle (excitation leads inhibition).
- Under `intact`, sender→receiver coherence in the gamma band that is clearly above the `phase_scramble` baseline.
- A peaked phase-tuning curve in Experiment 1 (the in-silico analogue of Womelsdorf et al., 2007).

If these don't hold, the network is mis-tuned; fix before interpreting the causal experiments.

---

## 6. Measurements and analysis

For every condition, compute and store:

1. **Firing rates** (per cell, per group; time-resolved and mean) — used to verify the rate-matching control.
2. **Power spectra** of each group's population activity (LFP proxy = summed synaptic currents or smoothed population rate) — used to verify the power-matching control and to read out gamma frequency.
3. **Inter-areal coherence** (sender–receiver) and **pairwise phase consistency (PPC)** in the gamma band — the manipulation check on coherence.
4. **Directed influence:** Granger causality and/or transfer entropy, sender→receiver. (Granger for comparability with Bastos/Schneider; transfer entropy as a model-free cross-check.)
5. **Information transfer / decoding accuracy (primary dependent variable):** train a decoder (e.g. linear estimator) to reconstruct the sender's stimulus pattern from the receiver's E-cell activity. Decoding accuracy = how much of the representation got through. This is the most direct operationalization of "effective communication" and is the headline metric. (Follows the spirit of Akam & Kullmann, 2012.)
6. For Experiment 4: **stimulus selectivity of the receiver** — does R's output represent A or B?

**The decisive comparison:** plot the primary dependent variable (decoding accuracy / mutual information) against coherence across conditions, and separately against firing rate and power. CTC-causal predicts decoding tracks coherence *even when rate and power are held constant*. The epiphenomenal view predicts decoding tracks connectivity/power and is insensitive to the coherence manipulation.

---

## 7. Implementation guidance

- **Simulator:** Brian2 (Python) is recommended for transparency and ease of custom channel logic. NEST or NEURON are acceptable if you prefer. Avoid frameworks that make it hard to insert the custom phase-scrambling channel between groups.
- **Time step:** ≤ 0.1 ms (gamma + AMPA dynamics need fine resolution).
- **Trial length:** long enough for stable spectra and decoding (e.g. ≥ several hundred ms per trial after a settling period; discard the first ~200 ms transient).
- **Reproducibility:** fix and log all random seeds; version the parameter set with each run; output a machine-readable config alongside results.
- **The phase-scramble channel** is the trickiest piece of code. Implement it as an explicit intermediary that ingests sender spikes and emits delivered spikes, with a unit test demonstrating rate/power preservation and coherence reduction on synthetic input *before* wiring it into the full model.
- Keep the analysis pipeline separate from the simulation so conditions can be re-analyzed without re-running.

---

## 8. Deliverables

1. **Code:** the simulation (model + configurable channel), the analysis pipeline, and unit tests for the channel.
2. **A baseline calibration report** showing the Section 5.5 benchmarks are met.
3. **Results for Experiments 1–4**, each with: figures (phase-tuning curve; transfer under intact vs scrambled vs Poisson; receiver-oscillation on/off; two-sender routing), summary statistics with confidence intervals across seeds, and the manipulation checks (rate/power preserved, coherence changed).
4. **A short written interpretation** stating, for each hypothesis H1–H4, which interpretation (causal CTC vs epiphenomenal) the results support, with appropriate caveats.
5. **A parameter-sensitivity appendix:** how the central result (Experiment 2) depends on connection strength, conduction delay, and noise level.

## 9. Scope, non-goals, and known risks

- **Non-goal:** full anatomical realism, multi-area hierarchies, or laminar structure. Keep it to the minimal architecture that can decide the causal question. (Those extensions are separate future projects.)
- **Risk — imperfect control:** perfectly preserving power while destroying coherence is hard, because oscillatory power and coherence are statistically entangled. Be transparent about residual changes and, where they occur, bound their size and argue whether they could account for any transfer change.
- **Risk — decoder confounds:** ensure decoding-accuracy differences reflect genuine transmission, not changes in receiver excitability or overall rate. Include rate-matched control decoders.
- **Risk — interpretive overreach:** a model result supports an interpretation; it does not prove the brain works that way. State conclusions as "consistent with / inconsistent with," tied to the specific manipulations.

## 10. Key references

- Fries, P. (2005). A mechanism for cognitive dynamics: neuronal communication through neuronal coherence. *Trends in Cognitive Sciences*, 9, 474–480.
- Fries, P. (2015). Rhythms for cognition: communication through coherence. *Neuron*, 88(1), 220–235.
- Womelsdorf, T. et al. (2007). Modulation of neuronal interactions through neuronal synchronization. *Science*, 316, 1609–1612. (Phase-dependence of effective connectivity — the target of Experiment 1.)
- Börgers, C. & Kopell, N. (2008). Gamma oscillations and stimulus selection. *Neural Computation*, 20, 383–414. (PING + selection mechanism.)
- Börgers, C., Epstein, S. & Kopell, N. (2008). Gamma oscillations mediate stimulus competition and attentional selection in a cortical network model. *PNAS*, 105, 18023–18028.
- Akam, T. & Kullmann, D. (2012). Efficient "communication through coherence" requires oscillations structured to minimize interference between signals. *PLoS Comput. Biol.*, 8, e1002760. (Decoding-based readout of transmission.)
- Bosman, C. et al. (2012). Attentional stimulus selection through selective synchronization between monkey visual areas. *Neuron*, 75, 875–888.
- Bastos, A. et al. (2015). Visual areas exert feedforward and feedback influences through distinct frequency channels. *Neuron*, 85, 390–401.
- Schneider, M. et al. (2021). A mechanism for inter-areal coherence through communication based on connectivity and oscillatory power. *Neuron* (the central counter-hypothesis this project tests against).
