# Python Template Usage

## Template file

- `templates/python_search_match_template.py`

## When to use it

Use this template when the user wants:
- a runnable Python starting point
- CSV-based experimental XRD matching
- CIF-based theoretical reference generation
- simple search-match scoring
- a first-pass multiphase NNLS idea

## What the template does

- reads experimental CSV (`2theta,intensity`)
- preprocesses and extracts peaks
- loads reference peaks from JSON and/or builds them from CIF
- runs single-phase search-match ranking
- optionally runs simple whole-pattern NNLS on top candidates

## What it does not pretend to solve

- it is not a full Rietveld refinement engine
- it is not a replacement for GSAS-II
- it does not guarantee phase quantification quality
- it does not eliminate the need for chemistry/microscopy cross-checks

## Example usage

### Using a JSON reference database

```bash
python templates/python_search_match_template.py sample.csv --reference-json refs.json --show-peaks
```

### Using local CIF files

```bash
python templates/python_search_match_template.py sample.csv --cif phase_a.cif --cif phase_b.cif --show-peaks
```

### With simple NNLS mixture estimation

```bash
python templates/python_search_match_template.py sample.csv --reference-json refs.json --nnls
```

## Answering guidance

When presenting this template to users, explain:
1. where they provide experimental CSV
2. where they provide CIF or reference peaks
3. that search-match ranking is screening
4. that final confirmation may still need GSAS-II / refinement
