# Python Search-Match Reference

## Core idea

A practical Python XRD identification pipeline is:

1. background correction / smoothing / normalization
2. peak extraction from experimental pattern
3. convert candidate structures or cards into reference patterns
4. search-match scoring using peak position + intensity
5. test single-phase explanation first
6. escalate to multiphase fitting when unexplained strong peaks remain
7. use refinement for publication-grade confirmation

## Typical Python stack

- `scipy.signal.find_peaks` for peak detection
- `scipy.signal.savgol_filter` for smoothing
- `pymatgen.analysis.diffraction.xrd.XRDCalculator` for theoretical XRD from `.cif`
- `scipy.optimize.nnls` for non-negative whole-pattern combination ideas
- `GSAS-II` for Rietveld refinement / higher-confidence confirmation

## Expected input

Typical experimental input:

- `two_theta`
- `intensity`
- optional metadata: wavelength, target, scan range, step size, GI-XRD vs conventional, cleaning history

## Matching logic

### Peak-position matching

Two common criteria:

- `|Δ2θ| < tolerance`
- or relative d-spacing error threshold

### Intensity-aware scoring

A practical score may combine:

- fraction of strong reference peaks that are matched
- relative intensity similarity
- penalty for missing hallmark peaks
- penalty when experimental strong peaks remain unexplained

## Suggested response style when user asks for algorithm

Explain in this order:

1. experimental preprocessing
2. peak extraction
3. reference pattern source
4. scoring formula or search-match logic
5. multiphase extension
6. CIF integration path
7. refinement / validation path

## Multiphase policy

If one phase cannot explain major peaks, recommend:

- greedy residual matching
- or whole-pattern linear combination / NNLS

Do not present a single-phase answer as final when strong unexplained peaks remain.

## Refinement policy

For research-grade or paper-grade conclusions:

- search-match ranking is screening, not final proof
- recommend Rietveld refinement, GSAS-II, and chemistry/microscopy cross-checks when needed
