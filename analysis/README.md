# /analysis

Simulation code, channels, analysis pipeline, and raw results.

## Layout
- `ping_group.py` — single-group PING microcircuit (Brian2)
- `channels.py` — phase-scramble + rate-matched Poisson channels
- `network.py` — sender → channel → receiver topology + stimulus drive
- `metrics.py` — rates, LFP-proxy power, coherence, PPC, Granger, transfer
  entropy, linear decoder
- `exp1_phase_tuning.py` — Experiment 1 runner (H1)
- `exp2_causal_disruption.py` — Experiment 2 runner (H2)
- `results/` — per-experiment outputs (one subfolder per experiment), each
  containing raw .npz/.h5 data + a machine-readable config.yaml
- `tests/` — unit tests, especially the phase-scramble triple-check on
  synthetic input
- `requirements.txt` — pinned Python dependencies

## Rules
- Every numeric result must come from a script saved here.
- Every random seed is fixed and logged in the per-run config.
- Analysis pipeline reads stored simulation outputs so conditions can be
  re-analyzed without re-running (spec Section 7).
