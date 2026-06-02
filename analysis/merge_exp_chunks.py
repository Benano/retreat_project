"""Merge per-chunk exp1 results (different delay subsets) into one summary +
phase-tuning figure. Usage: ``python merge_exp_chunks.py <out_dir> <chunk_dirs...>``"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--chunks", nargs="+", required=True)
    ap.add_argument("--fig-path", default=None)
    ap.add_argument("--title", default="Experiment 1: phase tuning (dev scale)")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    summary = []
    metrics_rows = []
    n_stim = None
    for chunk in args.chunks:
        with open(os.path.join(chunk, "summary.json")) as fh:
            summary.extend(json.load(fh))
        with open(os.path.join(chunk, "metrics_rows.json")) as fh:
            metrics_rows.extend(json.load(fh))
        # capture n_stimuli from the first run_config
        if n_stim is None:
            with open(os.path.join(chunk, "run_config.json")) as fh:
                rc = json.load(fh)
                n_stim = rc.get("n_stimuli", 4)

    summary.sort(key=lambda r: r["delay_ms"])
    with open(os.path.join(args.out_dir, "summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)
    with open(os.path.join(args.out_dir, "metrics_rows.json"), "w") as fh:
        json.dump(metrics_rows, fh, indent=2)
    print(f"Merged {len(summary)} delays from {len(args.chunks)} chunks.")

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
    axes[0].set_title("H1: stimulus decoding")
    axes[0].legend(loc="lower right")

    plot_metric(axes[1], "gamma_coherence", "γ-band coherence", "C2")
    axes[1].set_ylim(0, 1)
    axes[1].set_title("Sender → receiver γ coherence")

    plot_metric(axes[2], "granger_F_sr", "Granger F (sender → receiver)", "C3")
    axes[2].set_title("Directed influence")

    fig.suptitle(args.title, fontweight="bold")
    fig.tight_layout()
    fig_path = args.fig_path or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "figures", "fig_phase_tuning.png"
    )
    os.makedirs(os.path.dirname(fig_path), exist_ok=True)
    fig.savefig(fig_path, dpi=140)
    print(f"Saved figure {fig_path}")


if __name__ == "__main__":
    main()
