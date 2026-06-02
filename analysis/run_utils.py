"""
Utilities shared by the experiment runners: parallel-ish trial execution
(via concurrent.futures.ProcessPoolExecutor), per-trial pickle output,
machine-readable run config, master-seed bookkeeping.
"""
from __future__ import annotations

import json
import os
import pickle
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from typing import Callable, Iterable

import numpy as np


def save_pickle(obj, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        pickle.dump(obj, fh)


def load_pickle(path: str):
    with open(path, "rb") as fh:
        return pickle.load(fh)


def save_json(obj, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(obj, fh, indent=2, default=_json_default)


def _json_default(o):
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.floating, np.integer, np.bool_)):
        return o.item()
    if hasattr(o, "to_dict"):
        return o.to_dict()
    if hasattr(o, "__dict__"):
        return asdict(o)
    raise TypeError(f"Object of type {type(o)} not JSON serializable")


def trim_trial_for_disk(trial: dict) -> dict:
    """Strip large arrays we don't need to keep on disk for downstream analysis.

    We keep spike times/indices, population rates, and metadata. We drop the
    state monitor (which is huge) and the sender's smoothed rate (re-derivable).
    """
    keep_sender = {
        "spikes_E_t": np.asarray(trial["sender"]["spikes_E_t"], dtype=np.float32),
        "spikes_E_i": np.asarray(trial["sender"]["spikes_E_i"], dtype=np.int32),
        "config": trial["sender"]["config"],
        "seed": trial["sender"]["seed"],
        "duration_ms": trial["sender"]["duration_ms"],
        "stimulus_pa": trial["sender"]["stimulus_pa"],
    }
    keep_recv = {
        "spikes_E_t": np.asarray(trial["receiver"]["spikes_E_t"], dtype=np.float32),
        "spikes_E_i": np.asarray(trial["receiver"]["spikes_E_i"], dtype=np.int32),
        "spikes_I_t": np.asarray(trial["receiver"]["spikes_I_t"], dtype=np.float32),
        "spikes_I_i": np.asarray(trial["receiver"]["spikes_I_i"], dtype=np.int32),
        "config_recv": trial["receiver"]["config_recv"],
        "ff": trial["receiver"]["ff"],
        "seed": trial["receiver"]["seed"],
        "duration_ms": trial["receiver"]["duration_ms"],
    }
    return {
        "trial": trial["trial"],
        "sender": keep_sender,
        "receiver": keep_recv,
        "delivered_t": np.asarray(trial["delivered_t"], dtype=np.float32),
        "delivered_i": np.asarray(trial["delivered_i"], dtype=np.int32),
    }


def run_trials_parallel(work_items: list, fn: Callable, n_workers: int = 4,
                        progress_every: int = 5) -> list:
    """Run fn(item) for each item, returning results in the original order.

    fn must be a top-level picklable function.
    """
    if n_workers <= 1:
        out = []
        t0 = time.time()
        for k, item in enumerate(work_items):
            r = fn(item)
            out.append(r)
            if (k + 1) % progress_every == 0:
                el = time.time() - t0
                eta = el / (k + 1) * (len(work_items) - k - 1)
                print(f"  [serial] {k + 1}/{len(work_items)}  ({el:.0f}s elapsed, ~{eta:.0f}s left)")
        return out

    out = [None] * len(work_items)
    t0 = time.time()
    done = 0
    with ProcessPoolExecutor(max_workers=n_workers) as exe:
        futures = {exe.submit(fn, it): k for k, it in enumerate(work_items)}
        for fut in as_completed(futures):
            k = futures[fut]
            out[k] = fut.result()
            done += 1
            if done % progress_every == 0 or done == len(work_items):
                el = time.time() - t0
                eta = el / done * (len(work_items) - done)
                print(f"  [parallel] {done}/{len(work_items)}  "
                      f"({el:.0f}s elapsed, ~{eta:.0f}s left)")
    return out
