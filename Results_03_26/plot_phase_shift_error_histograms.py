#!/usr/bin/env python3

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


def parse_args():
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description=(
            "Plot histograms of raw current measurements from PhaseShift runs, "
            "grouped by voltage level."
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=script_dir / "measurement_data",
        help="Root folder that contains the measurement run folders (local copy in Results_03_26/measurement_data).",
    )
    parser.add_argument(
        "--bins",
        type=int,
        default=40,
        help="Number of histogram bins.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=script_dir / "phase_shift_current_histograms",
        help="Directory where histogram images are saved.",
    )
    return parser.parse_args()


def load_numeric_series(csv_path: Path):
    raw = csv_path.read_text(encoding="utf-8").strip()
    if not raw:
        return []

    if raw.startswith("["):
        values = json.loads(raw)
    else:
        values = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                values.append(float(line))
            except ValueError as exc:
                raise ValueError(f"Unsupported numeric format in {csv_path}") from exc

    return [float(value) for value in values]

def discover_phase_dirs(root: Path):
    phase_dirs = []
    for run_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        phase_root = run_dir / "PhaseShift"
        if not phase_root.is_dir():
            continue
        for phase_dir in sorted(path for path in phase_root.iterdir() if path.is_dir()):
            phase_dirs.append(phase_dir)
    return phase_dirs


def find_current_csv(phase_dir: Path):
    csv_dirs = [phase_dir / "data", phase_dir / "csv", phase_dir]
    for csv_dir in csv_dirs:
        if not csv_dir.is_dir():
            continue
        for csv_path in sorted(csv_dir.glob("csv-*.csv")):
            if csv_path.name.startswith(".~lock."):
                continue
            if csv_path.name.lower().endswith("-current.csv"):
                return csv_path
    return None


def get_voltage_label(phase_dir: Path):
    match = re.match(r"Voltage_(\d+)_", phase_dir.name)
    if not match:
        raise ValueError(f"Unable to extract voltage from folder name: {phase_dir.name}")
    return f"{match.group(1)}V"


def plot_single_histogram(values, bins, title, x_label, output_path: Path):
    plt.figure(figsize=(10, 6))
    plt.hist(values, bins=bins, edgecolor="black", alpha=0.8)
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel("Count")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def main():
    args = parse_args()
    root = args.root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    current_by_voltage = defaultdict(list)
    summaries = defaultdict(list)

    for phase_dir in discover_phase_dirs(root):
        csv_path = find_current_csv(phase_dir)
        if csv_path is None:
            continue

        voltage_label = get_voltage_label(phase_dir)
        samples = load_numeric_series(csv_path)
        if not samples:
            continue

        current_by_voltage[voltage_label].extend(samples)
        summaries[voltage_label].append((phase_dir.parent.parent.name, phase_dir.name, len(samples)))

    if not current_by_voltage:
        raise SystemExit(f"No current PhaseShift CSV files found under {root}")

    for voltage_label, samples in sorted(current_by_voltage.items()):
        output_path = output_dir / f"all_runs__{voltage_label}_current_histogram.png"
        plot_single_histogram(
            values=samples,
            bins=args.bins,
            title=f"All current values combined for {voltage_label}",
            x_label="Current (A)",
            output_path=output_path,
        )
        print(
            f"- {voltage_label}: {len(samples)} current samples combined from "
            f"{len(summaries[voltage_label])} folders -> {output_path}"
        )
        for run_name, phase_name, sample_count in summaries[voltage_label]:
            print(f"  {run_name} | {phase_name}: {sample_count} samples")


if __name__ == "__main__":
    main()
