from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import csv
import re

import matplotlib.pyplot as plt
import numpy as np


XY_PATTERN = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)\s+([0-9]+(?:\.[0-9]+)?)\s*$")


@dataclass
class Trace:
    label: str
    xy: np.ndarray


@dataclass
class ReferencePeaks:
    label: str
    positions: list[float]
    color: str


def load_smartlab_xy(path: Path) -> np.ndarray:
    rows: list[tuple[float, float]] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = XY_PATTERN.match(line)
        if match:
            rows.append((float(match.group(1)), float(match.group(2))))
    if not rows:
        raise ValueError(f"No XY data found in {path}")
    return np.asarray(rows, dtype=float)


def moving_average(values: np.ndarray, window: int = 5) -> np.ndarray:
    if window <= 1:
        return values.copy()
    radius = window // 2
    out = np.empty_like(values)
    for idx in range(len(values)):
        start = max(0, idx - radius)
        stop = min(len(values), idx + radius + 1)
        out[idx] = np.mean(values[start:stop])
    return out


def detect_peaks(xy: np.ndarray, min_prominence: float = 1500.0, min_spacing: float = 0.35) -> list[tuple[float, float]]:
    x = xy[:, 0]
    y = moving_average(xy[:, 1], window=7)
    candidates: list[tuple[float, float, float]] = []
    for idx in range(4, len(y) - 4):
        center = y[idx]
        if center <= y[idx - 1] or center < y[idx + 1]:
            continue
        if center <= y[idx - 2] or center < y[idx + 2]:
            continue
        left_min = float(np.min(y[max(0, idx - 30):idx]))
        right_min = float(np.min(y[idx + 1:min(len(y), idx + 31)]))
        prominence = center - max(left_min, right_min)
        if prominence >= min_prominence:
            candidates.append((prominence, x[idx], xy[idx, 1]))
    candidates.sort(reverse=True)
    selected: list[tuple[float, float]] = []
    for _, peak_x, peak_y in candidates:
        if all(abs(peak_x - existing_x) > min_spacing for existing_x, _ in selected):
            selected.append((peak_x, peak_y))
    selected.sort(key=lambda item: item[0])
    return selected


def normalize_trace(y: np.ndarray) -> np.ndarray:
    ymin = float(np.min(y))
    ymax = float(np.max(y))
    if ymax == ymin:
        return np.zeros_like(y)
    return (y - ymin) / (ymax - ymin)


def save_peaks_csv(output_path: Path, peaks: list[tuple[float, float]]) -> None:
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["two_theta_deg", "intensity"])
        writer.writerows([[f"{x:.4f}", f"{y:.4f}"] for x, y in peaks])


def load_peaks_csv(peak_csv: Path, xy: np.ndarray) -> list[tuple[float, float]]:
    peaks: list[tuple[float, float]] = []
    with peak_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            peak_x = float(row["two_theta_deg"])
            intensity_raw = row.get("intensity")
            if intensity_raw not in (None, ""):
                peak_y = float(intensity_raw)
            else:
                idx = int(np.argmin(np.abs(xy[:, 0] - peak_x)))
                peak_y = float(xy[idx, 1])
            peaks.append((peak_x, peak_y))
    peaks.sort(key=lambda item: item[0])
    return peaks


def resolve_peaks(trace: Trace, peak_csv: Path | None = None) -> list[tuple[float, float]]:
    if peak_csv is not None:
        return load_peaks_csv(peak_csv, trace.xy)
    return detect_peaks(trace.xy)


def plot_single(trace: Trace, output: Path, peak_csv: Path | None = None) -> list[tuple[float, float]]:
    peaks = resolve_peaks(trace, peak_csv=peak_csv)
    output_peak_csv = peak_csv
    fig, ax = plt.subplots(figsize=(7.2, 5.2), dpi=180)
    ax.plot(trace.xy[:, 0], trace.xy[:, 1], color="#244c8f", lw=1.0)
    for peak_x, peak_y in peaks:
        ax.vlines(peak_x, peak_y * 0.96, peak_y, color="#a94442", linewidth=0.8)
        ax.text(peak_x, peak_y * 1.01, f"{peak_x:.2f}", rotation=90, ha="center", va="bottom", fontsize=8)
    ax.set_xlabel(r"2$\theta$ (°)")
    ax.set_ylabel("Intensity (cps)")
    ax.set_title(trace.label)
    ax.tick_params(axis="both", which="major", direction="in")
    ax.minorticks_on()
    fig.tight_layout()
    fig.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(fig)
    if output_peak_csv is not None:
        save_peaks_csv(output_peak_csv, peaks)
    return peaks


def parse_peak_csv_map(values: list[str]) -> dict[str, Path]:
    mapping: dict[str, Path] = {}
    for value in values:
        label, path = value.split("=", 1)
        mapping[label] = Path(path)
    return mapping


def plot_stacked(traces: list[Trace], output: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.4, 6.8), dpi=180)
    colors = ["#244c8f", "#d23b31", "#2f7d32", "#6a3d9a", "#8c564b", "#e377c2"]
    x_min = max(trace.xy[:, 0].min() for trace in traces)
    x_max = min(trace.xy[:, 0].max() for trace in traces)
    offset_step = 1.15
    total = len(traces)
    for idx, trace in enumerate(traces):
        mask = (trace.xy[:, 0] >= x_min) & (trace.xy[:, 0] <= x_max)
        x = trace.xy[mask, 0]
        y = normalize_trace(trace.xy[mask, 1])
        offset = (total - 1 - idx) * offset_step
        y_plot = y + offset
        color = colors[idx % len(colors)]
        ax.plot(x, y_plot, color=color, lw=1.0)
        ax.text(x_max - 0.35, offset + 0.15, trace.label, ha="right", va="bottom", fontsize=10)
    ax.set_xlim(x_min, x_max)
    ax.set_xlabel(r"2$\theta$ (°)")
    ax.set_ylabel("Intensity (a.u.)")
    ax.set_yticks([])
    ax.tick_params(axis="both", which="major", direction="in")
    ax.minorticks_on()
    fig.tight_layout()
    fig.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_with_refs(trace: Trace, refs: list[ReferencePeaks], output: Path, peak_csv: Path | None = None) -> list[tuple[float, float]]:
    peaks = resolve_peaks(trace, peak_csv=peak_csv)
    fig, ax = plt.subplots(figsize=(7.4, 5.6), dpi=180)
    x = trace.xy[:, 0]
    y = normalize_trace(trace.xy[:, 1])
    ax.plot(x, y, color="#1f1f1f", lw=1.1, label=trace.label)
    for peak_x, peak_y_raw in peaks:
        idx = int(np.argmin(np.abs(x - peak_x)))
        peak_y = y[idx]
        ax.vlines(peak_x, peak_y * 0.94, peak_y, color="#666666", linewidth=0.6)
    for ref in refs:
        for pos in ref.positions:
            ax.vlines(pos, -0.08, -0.02, color=ref.color, linewidth=1.0)
        ax.plot([], [], color=ref.color, label=ref.label)
    ax.set_ylim(-0.12, 1.05)
    ax.set_xlabel(r"2$\theta$ (°)")
    ax.set_ylabel("Normalized intensity")
    ax.legend(frameon=False, loc="upper right")
    ax.tick_params(axis="both", which="major", direction="in")
    ax.minorticks_on()
    fig.tight_layout()
    fig.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return peaks


def parse_refs(values: list[str]) -> list[ReferencePeaks]:
    colors = ["#d23b31", "#2f7d32", "#6a3d9a", "#8c564b"]
    refs: list[ReferencePeaks] = []
    for idx, value in enumerate(values):
        name, raw_positions = value.split("=", 1)
        positions = [float(item) for item in raw_positions.split(",") if item.strip()]
        refs.append(ReferencePeaks(label=name.strip(), positions=positions, color=colors[idx % len(colors)]))
    return refs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generic XRD plotting helper")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    single = subparsers.add_parser("single")
    single.add_argument("input")
    single.add_argument("output")
    single.add_argument("--label", default="sample")
    single.add_argument("--peak-csv")

    stacked = subparsers.add_parser("stacked")
    stacked.add_argument("--peak-csv", action="append", default=[], help="label=path to precomputed peaks csv")
    stacked.add_argument("output")
    stacked.add_argument("inputs", nargs="+", help="label=path entries")

    overlay = subparsers.add_parser("overlay")
    overlay.add_argument("input")
    overlay.add_argument("output")
    overlay.add_argument("--label", default="sample")
    overlay.add_argument("--peak-csv")
    overlay.add_argument("--ref", action="append", default=[], help="phase=43.3,50.4,74.3")

    return parser


def main() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "axes.linewidth": 1.1,
            "xtick.direction": "in",
            "ytick.direction": "in",
        }
    )
    parser = build_parser()
    args = parser.parse_args()

    if args.mode == "single":
        trace = Trace(label=args.label, xy=load_smartlab_xy(Path(args.input)))
        peak_csv = Path(args.peak_csv) if args.peak_csv else None
        peaks = plot_single(trace, Path(args.output), peak_csv=peak_csv)
        print(f"Saved single plot to {args.output}")
        print(f"Detected {len(peaks)} peaks")
        return

    if args.mode == "stacked":
        traces: list[Trace] = []
        peak_csv_map = parse_peak_csv_map(args.peak_csv)
        for item in args.inputs:
            label, path = item.split("=", 1)
            traces.append(Trace(label=label, xy=load_smartlab_xy(Path(path))))
        plot_stacked(traces, Path(args.output))
        if peak_csv_map:
            print(f"Loaded {len(peak_csv_map)} precomputed peak tables")
        print(f"Saved stacked plot to {args.output}")
        return

    if args.mode == "overlay":
        trace = Trace(label=args.label, xy=load_smartlab_xy(Path(args.input)))
        refs = parse_refs(args.ref)
        peak_csv = Path(args.peak_csv) if args.peak_csv else None
        peaks = plot_with_refs(trace, refs, Path(args.output), peak_csv=peak_csv)
        print(f"Saved overlay plot to {args.output}")
        print(f"Detected {len(peaks)} peaks")
        return


if __name__ == "__main__":
    main()
