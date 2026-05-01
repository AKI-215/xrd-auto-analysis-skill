from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class ExpPeak:
    two_theta: float
    intensity: float
    rel_intensity: float
    quality_flag: str = ""


@dataclass
class RefPeak:
    phase: str
    two_theta: float
    rel_intensity: float
    hkl: str = ""
    source: str = ""


@dataclass
class PhaseScore:
    phase: str
    score: float
    label: str
    matched_ref_coverage: float
    matched_obs_coverage: float
    rms_delta_2theta: float | None
    matched_count: int
    missing_strong_refs: list[dict]
    unmatched_strong_obs: list[dict]
    matches: list[dict]
    why_not_higher: list[str]


def first_existing(row: dict, names: list[str], default: str | None = None) -> str | None:
    for n in names:
        if n in row and row[n] not in (None, ""):
            return row[n]
    return default


def read_exp_peaks(path: Path) -> list[ExpPeak]:
    rows = list(csv.DictReader(path.open("r", encoding="utf-8-sig")))
    raw: list[tuple[float, float, float | None, str]] = []
    intensities: list[float] = []
    for r in rows:
        x = float(first_existing(r, ["two_theta_deg", "two_theta", "2theta", "x"]) or 0)
        intensity = float(first_existing(r, ["intensity", "I", "y"], "0") or 0)
        rel_raw = first_existing(r, ["rel_intensity", "relative_intensity"], None)
        rel = float(rel_raw) if rel_raw not in (None, "") else None
        quality = first_existing(r, ["quality_flag"], "") or ""
        intensities.append(intensity)
        raw.append((x, intensity, rel, quality))
    ymax = max(intensities) if intensities else 1.0
    peaks: list[ExpPeak] = []
    for x, intensity, rel, quality in raw:
        if rel is None:
            rel = 100.0 * intensity / ymax if ymax else 0.0
        peaks.append(ExpPeak(x, intensity, rel, quality))
    return peaks


def read_ref_peaks(path: Path) -> list[RefPeak]:
    rows = list(csv.DictReader(path.open("r", encoding="utf-8-sig")))
    refs: list[RefPeak] = []
    for r in rows:
        phase = (first_existing(r, ["phase", "phase_name"]) or "").strip()
        if not phase:
            continue
        refs.append(
            RefPeak(
                phase=phase,
                two_theta=float(first_existing(r, ["two_theta_deg", "two_theta", "2theta"]) or 0),
                rel_intensity=float(first_existing(r, ["rel_intensity", "intensity"], "100") or 100),
                hkl=(first_existing(r, ["hkl"], "") or "").strip(),
                source=(first_existing(r, ["source"], "") or "").strip(),
            )
        )
    return refs


def best_match(ref: RefPeak, exp_peaks: list[ExpPeak], tolerance: float) -> tuple[int, ExpPeak, float] | None:
    candidates = [
        (i, p, abs(p.two_theta - ref.two_theta))
        for i, p in enumerate(exp_peaks)
        if abs(p.two_theta - ref.two_theta) <= tolerance
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda item: item[2])


def label_from_score(score: float, matched_count: int, rms: float | None, strong_unmatched: int, strong_missing: int) -> str:
    if matched_count < 2:
        return "低置信可能" if score >= 0.35 else "暂不支持"
    if strong_unmatched >= 2 or strong_missing >= 2:
        return "中置信倾向" if score >= 0.55 else "低置信可能"
    if rms is not None and rms > 0.20:
        return "中置信倾向" if score >= 0.55 else "低置信可能"
    if score >= 0.75 and matched_count >= 3:
        return "高置信支持"
    if score >= 0.55:
        return "中置信倾向"
    if score >= 0.35:
        return "低置信可能"
    return "暂不支持"


def score_phase(
    phase: str,
    refs: list[RefPeak],
    exp_peaks: list[ExpPeak],
    tolerance: float,
    strong_ref_threshold: float,
    strong_obs_threshold: float,
    calibration_score: float,
    context_score: float,
    independent_evidence_score: float,
) -> PhaseScore:
    phase_refs = sorted([r for r in refs if r.phase == phase], key=lambda r: r.rel_intensity, reverse=True)
    if not phase_refs:
        raise ValueError(f"No refs for phase {phase}")

    matches: list[dict] = []
    matched_exp_indices: set[int] = set()
    deltas: list[float] = []
    matched_ref_intensity = 0.0
    total_ref_intensity = sum(r.rel_intensity for r in phase_refs) or 1.0

    for ref in phase_refs:
        m = best_match(ref, exp_peaks, tolerance)
        if m is None:
            continue
        exp_idx, exp, delta_abs = m
        matched_exp_indices.add(exp_idx)
        delta = exp.two_theta - ref.two_theta
        deltas.append(delta)
        matched_ref_intensity += ref.rel_intensity
        matches.append(
            {
                "phase": phase,
                "ref_2theta": round(ref.two_theta, 4),
                "exp_2theta": round(exp.two_theta, 4),
                "delta": round(delta, 4),
                "ref_rel_intensity": round(ref.rel_intensity, 2),
                "exp_rel_intensity": round(exp.rel_intensity, 2),
                "hkl": ref.hkl,
                "source": ref.source,
                "quality_flag": exp.quality_flag,
            }
        )

    matched_obs_intensity = sum(exp_peaks[i].rel_intensity for i in matched_exp_indices)
    total_obs_intensity = sum(p.rel_intensity for p in exp_peaks) or 1.0

    missing_strong_refs = [
        {
            "phase": r.phase,
            "ref_2theta": round(r.two_theta, 4),
            "ref_rel_intensity": round(r.rel_intensity, 2),
            "hkl": r.hkl,
            "source": r.source,
        }
        for r in phase_refs
        if r.rel_intensity >= strong_ref_threshold and best_match(r, exp_peaks, tolerance) is None
    ]

    unmatched_strong_obs = [
        {
            "exp_2theta": round(p.two_theta, 4),
            "exp_rel_intensity": round(p.rel_intensity, 2),
            "quality_flag": p.quality_flag,
        }
        for i, p in enumerate(exp_peaks)
        if p.rel_intensity >= strong_obs_threshold and i not in matched_exp_indices
    ]

    rms = None
    if deltas:
        rms = (sum(d * d for d in deltas) / len(deltas)) ** 0.5

    ref_cov = matched_ref_intensity / total_ref_intensity
    obs_cov = matched_obs_intensity / total_obs_intensity
    count_score = min(len(matches) / 3.0, 1.0)

    rms_penalty = min((rms or 0.0) / max(tolerance, 1e-6), 1.0) * 0.12
    missing_penalty = min(len(missing_strong_refs) * 0.10, 0.25)
    unmatched_penalty = min(len(unmatched_strong_obs) * 0.08, 0.25)

    raw_score = (
        0.30 * ref_cov
        + 0.25 * obs_cov
        + 0.15 * count_score
        + 0.10 * calibration_score
        + 0.10 * context_score
        + 0.10 * independent_evidence_score
    )
    score = max(0.0, min(1.0, raw_score - rms_penalty - missing_penalty - unmatched_penalty))
    label = label_from_score(score, len(matches), rms, len(unmatched_strong_obs), len(missing_strong_refs))

    why_not_higher: list[str] = []
    if len(matches) < 3:
        why_not_higher.append("匹配峰少于 3 个，不能作为高置信定相。")
    if rms is not None and rms > 0.15:
        why_not_higher.append(f"匹配峰 RMS Δ2θ = {rms:.3f}°，偏大。")
    if missing_strong_refs:
        why_not_higher.append("存在候选相强参考峰缺失。")
    if unmatched_strong_obs:
        why_not_higher.append("存在强实验峰尚未被该候选相解释。")
    if calibration_score < 0.8:
        why_not_higher.append("零点/主相峰校准状态不充分。")
    if independent_evidence_score < 0.5:
        why_not_higher.append("缺少 SEM-EDS / XPS / Raman / GIXRD 等独立证据支持。")
    if not why_not_higher and label == "高置信支持":
        why_not_higher.append("当前满足高置信最低条件；仍建议结合样品背景复核。")

    return PhaseScore(
        phase=phase,
        score=round(score, 3),
        label=label,
        matched_ref_coverage=round(ref_cov, 3),
        matched_obs_coverage=round(obs_cov, 3),
        rms_delta_2theta=round(rms, 4) if rms is not None else None,
        matched_count=len(matches),
        missing_strong_refs=missing_strong_refs,
        unmatched_strong_obs=unmatched_strong_obs,
        matches=matches,
        why_not_higher=why_not_higher,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Score XRD phase confidence from experimental peaks and reference peaks.")
    parser.add_argument("--peaks", required=True, help="Experimental peaks CSV")
    parser.add_argument("--refs", required=True, help="Reference peaks CSV: phase,two_theta_deg,rel_intensity,hkl,source")
    parser.add_argument("--out", default="xrd_phase_confidence_report.json")
    parser.add_argument("--tolerance", type=float, default=0.20, help="2theta matching tolerance in degrees")
    parser.add_argument("--strong-ref", type=float, default=35.0, help="Reference peaks >= this rel intensity are strong")
    parser.add_argument("--strong-obs", type=float, default=20.0, help="Experimental peaks >= this rel intensity are strong")
    parser.add_argument("--calibration-score", type=float, default=0.5, help="0-1; use 1 only after explicit calibration")
    parser.add_argument("--context-score", type=float, default=0.7, help="0-1; chemistry/environment plausibility")
    parser.add_argument("--independent-evidence-score", type=float, default=0.0, help="0-1; SEM-EDS/XPS/Raman/GIXRD support")
    args = parser.parse_args()

    exp_peaks = read_exp_peaks(Path(args.peaks))
    refs = read_ref_peaks(Path(args.refs))
    phases = sorted({r.phase for r in refs if r.phase})
    scores = [
        score_phase(
            p,
            refs,
            exp_peaks,
            args.tolerance,
            args.strong_ref,
            args.strong_obs,
            args.calibration_score,
            args.context_score,
            args.independent_evidence_score,
        )
        for p in phases
    ]
    scores.sort(key=lambda s: s.score, reverse=True)

    out = {
        "settings": {
            "tolerance_2theta_deg": args.tolerance,
            "strong_ref_threshold": args.strong_ref,
            "strong_obs_threshold": args.strong_obs,
            "calibration_score": args.calibration_score,
            "context_score": args.context_score,
            "independent_evidence_score": args.independent_evidence_score,
        },
        "phase_scores": [asdict(s) for s in scores],
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved: {args.out}")
    for s in scores:
        print(f"{s.phase}: {s.score:.3f} | {s.label} | matches={s.matched_count} | rms={s.rms_delta_2theta}")


if __name__ == "__main__":
    main()
