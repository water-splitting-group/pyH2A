"""Track memory usage of a subprocess (and its children) over time.

Wraps an arbitrary command, samples the RSS of the whole process tree at a
fixed interval while it runs, and writes out a CSV log plus a PNG plot.
Child processes are included because pyH2A's Monte Carlo plugin runs its
workers via multiprocessing.Pool, so the main PID alone would undercount.

Usage:
    python scripts/track_memory.py -- pyH2A run -i data/LCA/PVE.md -o .
    python scripts/track_memory.py --interval 0.2 --label pve -- pyH2A run -i data/LCA/PVE.md -o .

Requires psutil (not a pyH2A runtime dependency):
    uv pip install psutil
"""

import argparse
import csv
import subprocess
import sys
import time
from pathlib import Path

import psutil


def process_tree_rss_mb(proc):
    """Sum RSS (MB) of proc and all its living descendants."""
    total = 0
    try:
        total += proc.memory_info().rss
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return 0.0, 0
    children = proc.children(recursive=True)
    for child in children:
        try:
            total += child.memory_info().rss
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return total / (1024 ** 2), 1 + len(children)


def track(command, interval, out_dir, label):
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"{label}_memory.csv"
    plot_path = out_dir / f"{label}_memory.png"

    print(f"Running: {' '.join(command)}")
    start = time.monotonic()
    popen = subprocess.Popen(command)
    proc = psutil.Process(popen.pid)

    samples = []  # (elapsed_s, rss_mb, n_processes)
    try:
        while popen.poll() is None:
            elapsed = time.monotonic() - start
            rss_mb, n_procs = process_tree_rss_mb(proc)
            samples.append((elapsed, rss_mb, n_procs))
            time.sleep(interval)
    except KeyboardInterrupt:
        popen.terminate()
        raise
    finally:
        returncode = popen.wait()
        # one final sample so the tail of the run (last measured point) is recorded
        elapsed = time.monotonic() - start
        samples.append((elapsed, samples[-1][1] if samples else 0.0, 0))

    with csv_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["elapsed_s", "rss_mb", "n_processes"])
        writer.writerows(samples)

    peak = max(s[1] for s in samples) if samples else 0.0
    peak_t = next(s[0] for s in samples if s[1] == peak) if samples else 0.0
    duration = samples[-1][0] if samples else 0.0
    print(f"Exit code: {returncode}")
    print(f"Duration: {duration:.1f}s")
    print(f"Peak memory: {peak:.1f} MB (at {peak_t:.1f}s)")
    print(f"CSV written to: {csv_path}")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        xs = [s[0] for s in samples]
        ys = [s[1] for s in samples]
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(xs, ys, linewidth=1.2)
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Memory (MB, RSS, process tree)")
        ax.set_title(f"Memory usage: {' '.join(command)}")
        ax.axhline(peak, color="red", linestyle="--", linewidth=0.8, label=f"peak {peak:.0f} MB")
        ax.legend()
        fig.tight_layout()
        fig.savefig(plot_path, dpi=150)
        print(f"Plot written to: {plot_path}")
    except ImportError:
        print("matplotlib not available; skipped plot generation.")

    return returncode


def main():
    parser = argparse.ArgumentParser(
        description="Track memory usage of a command over time.",
        usage="%(prog)s [--interval SEC] [--output-dir DIR] [--label NAME] -- COMMAND [ARGS...]",
    )
    parser.add_argument("--interval", type=float, default=0.5, help="Sampling interval in seconds (default: 0.5)")
    parser.add_argument("--output-dir", type=Path, default=Path("."), help="Directory for CSV/plot output (default: current dir)")
    parser.add_argument("--label", type=str, default="pyH2A_run", help="Prefix for output file names")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command to run, e.g. -- pyH2A run -i data/LCA/PVE.md -o .")
    args = parser.parse_args()

    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("no command given; pass it after --, e.g. -- pyH2A run -i data/LCA/PVE.md -o .")

    returncode = track(command, args.interval, args.output_dir, args.label)
    sys.exit(returncode)


if __name__ == "__main__":
    main()
