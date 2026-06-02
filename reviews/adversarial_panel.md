# Adversarial Review Panel — `very_good_paper.docx`

*Transcript of a three-reviewer panel discussion on the manuscript "Disrupting
inter-areal coherence while preserving rate and power degrades stimulus
transmission in a spiking-network model" and the supporting code in
`/analysis/`. Participants: Reviewer 1 (cognitive / systems neuroscience,
friendly), Reviewer 2 (computational modelling & statistics, challenging),
Reviewer 3 — "Mighty M" (biophysical modelling, anti-LLM).*

---

**R1 (cogneuro):** Let me start with what I actually liked, because I want
to be clear this is not a hatchet job. Someone finally built the
rate-and-power-matched control channel that the CTC literature has been
arguing past each other about for fifteen years. The paired-seed design is
right, the scramble-vs-Poisson dissociation is clean, and the H3 confound
is acknowledged in the open rather than hidden. The Discussion sentence
that frames coherence as "byproduct in passive observation, cause when
manipulated as input" is the most honest synthesis of Fries vs. Schneider
I've read in a while. I'd elevate it into the abstract. My read is **minor
revision**.

**R2 (compmodel):** I have a very different read. I agree the *idea* is
right and the paired-seed design is the right scaffold. But the
"phase-scramble channel" in `channels.py` lines 154–183 is a
**block-permutation** that preserves within-block fine timing exactly,
including cross-cell co-firing inside each 16 ms block, and the same
permutation index is applied to every cell on line 168. That is not a
phase-scramble. It destroys *block-to-block alignment with the receiver's
intrinsic γ phase*, which is a finer and weaker claim than "coherence is
causal." The delivered signal still has a γ envelope — that's why
delivered γ-power only drops 9.4%. The headline is doing more rhetorical
work than the manipulation supports. **Major revision.**

**R3 (Mighty M):** I'll back R2 on the manipulation, but I want to put a
different load-bearing complaint on the table first. The model's
τ_GABA was **halved** from the spec's biologically-motivated 8–10 ms range
to 4 ms, because 8 ms placed γ at 36 Hz instead of the spec's 50–70 Hz
target. The defence in `decisions.md` D7 is essentially "we wanted gamma
in band." That is the wrong direction of reasoning. 36 Hz is *low gamma* —
plenty of in-vivo recordings sit there. The authors retuned the
biophysics to hit a frequency target rather than retuning the target.
Bartos et al. 2002 and Salin & Prince 1996 give the 8–10 ms number for
a reason. There is no primary cell-physiology citation anywhere in the
bibliography. The gamma in this network exists because the modeller asked
for it, not because the cells produced it. **Major revision.**

**R1:** That's harsh but I can't fully disagree. Methods line 78 admits
the shortening offhand, and I flagged it as a SHOULD-FIX in my own memo
(S-R1.1) because shortening τ_GABA changes the excitable-window duty
cycle, which is exactly the mechanistic parameter CTC depends on per
Fries 2015. One sentence justifying that the realised window is still in
the ~2–5 ms range Fries invokes would close the loop. But I'd note —
this is a *modelling* paper, not a biophysics paper. Some
parameter-tuning to land the regime is normal practice.

**R3:** Normal practice when the parameter you're tuning isn't the
parameter the mechanism depends on. Here it is. Fries' phase-gating story
*is* a story about the inhibitory time constant setting the duty cycle.
Halve τ_GABA and you've halved the window the whole paper is about. The
analytic PING period from `2·(delay + τ_GABA)` is also internally
inconsistent — with τ_GABA = 8 ms it predicts ~59 Hz, very close to the
spec target, so the "8 ms placed γ at 36 Hz" result probably reflects a
coupling or drive imbalance the authors did not diagnose before reaching
for τ_GABA. No analytic sanity check appears in the repo.

**R2:** Related issue: at full scale the γ peak is **bimodal — 43 *or*
63 Hz** across the three calibration seeds, mean 49.5 ± 11.6 Hz
(`calibration_full_scale.json`). That is one seed on a slow attractor for
every seed on a fast one. The H2 paired-seed design assumes the receiver
is in a comparable γ regime across conditions, and we are not shown that
per-seed γ peak is matched seed-by-seed across the n=20 intact / scramble
/ poisson conditions. If which attractor a seed lands on co-varies with
channel mode through stochastic interactions, part of the H2 contrast is
a regime-switch, not a phase-locking effect.

**R1:** That bimodality is honestly flagged in Limitations item 3, but
you're right that "mean ± SD" is a misleading summary statistic for a
bimodal distribution. A supplementary panel of n_seeds × peak frequency
across the three conditions is cheap and would settle it.

**R3:** Cheap and load-bearing. I have it as S-M3 in my memo.

**R2:** While we're on confounds — the decoder is **at ceiling** for both
intact and Poisson. Per-seed accuracy is quantised to {0, 0.25, 0.5,
0.75, 1} because there are four stimuli and leave-one-seed-out. Intact
mean is 0.94 with 15/20 seeds at 1.0; Poisson is 0.975 with 19/20 at 1.0.
The "intact ≈ poisson" non-difference (p=0.18) the manuscript leans on
is a *test resolution failure*, not a substantive result. The authors
acknowledge this in Limitations item 2 but still treat intact-vs-poisson
as informative in the Results. It is not.

**R1:** Granted, but the intact-vs-scramble contrast doesn't depend on
that. Twelve seeds out of 20 go down, two go up, six tied. Direction is
solid even if Wilcoxon drops the ties.

**R2:** Direction is solid *given* the manipulation. But the manipulation
also drops delivered rate 8.6% and γ-power 9.4% — both in the *same
direction* as the decoder drop. The authors call this "preserved within
±10%" but never run a rate-matched decoder. Thinning intact-condition
delivered spikes to match scramble rate per cell per trial and retraining
is one afternoon's work. Without it I can't tell whether the 16 percentage
point decoder gap is coherence loss or rate loss.

**R3:** And the receiver's own γ-power is 17% lower under scramble
(10.07 vs 8.63). The "manipulation" changes the input alignment *and*
the receiver state. "Rate and power preserved" is true of the input
within tolerance; it is not true of the receiver. SHOULD-FIX at minimum.

**R1:** This is where I want to defend the paper a bit. The bar you two
are setting — perfect counterfactual isolation of a single population
statistic — is higher than any actual experimental CTC paper meets either.
Womelsdorf 2007, Bosman 2012, Bastos 2015 — none of those isolated
coherence from rate cleanly. The simulator at least *delivers* its
manipulation check on the same signal the receiver sees, which is more
than the experimental literature does. I think the right response is to
*restate the claim more carefully* rather than to demand a clean
factorial.

**R2:** A 2×2 factorial — phase preserved/scrambled × power
preserved/destroyed — would actually settle this. The current
manipulations sit on the diagonal only. With both off-diagonal cells the
authors would dissociate the two claims they currently conflate. It's not
an unreasonable demand of a simulation paper; the cells already exist
piecewise.

**R3:** I'd add — the bibliography has 15 references and *all* of them
are CTC-controversy papers. There is no primary cell-physiology citation
to defend any neuron parameter. No Bartos, Geiger, Jonas, Markram,
McCormick, Hu, Sohal, Cardin. The cells are not cells; they are points
labelled "E" and "I" with the spec table copy-pasted into a dataclass.
The conductances are 0.10 / 0.20 / 0.50 / 0.80 / 0.20 nS — suspiciously
even multiples of 0.1. `g_L = 10 nS by convention` (ping_group.py line 53)
— *whose* convention? That comment is a tell.

**R1:** This is where you're going to lose general readers, M. A short
report doesn't need to defend every membrane parameter against the
primary biophysics. Two citations for cell-type parameters, fine; I'd
back that as a SHOULD-FIX. But asking the authors to re-justify
`V_th = −50 mV` and `V_reset = −65 mV` is over-reading.

**R3:** I'm not asking them to defend the textbook values. I'm asking
them to *show me one place in the repo* where a parameter was chosen
deliberately against an alternative. `decisions.md` D6 (block-shuffle vs
jitter) is exactly that kind of choice — owned, defended, with a real
mechanistic reason. So is D11 (the spike-wrap fix). So is D14 (the typo
correction). The *analytic* layer is clearly human-paced. The *modelling*
layer is not. The authors picked LIF over AdEx with no comment, despite
citing Dowdall, Schneider & Vinck 2023 in the Discussion — a paper whose
slow-frequency-shift account literally requires adaptation. The model
cannot test the alternative it cites. That is the failure of judgement I
care about.

**R2:** I'll agree with M on the analyst layer — I was harsh in my memo
but the `decisions.md` log is unusually candid. D11 frankly admitting a
confound that flipped the headline at n=6, D14 owning a typo in
sign-counts, D17 owning the H3 hyperactivity confound. That is real
iteration. The problem is that all this honesty lives in the engineering
log and not in the manuscript itself, which reads more confidently than
the log warrants.

**R1:** On H3 specifically — the Results lead with "consistent with the
H3 prediction" before raising the receiver hyperactivity confound. I'd
re-order so the confound is presented *with* the result, not after.
M had this as S-M1; I'd second it.

**R3:** Yes. And the fix is cheap — scale `g_IE` smoothly or rescale
`drive_E` to rate-match. The infrastructure exists. The Limitations
section listing this as "out of scope" is the engineering log leaking
through into the paper.

**R2:** Statistics issues no one has raised yet. Coherence is computed
via Welch with `nperseg ≈ N/3` over 350 ms — ~3–6 segments, analytical
bias ~0.08–0.17 on raw MSC. No bias correction. The intact value 0.892
is at the upper edge where bias is small; the scramble value 0.301 is
where bias is largest. PPC, debiased MSC, or jackknife — any of them.

**R1:** PPC is my one BLOCKING. The spec asked for it in §6 item 3 and
it was never computed. With H3 tripling receiver rate, MSC there is
unreliable in the textbook way Vinck introduced PPC to fix. At minimum
run PPC on the H2 conditions. If it tracks MSC the paper is stronger;
if it diverges, that's the finding.

**R2:** Granger is worse. Granger F is 100 intact, 12 scramble, **143
Poisson**. Granger picks Poisson > intact, which is mechanistically
nonsensical and tells you the estimator is not measuring "effective
communication" comparably across conditions. Bootstrap CIs or drop it
from the headline. Same for TE — 4 equiprobable bins with lag 2, no
embedding justification, no bias correction.

**R3:** No sensitivity check that the H2 Granger result survives lag
∈ {3..7} ms. The chosen lag of 5 ms is justified verbally as "γ period
~16 ms → half-cycle lag" — that's a real reason, but a robustness panel
is one figure.

**R1:** Two things I want to add before we wrap. First, two DOIs in the
references are wrong (refs 13 and 14, flagged in `final_verification.md`)
and the manuscript-internal CLAUDE.md guardrail explicitly forbids
fabricated references. Trivial fix but essential. Second, the manuscript
is silent on experimental analogues — no mention that the phase-scramble
isn't realisable in monkey or mouse, no pointer to optogenetic PV+
perturbation (Cardin 2009, Sohal 2009) or pulvinar α-pacing (Quax 2017,
already in the bib but uncited). One Discussion paragraph fixes it and
pre-empts the "this is unphysiological" reviewer reflex.

**R3:** And one thing on falsifiability. The manuscript hedges to
"consistent with" everywhere — appropriate, but it means almost no
observation could falsify the claim as stated. The closest thing to a
falsifier is implicit: had n=20 scramble matched intact, the causal-CTC
reading would be untenable. That observation actually *happened* at n=6
(D12) and was correctly attributed to power. The authors should state
the falsifier explicitly in the Discussion. Same for the H1 plateau —
they should commit to "had the curve been monotonic in delay rather than
plateau-then-drop, that would have argued against a rhythmic gate."

**R1:** On H1 I'd note Palmigiano et al. 2017 predicts exactly the kind
of broad phase-tuning window the data show — transient-synchrony routing
gives plateau-then-drop, not the sharp Womelsdorf peak. Ref 20 in the
bib, never cited. Citing it would turn the "weaker than expected" H1
into a literature contact.

---

## Where we converge

All three of us agree on the following, in roughly descending priority:

1. **The phase-scramble channel is doing less than the manuscript
   claims** (R2 BLOCKING; R3 BLOCKING in spirit; R1 SHOULD-FIX). Either
   add controls (per-cell independent permutation; within-block jitter;
   factorial 2×2) or restate the claim as "block-permuting the sender's
   spike train relative to the receiver's intrinsic γ phase reduces
   decoding."
2. **Rate confound is uncontrolled** (R2 BLOCKING; R1 MINOR; R3 implicit).
   Rate-matched decoder control: thin intact spikes to match scramble
   rate, retrain, report.
3. **τ_GABA = 4 ms is biologically unjustified and load-bearing**
   (R3 BLOCKING; R1 SHOULD-FIX; R2 silent — would be a SHOULD-FIX if I
   thought it changed the inference). Defend with a primary citation or
   rerun headline with τ_GABA = 8 ms.
4. **Full-scale γ peak is bimodal across seeds** (all three SHOULD-FIX).
   Show per-seed γ-peak distribution across the three H2 conditions.
5. **PPC is missing** (R1 BLOCKING; R2 SHOULD-FIX). Bias-corrected
   coherence or PPC, at least on H2.
6. **Decoder is at ceiling for intact and Poisson** (R2 BLOCKING; R1
   implicit). Either harder discriminability regime or report continuous
   posterior probability.
7. **H3 confound should be presented with the result, not in Limitations**
   (R3 SHOULD-FIX; R1 implicit). Rate-matched H3 control is cheap and
   would settle it.
8. **Discussion needs an experimental-analogues paragraph** (R1
   SHOULD-FIX). One paragraph on optogenetic PV+ perturbation and
   pulvinar α as the closest in-vivo handles.
9. **Granger F is mechanistically nonsensical across conditions** (R2
   SHOULD-FIX; R3 lag-sensitivity panel). Bootstrap CIs or drop from
   headline.

## Where we disagree

- **R1 vs R2/R3 on overall verdict.** R1 sees minor revision because the
  framing is honest and the constraints are visible; R2 and R3 see major
  revision because the manipulation and the model do not actually isolate
  the variable the headline names. The disagreement is mostly about
  whether honest hedging in the Discussion compensates for a confounded
  manipulation; R2 and R3 think no, R1 thinks largely yes.
- **R3 vs R1 on biophysical fidelity.** R3 wants primary cell-physiology
  citations and a defended neuron model; R1 thinks a short modelling
  report doesn't owe that. Compromise: two citations for cell-type
  parameters and one analytic PING-period sanity check.
- **R2 vs R1 on the intact-vs-Poisson contrast.** R2 thinks the contrast
  is uninformative because both conditions are at the decoder ceiling;
  R1 thinks the direction is solid and the framing handles it. The
  truthful path is probably R2's — report a continuous DV.

## Aggregate verdict

**Major revision.** Two of three reviewers, including the methodological
hawk and the biophysical hawk. The work is good in conception, honest in
its self-review trail, but the headline rides on a manipulation that
isn't quite the manipulation it claims to be, a network whose gamma was
tuned-into-band, and a decoder at the ceiling for two of three
conditions. Most fixes are tractable on existing infrastructure.
