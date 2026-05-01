# XRD Matching Workflow

## Stage 1 — Sample constraint intake

Collect before any matching:

- sample type / material family
- main elements
- minor / trace elements
- impossible elements
- optional: target/wavelength, GI-XRD vs conventional XRD, cleaning history, residue risk
- optional: 2theta, d-spacing, relative intensity

## Search-match algorithm backbone

When the task is phase identification rather than pure note-taking, use this backbone:

1. preprocess experimental spectrum
2. extract peaks from experimental pattern
3. generate reference patterns from database cards or CIF structures
4. perform peak-position + intensity weighted search-match scoring
5. test whether a single phase explains the strong peaks
6. if not, escalate to multiphase interpretation
7. recommend refinement / Rietveld validation for publication-grade conclusions

Useful Python framing:
- `scipy.signal.find_peaks` for peak picking
- `pymatgen.analysis.diffraction.xrd.XRDCalculator` for theoretical patterns from `.cif`
- `GSAS-II` when the user needs whole-pattern refinement or high-confidence quantification

## Stage 2 — Branch by evidence level

### Branch A: no peak data

This is **candidate prescreening only**.

You may:
- rank plausible phases by element fit
- exclude phases containing impossible elements
- highlight underdetermined candidates

You may not:
- claim final phase identification
- say a phase is confirmed

### Branch B: peak data present

Use both composition and peak support.

For each candidate phase:
- note supporting peaks
- note conflicting peaks
- note missing hallmark peaks
- lower confidence when overlap is common or key peaks are absent

## Confidence rules

### High
- composition strongly fits
- no impossible-element conflict
- hallmark peaks are supported
- no obvious conflicting peak set

### Medium
- composition fits
- peak support is partial or overlapping
- one or more confirmation methods still needed

### Low
- weak composition fit
- missing hallmark peaks
- possible forbidden-element issue
- plausible only as a remote candidate

## Output policy

Always output:
1. sample constraint summary
2. candidate match card area
3. next-step confirmation advice

## CIF/PDF rule

A candidate card may contain:
- actual local `.cif` path if known
- actual PDF card reference if user provided one
- otherwise: `待绑定实际 CIF/PDF 卡确认`

Never invent a CIF file, PDF number, or structure path.

## General cautions

- XRD identifies crystalline phases, not full mechanism.
- Thin or amorphous phases may be invisible.
- Residual contamination can mimic real products.
- Overlapping oxides/spinels need auxiliary methods.
