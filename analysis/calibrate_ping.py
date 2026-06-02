"""
Calibrate a single PING group to hit the Section 5.5 benchmarks:
  - Gamma peak in the population-rate spectrum at 50–70 Hz
  - E → I cycle lag of 2–3 ms
  - Sparse per-cell firing (E cells fire well below the gamma frequency,
    i.e. on a minority of cycles)

Approach: try a small grid of (drive, background-rate, g_IE) combinations
that should tune the network without changing the architecture. Pick the
combination closest to the targets. Save a calibration report PNG and a
JSON of realized values.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import replace

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import welch, correlate

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ping_group import PINGConfig, run_isolated


def spectrum(rate, dt_ms, band=(1, 200)):
    fs = 1000.0 / dt_ms
    f, p = welch(rate - np.mean(rate), fs=fs, nperseg=min(len(rate), int(fs)))
    m = (f >= band[0]) & (f <= band[1])
    return f[m], p[m]


def peak_in_band(f, p, band=(30, 90)):
    m = (f >= band[0]) & (f <= band[1])
    if not m.any() or p[m].max() <= 0:
        return None, None
    idx = np.argmax(p[m])
    return float(f[m][idx]), float(p[m][idx])


def ei_lag_ms(rE, rI, dt_ms):
    """Time-lag at which the rE→rI cross-correlation peaks. Positive = E leads."""
    x = rE - rE.mean()
    y = rI - rI.mean()
    n = len(x)
    cc = correlate(y, x, mode="full")  # cc[k] correlates y at t with x at t-k+n-1
    lags = np.arange(-n + 1, n)
    # restrict to ±20 ms
    lim_bins = int(20.0 / dt_ms)
    mid = n - 1
    sl = slice(mid - lim_bins, mid + lim_bins + 1)
    cc_w = cc[sl]
    lags_w = lags[sl] * dt_ms
    return float(lags_w[np.argmax(cc_w)])


def per_cell_rates(spikes_i, n_cells, duration_ms):
    counts = np.bincount(spikes_i, minlength=n_cells)
    return counts / (duration_ms / 1000.0)


def try_one(cfg: PINGConfig, duration_ms=1500.0, seed=0, transient_ms=500.0):
    out = run_isolated(cfg=cfg, duration_ms=duration_ms, rng_seed=seed)
    # Discard transient
    mask = out["rate_E_t"] >= transient_ms
    rE = out["rate_E"][mask]
    rI = out["rate_I"][mask]
    dt_ms = cfg.dt
    f, p = spectrum(rE, dt_ms)
    peak_f, peak_p = peak_in_band(f, p)
    lag_ms = ei_lag_ms(rE, rI, dt_ms)
    # Per-cell rates
    sp_E_t, sp_E_i = out["spikes_E_t"], out["spikes_E_i"]
    sp_I_t, sp_I_i = out["spikes_I_t"], out["spikes_I_i"]
    keep_E = sp_E_t >= transient_ms
    keep_I = sp_I_t >= transient_ms
    perE = per_cell_rates(sp_E_i[keep_E], cfg.N_E, duration_ms - transient_ms)
    perI = per_cell_rates(sp_I_i[keep_I], cfg.N_I, duration_ms - transient_ms)
    return {
        "out": out,
        "f": f, "p": p,
        "peak_f": peak_f, "peak_p": peak_p,
        "ei_lag_ms": lag_ms,
        "perE_mean": float(perE.mean()),
        "perE_med": float(np.median(perE)),
        "perI_mean": float(perI.mean()),
        "perI_med": float(np.median(perI)),
        "popE_mean": float(rE.mean()),
        "popI_mean": float(rI.mean()),
        "config": cfg.to_dict(),
        "duration_ms": duration_ms,
        "transient_ms": transient_ms,
    }


def calibration_check(cfg: PINGConfig, label: str, duration_ms=1200.0,
                      out_dir=None, seeds=(0, 1, 2)):
    """Verify Section 5.5 benchmarks for a fixed PINGConfig (used for full-scale
    drift check at task 6/S4)."""
    out_dir = out_dir or os.path.join(os.path.dirname(__file__), "..", "figures", "calibration")
    os.makedirs(out_dir, exist_ok=True)
    summaries = []
    for seed in seeds:
        r = try_one(cfg, duration_ms=duration_ms, seed=seed)
        summaries.append(r)
    peaks = [r["peak_f"] for r in summaries if r["peak_f"] is not None]
    lags = [r["ei_lag_ms"] for r in summaries]
    out = {
        "label": label,
        "N_E": cfg.N_E, "N_I": cfg.N_I,
        "peak_hz_per_seed": peaks,
        "peak_hz_mean": float(np.mean(peaks)) if peaks else None,
        "peak_hz_std": float(np.std(peaks, ddof=1)) if len(peaks) > 1 else 0.0,
        "ei_lag_ms_per_seed": lags,
        "ei_lag_ms_mean": float(np.mean(lags)),
        "pop_rate_E_hz_mean": float(np.mean([r["popE_mean"] for r in summaries])),
        "per_cell_E_med_hz_mean": float(np.mean([r["perE_med"] for r in summaries])),
        "duration_ms": duration_ms,
        "transient_ms": 500.0,
        "n_seeds": len(seeds),
    }
    save_path = os.path.join(out_dir, f"calibration_{label}.json")
    with open(save_path, "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"\n[{label}] gamma peak: {out['peak_hz_mean']} ± {out['peak_hz_std']:.2f} Hz "
          f"(per seed {peaks}); E→I lag: {out['ei_lag_ms_mean']:.2f} ms; "
          f"pop E rate {out['pop_rate_E_hz_mean']:.1f} Hz")
    print(f"  saved {save_path}")
    return out


def main():
    out_dir = os.path.join(os.path.dirname(__file__), "..", "figures", "calibration")
    os.makedirs(out_dir, exist_ok=True)
    base = PINGConfig()

    # Coarse grid. Goal: gamma peak in 50-70 Hz, E per-cell rate ~5-25 Hz, E->I lag 1-4 ms.
    # First grid showed slow gamma (36 Hz) with tau_GABA=8. Shorten it and tune drive.
    grid = []
    for tau_g in (4.0, 5.5):
        for drive_E in (100.0, 150.0):
            for g_EI in (0.7, 1.0):
                grid.append(replace(base,
                                    bg_rate_E=1200.0, bg_rate_I=1200.0,
                                    tau_GABA=tau_g,
                                    drive_E=drive_E,
                                    g_EI=g_EI,
                                    g_IE=0.8))

    print(f"Calibration grid: {len(grid)} configs, dev-scale ({base.N_E}E/{base.N_I}I)")
    results = []
    for k, cfg in enumerate(grid):
        try:
            r = try_one(cfg, duration_ms=1000.0, seed=0)
        except Exception as e:
            print(f"[{k:02d}] FAILED: {e}")
            continue
        pf = r["peak_f"]
        score = _score(r)
        print(f"[{k:02d}] bg={cfg.bg_rate_E:.0f} drive={cfg.drive_E:.0f} g_IE={cfg.g_IE:.2f}  "
              f"peak={pf:.1f}Hz" if pf else f"[{k:02d}] no gamma peak",
              f" popE={r['popE_mean']:.1f}Hz perE_med={r['perE_med']:.2f}Hz lag={r['ei_lag_ms']:.2f}ms"
              f" score={score:.2f}")
        results.append((score, cfg, r))

    results.sort(key=lambda x: x[0])
    best_score, best_cfg, best_r = results[0]
    print(f"\nBest config (score {best_score:.2f}):")
    print(f"  bg_rate={best_cfg.bg_rate_E}, drive_E={best_cfg.drive_E}, g_IE={best_cfg.g_IE}")
    print(f"  gamma peak: {best_r['peak_f']:.2f} Hz")
    print(f"  E->I lag : {best_r['ei_lag_ms']:.2f} ms")
    print(f"  pop rate E: {best_r['popE_mean']:.2f} Hz (per-cell median {best_r['perE_med']:.2f} Hz)")
    print(f"  pop rate I: {best_r['popI_mean']:.2f} Hz (per-cell median {best_r['perI_med']:.2f} Hz)")

    # Plot calibration report
    fig, axes = plt.subplots(2, 2, figsize=(11, 7))
    out = best_r["out"]
    tmask = out["rate_E_t"] >= best_r["transient_ms"]
    t = out["rate_E_t"][tmask]
    axes[0, 0].plot(t, out["rate_E"][tmask], label="E pop rate", color="C0", lw=0.8)
    axes[0, 0].plot(t, out["rate_I"][tmask], label="I pop rate", color="C3", lw=0.8)
    axes[0, 0].set_xlabel("Time (ms)")
    axes[0, 0].set_ylabel("Rate (Hz)")
    axes[0, 0].set_xlim(t[0], t[0] + 300)
    axes[0, 0].legend()
    axes[0, 0].set_title("Population rates (300 ms window)")

    axes[0, 1].semilogy(best_r["f"], best_r["p"], color="k")
    axes[0, 1].axvspan(30, 90, alpha=0.15, color="C2", label="gamma band")
    if best_r["peak_f"]:
        axes[0, 1].axvline(best_r["peak_f"], color="C2", ls="--",
                           label=f"peak {best_r['peak_f']:.1f} Hz")
    axes[0, 1].set_xlabel("Frequency (Hz)")
    axes[0, 1].set_ylabel("Power")
    axes[0, 1].legend()
    axes[0, 1].set_title("E population rate spectrum")

    # E-I cross correlogram (zoomed)
    dt_ms = best_cfg.dt
    rE = out["rate_E"][tmask] - out["rate_E"][tmask].mean()
    rI = out["rate_I"][tmask] - out["rate_I"][tmask].mean()
    n = len(rE)
    cc = correlate(rI, rE, mode="full")
    lags = (np.arange(-n + 1, n)) * dt_ms
    lim = 20.0
    mask = (lags > -lim) & (lags < lim)
    axes[1, 0].plot(lags[mask], cc[mask], color="k")
    axes[1, 0].axvline(best_r["ei_lag_ms"], color="C3", ls="--",
                       label=f"peak lag {best_r['ei_lag_ms']:.2f} ms")
    axes[1, 0].axvline(0, color="gray", lw=0.5)
    axes[1, 0].set_xlabel("Lag (ms)  (positive = E leads I)")
    axes[1, 0].set_ylabel("Cross-corr")
    axes[1, 0].set_title("E→I cycle lag")
    axes[1, 0].legend()

    axes[1, 1].axis("off")
    txt = "Calibration report (best config)\n\n"
    txt += f"bg_rate = {best_cfg.bg_rate_E:.0f} Hz\n"
    txt += f"drive_E = {best_cfg.drive_E:.0f} pA\n"
    txt += f"g_IE = {best_cfg.g_IE:.2f} nS\n\n"
    txt += f"gamma peak: {best_r['peak_f']:.2f} Hz   (target 50–70)\n"
    txt += f"E→I lag: {best_r['ei_lag_ms']:.2f} ms     (target 2–3)\n"
    txt += f"pop E rate: {best_r['popE_mean']:.2f} Hz\n"
    txt += f"per-cell E rate (median): {best_r['perE_med']:.2f} Hz\n"
    txt += f"pop I rate: {best_r['popI_mean']:.2f} Hz\n"
    txt += f"per-cell I rate (median): {best_r['perI_med']:.2f} Hz\n"
    axes[1, 1].text(0.0, 1.0, txt, va="top", family="monospace")

    fig.suptitle("PING calibration — Section 5.5 benchmarks", fontweight="bold")
    fig.tight_layout()
    png_path = os.path.join(out_dir, "calibration_report.png")
    fig.savefig(png_path, dpi=120)
    print(f"\nSaved {png_path}")

    # Save the best config and headline metrics as JSON
    j = {
        "best_config": best_cfg.to_dict(),
        "gamma_peak_hz": best_r["peak_f"],
        "ei_lag_ms": best_r["ei_lag_ms"],
        "pop_rate_E_hz": best_r["popE_mean"],
        "pop_rate_I_hz": best_r["popI_mean"],
        "per_cell_E_median_hz": best_r["perE_med"],
        "per_cell_I_median_hz": best_r["perI_med"],
        "duration_ms": best_r["duration_ms"],
        "transient_ms": best_r["transient_ms"],
        "grid_size": len(grid),
        "score": best_score,
    }
    json_path = os.path.join(out_dir, "calibration_report.json")
    with open(json_path, "w") as fh:
        json.dump(j, fh, indent=2)
    print(f"Saved {json_path}")

    # Also dump the best config alone to a stable path that downstream scripts
    # (network.py, experiments) will import from.
    cfg_path = os.path.join(os.path.dirname(__file__), "calibrated_ping.json")
    with open(cfg_path, "w") as fh:
        json.dump(best_cfg.to_dict(), fh, indent=2)
    print(f"Saved {cfg_path}")
    return j


def _score(r):
    """Loss function: lower is better. Penalize off-target gamma, lag, and runaway rates."""
    s = 0.0
    if r["peak_f"] is None:
        s += 100.0
    else:
        # Target 60 Hz, acceptable 50-70
        s += ((r["peak_f"] - 60.0) / 10.0) ** 2
    # Target lag 2-3 ms
    s += ((r["ei_lag_ms"] - 2.5) / 1.5) ** 2
    # Per-cell E rate target ~5-20 Hz
    perE = r["perE_med"]
    if perE > 35:
        s += ((perE - 35) / 10.0) ** 2
    if perE < 2:
        s += ((2 - perE) / 2.0) ** 2
    # Population rate near gamma frequency is OK; runaway > 80 Hz suggests instability
    if r["popE_mean"] > 100:
        s += 50
    return s


if __name__ == "__main__":
    main()
