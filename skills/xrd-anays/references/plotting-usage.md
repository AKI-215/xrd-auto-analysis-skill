# XRD Plotting Usage

## Template file

- `templates/plot_xrd_generic.py`

## When to use it

Use this plotting helper when the user wants:
- a quick single-pattern figure with labeled peaks
- a stacked comparison across multiple samples
- an overlay of sample pattern and candidate reference peak positions
- a reusable plotting script alongside the phase-identification skill

## What the script expects

The script reads text XY data where each valid data row contains:
- `2theta intensity`

It is tolerant of header noise and keeps only rows matching a numeric two-column pattern.

## Modes

### 1. Single plot

Purpose:
- plot one experimental trace
- detect peaks automatically or reuse a prepared peak CSV
- annotate peak positions on the figure

Example:

```bash
python templates/plot_xrd_generic.py single sample.xy sample_single.png --label "sample A"
```

With precomputed peaks:

```bash
python templates/plot_xrd_generic.py single sample.xy sample_single.png --label "sample A" --peak-csv sample_peaks.csv
```

Peak CSV format:

```csv
two_theta_deg,intensity
43.50,12500
50.70,9800
74.60,8700
```

If `intensity` is omitted or blank, the script snaps the peak height from the nearest point in the trace.

### 2. Stacked plot

Purpose:
- compare several samples in one figure
- normalize each trace independently
- apply vertical offsets for readability

Example:

```bash
python templates/plot_xrd_generic.py stacked stacked.png A=sample_a.xy B=sample_b.xy C=sample_c.xy
```

Notes:
- labels are passed as `label=path`
- the script plots only the common overlapping 2theta range across all traces
- current implementation accepts `--peak-csv label=path` arguments for bookkeeping, but does not draw those peak tables in stacked mode

### 3. Overlay plot with reference peaks

Purpose:
- compare one experimental trace against one or more candidate reference peak sets
- show candidate phases as tick marks beneath the normalized trace
- visually support search-match discussion

Example:

```bash
python templates/plot_xrd_generic.py overlay sample.xy overlay.png --label "sample A" --ref "Fe3O4=30.1,35.5,43.1,57.0,62.6" --ref "Fe2O3=24.1,33.2,35.6,49.5,54.1,62.5"
```

Optional peak reuse:

```bash
python templates/plot_xrd_generic.py overlay sample.xy overlay.png --label "sample A" --peak-csv sample_peaks.csv --ref "NiO=37.2,43.3,62.9,75.4,79.4"
```

## Recommended workflow

1. use `single` to inspect raw sample quality and auto-picked peaks
2. adjust or replace peaks with a curated CSV if needed
3. use `overlay` to compare the sample with candidate phase peak lists
4. use `stacked` when comparing oxidation states, time points, depths, or processing conditions

## Limitations

- this script is a visualization helper, not a final phase-confirmation engine
- automatic peak picking is heuristic and may miss weak, broad, or heavily overlapped peaks
- overlay references are only as reliable as the peak list you provide
- if reference peaks are not derived from a real PDF card or real `.cif` calculation, state that clearly in the analysis

## Answering guidance

When presenting plots from this helper, explain:
1. whether peaks were auto-detected or manually curated
2. whether reference ticks came from CIF/PDF-backed data or provisional candidate lists
3. that visual agreement supports ranking but does not by itself prove final phase identification
