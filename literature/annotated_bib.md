# Annotated Bibliography — Causal status of Communication-Through-Coherence (CTC)

*Compiled by the literature-scout for the project "Testing the causal direction of CTC".
See `CTC_causality_simulation_spec.md` for the scientific brief.
Each DOI/URL below was retrieved during this session via WebSearch or WebFetch;
items I could only see as an abstract / through search-engine snippets are flagged.*

## Synthesis (4–6 sentences)

The "communication-through-coherence" (CTC) framework (refs 1, 2) proposes that
gamma-band phase-locking between neuronal groups is a **cause** of selective
inter-areal communication, supported by phase-dependent effective connectivity
in V4 (ref 3), attentional V1→V4 selective gamma synchronization (ref 7), and
frequency-asymmetric Granger influences across the visual hierarchy (ref 8).
A parallel computational tradition (Börgers & Kopell; refs 4, 5) demonstrated
that PING-like local circuits naturally produce gamma and that more-coherent
inputs out-compete less-coherent ones at downstream targets; Akam & Kullmann
(ref 6) showed analytically that coherent gain modulation can in principle
route signals if the oscillatory structure is well chosen. Schneider et al.
(ref 9) inverted the causal arrow: a "synaptic mixing" / coherence-through-
communication account shows that inter-areal LFP coherence and frequency-
specific Granger causality arise as **byproducts** of connectivity and
sender power, without requiring receiver oscillations or any causal role for
phase-locking. Recent follow-ups (refs 10–14) extend this critique
(coherence is misleading under bidirectional delays, attentional coherence
modulation can be explained by sender frequency shifts, V1 gamma engages only
V4 fast-spiking interneurons), while a 2024 firing-rate model (ref 15)
partially defends a *limited* CTC for attention. The headline takeaway: as
of 2026 the field has not converged; the project's "phase-scramble channel"
manipulation is well-motivated because no existing simulation cleanly
dissociates coherence from rate and power as an independent variable.

---

## 1. Fries, P. (2005). A mechanism for cognitive dynamics: neuronal communication through neuronal coherence. *Trends in Cognitive Sciences*, 9(10), 474–480.
- **DOI/URL:** 10.1016/j.tics.2005.08.011 (https://www.cell.com/trends/cognitive-sciences/abstract/S1364-6613(05)00242-1)
- **Source quality:** Abstract / search snippets only; full text paywalled. Flagged.
- **Core claim:** Activated neuronal groups produce rhythmic excitability fluctuations; effective communication requires coherent phase relations between sender and receiver so that sender spikes arrive in the receiver's excitable windows.
- **Method:** Conceptual / theory paper. No new data.
- **Key result:** Articulates the CTC hypothesis: "neuronal communication is mechanistically subserved by neuronal coherence." Proposes gamma as the primary band for the high-frequency excitability gate.
- **Limitations (stated):** Speculative; framed as a mechanism to be tested. (Read from abstract; full discussion of caveats not verified.)
- **Bears on:** causal-CTC (foundational statement).
- **Notes:** The originating paper of the field. The 2015 update (ref 2) supersedes it for current readers but historically this is the canonical citation.

---

## 2. Fries, P. (2015). Rhythms for cognition: communication through coherence. *Neuron*, 88(1), 220–235.
- **DOI/URL:** 10.1016/j.neuron.2015.09.034 (https://www.cell.com/neuron/fulltext/S0896-6273(15)00823-5; PubMed 26447583)
- **Source quality:** Abstract and search-snippets only; full text paywalled. Flagged.
- **Core claim:** Updated CTC: gamma (30–90 Hz) provides a ~3 ms window of excitation per cycle (followed by a longer inhibition phase); a postsynaptic group preferentially responds to the presynaptic group with which it is coherent; selective coherence implements selective routing.
- **Method:** Review/perspective synthesizing 2005–2015 evidence (single-unit, LFP, ECoG, MEG, attention experiments).
- **Key result:** Refines the duty-cycle account; notes ~3 ms excitatory window vs. longer inhibitory dominance per gamma cycle; integrates the attention-as-gamma-bias proposal.
- **Limitations (stated):** Inferred (not directly verified): acknowledges that the mechanism is normative and predictions are correlational. The 2015 paper is the version most CTC critiques engage with.
- **Bears on:** causal-CTC (canonical modern statement).
- **Notes:** This is the version the project should treat as the operational CTC hypothesis.

---

## 3. Womelsdorf, T., Schoffelen, J.-M., Oostenveld, R., Singer, W., Desimone, R., Engel, A. K. & Fries, P. (2007). Modulation of neuronal interactions through neuronal synchronization. *Science*, 316(5831), 1609–1612.
- **DOI/URL:** 10.1126/science.1139597 (https://www.science.org/doi/10.1126/science.1139597; full PDF: https://pure.mpg.de/rest/items/item_1566173_3/component/file_1566384/content)
- **Source quality:** Abstract verified; MPG full-text URL exists but I did not render the PDF — read from abstract + summaries. Flagged as abstract-only for the detailed methods.
- **Core claim:** The mutual influence between gamma-band-synchronized neuronal groups depends on their **phase relation**: at "good" phases interactions are strong, at "bad" phases they are weak.
- **Method:** Multi-site LFP/MUA recordings in awake macaque cat visual cortex (and V4 in monkey), measured power–power correlation and transfer entropy as a function of inter-group gamma phase difference.
- **Key result:** Power–power correlation and transfer entropy between gamma-synchronized sites varied systematically and ~periodically with gamma phase offset; phase relations preceded the interaction by a few ms, consistent with a mechanistic (causal) role.
- **Limitations (stated):** Correlational; observed in V4 / cat visual cortex; "consistent with" a mechanistic role rather than proof. (Inference from abstract; not all caveats verified in full text.)
- **Bears on:** causal-CTC (the empirical phase-tuning result the project's Experiment 1 is designed to replicate in silico).
- **Notes:** This is the empirical anchor for H1 in the spec.

---

## 4. Börgers, C. & Kopell, N. (2008). Gamma oscillations and stimulus selection. *Neural Computation*, 20(2), 383–414.
- **DOI/URL:** 10.1162/neco.2007.07-06-289 (https://direct.mit.edu/neco/article/20/2/383/7267)
- **Source quality:** Abstract + journal summary; not full text. Flagged.
- **Core claim:** When two excitatory input streams converge on a target population with PING-style E–I circuitry, the **more coherent** input gains a strong competitive advantage, especially when the coherent input oscillates in the gamma band and the target's inhibition is GABA_A-mediated.
- **Method:** Network simulations (PING microcircuits, conductance-based).
- **Key result:** Coherent gamma input dominates the target's output; demonstrates a mechanistic role for gamma synchronization in stimulus selection. Provides theoretical scaffolding for CTC at the circuit level.
- **Limitations (stated):** Inferred: simulation-only; PING assumes a specific E–I tuning; results contingent on the GABA_A time constant.
- **Bears on:** causal-CTC (mechanistic plausibility), but note Schneider et al. (ref 9) explicitly criticize PING-based simulations for presupposing what they aim to demonstrate.
- **Notes:** Reference architecture for the spec's PING-based local-circuit choice.

---

## 5. Börgers, C., Epstein, S. & Kopell, N. J. (2008). Gamma oscillations mediate stimulus competition and attentional selection in a cortical network model. *PNAS*, 105(46), 18023–18028.
- **DOI/URL:** 10.1073/pnas.0809511105 (https://www.pnas.org/doi/full/10.1073/pnas.0809511105; PubMed 19004759)
- **Source quality:** Abstract + summary; not full text. Flagged.
- **Core claim:** Multi-stimulus presentations can suppress firing rates in extrastriate cortex through loss of inhibitory coherence; attention can restore gamma rhythmicity (and the competitive advantage) through cholinergic inhibition of fast-spiking interneurons.
- **Method:** Cortical network model with E cells and (at least) two classes of inhibitory interneurons, attentional modulation simulated as cholinergic input.
- **Key result:** Gamma rhythmicity is an emergent network property whose presence/absence biases stimulus competition; attention biases selection by restoring conditions for gamma in attended representations.
- **Limitations (stated):** Inferred: relies on a specific interneuron architecture; predictions about cholinergic interneurons were largely theoretical in 2008.
- **Bears on:** causal-CTC (provides the dual-stimulus / attentional-selection scaffolding for the project's H4).
- **Notes:** Relevant to H4 (selective routing). Note that Vinck et al. 2023 (ref 11) and Spyropoulos et al. 2024 (ref 13) revisit the cell-type / cholinergic story with cell-type-specific data that complicates this account.

---

## 6. Akam, T. & Kullmann, D. M. (2012). Efficient "communication through coherence" requires oscillations structured to minimize interference between signals. *PLoS Computational Biology*, 8(11), e1002760.
- **DOI/URL:** 10.1371/journal.pcbi.1002760 (https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1002760; PMC3493486)
- **Source quality:** Full-text abstract, intro, methods read via PMC (PMC3493486). Verified.
- **Core claim:** Coherent gain modulation in a receiver can in principle selectively route a population-coded target signal from converging distractors **only if** the oscillatory structure satisfies non-trivial constraints: target and distractors must differ in amplitude, phase, or frequency; same-band incoherent distractors severely degrade communication; modulation depth must be strong relative to Poisson spike noise.
- **Method:** Analytical/algorithmic model of a convergent pathway (multiple input networks → one receiver), with the receiver's gain modulation optimized via matched-filter / gradient-descent. 10,000-neuron Poisson input populations. Performance assessed by Fisher information / decoding accuracy of the target's spatial firing-rate pattern using locally optimal linear estimators.
- **Key result:** Provides quantitative proof-of-principle that CTC can route information selectively, but identifies previously unrecognized constraints (frequency/phase/amplitude separation of targets vs distractors; need for strong modulation). Decoding accuracy of the target is the explicit dependent variable — the spec adopts this readout style (Section 6.5).
- **Limitations (stated):** Algorithmic receiver, not biophysical; assumes a top-down control signal that pre-synchronizes the gain modulation with the target's rhythm (the more realistic case without this assumption is also examined).
- **Bears on:** both — supports causal-CTC in principle, but sharpens the conditions under which it can work.
- **Notes:** The project's decoder-based dependent variable follows this paper directly. Their convergent-pathway design also anticipates the spec's H4 (two-sender selective routing).

---

## 7. Bosman, C. A., Schoffelen, J.-M., Brunet, N., Oostenveld, R., Bastos, A. M., Womelsdorf, T., Rubehn, B., Stieglitz, T., De Weerd, P. & Fries, P. (2012). Attentional stimulus selection through selective synchronization between monkey visual areas. *Neuron*, 75(5), 875–888.
- **DOI/URL:** 10.1016/j.neuron.2012.06.037 (https://www.cell.com/neuron/fulltext/S0896-6273(12)00623-X; PMC3457649)
- **Source quality:** Abstract + summary; full PDF not rendered. Flagged.
- **Core claim:** When two V1 sites that each drive a common V4 site are presented simultaneously, V4 selectively gamma-synchronizes with the V1 site representing the **attended** stimulus; Granger causality runs V1→V4 in the gamma band more strongly than vice versa.
- **Method:** Multi-area ECoG/MUA recordings in awake macaques performing covert spatial attention with overlapping V1 receptive-field pairs converging onto V4.
- **Key result:** Selective inter-areal gamma synchronization tracks attention at 60–80 Hz; attended V1 sites show higher gamma frequency than unattended ones, producing systematic phase precession (a candidate mechanism for the selection).
- **Limitations (stated):** Inferred: correlational; relies on assuming LFP gamma coherence indexes effective communication — exactly the assumption Schneider et al. (ref 9) and Spyropoulos et al. (ref 13) later contest.
- **Bears on:** causal-CTC (the headline empirical attention finding cited in the CTC narrative). Also bears on the slight-gamma-frequency-shift mechanism the spec mentions for attention.
- **Notes:** A key reference for H4 (selective routing under matched-rate competing senders).

---

## 8. Bastos, A. M., Vezoli, J., Bosman, C. A., Schoffelen, J.-M., Oostenveld, R., Dowdall, J. R., De Weerd, P., Kennedy, H. & Fries, P. (2015). Visual areas exert feedforward and feedback influences through distinct frequency channels. *Neuron*, 85(2), 390–401.
- **DOI/URL:** 10.1016/j.neuron.2014.12.018 (https://www.cell.com/neuron/fulltext/S0896-6273(14)01099-X; PubMed 25556836; bioRxiv preprint: https://www.biorxiv.org/content/10.1101/004804.full.pdf)
- **Source quality:** Abstract + summary; full text not rendered. Flagged.
- **Core claim:** Across 8 macaque visual areas, **feedforward** Granger-causal influence is carried by theta (~4 Hz) and gamma (~60–80 Hz) bands, while **feedback** is carried by beta (~14–18 Hz).
- **Method:** ECoG recordings; pairwise Granger-causal analysis (using a "directed asymmetry index" DAI = [GCout − GCin] / [GCin + GCout]) and correlation of DAI with anatomical hierarchy (SLN, % supragranular labelled neurons from retrograde tracing).
- **Key result:** Significant positive DAI–SLN correlation for theta and gamma; significant negative correlation for beta. Establishes a frequency-asymmetric account of cortical hierarchy.
- **Limitations (stated):** Inferred: Granger causality measured on LFPs is exactly what Schneider et al. (ref 9) and Dowdall & Vinck (ref 12) later show can arise from synaptic mixing / breaks down with bidirectional delays.
- **Bears on:** causal-CTC at the systems level (frequency-channel feedforward/feedback story). The project's directional measure (Granger) traces to this paper.
- **Notes:** Influential but methodologically debated; treat as the canonical CTC-aligned systems-level finding and acknowledge the 2021/2023 critiques.

---

## 9. Schneider, M., Broggini, A. C., Dann, B., Tzanou, A., Uran, C., Sheshadri, S., Scherberger, H. & Vinck, M. (2021). A mechanism for inter-areal coherence through communication based on connectivity and oscillatory power. *Neuron*, 109(24), 4050–4067.e12.
- **DOI/URL:** 10.1016/j.neuron.2021.09.037 (https://www.cell.com/neuron/fulltext/S0896-6273(21)00710-8; PMC8691951; bioRxiv preprint with full text: https://www.biorxiv.org/content/10.1101/2020.06.17.156190v1; code: https://github.com/SchneiderMarius/coherence2021 and Zenodo 5507277)
- **Source quality:** Full intro, results, discussion read from bioRxiv preprint (the preprint and final paper share the same core analysis). Verified.
- **Core claim:** Inter-areal LFP–LFP coherence (and frequency-specific Granger causality) is the **consequence**, not the **cause**, of communication: it emerges automatically from synaptic mixing — afferent spikes from area 1 produce postsynaptic potentials in area 2 that are a delayed, scaled, partially coherent copy of area-1 activity.
- **Method:** Multi-area recordings (macaque parietal 7B and premotor F5; beta-band example) combined with (a) analytical derivation expressing inter-areal coherence as a function of sender oscillation strength (SOS), inter-areal connection weight w, projection-source coherence (depending on number of projecting neurons N_p and individual spike-LFP PPC), and (b) numerical simulations using autoregressive AR(2) models and Wilson-Cowan E/I networks. Bidirectional gamma/beta simulations reproduce Bastos-2015-like Granger spectra without invoking frequency-channel coupling.
- **Key result:** Closed-form expression C²(f) ∝ w²·φ²(f)·... predicts that 2-fold changes in sender spike-LFP coherence or firing rate can produce 16-fold changes in squared inter-areal coherence. A clear LFP-LFP beta-coherence peak between 7B and F5 is observed despite no detectable beta spiking entrainment in F5 — reproducible by the synaptic-mixing model. Wilson-Cowan E/I simulations show that spiking entrainment in the receiver contributes substantially to LFP coherence **only** when sender and receiver oscillate at the same (resonant) frequency.
- **Limitations (stated):** Authors note: hard to distinguish "intrinsic" oscillations from mixed afferent rhythms using LFP alone; argue for spike-based and laminar (CSD/ICA) analyses; concede that consistent "bad" phase relationships *could* in principle block communication and are not captured by mixing models.
- **Bears on:** epiphenomenal (the central counter-hypothesis the project tests).
- **Notes:** This is the paper the project's phase-scramble experiment is designed to adjudicate. Their published code (SchneiderMarius/coherence2021) is a useful reference implementation. They explicitly identify gain modulation, dendritic inhibition and neuromodulators as alternative routes by which "communication" (and hence coherence) can be modulated rapidly, without requiring CTC-style phase gating.

---

## 10. Vinck, M., Uran, C., Spyropoulos, G., Onorato, I., Broggini, A. C., Schneider, M. & Canales-Johnson, A. (2023). Principles of large-scale neural interactions. *Neuron*, 111(7), 987–1002.
- **DOI/URL:** 10.1016/j.neuron.2023.03.015 (https://www.cell.com/neuron/fulltext/S0896-6273(23)00211-8; PubMed 37023720)
- **Source quality:** Abstract + extended summary; full text not rendered. Flagged.
- **Core claim:** Comprehensive review proposing **four** mechanisms for inter-areal communication: (i) oscillatory synchronization (CTC); (ii) communication-through-resonance; (iii) non-linear integration; (iv) linear signal transmission (coherence-through-communication). Argues (ii)–(iv) are viable alternatives to (i) for flexible, selective communication.
- **Method:** Review of layer- and cell-type-specific spike phase-locking data, computational models, and recordings across cortical areas.
- **Key result:** Inter-areal gamma coherence in monkey V1–V2/V4 is mostly inconsistent with intrinsic oscillator coupling; rat CA1, V1, S1, perirhinal lacks inter-areal gamma phase-locking despite local gamma. Suggests gamma feedforward / alpha-beta feedback story is not robust to these challenges.
- **Limitations (stated):** Inferred: a review; conclusions hinge on the interpretation of LFP vs spike data and on the cell-type / layer-resolved studies the authors and their lab have led.
- **Bears on:** epiphenomenal (extends Schneider 2021 into a general theoretical framework). Important background for the Discussion section of the planned paper.
- **Notes:** Provides the modern taxonomy (resonance vs. mixing vs. CTC) the project's interpretation can position itself within.

---

## 11. Dowdall, J. R. & Vinck, M. (2023). Coherence fails to reliably capture inter-areal interactions in bidirectional neural systems with transmission delays. *NeuroImage*, 271, 119998.
- **DOI/URL:** 10.1016/j.neuroimage.2023.119998 (https://www.sciencedirect.com/science/article/pii/S1053811923001441; PubMed 36863546; PMC7614400)
- **Source quality:** Abstract + summary; full text not rendered. Flagged.
- **Core claim:** Coherence and Granger-Geweke causality are unreliable indices of bidirectional interactions when transmission delays produce destructive interference in the cross-covariance function — coherence can be entirely abolished even when a true bidirectional interaction exists.
- **Method:** Analytical derivation and numerical simulations of bidirectionally coupled oscillators with various delays and overlapping spectra; introduces two alternative methods that mitigate the interference problem.
- **Key result:** For overlapping spectra in bidirectional systems with delays, coherence (and standard Granger) can dramatically under- or mis-estimate true coupling; the magnitude of this failure depends sensitively on delay structure.
- **Limitations (stated):** Inferred: methodological focus; effects shown in simulations and analytical models, not directly in vivo.
- **Bears on:** epiphenomenal-side methodology critique — undermines the interpretation of CTC-aligned coherence measurements.
- **Notes:** Worth citing in the Discussion when interpreting the project's coherence vs. transfer-entropy/Granger comparisons.

---

## 12. Dowdall, J. R., Schneider, M. & Vinck, M. (2023). Attentional modulation of inter-areal coherence explained by frequency shifts. *NeuroImage*, 278, 120256.
- **DOI/URL:** 10.1016/j.neuroimage.2023.120256 (https://www.sciencedirect.com/science/article/pii/S105381192300407X; PubMed 37392809; PMC7616852)
- **Source quality:** Abstract + summary; full text not rendered. Flagged.
- **Core claim:** Attention- and salience-related changes in V1 gamma **peak frequency** can produce most of the observed attentional modulation of inter-areal V1–V4 gamma coherence, without invoking selective inter-areal phase-locking.
- **Method:** Simulations and re-analysis: change in coherence magnitude is shown to be driven by sender peak frequency; coherence pattern depends on whether receiver integrates or resonates.
- **Key result:** "Selective synchronization" observed in attention (Bosman et al. 2012, ref 7) can be reproduced by sender frequency shifts alone in the synaptic-mixing / coherence-through-communication framework.
- **Limitations (stated):** Inferred: shows alternative explanation is sufficient, not that CTC explanations are wrong.
- **Bears on:** epiphenomenal (direct re-interpretation of the Bosman et al. 2012 attentional finding).
- **Notes:** Highly relevant to H4 (selective routing) — provides the counter-explanation the project should engage with.

---

## 13. Spyropoulos, G., Schneider, M., van Kempen, J., Gieselmann, M. A., Thiele, A. & Vinck, M. (2024). Distinct feedforward and feedback pathways for cell-type specific attention effects. *Neuron*, 112(14), 2423–2434.
- **DOI/URL:** 10.1016/j.neuron.2024.04.020 (https://www.cell.com/neuron/fulltext/S0896-6273(24)00281-2; PubMed 38759641; PMC7616856; bioRxiv: https://www.biorxiv.org/content/10.1101/2022.11.04.515185v3.full)
- **Source quality:** Abstract + summary; full text not rendered. Flagged.
- **Core claim:** Although attention increases V1–V4 gamma LFP–LFP phase-locking, the V1 gamma rhythm engages **only** fast-spiking interneurons in V4 L4 — **not** V4 excitatory cells. The attentional firing-rate enhancement in V4 excitatory neurons is largest in L2/3 and precedes V1 in time, suggesting a feedback rather than a feedforward effect.
- **Method:** Simultaneous laminar/cell-type-specific recordings in V1 and V4 of macaques performing attention; cell classification (broad/narrow spike), Granger and phase-locking analyses by layer and cell type.
- **Key result:** Dissociates feedforward synchronization (gamma; engages only L4 PV-like interneurons) from feedback rate enhancement (L2/3, leading V1). Empirically challenges the cell-type-agnostic CTC story for attention.
- **Limitations (stated):** Inferred: V1–V4 system specifically; interpretation of layer-specific Granger depends on signal quality.
- **Bears on:** both — refines what gamma synchronization actually does at cell-type resolution; weakens the strong-form "gamma coherence drives V4 excitatory spiking" reading of Bosman 2012.
- **Notes:** Crucial recent empirical constraint for the Discussion; suggests CTC, if it exists, is engaging interneurons more than principal cells.

---

## 14. Vinck, M., Uran, C., Dowdall, J. R., Rummell, B. & Canales-Johnson, A. (2024). Large-scale interactions in predictive processing: oscillatory versus transient dynamics. *Trends in Cognitive Sciences*, 28(11), 1056–1074.
- **DOI/URL:** 10.1016/j.tics.2024.09.013 (https://www.cell.com/trends/cognitive-sciences/fulltext/S1364-6613(24)00256-0; PubMed 39424521; PMC7616854; PsyArXiv: https://psyarxiv.com/n3afb)
- **Source quality:** Abstract + summary; full text not rendered. Flagged.
- **Core claim:** Reviews evidence that **transient, aperiodic** dynamics — not sustained oscillations — may be the principal substrate for inter-areal communication during sensory inference, while oscillations stabilize representations and support plasticity. Critiques the gamma-feedforward / alpha-beta-feedback dichotomy.
- **Method:** Review; integrates predictive-coding theory with empirical critique of oscillatory communication.
- **Key result:** Narrow-band gamma tends to increase for *predicted* stimuli (when stable representations dominate), broadband gamma tends to increase for *unpredicted* stimuli — opposite to a naive predictive-routing-via-gamma account.
- **Limitations (stated):** Inferred: a perspective paper; selective citation toward the authors' framework.
- **Bears on:** epiphenomenal (and complementary to it: argues the alternative is aperiodic transmission).
- **Notes:** Background for situating CTC in the wider predictive-coding debate.

---

## 15. Greenwood, P. E. & Ward, L. M. (2024). Attentional selection and communication through coherence: Scope and limitations. *PLoS Computational Biology*, 20(8), e1011431.
- **DOI/URL:** 10.1371/journal.pcbi.1011431 (https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1011431; PubMed 39102437; PMC11326628; bioRxiv: https://www.biorxiv.org/content/10.1101/2023.08.16.553483v1)
- **Source quality:** Abstract + extended summary; full text not rendered. Flagged.
- **Core claim:** Interaction between 10 Hz and 40 Hz oscillations in a computational model can produce increases in inter-areal coherence and information transmission consistent with CTC, but with important limitations.
- **Method:** Computational model of two cortical areas with attention modulating 10 Hz / 40 Hz oscillatory interaction; quantifies coherence and information transmission across parameter regimes.
- **Key result:** A bounded defense of CTC: synchronization between oscillations *can* facilitate communication, especially under selective attention; outside that regime the causal arrow may run the other way (consistent with coherence-through-communication).
- **Limitations (stated):** Authors note the model's sensitivity to parameters and that the coherence→communication direction is not universal.
- **Bears on:** both — recent attempt to delineate the *scope* of causal CTC; useful for the Discussion's "when (if ever) is CTC causal?" framing.
- **Notes:** Closest available 2024 paper that engages the Schneider 2021 challenge from a CTC-leaning angle.

---

## 16. Vezoli, J., Vinck, M., Bosman, C. A., Bastos, A. M., Lewis, C. M., Kennedy, H. & Fries, P. (2021). Brain rhythms define distinct interaction networks with differential dependence on anatomy. *Neuron*, 109(23), 3862–3878.e5.
- **DOI/URL:** 10.1016/j.neuron.2021.09.052 (https://www.cell.com/neuron/fulltext/S0896-6273(21)00725-X; PubMed 34672985; PMC8639786)
- **Source quality:** Abstract + summary; full text not rendered. Flagged.
- **Core claim:** Functional inter-areal networks defined by coherence, power correlation, and Granger causality in theta, beta, high-beta and gamma bands are largely independent across rhythms; coherence and Granger correlate with anatomical projection strength (largest effect for Granger).
- **Method:** ECoG across 105 area pairs (macaque), correlated with retrograde tracing across 91 pairs.
- **Key result:** Establishes empirically that band-specific functional networks differ; the anatomy–function link is strongest for Granger causality in specific bands.
- **Limitations (stated):** Inferred: correlational; LFP signals subject to mixing concerns raised in companion paper Schneider 2021 (same lab, same issue of Neuron).
- **Bears on:** both — supports frequency-channel idea while constraining its anatomical substrate. Useful neutral-background reference for the planned paper's introduction.
- **Notes:** Same lab as ref 9; published in the same year and engages many of the same data sets.

---

## 17. Akam, T. & Kullmann, D. M. (2010). Oscillations and filtering networks support flexible routing of information. *Neuron*, 67(2), 308–320.
- **DOI/URL:** Cited only as background in Akam & Kullmann 2012 (ref 6), reference [15] therein; I did not retrieve a standalone search hit and so omit a DOI. **I could not directly retrieve a resolvable identifier in this session — listed for reference only and not cited.**
- **Source quality:** Not retrieved. Flagged.
- **Notes:** Marked as a candidate worth searching later if the project's Discussion benefits from the earlier convergent-pathway model.

---

## 18. Quax, S., Jensen, O. & Tiesinga, P. (2017). Top-down control of cortical gamma-band communication via pulvinar-induced phase shifts in the alpha rhythm. *PLoS Computational Biology*, 13(5), e1005519.
- **DOI/URL:** 10.1371/journal.pcbi.1005519 (https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1005519; PubMed 28472057; PMC5436894)
- **Source quality:** Abstract + summary; full text not rendered. Flagged.
- **Core claim:** Pulvinar-driven alpha phase shifts can modulate cortical gamma coherence between two PING areas, providing a candidate mechanism for top-down control of CTC.
- **Method:** Network model of two unidirectionally connected spiking PING populations with pulvinar-derived alpha modulation; quantifies V1→V4-like gamma coherence as a function of alpha phase difference.
- **Key result:** Shifting the alpha phase between the two cortical areas modulates inter-areal gamma coherence and information transmission — supports a causal role for phase coordination at multiple frequencies.
- **Limitations (stated):** Inferred: unidirectional, idealized; not all parameter regimes tested.
- **Bears on:** causal-CTC (provides a mechanism for *how* phase could be manipulated by top-down control, complementary to the spec's artificial phase-channel intervention).
- **Notes:** Useful "what could the brain implement?" reference for the spec's phase-channel.

---

## 19. Bastos, A. M., Lundqvist, M., Waite, A. S., Kopell, N. & Miller, E. K. (2020). Layer and rhythm specificity for predictive routing. *PNAS*, 117(49), 31459–31469.
- **DOI/URL:** 10.1073/pnas.2014868117 (https://www.pnas.org/doi/10.1073/pnas.2014868117; PMC7733827; bioRxiv: https://www.biorxiv.org/content/10.1101/2020.01.27.921783v1)
- **Source quality:** Abstract + summary; full text not rendered. Flagged.
- **Core claim:** Empirical/predictive-coding extension of the feedforward-gamma / feedback-alpha-beta story: predicted stimuli show enhanced superficial-layer alpha/beta that suppresses deep-layer gamma; unpredicted stimuli release deep gamma. Frames CTC-style frequency channels within a predictive-routing account.
- **Method:** Laminar recordings (Utah probes) in monkey prefrontal/sensory cortex during a working-memory task with manipulated stimulus predictability.
- **Key result:** Layer-specific alpha/beta and gamma show predictability-dependent dynamics consistent with predictive routing.
- **Limitations (stated):** Inferred: correlational; specific to the tested areas.
- **Bears on:** causal-CTC (extends the Bastos 2015 story); flagged because ref 14 (Vinck et al. 2024 TICS) criticises this framework.
- **Notes:** Useful for the Introduction's account of why frequency channels matter and how the predictive-coding framing sits on top of CTC.

---

## 20. Palmigiano, A., Geisel, T., Wolf, F. & Battaglia, D. (2017). Flexible information routing by transient synchrony. *Nature Neuroscience*, 20(7), 1014–1022.
- **DOI/URL:** 10.1038/nn.4569 (https://www.nature.com/articles/nn.4569; PubMed 28530664; full PDF: https://funsyteam.org/wp-content/uploads/2022/12/palmigiano-et-al-2017.pdf)
- **Source quality:** Abstract + summary; full PDF available but not rendered here. Flagged.
- **Core claim:** Even short, irregular **bursts** of gamma can selectively route information through "large-scale routing states" in a canonical multi-area circuit; transient synchrony — not sustained coherence — suffices.
- **Method:** Multi-area spiking network simulations near the onset of oscillatory synchrony; analyses of information routing.
- **Key result:** Reconciles the stochastic, transient empirical character of in-vivo gamma with a CTC-style functional role.
- **Limitations (stated):** Inferred: simulation-only; tested in canonical circuits.
- **Bears on:** causal-CTC (a transient-synchrony defense), but also bridges to the aperiodic-transient view of ref 14.
- **Notes:** Worth citing as a precedent for CTC-leaning models that engage with the temporal-irregularity critique.

---

## Sources I could not retrieve (or only obtained from indirect references)

- **Akam & Kullmann 2010** (*Neuron*, "Oscillations and filtering networks support flexible routing of information"). Cited in ref 6's reference list but I did not run a clean independent search/retrieval. Omitted from numbered list above.
- **Several full PDFs** behind paywalls (Fries 2005, Fries 2015, Womelsdorf 2007, Börgers & Kopell 2008, Börgers Epstein Kopell 2008, Bosman 2012, Bastos 2015): I was able to retrieve DOIs, journal URLs, and abstracts/search-engine summaries, but not the full text. The annotations for these are conservatively based on the abstract, search-result summaries, and (for Bastos 2015) the bioRxiv preprint version. The Schneider 2021 annotation is anchored on the bioRxiv preprint full text (https://www.biorxiv.org/content/10.1101/2020.06.17.156190v1), which matches the published version's central claims.
- **PubMed pages** were inaccessible via the fetch tool (reCAPTCHA wall), but PubMed IDs are recorded above for human verification.

All DOIs above were located via search results; before submission, the author should re-verify each DOI by following the link, and replace any annotation that requires nuance only present in the full text.
