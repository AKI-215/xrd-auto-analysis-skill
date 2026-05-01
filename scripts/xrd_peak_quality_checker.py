from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

XY_PATTERN = re.compile(r"^\s*([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s+([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s*$")


@dataclass
class Peak:
    two_theta: float
    intensity: float
    baseline: float
    net_intensity: float
    rel_intensity: float
    prominence: float
    snr_est: float
    quality_flag: str


def load_xy(path: Path) -> np.ndarray:
    rows: list[tuple[float, float]] = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    for line in text.splitlines():
        s = line.strip().replace(",", " ")
        m = XY_PATTERN.match(s)
        if m:
            rows.append((float(m.group(1)), float(m.group(2))))
    if not rows:
        raise ValueError(f"No two-column XY data found in {path}")
    arr = np.asarray(rows, dtype=float)
    order = np.argsort(arr[:, 0])
    return arr[order]


def moving_average(values: np.ndarray, window: int) -> np.ndarray:
    window = max(1, int(window))
    if window <= 1:
        return values.copy()
    pad = window // 2
    padded = np.pad(values, (pad, pad), mode="edge")
    kernel = np.ones(window, dtype=float) / window
    return np.convolve(padded, kernel, mode="valid")[: len(values)]


def rolling_percentile(values: np.ndarray, window: int, percentile: float) -> np.ndarray:
    window = max(3, int(window))
    if window % 2 == 0:
        window += 1
    radius = window // 2
    out = np.empty_like(values, dtype=float)
    for i in range(len(values)):
        lo = max(0, i - radius)
        hi = min(len(values), i + radius + 1)
        out[i] = np.percentile(values[lo:hi], percentile)
    return out


def estimate_noise(net: np.ndarray) -> float:
    diff = np.diff(net)
    if len(diff) == 0:
        return 1.0
    mad = np.median(np.abs(diff - np.median(diff)))
    sigma = 1.4826 * mad / np.sqrt(2)
    return float(max(sigma, 1e-9))


def parse_min_prominence(value: str, net: np.ndarray, noise: float) -> float:
    if value.lower() == "auto":
        return max(5.0 * noise, 0.03 * float(np.max(net) - np.min(net)))
    return float(value)


def detect_peaks(
    xy: np.ndarray,
    smooth_window: int = 7,
    baseline_window: int = 151,
    min_prominence: str = "auto",
    min_spacing: float = 0.25,
) -> list[Peak]:
    x = xy[:, 0]
    y_raw = xy[:, 1]
    y_smooth = moving_average(y_raw, smooth_window)
    baseline = rolling_percentile(y_smooth, baseline_window, 10)
    net = y_smooth - baseline
    noise = estimate_noise(net)
    prominence_threshold = parse_min_prominence(min_prominence, net, noise)

    candidates: list[tuple[float, int]] = []
    half_window = max(3, smooth_window)
    for i in range(half_window, len(net) - half_window):
        center = net[i]
        if center <= 0:
            continue
        if not (center >= net[i - 1] and center > net[i + 1]):
            continue
        left_min = float(np.min(net[max(0, i - 30):i]))
        right_min = float(np.min(net[i + 1:min(len(net), i + 31)]))
        prominence = center - max(left_min, right_min)
        if prominence >= prominence_threshold:
            candidates.append((prominence, i))

    candidates.sort(reverse=True, key=lambda item: item[0])
    selected: list[tuple[float, int]] = []
    for prominence, idx in candidates:
        if all(abs(float(x[idx]) - float(x[j])) >= min_spacing for _, j in selected):
            selected.append((prominence, idx))

    selected.sort(key=lambda item: x[item[1]])
    max_net = max([float(net[idx]) for _, idx in selected], default=1.0)
    peaks: list[Peak] = []
    for prominence, idx in selected:
        net_i = float(max(net[idx], 0.0))
        rel = 100.0 * net_i / max_net if max_net else 0.0
        snr = net_i / noise if noise else 0.0
        if snr >= 10 and rel >= 10:
            flag = "strong"
        elif snr >= 5 and rel >= 3:
            flag = "medium"
        else:
            flag = "weak_check_manually"
        peaks.append(
            Peak(
                two_theta=float(x[idx]),
                intensity=float(y_raw[idx]),
                baseline=float(baseline[idx]),
                net_intensity=net_i,
                rel_intensity=rel,
                prominence=float(prominence),
                snr_est=float(snr),
                quality_flag=flag,
            )
        )
    return peaks


def write_peaks(path: Path, peaks: list[Peak]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "two_theta_deg",
            "intensity",
            "baseline",
            "net_intensity",
            "rel_intensity",
            "prominence",
            "snr_est",
            "quality_flag",
        ])
        for p in peaks:
            writer.writerow([
                f"{p.two_theta:.4f}",
                f"{p.intensity:.4f}",
                f"{p.baseline:.4f}",
                f"{p.net_intensity:.4f}",
                f"{p.rel_intensity:.2f}",
                f"{p.prominence:.4f}",
                f"{p.snr_est:.2f}",
                p.quality_flag,
            ])


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract XRD peaks with quality metrics.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--smooth-window", type=int, default=7)
    parser.add_argument("--baseline-window", type=int, default=151)
    parser.add_argument("--min-prominence", default="auto")
    parser.add_argument("--min-spacing", type=float, default=0.25)
    args = parser.parse_args()

    xy = load_xy(Path(args.input))
    peaks = detect_peaks(
        xy,
        smooth_window=args.smooth_window,
        baseline_window=args.baseline_window,
        min_prominence=args.min_prominence,
        min_spacing=args.min_spacing,
    )
    write_peaks(Path(args.out), peaks)
    print(f"Saved: {args.out}")
    print(f"Detected peaks: {len(peaks)}")
    for p in peaks:
        print(f"{p.two_theta:.3f} deg | rel={p.rel_intensity:.1f} | snr={p.snr_est:.1f} | {p.quality_flag}")


if __name__ == "__main__":
    main()
