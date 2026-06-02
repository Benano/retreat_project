"""Generate final paper figures from the canonical n=20 + H3 data."""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(os.path.dirname(HERE), "figures")
os.makedirs(FIG, exist_ok=True)


def load(p): return json.load(open(p))


def fig1_phase_tuning(out_path):
    """Figure 1 — H1 phase tuning curve (full scale)."""
    s = load(os.path.join(HERE, "results", "exp1_full", "summary.json"))
    ds = np.array([r["delay_ms"] for r in s])
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4))
    for ax, key, ylab, color, ylim in [
        (axes[0], "decode_acc",       "Decoding accuracy",         "#1f77b4", (0.4, 1.0)),
        (axes[1], "gamma_coherence",  "Sender→receiver γ coh.",    "#2ca02c", (0, 1.0)),
        (axes[2], "granger_F_sr",     "Granger F (sender→receiver)","#d62728", None),
    ]:
        m  = np.array([r[f"{key}_mean"] for r in s])
        sd = np.array([r[f"{key}_sd"]   for r in s])
        n  = np.array([r[f"{key}_n"]    for r in s])
        se = sd / np.sqrt(np.maximum(n, 1))
        ax.errorbar(ds, m, yerr=1.96 * se, color=color, marker="o", capsize=3, lw=1.5)
        ax.set_xlabel("Conduction delay (ms)")
        ax.set_ylabel(ylab)
        ax.grid(alpha=0.3)
        if ylim: ax.set_ylim(*ylim)
    axes[0].axhline(0.25, ls="--", color="gray", label="chance")
    axes[0].legend(loc="lower left", fontsize=8)
    axes[0].set_title("a", loc="left", fontweight="bold")
    axes[1].set_title("b", loc="left", fontweight="bold")
    axes[2].set_title("c", loc="left", fontweight="bold")
    fig.suptitle("Figure 1 — H1: phase tuning of effective communication "
                 "(800E/200I, n=6 seeds × 4 stim)", fontsize=10)
    fig.tight_layout()
    fig.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def fig2_h2_causal(out_path):
    """Figure 2 — H2 causal disruption at n=20."""
    s = load(os.path.join(HERE, "results", "exp2_full_n20", "summary.json"))
    ps = load(os.path.join(HERE, "results", "exp2_full_n20", "paired_stats.json"))
    colors = {"intact": "#1f77b4", "scramble": "#d62728", "poisson": "#7f7f7f"}
    conds = [r["condition"] for r in s]
    xs = np.arange(len(conds))

    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6))

    # Panel a: decoding accuracy (per seed)
    accs = np.array([r["decode_acc_mean"] for r in s])
    se   = np.array([r["decode_acc_se"]   for r in s])
    axes[0].bar(xs, accs, yerr=1.96 * se, capsize=5,
                color=[colors[c] for c in conds])
    axes[0].axhline(0.25, ls="--", color="gray", label="chance")
    axes[0].set_xticks(xs); axes[0].set_xticklabels(conds)
    axes[0].set_ylabel("Decoding accuracy (mean ± 95% CI)")
    axes[0].set_ylim(0, 1.05)
    # add p-value brackets
    def bracket(ax, x1, x2, y, h, label):
        ax.plot([x1, x1, x2, x2], [y, y+h, y+h, y], lw=1.0, c="k")
        ax.text((x1+x2)/2, y+h*1.1, label, ha="center", va="bottom", fontsize=8)
    bracket(axes[0], 0, 1, 1.0, 0.03, "p=0.007")
    bracket(axes[0], 1, 2, 1.04, 0.03, "p=0.0004")
    axes[0].set_title("a", loc="left", fontweight="bold")
    axes[0].set_ylim(0, 1.18)

    # Panel b: delivered γ-coherence
    coh = np.array([r["delivered_coherence_mean"] for r in s])
    coh_sd = np.array([r["delivered_coherence_sd"] for r in s])
    coh_n  = np.array([r["delivered_coherence_n"]  for r in s])
    coh_se = coh_sd / np.sqrt(np.maximum(coh_n, 1))
    axes[1].bar(xs, coh, yerr=1.96 * coh_se, capsize=5,
                color=[colors[c] for c in conds])
    axes[1].set_xticks(xs); axes[1].set_xticklabels(conds)
    axes[1].set_ylabel("Sender↔delivered γ-coherence")
    axes[1].set_ylim(0, 1.05)
    axes[1].set_title("b", loc="left", fontweight="bold")

    fig.suptitle("Figure 2 — H2: causal disruption (800E/200I, n=20 seeds)", fontsize=10)
    fig.tight_layout()
    fig.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def fig3_manipulation_check(out_path):
    """Figure 3 — manipulation check (rate, power, coherence)."""
    s = load(os.path.join(HERE, "results", "exp2_full_n20", "summary.json"))
    colors = {"intact": "#1f77b4", "scramble": "#d62728", "poisson": "#7f7f7f"}
    conds = [r["condition"] for r in s]
    xs = np.arange(len(conds))

    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4))

    def bars(ax, key, label, title):
        m  = np.array([r[f"{key}_mean"] for r in s])
        sd = np.array([r[f"{key}_sd"]   for r in s])
        n  = np.array([r[f"{key}_n"]    for r in s])
        se = sd / np.sqrt(np.maximum(n, 1))
        ax.bar(xs, m, yerr=1.96 * se, capsize=5,
               color=[colors[c] for c in conds])
        ax.set_xticks(xs); ax.set_xticklabels(conds)
        ax.set_ylabel(label)
        ax.set_title(title, loc="left", fontweight="bold")

    bars(axes[0], "delivered_rate_hz",     "Delivered rate (Hz)",       "a")
    bars(axes[1], "delivered_gamma_power", "Delivered γ-power (a.u.)",  "b")
    bars(axes[2], "delivered_coherence",   "Sender↔delivered γ-coh.",   "c")
    fig.suptitle("Figure 3 — Manipulation check on the delivered signal (n=20)",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def fig4_h3(out_path):
    """Figure 4 — H3 receiver-oscillation-disabled comparison."""
    s_baseline = load(os.path.join(HERE, "results", "exp2_full_n20", "summary.json"))
    s_h3       = load(os.path.join(HERE, "results", "exp3_disabled", "summary.json"))

    cond_order = ["intact", "scramble"]
    colors = {"intact": "#1f77b4", "scramble": "#d62728"}

    def pick(s, cond):
        return next(r for r in s if r["condition"] == cond)

    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6))

    # Panel a: decoding side-by-side (intact vs scramble × baseline vs disabled)
    x_b = np.array([0, 1])      # intact, scramble
    x_d = np.array([2.5, 3.5])
    for ax in [axes[0]]:
        for i, cond in enumerate(cond_order):
            b = pick(s_baseline, cond)
            d = pick(s_h3,       cond)
            ax.bar(x_b[i], b["decode_acc_mean"], yerr=1.96*b["decode_acc_se"],
                   capsize=4, color=colors[cond], label=cond if i in (0,) else None)
            ax.bar(x_d[i], d["decode_acc_mean"], yerr=1.96*d["decode_acc_se"],
                   capsize=4, color=colors[cond], hatch="///", edgecolor="white",
                   label=None)
        ax.set_xticks([0.5, 3.0])
        ax.set_xticklabels(["Baseline\n(receiver oscillates)",
                            "H3: receiver\noscillation disabled"])
        ax.set_ylabel("Decoding accuracy")
        ax.axhline(0.25, ls="--", color="gray", label="chance")
        ax.set_ylim(0, 1.18)
        ax.set_title("a", loc="left", fontweight="bold")
        # Annotate p-values
        def bracket(ax, x1, x2, y, h, label):
            ax.plot([x1, x1, x2, x2], [y, y+h, y+h, y], lw=1.0, c="k")
            ax.text((x1+x2)/2, y+h*1.1, label, ha="center", va="bottom", fontsize=8)
        bracket(ax, 0, 1, 1.00, 0.03, "p=0.007")
        bracket(ax, 2.5, 3.5, 1.00, 0.03, "p=0.011 (reversed)")
        # legend
        import matplotlib.patches as mpatches
        handles = [
            mpatches.Patch(color=colors["intact"], label="intact"),
            mpatches.Patch(color=colors["scramble"], label="scramble"),
        ]
        ax.legend(handles=handles, loc="lower right", fontsize=8)

    # Panel b: receiver firing rate (baseline vs disabled)
    bar_data = []
    bar_labels = []
    bar_colors = []
    for tag, s_ in [("baseline", s_baseline), ("H3 disabled", s_h3)]:
        for cond in cond_order:
            r = pick(s_, cond)
            bar_data.append(r["receiver_rate_hz_mean"])
            bar_labels.append(f"{cond}\n{tag}")
            bar_colors.append(colors[cond])
    x = np.arange(len(bar_data))
    axes[1].bar(x, bar_data, color=bar_colors,
                hatch=["" if "baseline" in l else "///" for l in bar_labels],
                edgecolor="white")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(bar_labels, fontsize=8)
    axes[1].set_ylabel("Receiver E-cell rate (Hz)")
    axes[1].set_title("b — receiver hyperactivity (no inhibition)", loc="left",
                      fontweight="bold")
    fig.suptitle("Figure 4 — H3: receiver-oscillation manipulation (n=20)", fontsize=10)
    fig.tight_layout()
    fig.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def main():
    fig1_phase_tuning(os.path.join(FIG, "fig1_phase_tuning.png"))
    fig2_h2_causal(   os.path.join(FIG, "fig2_causal_test.png"))
    fig3_manipulation_check(os.path.join(FIG, "fig3_manipulation_check.png"))
    fig4_h3(          os.path.join(FIG, "fig4_h3.png"))
    print("Generated paper figures:")
    for f in ["fig1_phase_tuning.png", "fig2_causal_test.png",
              "fig3_manipulation_check.png", "fig4_h3.png"]:
        print(f"  {os.path.join(FIG, f)}")


if __name__ == "__main__":
    main()
