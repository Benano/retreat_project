"""Reviewer round 1 S4: verify Section 5.5 benchmarks at 800E/200I."""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ping_group import PINGConfig
from calibrate_ping import calibration_check


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "calibrated_ping.json")) as fh:
        cfg_dict = json.load(fh)
    # Full scale
    cfg_full = PINGConfig(**cfg_dict)
    cfg_full.N_E, cfg_full.N_I = 800, 200
    out = calibration_check(cfg_full, "full_scale", duration_ms=1200.0,
                            seeds=(0, 1, 2))
    # Compare against the dev calibration json (if present)
    dev_path = os.path.join(here, "..", "figures", "calibration", "calibration_report.json")
    if os.path.exists(dev_path):
        with open(dev_path) as fh:
            dev = json.load(fh)
        print(f"\nDev (200E/50I) calibration peak: {dev['gamma_peak_hz']:.2f} Hz, "
              f"lag {dev['ei_lag_ms']:.2f} ms")
    return out


if __name__ == "__main__":
    main()
