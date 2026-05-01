from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import csv
import json
import math
from typing import Iterable

import numpy as np
from scipy.signal import find_peaks, savgol_filter

try:
    from pymatgen.core import Structure
    from pymatgen.analysis.diffraction.xrd import XRDCalculator
except Exception:
    Structure = None
    XRDCalculator = None

try:
    from scipy.optimize import nnls
except Exception:
    nnls = None

LAMBDA_CUKA = 1.5406


@dataclass
class PeakPattern:
    two_theta: np.ndarray
    intensity: np.ndarray


@dataclass
class MatchResult:
    phase: str
    score: float
    matched_ratio: float
    missing_ratio: float
    support_pairs: list[dict]
    unmatched_ref_peaks: list[dict]
    unexplained_obs_peaks: list[dict]


def load_xrd_csv(csv_path: str | Path) -> PeakPattern:
    two_theta = []
    intensity = []
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header_checked = False
        for row in reader:
            if not row:
                continue
            if not header_checked:
                header_checked = True
                try:
                    float(row[0])
                    float(row[1])
                except ValueError:
                    continue
            two_theta.append(float(row[0]))
            intensity.append(float(row[1]))
    return PeakPattern(np.asarray(two_theta, dtype=float), np.asarray(intensity, dtype=float))


def normalize_intensity(values: Iterable[float]) -> np.ndarray:
    arr = np.asarray(list(values), dtype=float)
    arr = arr - np.min(arr)
    max_val = np.max(arr)
    if max_val > 0:
        arr = arr / max_val * 100.0
    return arr


def two_theta_to_d(two_theta_deg: Iterable[float], wavelength: float = LAMBDA_CUKA) -> np.ndarray:
    theta_rad = np.deg2rad(np.asarray(list(two_theta_deg), dtype=float) / 2.0)
    return wavelength / (2.0 * np.sin(theta_rad))


def preprocess_pattern(pattern: PeakPattern, window_length: int = 11, polyorder: int = 3) -> PeakPattern:
    y = normalize_intensity(pattern.intensity)
    if len(y) >= window_length and window_length % 2 == 1:
        y = savgol_filter(y, window_length=window_length, polyorder=polyorder)
    return PeakPattern(pattern.two_theta.copy(), y)


def extract_peaks(
    pattern: PeakPattern,
    prominence: float = 3.0,
    distance: int = 10,
    top_n: int = 30,
) -> PeakPattern:
    peaks, _ = find_peaks(pattern.intensity, prominence=prominence, distance=distance)
    peak_tt = pattern.two_theta[peaks]
    peak_i = pattern.intensity[peaks]
    order = np.argsort(peak_i)[::-1][:top_n]
    return PeakPattern(peak_tt[order], peak_i[order])


def gaussian_position_score(delta: float, tolerance: float) -> float:
    sigma = max(tolerance / 2.0, 1e-6)
    return math.exp(-(delta ** 2) / (2.0 * sigma ** 2))


def match_one_phase(
    obs: PeakPattern,
    ref: PeakPattern,
    tolerance: float = 0.2,
    top_n_ref: int = 20,
) -> MatchResult:
    obs_tt = np.asarray(obs.two_theta, dtype=float)
    obs_i = normalize_intensity(obs.intensity)
    ref_tt = np.asarray(ref.two_theta, dtype=float)
    ref_i = normalize_intensity(ref.intensity)

    ref_order = np.argsort(ref_i)[::-1][:top_n_ref]
    ref_tt = ref_tt[ref_order]
    ref_i = ref_i[ref_order]

    matched_weight = 0.0
    missing_weight = 0.0
    support_pairs = []
    unmatched_ref = []
    used_obs = set()

    for rt, ri in zip(ref_tt, ref_i):
        diffs = np.abs(obs_tt - rt)
        if len(diffs) == 0:
            missing_weight += ri
            unmatched_ref.append({"ref_two_theta": float(rt), "ref_intensity": float(ri)})
            continue
        idx = int(np.argmin(diffs))
        delta = float(diffs[idx])
        if delta <= tolerance:
            pos_score = gaussian_position_score(delta, tolerance)
            matched_weight += float(ri) * pos_score
            used_obs.add(idx)
            support_pairs.append(
                {
                    "ref_two_theta": float(rt),
                    "obs_two_theta": float(obs_tt[idx]),
                    "ref_intensity": float(ri),
                    "obs_intensity": float(obs_i[idx]),
                    "delta_two_theta": delta,
                    "position_score": pos_score,
                }
            )
        else:
            missing_weight += float(ri)
            unmatched_ref.append({"ref_two_theta": float(rt), "ref_intensity": float(ri)})

    unexplained_obs = []
    for idx, (ot, oi) in enumerate(zip(obs_tt, obs_i)):
        if idx not in used_obs:
            unexplained_obs.append({"obs_two_theta": float(ot), "obs_intensity": float(oi)})

    total_ref = float(np.sum(ref_i)) + 1e-9
    matched_ratio = matched_weight / total_ref
    missing_ratio = missing_weight / total_ref
    unexplained_penalty = min(len(unexplained_obs), 10) * 0.01
    score = matched_ratio - 0.3 * missing_ratio - unexplained_penalty

    return MatchResult(
        phase="",
        score=float(score),
        matched_ratio=float(matched_ratio),
        missing_ratio=float(missing_ratio),
        support_pairs=support_pairs,
        unmatched_ref_peaks=unmatched_ref,
        unexplained_obs_peaks=unexplained_obs,
    )


def search_match(
    obs: PeakPattern,
    reference_database: dict[str, PeakPattern],
    tolerance: float = 0.2,
    top_n_ref: int = 20,
) -> list[MatchResult]:
    results = []
    for phase_name, ref in reference_database.items():
        result = match_one_phase(obs, ref, tolerance=tolerance, top_n_ref=top_n_ref)
        result.phase = phase_name
        results.append(result)
    return sorted(results, key=lambda item: item.score, reverse=True)


def build_reference_from_cif(cif_path: str | Path, wavelength: str = "CuKa", two_theta_range=(10, 90)) -> PeakPattern:
    if Structure is None or XRDCalculator is None:
        raise RuntimeError("pymatgen is not available. Install pymatgen to build reference patterns from CIF.")
    structure = Structure.from_file(cif_path)
    pattern = XRDCalculator(wavelength=wavelength).get_pattern(structure, two_theta_range=two_theta_range)
    return PeakPattern(np.asarray(pattern.x, dtype=float), np.asarray(pattern.y, dtype=float))


def load_reference_database_from_json(json_path: str | Path) -> dict[str, PeakPattern]:
    with open(json_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    database = {}
    for phase_name, phase_data in raw.items():
        database[phase_name] = PeakPattern(
            np.asarray(phase_data["two_theta"], dtype=float),
            np.asarray(phase_data["intensity"], dtype=float),
        )
    return database


def whole_pattern_nnls(
    exp_pattern: PeakPattern,
    candidate_patterns: dict[str, PeakPattern],
    sigma: float = 0.12,
) -> dict[str, float]:
    if nnls is None:
        raise RuntimeError("scipy.optimize.nnls is not available.")

    x = exp_pattern.two_theta
    y = normalize_intensity(exp_pattern.intensity)
    columns = []
    names = []

    for name, pattern in candidate_patterns.items():
        vec = np.zeros_like(x, dtype=float)
        ref_i = normalize_intensity(pattern.intensity)
        for peak_tt, peak_i in zip(pattern.two_theta, ref_i):
            vec += peak_i * np.exp(-((x - peak_tt) ** 2) / (2.0 * sigma ** 2))
        columns.append(vec)
        names.append(name)

    A = np.column_stack(columns)
    coeffs, _ = nnls(A, y)
    total = float(np.sum(coeffs)) + 1e-9
    return {name: float(coeff / total) for name, coeff in zip(names, coeffs) if coeff > 1e-8}


def print_top_results(results: list[MatchResult], limit: int = 5) -> None:
    for result in results[:limit]:
        print(
            f"{result.phase}: score={result.score:.3f}, "
            f"matched_ratio={result.matched_ratio:.3f}, "
            f"missing_ratio={result.missing_ratio:.3f}, "
            f"unexplained_obs={len(result.unexplained_obs_peaks)}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Reusable XRD search-match template")
    parser.add_argument("experimental_csv", help="CSV with columns: 2theta, intensity")
    parser.add_argument("--reference-json", help="JSON database with reference peaks")
    parser.add_argument("--cif", action="append", default=[], help="One or more CIF files to convert into reference patterns")
    parser.add_argument("--prominence", type=float, default=3.0)
    parser.add_argument("--distance", type=int, default=10)
    parser.add_argument("--tolerance", type=float, default=0.2)
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument("--show-peaks", action="store_true")
    parser.add_argument("--nnls", action="store_true", help="Run simple whole-pattern NNLS on top ranked candidates")
    args = parser.parse_args()

    exp_raw = load_xrd_csv(args.experimental_csv)
    exp_processed = preprocess_pattern(exp_raw)
    obs_peaks = extract_peaks(exp_processed, prominence=args.prominence, distance=args.distance)

    if args.show_peaks:
        print("Observed peaks (2theta, intensity):")
        for tt, inten in zip(obs_peaks.two_theta, obs_peaks.intensity):
            print(f"  {tt:.3f}, {inten:.2f}")

    database = {}
    if args.reference_json:
        database.update(load_reference_database_from_json(args.reference_json))

    for cif_path in args.cif:
        phase_name = Path(cif_path).stem
        database[phase_name] = build_reference_from_cif(cif_path)

    if not database:
        raise SystemExit("No reference database provided. Use --reference-json and/or --cif.")

    results = search_match(obs_peaks, database, tolerance=args.tolerance, top_n_ref=args.top_n)
    print_top_results(results)

    if args.nnls:
        top_candidates = {result.phase: database[result.phase] for result in results[: min(5, len(results))]}
        fractions = whole_pattern_nnls(exp_processed, top_candidates)
        print("\nNNLS candidate fractions:")
        for phase, frac in sorted(fractions.items(), key=lambda item: item[1], reverse=True):
            print(f"  {phase}: {frac:.3f}")


if __name__ == "__main__":
    main()
