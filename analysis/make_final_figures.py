"""
Regenerate the headline figures from saved summary.json files (so both dev
and full-scale versions are available side-by-side in /figures/).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


HERE = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(os.path.dirname(HERE), "figures")
os.makedirs(FIG_DIR, exist_ok=True)


def load(path):
    with open(path) as fh:
        return json.load(fh)


def causal_figure(summary, suffix, title):
    """Two-panel: decoding by condition; γ coherence by condition."""
    conds = [r["condition"] for r in summary]
    accs = np.array([r["decode_acc_mean"] for r in summary])
    se = np.array([r["decode_acc_se"] for r in summary])
    gc = np.array([r["gamma_coherence_mean"] for r in summary])
    gc_se = np.array([r["gamma_coherence_sd"] / np.sqrt(max(r["gamma_coherence_n"], 1))
                      for r in summary])
    colors = {"intact": "#1f77b4", "scramble": "#d62728", "poisson": "#7f7f7f"}
    xs = np.arange(len(conds))

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].bar(xs, accs, yerr=1.96 * se, capsize=5,
                color=[colors.get(c, "C5") for c in conds])
    axes[0].axhline(summary[0]["decode_chance"], ls="--", color="gray", label="chance")
    axes[0].set_xticks(xs)
    axes[0].set_xticklabels(conds)
    axes[0].set_ylabel("Decoding accuracy (mean ± 95% CI)")
    axes[0].set_ylim(0, 1.05)
    axes[0].set_title("a. Stimulus decoding")
    axes[0].legend(loc="upper right")

    axes[1].bar(xs, gc, yerr=1.96 * gc_se, capsize=5,
                color=[colors.get(c, "C5") for c in conds])
    axes[1].set_xticks(xs)
    axes[1].set_xticklabels(conds)
    axes[1].set_ylabel("Sender → receiver γ-coherence")
    axes[1].set_ylim(0, max(gc) * 1.3 + 0.05)
    axes[1].set_title("b. γ-band coherence")

    fig.suptitle(title, fontweight="bold")
    fig.tight_layout()
    fp = os.path.join(FIG_DIR, f"fig_causal_test{suffix}.png")
    fig.savefig(fp, dpi=140)
    print(f"  {fp}")


def manip_figure(summary, suffix, title):
    conds = [r["condition"] for r in summary]
    colors = {"intact": "#1f77b4", "scramble": "#d62728", "poisson": "#7f7f7f"}
    xs = np.arange(len(conds))

    fig, axes = plt.subplots(1, 4, figsize=(14, 4))

    def bars(ax, key, label):
        m = np.array([r[f"{key}_mean"] for r in summary])
        sd = np.array([r[f"{key}_sd"] for r in summary])
        n = np.array([r[f"{key}_n"] for r in summary])
        se = sd / np.sqrt(np.maximum(n, 1))
        ax.bar(xs, m, yerr=1.96 * se, capsize=5,
               color=[colors.get(c, "C5") for c in conds])
        ax.set_xticks(xs)
        ax.set_xticklabels(conds)
        ax.set_ylabel(label)

    # Prefer DELIVERED-signal metrics (post-channel) — this is the actual
    # manipulation check (reviewer round 1, B1). Fall back to sender if
    # delivered keys aren't present (older summaries).
    rate_key = "delivered_rate_hz" if f"delivered_rate_hz_mean" in summary[0] else "sender_rate_hz"
    pow_key = "delivered_gamma_power" if f"delivered_gamma_power_mean" in summary[0] else "sender_gamma_power"
    coh_key = "delivered_coherence" if f"delivered_coherence_mean" in summary[0] else "gamma_coherence"

    bars(axes[0], rate_key, "Delivered E rate (Hz)" if rate_key.startswith("delivered")
         else "Sender E rate (Hz)")
    axes[0].set_title("Rate — preserved")
    bars(axes[1], pow_key, "Delivered γ power (a.u.)" if pow_key.startswith("delivered")
         else "Sender γ power (a.u.)")
    axes[1].set_title("Power — preserved")
    bars(axes[2], coh_key, "Sender ↔ delivered γ coh." if coh_key.startswith("delivered")
         else "Sender → receiver γ coh.")
    axes[2].set_title("Coherence — manipulated")
    bars(axes[3], "granger_F_sr", "Granger F (sender → receiver)")
    axes[3].set_title("Directed influence")
    fig.suptitle(title, fontweight="bold")
    fig.tight_layout()
    fp = os.path.join(FIG_DIR, f"fig_manipulation_check{suffix}.png")
    fig.savefig(fp, dpi=140)
    print(f"  {fp}")


def phase_tuning_figure(summary, suffix, title, n_stim=4):
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    ds = np.array([r["delay_ms"] for r in summary])

    def plot_metric(ax, key, ylabel, color):
        m = np.array([r[f"{key}_mean"] for r in summary])
        sd = np.array([r[f"{key}_sd"] for r in summary])
        n = np.array([r[f"{key}_n"] for r in summary])
        se = sd / np.sqrt(np.maximum(n, 1))
        ax.errorbar(ds, m, yerr=1.96 * se, color=color, marker="o",
                    capsize=3, lw=1.5)
        ax.set_xlabel("Conduction delay (ms)")
        ax.set_ylabel(ylabel)
        ax.grid(alpha=0.3)

    plot_metric(axes[0], "decode_acc", "Decoding accuracy", "C0")
    axes[0].axhline(1.0 / n_stim, ls="--", color="gray", label="chance")
    axes[0].set_ylim(0, 1.05)
    axes[0].set_title("a. Stimulus decoding")
    axes[0].legend(loc="lower right")

    plot_metric(axes[1], "gamma_coherence", "γ-band coherence", "C2")
    axes[1].set_ylim(0, 1)
    axes[1].set_title("b. Sender → receiver γ coh.")

    plot_metric(axes[2], "granger_F_sr", "Granger F (sender → receiver)", "C3")
    axes[2].set_title("c. Directed influence")

    fig.suptitle(title, fontweight="bold")
    fig.tight_layout()
    fp = os.path.join(FIG_DIR, f"fig_phase_tuning{suffix}.png")
    fig.savefig(fp, dpi=140)
    print(f"  {fp}")


if __name__ == "__main__":
    print("Generating final figures...")
    exp1_dev = load(os.path.join(HERE, "results", "exp1", "summary.json"))
    exp1_full = load(os.path.join(HERE, "results", "exp1_full", "summary.json"))
    exp2_dev = load(os.path.join(HERE, "results", "exp2", "summary.json"))
    exp2_full = load(os.path.join(HERE, "results", "exp2_full_n12", "summary.json"))

    phase_tuning_figure(exp1_dev, "_dev",
                        "Exp 1 (H1) — 200E/50I, n=8 seeds (γ-coh flat, F=1.3 p=0.25)")
    phase_tuning_figure(exp1_full, "",
                        "Exp 1 (H1) phase tuning — 800E/200I, n=6 seeds (γ-coh F=68 p<10⁻⁴⁷)")
    causal_figure(exp2_dev, "_dev", "Exp 2 (H2) — 200E/50I, n=8 seeds (underpowered)")
    manip_figure(exp2_dev, "_dev", "Manipulation check — 200E/50I (dev)")
    causal_figure(exp2_full, "",
                  "Exp 2 (H2) causal disruption — 800E/200I, n=12 seeds (W=0, p=0.0039)")
    manip_figure(exp2_full, "",
                 "Manipulation check (n=12) — rate ✓, power ✓, coherence ✗ (manipulated)")
    print("Done.")
