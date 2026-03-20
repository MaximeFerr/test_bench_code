#!/usr/bin/env python3

import argparse
import json
import math
import re
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


NPLC_ORDER = ["0.005", "0.05", "0.5", "1", "10"]
NPLC_COLORS = {
    "0.005": "#1f77b4",
    "0.05": "#ff7f0e",
    "0.5": "#2ca02c",
    "1": "#d62728",
    "10": "#9467bd",
}


def parse_args():
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description=(
            "Compare current measurements for each phase/current step across NPLC values. "
            "For each voltage, the script computes the mean and standard deviation of the "
            "current samples at every step."
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=script_dir / "measurement_data",
        help="Root folder that contains the measurement run folders (local copy in Results_03_26/measurement_data).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=script_dir / "nplc_current_step_comparison",
        help="Directory where comparison plots are saved.",
    )
    parser.add_argument(
        "--bins",
        type=int,
        default=40,
        help="Number of bins for the per-NPLC histograms.",
    )
    parser.add_argument(
        "--drop-start",
        type=float,
        default=0.15,
        help="Fraction of samples to discard at the beginning of each step.",
    )
    parser.add_argument(
        "--drop-end",
        type=float,
        default=0.05,
        help="Fraction of samples to discard at the end of each step.",
    )
    parser.add_argument(
        "--exclude-run-substring",
        action="append",
        default=[],
        help=(
            "Exclude runs whose folder name contains this substring. "
            "Can be passed multiple times."
        ),
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
            values.append(float(line))

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


def extract_voltage_label(phase_dir: Path):
    match = re.match(r"Voltage_(\d+)_", phase_dir.name)
    if not match:
        raise ValueError(f"Unable to extract voltage from {phase_dir.name}")
    return f"{match.group(1)}V"


def extract_nplc_label(run_name: str):
    match = re.search(r"NPLC([0-9]+)", run_name)
    if not match:
        raise ValueError(f"Unable to extract NPLC from {run_name}")

    digits = match.group(1)
    mapping = {
        "0005": "0.005",
        "005": "0.05",
        "05": "0.5",
        "1": "1",
        "10": "10",
    }
    return mapping.get(digits, digits)


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


def get_step_metadata(phase_dir: Path):
    config_path = next(phase_dir.glob("PhaseShift_*.json"))
    config = json.loads(config_path.read_text(encoding="utf-8"))

    phase_values = config.get("PhaseTab")
    if not phase_values:
        phase_values = list(
            range(
                int(config["PhaseInit"]),
                int(config["PhaseFinal"]) + 1,
                int(config["PhaseStep"]),
            )
        )

    results_path = phase_dir / "results.json"
    peak_values = None
    if results_path.exists():
        results = json.loads(results_path.read_text(encoding="utf-8"))
        peak_values = [
            results.get(f"Data{idx+1}", {}).get("2", {}).get("value")
            for idx in range(len(phase_values))
        ]

    return phase_values, peak_values


def split_into_steps(samples, step_count):
    usable_count = (len(samples) // step_count) * step_count
    if usable_count == 0:
        raise ValueError(f"Not enough samples ({len(samples)}) for {step_count} steps")

    trimmed = samples[:usable_count]
    step_size = usable_count // step_count
    steps = []
    for idx in range(step_count):
        start = idx * step_size
        steps.append(trimmed[start:start + step_size])
    return steps, step_size, usable_count


def trim_step_samples(samples, drop_start_ratio, drop_end_ratio):
    if not 0 <= drop_start_ratio < 1:
        raise ValueError(f"drop_start must be in [0, 1), got {drop_start_ratio}")
    if not 0 <= drop_end_ratio < 1:
        raise ValueError(f"drop_end must be in [0, 1), got {drop_end_ratio}")
    if drop_start_ratio + drop_end_ratio >= 1:
        raise ValueError(
            "drop_start + drop_end must be strictly less than 1 so samples remain."
        )

    sample_count = len(samples)
    start_index = int(sample_count * drop_start_ratio)
    end_index = int(sample_count * (1 - drop_end_ratio))
    trimmed = samples[start_index:end_index]
    return trimmed if trimmed else samples


def compute_mean(values):
    return sum(values) / len(values)


def compute_std(values, mean_value):
    if len(values) < 2:
        return 0.0
    variance = sum((value - mean_value) ** 2 for value in values) / (len(values) - 1)
    return math.sqrt(variance)


def label_for_step(step_index, phase_values, peak_values):
    parts = [f"Step {step_index + 1}"]
    if phase_values and step_index < len(phase_values):
        parts.append(f"{phase_values[step_index]}°")
    if peak_values and step_index < len(peak_values) and peak_values[step_index] is not None:
        parts.append(f"Ipeak {peak_values[step_index]:.3f} A")
    return " | ".join(parts)


def sanitize_label(value: str):
    return value.replace(".", "p").replace(" ", "_").replace("|", "").replace("/", "_")


def main():
    args = parse_args()
    root = args.root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    grouped_samples = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    step_labels = defaultdict(dict)
    summary_rows = []

    for phase_dir in discover_phase_dirs(root):
        csv_path = find_current_csv(phase_dir)
        if csv_path is None:
            continue

        run_name = phase_dir.parent.parent.name
        if any(pattern in run_name for pattern in args.exclude_run_substring):
            print(f"Skipping excluded run: {run_name}")
            continue
        voltage_label = extract_voltage_label(phase_dir)
        nplc_label = extract_nplc_label(run_name)
        samples = load_numeric_series(csv_path)
        if not samples:
            continue

        phase_values, peak_values = get_step_metadata(phase_dir)
        step_samples, step_size, usable_count = split_into_steps(samples, len(phase_values))

        for step_index, values in enumerate(step_samples):
            trimmed_values = trim_step_samples(values, args.drop_start, args.drop_end)
            grouped_samples[voltage_label][step_index][nplc_label].extend(trimmed_values)
            step_labels[voltage_label][step_index] = label_for_step(
                step_index, phase_values, peak_values
            )

        summary_rows.append(
            (
                run_name,
                voltage_label,
                nplc_label,
                len(samples),
                usable_count,
                step_size,
                args.drop_start,
                args.drop_end,
            )
        )

    if not summary_rows:
        raise SystemExit(f"No current PhaseShift data found under {root}")

    for voltage_label, step_map in sorted(grouped_samples.items()):
        step_count = len(step_map)
        fig, axes = plt.subplots(
            nrows=step_count,
            ncols=1,
            figsize=(10, 4 * step_count),
            squeeze=False,
        )
        axes = axes.flatten()

        print(f"\n[{voltage_label}]")
        for step_index in sorted(step_map):
            ax = axes[step_index]
            label = step_labels[voltage_label].get(step_index, f"Step {step_index + 1}")
            nplc_values = []
            means = []
            stds = []
            colors = []

            print(label)
            for nplc_label in NPLC_ORDER:
                samples = step_map[step_index].get(nplc_label)
                if not samples:
                    continue

                mean_value = compute_mean(samples)
                std_value = compute_std(samples, mean_value)

                nplc_values.append(nplc_label)
                means.append(mean_value)
                stds.append(std_value)
                colors.append(NPLC_COLORS.get(nplc_label, "#333333"))

                print(
                    f"  NPLC {nplc_label}: mean={mean_value:.6f} A, "
                    f"std={std_value:.6f} A, n={len(samples)}"
                )

            ax.bar(
                nplc_values,
                means,
                yerr=stds,
                color=colors,
                edgecolor="black",
                capsize=5,
            )
            ax.set_title(
                f"{voltage_label} | {label}\ntrim start={args.drop_start:.0%}, end={args.drop_end:.0%}"
            )
            ax.set_xlabel("NPLC")
            ax.set_ylabel("Current mean (A)")
            ax.grid(True, axis="y", alpha=0.3)

        plt.tight_layout()
        output_path = output_dir / f"{voltage_label}_nplc_current_step_comparison.png"
        plt.savefig(output_path, dpi=200)
        plt.close(fig)
        print(f"Saved plot: {output_path}")

        for step_index in sorted(step_map):
            label = step_labels[voltage_label].get(step_index, f"Step {step_index + 1}")
            hist_fig, hist_axes = plt.subplots(
                nrows=1,
                ncols=len(NPLC_ORDER),
                figsize=(4 * len(NPLC_ORDER), 4),
                squeeze=False,
            )
            hist_axes = hist_axes.flatten()

            plotted_any = False
            for axis_index, nplc_label in enumerate(NPLC_ORDER):
                ax = hist_axes[axis_index]
                samples = step_map[step_index].get(nplc_label)
                color = NPLC_COLORS.get(nplc_label, "#333333")

                if samples:
                    ax.hist(samples, bins=args.bins, color=color, edgecolor="black", alpha=0.8)
                    ax.set_title(f"NPLC {nplc_label}")
                    ax.set_xlabel("Current (A)")
                    ax.set_ylabel("Count")
                    ax.grid(True, axis="y", alpha=0.3)
                    plotted_any = True
                else:
                    ax.set_title(f"NPLC {nplc_label}")
                    ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
                    ax.set_xticks([])
                    ax.set_yticks([])

            if plotted_any:
                hist_fig.suptitle(
                    f"{voltage_label} | {label} | Current histograms | "
                    f"trim start={args.drop_start:.0%}, end={args.drop_end:.0%}",
                    y=1.02,
                )
                hist_fig.tight_layout()
                hist_output_path = output_dir / (
                    f"{voltage_label}_{sanitize_label(f'step_{step_index + 1}')}_"
                    f"nplc_histograms.png"
                )
                hist_fig.savefig(hist_output_path, dpi=200, bbox_inches="tight")
                print(f"Saved histograms: {hist_output_path}")
            plt.close(hist_fig)

    print("\nRuns used:")
    for (
        run_name,
        voltage_label,
        nplc_label,
        sample_count,
        usable_count,
        step_size,
        drop_start,
        drop_end,
    ) in summary_rows:
        kept_per_step = len(
            trim_step_samples([0.0] * step_size, drop_start, drop_end)
        )
        print(
            f"- {run_name} | {voltage_label} | NPLC {nplc_label}: "
            f"{sample_count} samples, used {usable_count}, {step_size} samples/step, "
            f"kept ~{kept_per_step} per step after trim"
        )


if __name__ == "__main__":
    main()
