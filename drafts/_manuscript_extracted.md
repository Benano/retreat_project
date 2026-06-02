**Disrupting inter-areal coherence while preserving rate and power
degrades stimulus transmission in a spiking-network model**

*Computational neuroscience --- short report --- Nature-style preprint*

Project author (orchestrating agent) • 2 June 2026

Abstract

The communication-through-coherence (CTC) hypothesis^1,2^ posits that
γ-band phase-locking between neuronal groups is a cause of selective
inter-areal communication. An alternative view^9,10^ treats coherence as
a byproduct of connectivity and oscillatory power. Existing simulations
almost universally illustrate one position by construction. Here we use
a paired-PING two-area spiking network in which a controllable
phase-scramble channel is inserted between sender and receiver. The
channel destroys cross-areal temporal alignment while preserving the
marginal firing rate and γ-power of the delivered spike train (verified
on synthetic input and re-verified on the delivered signal in the
coupled simulation). Across n=20 random seeds at 800E/200I per group,
disrupting coherence reduced stimulus decoding from 0.94 to 0.78 (paired
Wilcoxon W=12, p=0.0070), while a Poisson channel that destroys γ-power
10× but preserves coherence left decoding intact (0.98; W=0 vs scramble,
p=0.0004). Disabling the receiver\'s intrinsic γ loop abolished and
inverted the effect (W=11, p=0.011), although this manipulation also
produced a hyperactive receiver, leaving rhythmicity and saturation
co-varying. The results are *consistent with* a causal role for
γ-coherence in selective inter-areal communication, with caveats
discussed.

Introduction

The CTC framework^1,2^ proposes that two anatomically connected neuronal
groups communicate effectively only when their gamma-band rhythmic
excitability is appropriately phase-aligned: sender spikes that arrive
during the receiver\'s brief excitatory window are transmitted, those
that arrive during inhibition are not. Empirical support includes
phase-dependent effective connectivity in macaque V4^3^, attentional
V1→V4 selective γ-synchronization^7^, and frequency-asymmetric Granger
influences along the visual hierarchy^8^. A computational tradition
based on the pyramidal-interneuron-γ (PING) circuit^4,5^ has shown that
coherent γ inputs out-compete less-coherent inputs at downstream
targets, and that coherent gain modulation in principle suffices to
route population-coded signals^6^.

This causal reading is contested. Schneider et al.^9^ presented a
"coherence-through-communication" account in which inter-areal LFP
coherence and frequency-specific Granger causality arise as byproducts
of anatomical connectivity and sender oscillatory power, without any
causal role for phase-locking and without requiring receiver
oscillation. Recent follow-ups have extended this critique: coherence
misleads under bidirectional transmission delays^11^; attentional
modulation of coherence can be explained by sender-side frequency
shifts^12^; and V1 γ engages cell-type-specific feedforward pathways in
V4 that decouple feedforward γ-coherence from local oscillation^13^. A
2024 firing-rate model maintains a more limited CTC story for
attention^15^. The field has not converged.

Existing simulations cannot adjudicate because they cannot vary
coherence independently of rate and power. The contribution here is a
circuit in which an explicit phase-scramble channel is inserted between
sender and receiver. The channel is designed to destroy the cross-areal
temporal alignment of γ packets while preserving the per-cell firing
rate and the γ-band power of the delivered signal --- the
rate-and-power-matched control that prior simulations lacked^9,10^. We
test three hypotheses: (H1) effective communication depends on imposed
sender--receiver phase offset; (H2) selectively reducing coherence
reduces communication when rate and power are held fixed; (H3) the
phase-gating effect requires an intact receiver E↔I loop.

Methods

Spiking network

Two PING groups (sender, receiver), each with 800
leaky-integrate-and-fire excitatory cells and 200 inhibitory cells (4:1
ratio, spec §5.3). Conductance-based AMPA-like and GABA\_A-like synapses
(τ\_AMPA = 2.5 ms, τ\_GABA = 4 ms after calibration to place the γ peak
in the 50--70 Hz band; the 8--10 ms inhibitory time constant in the spec
proved too slow, placing γ at 36 Hz). Within-group connectivity is
sparse random (10--20% per pair). Each cell receives independent Poisson
background drive (1200 Hz per cell). The sender\'s excitatory drive
carries the stimulus as a Gaussian-bump spatial pattern across E-cell
indices; four stimuli used in all experiments. All simulations are in
Brian2 with 0.1-ms time step; trials are 500 ms, first 150 ms discarded
as a transient (spec §7). Model parameters were tuned on a 200E/50I dev
network and inherited at full scale.

Phase-scramble channel

The decisive intervention is an explicit channel placed between each
sender spike and the receiver. Three channel modes were compared.
intact: spikes delivered with a fixed 8-ms conduction delay (the
apparent decoding maximum from Exp 1). scramble: the sender\'s spike
train is split into 16-ms blocks (one γ cycle at 60 Hz) and a single
random permutation is applied across blocks, identical across cells,
with within-block timing preserved. End-of-window blocks wrap around so
total spike count is preserved exactly. poisson: each sender cell\'s
spike train is replaced by an inhomogeneous Poisson process with the
same Gaussian-smoothed instantaneous rate (σ = 5 ms).

On synthetic γ-modulated Poisson input the block-shuffle preserves rate
within ±1%, γ-power within ±25%, and reduces sender↔delivered
γ-coherence from 0.998 to 0.138. This triple check (CLAUDE.md guardrail
4) was repeated for every experimental condition on the delivered signal
in the coupled simulation; we report those numbers in Figure 3 and the
corresponding text.

Measurements

Per trial we computed per-cell and population firing rates, an LFP proxy
(Gaussian-smoothed population rate), Welch power spectra,
sender--receiver γ-band magnitude-squared coherence,
pairwise-conditional Granger F at a fixed lag of 5 ms (chosen to avoid
lag-max F inflation), and a binned transfer-entropy cross-check. The
headline dependent variable is stimulus decoding from receiver E-cell
spike counts via per-trial z-scored logistic regression with
leave-one-seed-out cross-validation. Per-condition comparisons use
paired Wilcoxon tests across the n=20 per-seed accuracies.

Calibration

At the dev scale (200E/50I) the realized γ peak was 56 Hz with E→I lag
3.1 ms --- inside the 50--70 Hz target band (spec §5.5). At full scale
(800E/200I), using the same per-cell parameters, the realized γ peak
across three seeds was 43, 63, and 43 Hz (mean 49.5 ± 11.6, bimodal
between a long- and short-period attractor). E→I lag dropped to 1.7 ms.
We did not retune at full scale and note this in Limitations.

Results

H1 --- Phase tuning

Sweeping the intact-channel conduction delay from 2 to 16 ms (one γ
cycle) produced a graded reduction of sender↔delivered γ-coherence from
0.89 to 0.32, with a one-way ANOVA on coherence across delays giving
F(7,184)=68.2, p\<10⁻⁴⁷ (Fig. 1b; n=6 seeds × 4 stim per delay). At the
dev scale the same sweep produced no detectable coherence modulation
(F=1.29, p=0.25); the manipulation reaches the receiver only at full
scale, presumably because the receiver\'s intrinsic γ is more reliable
when the population is larger. Decoding accuracy stayed on a plateau
between 0.84 and 0.88 for delays 2--10 ms and dropped to 0.67 at 12 ms
(Fig. 1a). The shape is plateau-then-drop rather than the textbook
single sharp peak^3^, but is consistent with the CTC prediction that
short delays place delivered spikes near the receiver\'s excitable
window.

![fig1\_phase\_tuning.png](media/ac76f0f3c58a91e25ab9ac663609a6bba8586615.png "fig1_phase_tuning.png"){width="5.625in"
height="2.0833333333333335in"}

***Figure 1.** H1 phase tuning at full scale. (a) Decoding accuracy by
conduction delay, leave-one-seed-out (n=6 seeds × 4 stim). (b)
Sender→receiver γ-coherence (ANOVA F=68, p\<10⁻⁴⁷). (c) Granger F
(sender→receiver) at fixed lag 5 ms.*

H2 --- Causal disruption (rate- and power-matched)

At delay 8 ms (a point on the H1 high-decoding plateau) the
block-shuffle channel destroyed sender↔delivered γ-coherence (0.89 →
0.30, a 66% drop) while preserving the delivered firing rate (14.36 →
13.12 Hz, −9%) and the delivered γ-power (4.02 → 3.62 a.u., −10%).
Granger F dropped from 100 to 0.1. Sender firing rate and sender γ-power
were identical to three significant figures across all three conditions
by construction (paired seeds). The decoder shows the predicted
dissociation: stimulus decoding dropped from 0.94 ± 0.025 (intact) to
0.78 ± 0.036 (scramble), paired Wilcoxon W=12, p=0.0070, n=20 (12
positive paired differences, 2 negative, 6 ties; Fig. 2).

The Poisson channel --- which destroys γ-power 10× (from 4.02 to 0.41
a.u.) but largely preserves sender↔delivered γ-coherence (0.71) because
the receiver entrains to the smoothed rate envelope --- left decoding
intact at 0.98 ± 0.017, statistically indistinguishable from intact
(W=3, p=0.18) and significantly higher than scramble (W=0, p=0.0004).
The intact-vs-Poisson non-difference reflects ceiling decoding under
both conditions and is not interpreted as a positive finding; the
load-bearing test is scramble-vs-Poisson, which preserves rate and
contrasts the two channels at the level of γ-coherence.

![fig2\_causal\_test.png](media/f24dec68ec75280f86696e11f192751957c66328.png "fig2_causal_test.png"){width="4.791666666666667in"
height="2.0833333333333335in"}

***Figure 2.** H2 causal disruption (800E/200I, n=20 seeds). (a)
Per-seed decoding accuracy with leave-one-seed-out CV; p-values from
paired Wilcoxon. (b) Sender↔delivered γ-coherence (manipulation check).
Chance = 0.25 (four stimuli).*

![fig3\_manipulation\_check.png](media/6fa6257e973ff43ecf0a18457abd8de39b59903f.png "fig3_manipulation_check.png"){width="5.625in"
height="2.0833333333333335in"}

***Figure 3.** Manipulation check on the delivered signal across the
three channels (n=20). The block-shuffle preserves delivered rate (a)
and γ-power (b) to within ±10%; coherence (c) drops by 66%. Poisson
destroys γ-power 10× but largely preserves coherence.*

H3 --- Receiver-oscillation manipulation

Disabling the receiver\'s within-group E↔I coupling (g\_EI = g\_IE = 0)
abolished the receiver\'s intrinsic γ rhythm. Under this manipulation,
the intact vs scramble decoding effect did not merely vanish --- it
inverted. Across n=20 seeds, intact decoding fell to 0.74 ± 0.038 and
scramble decoding rose to 0.89 ± 0.042 (paired Wilcoxon W=11, p=0.011;
11 seeds with scramble \> intact, 2 with the original direction, 7 ties;
Fig. 4a). The result is consistent with the H3 prediction that an intact
receiver E↔I loop is required for the phase-gating effect of H2.

**Important confound.** Removing within-receiver inhibition does not
only abolish the rhythm. It also disinhibits receiver E cells, which
fired at 60 Hz under H3 compared to \~20 Hz at baseline (Fig. 4b). The
reversed direction (scramble \> intact) is plausibly produced by
saturation: bursty intact-channel input drives the disinhibited receiver
into refractoriness and discards per-cell rate distinctions, whereas
evenly-spread scrambled input integrates more linearly. We therefore
cannot, from this experiment alone, separate "rhythm is required for
gating" from "rhythm controls the receiver\'s dynamic range and
disinhibition reverses the input statistics that matter." An honest
reading is that H3 demonstrates the H2 effect requires an intact
receiver E↔I loop, without isolating rhythmicity from saturation.

![fig4\_h3.png](media/3ef5ecd7054e445498142a8ae02a7f7067eec9bf.png "fig4_h3.png"){width="4.791666666666667in"
height="2.2916666666666665in"}

***Figure 4.** H3 receiver-oscillation manipulation (n=20). (a) Decoding
accuracy in the baseline receiver (left) and with the receiver E↔I loop
disabled (right); hatched bars indicate the H3 condition. The intact vs
scramble difference inverts. (b) Receiver E-cell firing rate triples
(\~20 → \~60 Hz) under H3, indicating disinhibition-driven saturation
co-varies with the loss of rhythmicity.*

Discussion

Across H1, H2 and H3 the simulation produces a coherent picture: when
the phase relationship between sender and receiver is varied while every
other anatomically interpretable variable is held fixed, effective
transmission of the sender\'s stimulus pattern degrades. The most
decisive test is the scramble--vs--Poisson contrast: both channels
destroy a major feature of the sender\'s output (alignment vs γ-power),
but only the alignment-destroying one degrades transmission. This is
*consistent with* a causal role for γ-coherence in selective inter-areal
communication, in line with the original CTC proposal^1,2^ and the
PING-based selection literature^4,5,6^.

The result is *not* inconsistent with the
coherence-through-communication view^9,10,11,12^: in our manipulation
the receiver still oscillates and the channel still delivers a coherence
signature when intact, so we are not testing whether coherence can arise
as a byproduct. We are testing whether breaking the coherence ---
without breaking rate or power --- disrupts transmission. The two claims
are compatible: coherence may be a byproduct of communication in passive
observation, and a cause of communication when used as an experimentally
manipulated input.

H3 needs a sharper follow-up. The cleanest variant would reduce the
receiver\'s E↔I coupling smoothly rather than zero it (e.g., scaling
g\_IE down by a multiplicative factor), so the receiver\'s oscillation
weakens without losing inhibitory tone. This would dissociate
rhythmicity from saturation. We did not run this variant due to compute
budget; it is the most informative next step.

Limitations

1.  The H3 hyperactivity confound --- disabling the receiver E↔I loop
    also removes inhibitory tone, producing a 60 Hz hyperactive
    receiver. The scramble \> intact reversal is consistent with both
    "rhythm gates phase-tuning" and "saturation reverses the
    input-statistics relevance." A graded reduction of g\_IE is the next
    experiment.

2.  Decoder quantization. With four stimuli and leave-one-seed-out CV,
    each per-seed accuracy is quantized to {0, 0.25, 0.5, 0.75, 1}. The
    n=20 paired tests carry meaningful ties (6 in H2 intact-vs-scramble;
    7 in H3). Finer-grained DVs (e.g., trial-level posterior
    probability) would tighten the tests but were not implemented here.

3.  Full-scale γ peak bimodality. Per-cell parameters were calibrated at
    the dev scale (200E/50I, 56 Hz peak) and used unchanged at the full
    scale (800E/200I), where the realized γ peak is bimodal at 43/63 Hz
    (mean 49.5 Hz). Individual trials remain inside the broader γ band;
    effects might be sharper with a full-scale calibration.

4.  Exp 1 (H1) decoding CIs are CV-fold based, not seed-level. The H1
    curve should be read as qualitative; the load-bearing per-seed
    paired tests are in H2 and H3.

5.  We did not run the spec\'s parameter-sensitivity sweep (Deliverable
    5). Connection strength, conduction delay, and background-noise
    sensitivity are explicitly out of scope here.

6.  Experiment 4 (two-sender selective routing, H4 in the spec) was out
    of scope for this pass. The infrastructure (sender, channel,
    decoder) is in place for a follow-up that adds a second sender at
    anti-phase to test whether the phase-matched sender dominates the
    receiver\'s output.

References

1.  Fries, P. A mechanism for cognitive dynamics: neuronal communication
    through neuronal coherence. Trends Cogn. Sci. 9, 474--480 (2005).
    doi:10.1016/j.tics.2005.08.011

2.  Fries, P. Rhythms for cognition: communication through coherence.
    Neuron 88, 220--235 (2015). doi:10.1016/j.neuron.2015.09.034

3.  Womelsdorf, T. et al. Modulation of neuronal interactions through
    neuronal synchronization. Science 316, 1609--1612 (2007).
    doi:10.1126/science.1139597

4.  Börgers, C. & Kopell, N. Gamma oscillations and stimulus selection.
    Neural Comput. 20, 383--414 (2008). doi:10.1162/neco.2007.07-06-289

5.  Börgers, C., Epstein, S. & Kopell, N. J. Gamma oscillations mediate
    stimulus competition and attentional selection in a cortical network
    model. PNAS 105, 18023--18028 (2008). doi:10.1073/pnas.0809511105

6.  Akam, T. & Kullmann, D. M. Efficient \'communication through
    coherence\' requires oscillations structured to minimize
    interference between signals. PLoS Comput. Biol. 8, e1002760 (2012).
    doi:10.1371/journal.pcbi.1002760

7.  Bosman, C. A. et al. Attentional stimulus selection through
    selective synchronization between monkey visual areas. Neuron 75,
    875--888 (2012). doi:10.1016/j.neuron.2012.06.037

8.  Bastos, A. M. et al. Visual areas exert feedforward and feedback
    influences through distinct frequency channels. Neuron 85, 390--401
    (2015). doi:10.1016/j.neuron.2014.12.018

9.  Schneider, M. et al. A mechanism for inter-areal coherence through
    communication based on connectivity and oscillatory power. Neuron
    109, 4050--4067.e12 (2021). doi:10.1016/j.neuron.2021.09.037

10. Vinck, M. et al. Principles of large-scale neural interactions.
    Neuron 111, 987--1002 (2023). doi:10.1016/j.neuron.2023.03.015

11. Dowdall, J. R. & Vinck, M. Coherence fails to reliably capture
    inter-areal interactions in bidirectional neural systems with
    transmission delays. NeuroImage 271, 119998 (2023).
    doi:10.1016/j.neuroimage.2023.119998

12. Dowdall, J. R., Schneider, M. & Vinck, M. Attentional modulation of
    inter-areal coherence explained by frequency shifts. NeuroImage 278,
    120256 (2023). doi:10.1016/j.neuroimage.2023.120256

13. Spyropoulos, G. et al. Distinct feedforward and feedback pathways
    for cell-type specific attention effects. Neuron 112, 2423--2434
    (2024). doi:10.1016/j.neuron.2024.04.013

14. Vinck, M. et al. Large-scale interactions in predictive processing:
    oscillatory versus transient dynamics. Trends Cogn. Sci. 28,
    1056--1074 (2024). doi:10.1016/j.tics.2024.07.005

15. Greenwood, P. E. & Ward, L. M. Attentional selection and
    communication through coherence: scope and limitations. PLoS Comput.
    Biol. 20, e1011431 (2024). doi:10.1371/journal.pcbi.1011431

*Code, raw per-trial pickles, manipulation-check unit tests, reviewer
memos (rounds 1--3) and the running decisions.md log are reproducible
from https://github.com/\<repo\>. Canonical artifacts for the headline
numbers: analysis/results/exp2\_full\_n20/ (H2) and
analysis/results/exp3\_disabled/ (H3).*
