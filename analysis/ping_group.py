"""
Single-group PING microcircuit (Brian2).

A local excitatory–inhibitory (E–I) network that generates a gamma rhythm
endogenously via the pyramidal-interneuron-gamma (PING) mechanism.

Defaults follow CTC_causality_simulation_spec.md, Section 5:
  - LIF neurons, conductance-based AMPA / GABA_A synapses
  - 200 E / 50 I per group (dev scale); 800 / 200 for final
  - AMPA decay ~2-3 ms, GABA_A decay ~8-10 ms (sets gamma period)
  - 10-20% sparse within-group connectivity
  - Independent Poisson background drive

Tune the coupling so the population fires synchronously at 50-70 Hz with
excitation leading inhibition by ~2-3 ms (Section 5.5).
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional

import brian2 as b2
import numpy as np


# -- units shortcut ---------------------------------------------------------
mV = b2.mV
ms = b2.ms
Hz = b2.Hz
nS = b2.nS
pF = b2.pF
pA = b2.pA


@dataclass
class PINGConfig:
    """All numbers in SI-like units understood by Brian2. Defaults per spec."""

    # Population sizes (dev = 200/50, full = 800/200)
    N_E: int = 200
    N_I: int = 50

    # Membrane (LIF)
    tau_m_E: float = 20.0    # ms
    tau_m_I: float = 10.0    # ms
    V_rest_E: float = -65.0  # mV
    V_rest_I: float = -65.0  # mV
    V_th: float = -50.0      # mV
    V_reset: float = -65.0   # mV
    t_ref_E: float = 2.0     # ms
    t_ref_I: float = 1.0     # ms

    # Capacitance (LIF normalized) — C = tau_m * g_L; g_L = 10 nS by convention
    g_L_E: float = 10.0      # nS
    g_L_I: float = 10.0      # nS

    # Synapses (conductance-based)
    tau_AMPA: float = 2.5    # ms  (decay)
    tau_GABA: float = 8.0    # ms  (decay; controls gamma period)
    E_AMPA: float = 0.0      # mV
    E_GABA: float = -75.0    # mV

    # Within-group connection probabilities
    p_EE: float = 0.15
    p_EI: float = 0.20  # E -> I
    p_IE: float = 0.20  # I -> E
    p_II: float = 0.20

    # Within-group conductance per connection (peak)
    g_EE: float = 0.10  # nS
    g_EI: float = 0.50  # nS  (E drives I — strong, recruits PING)
    g_IE: float = 0.80  # nS  (I clamps E — strong, sets duty cycle)
    g_II: float = 0.20  # nS

    # Synaptic delays (intra-group)
    delay_intra: float = 0.5  # ms

    # Background Poisson drive (independent per cell)
    bg_rate_E: float = 1600.0  # Hz  (combined external excitation)
    bg_rate_I: float = 1600.0  # Hz
    g_bg_E: float = 0.20       # nS per background event onto E cell
    g_bg_I: float = 0.20       # nS per background event onto I cell

    # External drive (stimulus). When >0, applied as extra mean current.
    drive_E: float = 200.0     # pA  (default tonic drive to E cells)
    drive_I: float = 0.0       # pA

    # Simulation
    dt: float = 0.1            # ms
    name: str = "G"            # group name prefix

    # H3: disable_oscillation flag. When True, set within-group E↔I coupling
    # to zero so the receiver cannot generate its own gamma rhythm. Used to
    # ask whether receiver oscillation is required for phase-gating
    # (spec §3, Table H3).
    disable_oscillation: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


class PINGGroup:
    """Wraps one PING microcircuit: E and I NeuronGroups plus internal synapses.

    Build the group, then optionally attach external input (other PING groups,
    a phase-scramble channel, a SpikeGeneratorGroup) by exposing `self.E` and
    `self.I` as targets and `self.spikemon_E`, `self.spikemon_I`, etc.
    """

    def __init__(self, cfg: Optional[PINGConfig] = None, rng_seed: int = 0):
        self.cfg = cfg or PINGConfig()
        self.rng_seed = rng_seed
        b2.seed(rng_seed)

        c = self.cfg
        ns = c.name

        # ---- LIF + conductance-based synapse equations ------------------
        # State variables on each neuron: v, g_e (AMPA), g_i (GABA)
        eqs_E = f"""
        dv/dt = (-g_L*(v - V_rest) - g_e*(v - E_AMPA) - g_i*(v - E_GABA) + I_drive) / C : volt (unless refractory)
        dg_e/dt = -g_e / tau_AMPA : siemens
        dg_i/dt = -g_i / tau_GABA : siemens
        I_drive : amp
        """
        eqs_I = eqs_E  # same structure; we'll set parameters in namespaces

        ns_E = {
            "g_L": c.g_L_E * nS,
            "C": c.g_L_E * c.tau_m_E * nS * ms,  # C = g_L * tau_m
            "V_rest": c.V_rest_E * mV,
            "E_AMPA": c.E_AMPA * mV,
            "E_GABA": c.E_GABA * mV,
            "tau_AMPA": c.tau_AMPA * ms,
            "tau_GABA": c.tau_GABA * ms,
        }
        ns_I = {
            "g_L": c.g_L_I * nS,
            "C": c.g_L_I * c.tau_m_I * nS * ms,
            "V_rest": c.V_rest_I * mV,
            "E_AMPA": c.E_AMPA * mV,
            "E_GABA": c.E_GABA * mV,
            "tau_AMPA": c.tau_AMPA * ms,
            "tau_GABA": c.tau_GABA * ms,
        }

        self.E = b2.NeuronGroup(
            c.N_E, eqs_E,
            threshold=f"v > {c.V_th}*mV",
            reset=f"v = {c.V_reset}*mV",
            refractory=c.t_ref_E * ms,
            method="euler",
            namespace=ns_E,
            name=f"{ns}_E",
        )
        self.I = b2.NeuronGroup(
            c.N_I, eqs_I,
            threshold=f"v > {c.V_th}*mV",
            reset=f"v = {c.V_reset}*mV",
            refractory=c.t_ref_I * ms,
            method="euler",
            namespace=ns_I,
            name=f"{ns}_I",
        )

        # Initial conditions: random voltages near rest to desynchronize
        rng = np.random.default_rng(rng_seed)
        self.E.v = (c.V_rest_E + rng.uniform(-5, 5, c.N_E)) * mV
        self.I.v = (c.V_rest_I + rng.uniform(-5, 5, c.N_I)) * mV
        self.E.g_e = 0 * nS
        self.E.g_i = 0 * nS
        self.I.g_e = 0 * nS
        self.I.g_i = 0 * nS
        self.E.I_drive = c.drive_E * pA
        self.I.I_drive = c.drive_I * pA

        # ---- Within-group synapses --------------------------------------
        # If disable_oscillation is set, zero the E↔I coupling that gives the
        # PING rhythm. E→E and I→I are kept so the group still has its
        # baseline recurrent statistics; only the rhythm-generating loop is
        # broken. (H3 manipulation, spec §3 Table.)
        g_EI_eff = 0.0 if c.disable_oscillation else c.g_EI
        g_IE_eff = 0.0 if c.disable_oscillation else c.g_IE

        self.S_EE = b2.Synapses(self.E, self.E, on_pre=f"g_e_post += {c.g_EE}*nS",
                                delay=c.delay_intra * ms, name=f"{ns}_S_EE")
        self.S_EE.connect(p=c.p_EE, condition="i != j")

        self.S_EI = b2.Synapses(self.E, self.I, on_pre=f"g_e_post += {g_EI_eff}*nS",
                                delay=c.delay_intra * ms, name=f"{ns}_S_EI")
        self.S_EI.connect(p=c.p_EI)

        self.S_IE = b2.Synapses(self.I, self.E, on_pre=f"g_i_post += {g_IE_eff}*nS",
                                delay=c.delay_intra * ms, name=f"{ns}_S_IE")
        self.S_IE.connect(p=c.p_IE)

        self.S_II = b2.Synapses(self.I, self.I, on_pre=f"g_i_post += {c.g_II}*nS",
                                delay=c.delay_intra * ms, name=f"{ns}_S_II")
        self.S_II.connect(p=c.p_II, condition="i != j")

        # ---- Background drive (independent Poisson on each cell) --------
        self.bg_E = b2.PoissonInput(self.E, "g_e", N=1, rate=c.bg_rate_E * Hz,
                                    weight=f"{c.g_bg_E}*nS")
        self.bg_I = b2.PoissonInput(self.I, "g_e", N=1, rate=c.bg_rate_I * Hz,
                                    weight=f"{c.g_bg_I}*nS")

        # ---- Monitors ---------------------------------------------------
        self.spikemon_E = b2.SpikeMonitor(self.E, name=f"{ns}_sm_E")
        self.spikemon_I = b2.SpikeMonitor(self.I, name=f"{ns}_sm_I")
        # LFP proxy: summed synaptic conductance on E cells, sampled every dt
        self.popmon_E = b2.PopulationRateMonitor(self.E, name=f"{ns}_rm_E")
        self.popmon_I = b2.PopulationRateMonitor(self.I, name=f"{ns}_rm_I")
        # State monitor for LFP proxy (mean g_e + g_i across E cells)
        self.statemon_E = b2.StateMonitor(self.E, ["g_e", "g_i"],
                                          record=range(min(50, c.N_E)),
                                          name=f"{ns}_stm_E")

    @property
    def brian_objects(self):
        """All Brian2 objects to add to a Network."""
        return [
            self.E, self.I,
            self.S_EE, self.S_EI, self.S_IE, self.S_II,
            self.bg_E, self.bg_I,
            self.spikemon_E, self.spikemon_I,
            self.popmon_E, self.popmon_I,
            self.statemon_E,
        ]


def run_isolated(cfg: Optional[PINGConfig] = None, duration_ms: float = 1000.0,
                 rng_seed: int = 0) -> dict:
    """Run a single PING group in isolation. Returns a dict of recorded outputs.

    Used by the calibration script (task 6) to verify Section 5.5 benchmarks
    before wiring the channel.
    """
    b2.start_scope()
    b2.defaultclock.dt = (cfg.dt if cfg else 0.1) * ms
    grp = PINGGroup(cfg=cfg, rng_seed=rng_seed)
    net = b2.Network(grp.brian_objects)
    net.run(duration_ms * ms, report=None)

    return {
        "config": grp.cfg.to_dict(),
        "seed": rng_seed,
        "duration_ms": duration_ms,
        "spikes_E_t": np.asarray(grp.spikemon_E.t / ms),
        "spikes_E_i": np.asarray(grp.spikemon_E.i),
        "spikes_I_t": np.asarray(grp.spikemon_I.t / ms),
        "spikes_I_i": np.asarray(grp.spikemon_I.i),
        "rate_E_t": np.asarray(grp.popmon_E.t / ms),
        "rate_E": np.asarray(grp.popmon_E.smooth_rate(window="gaussian", width=1 * ms) / Hz),
        "rate_I": np.asarray(grp.popmon_I.smooth_rate(window="gaussian", width=1 * ms) / Hz),
        "lfp_proxy_t": np.asarray(grp.statemon_E.t / ms),
        # LFP proxy ≈ mean synaptic conductance on E cells
        "lfp_proxy": np.asarray(
            (grp.statemon_E.g_e + grp.statemon_E.g_i).mean(axis=0) / nS
        ),
    }


if __name__ == "__main__":
    # Quick self-check: run for 500 ms and report a few headline numbers
    out = run_isolated(duration_ms=500.0, rng_seed=0)
    rE = out["rate_E"]
    rI = out["rate_I"]
    print(f"Mean E rate: {rE.mean():.2f} Hz, Mean I rate: {rI.mean():.2f} Hz")
    print(f"#E spikes: {len(out['spikes_E_t'])}, #I spikes: {len(out['spikes_I_t'])}")
