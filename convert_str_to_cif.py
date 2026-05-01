from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path


PARAM_PATTERN = re.compile(r"PARAM=([A-Z]+)=([^\s/]+)")
BARE_CELL_PATTERN = re.compile(r"\b(ALPHA|BETA|GAMMA|A|B|C)=([^\s/]+)")
FIELD_PATTERN = re.compile(r"([A-Za-z][A-Za-z0-9_]*)=([^=\s][^=]*?)(?=\s+[A-Za-z][A-Za-z0-9_]*=|$)")
SPECIES_MIX_PATTERN = re.compile(r"([A-Za-z]{1,3})(?:[+-]\d+)?(?:\(([0-9.]+)\))?")


@dataclass
class AtomSite:
    symbol: str
    occupancy: float
    x: float
    y: float
    z: float


def normalize_symbol(raw: str) -> str:
    letters = "".join(ch for ch in raw if ch.isalpha())
    if not letters:
        return "X"
    if len(letters) == 1:
        return letters.upper()
    return letters[0].upper() + letters[1:].lower()


def parse_species(raw: str) -> list[tuple[str, float]]:
    raw = raw.strip()
    if raw.startswith("(") and raw.endswith(")"):
        matches = SPECIES_MIX_PATTERN.findall(raw)
        species = []
        for symbol, occ in matches:
            occupancy = float(occ) if occ else 1.0
            species.append((normalize_symbol(symbol), occupancy))
        return species or [("X", 1.0)]
    return [(normalize_symbol(raw), 1.0)]


def parse_float(value: str | None, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def parse_param_value(token: str) -> float:
    base = token.split("_", 1)[0]
    base = base.split("^", 1)[0]
    return float(base)


def strip_comment(text: str) -> str:
    return text.split("//", 1)[0].strip()


def infer_crystal_system(spacegroup_no: int | None, lattice_name: str | None) -> str:
    if lattice_name:
        name = lattice_name.strip().lower()
        if "rhombo" in name:
            return "rhombohedral"
        if "trig" in name:
            return "trigonal"
        if "hexa" in name:
            return "hexagonal"
        if "tetra" in name:
            return "tetragonal"
        if "ortho" in name:
            return "orthorhombic"
        if "mono" in name:
            return "monoclinic"
        if "tri" in name:
            return "triclinic"
        if "cubic" in name:
            return "cubic"
    if spacegroup_no is None:
        return "triclinic"
    if 1 <= spacegroup_no <= 2:
        return "triclinic"
    if 3 <= spacegroup_no <= 15:
        return "monoclinic"
    if 16 <= spacegroup_no <= 74:
        return "orthorhombic"
    if 75 <= spacegroup_no <= 142:
        return "tetragonal"
    if 143 <= spacegroup_no <= 167:
        return "trigonal"
    if 168 <= spacegroup_no <= 194:
        return "hexagonal"
    if 195 <= spacegroup_no <= 230:
        return "cubic"
    return "triclinic"


def infer_angles(crystal_system: str, params: dict[str, float]) -> tuple[float, float, float]:
    alpha = params.get("ALPHA")
    beta = params.get("BETA")
    gamma = params.get("GAMMA")
    if crystal_system in {"cubic", "tetragonal", "orthorhombic"}:
        return 90.0, 90.0, 90.0
    if crystal_system in {"hexagonal", "trigonal"}:
        return 90.0, 90.0, 120.0
    if crystal_system == "monoclinic":
        return alpha or 90.0, beta or 90.0, gamma or 90.0
    return alpha or 90.0, beta or 90.0, gamma or 90.0


def parse_atom_line(line: str) -> list[AtomSite]:
    fields = dict(FIELD_PATTERN.findall(line))
    species = parse_species(fields.get("E", "X"))
    x = parse_float(fields.get("x"))
    y = parse_float(fields.get("y"))
    z = parse_float(fields.get("z"))
    return [AtomSite(symbol=symbol, occupancy=occupancy, x=x, y=y, z=z) for symbol, occupancy in species]


def parse_str_file(path: Path) -> dict:
    lines = [line.strip() for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip()]
    metadata: dict[str, str] = {}
    params: dict[str, float] = {}
    atom_sites: list[AtomSite] = []

    for line in lines:
        if line.startswith("E="):
            atom_sites.extend(parse_atom_line(line))
            continue
        for key, value in FIELD_PATTERN.findall(line):
            metadata.setdefault(key, strip_comment(value))
        for key, value in PARAM_PATTERN.findall(line):
            try:
                params[key] = parse_param_value(value)
            except ValueError:
                continue
        for key, value in BARE_CELL_PATTERN.findall(strip_comment(line)):
            if key not in params:
                try:
                    params[key] = parse_param_value(value)
                except ValueError:
                    continue

    if "A" not in params:
        raise ValueError("missing lattice parameter A")

    # The .str cards store cell lengths in nm; CIF expects Angstrom.
    a = params["A"] * 10.0
    b = params.get("B", params["A"]) * 10.0
    c = params.get("C", params.get("A")) * 10.0

    spacegroup_no = None
    if "SpacegroupNo" in metadata:
        try:
            spacegroup_no = int(metadata["SpacegroupNo"])
        except ValueError:
            spacegroup_no = None

    crystal_system = infer_crystal_system(spacegroup_no, metadata.get("Lattice"))
    alpha, beta, gamma = infer_angles(crystal_system, params)

    return {
        "phase": strip_comment(metadata.get("PHASE", path.stem)),
        "formula": strip_comment(metadata.get("Formula", "?")),
        "reference": strip_comment(metadata.get("Reference", "")),
        "hm": strip_comment(metadata.get("HermannMauguin", "P1")),
        "spacegroup_no": spacegroup_no or 1,
        "a": a,
        "b": b,
        "c": c,
        "alpha": alpha,
        "beta": beta,
        "gamma": gamma,
        "atom_sites": atom_sites,
    }


def cif_safe_value(value: str) -> str:
    text = value.strip()
    if not text:
        return "?"
    if re.search(r"\s", text):
        return f"'{text}'"
    return text


def write_cif(data: dict, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    phase_id = re.sub(r"[^A-Za-z0-9_]+", "_", data["phase"]).strip("_") or dest.stem
    formula = data["formula"].replace("_", " ")

    lines = [
        f"data_{phase_id}",
        f"_chemical_name_common {cif_safe_value(data['phase'])}",
        f"_chemical_formula_sum {cif_safe_value(formula)}",
        f"_symmetry_space_group_name_H-M {cif_safe_value(data['hm'])}",
        f"_space_group_IT_number {data['spacegroup_no']}",
        f"_cell_length_a {data['a']:.6f}",
        f"_cell_length_b {data['b']:.6f}",
        f"_cell_length_c {data['c']:.6f}",
        f"_cell_angle_alpha {data['alpha']:.6f}",
        f"_cell_angle_beta {data['beta']:.6f}",
        f"_cell_angle_gamma {data['gamma']:.6f}",
        "",
        "loop_",
        "_atom_site_label",
        "_atom_site_type_symbol",
        "_atom_site_fract_x",
        "_atom_site_fract_y",
        "_atom_site_fract_z",
        "_atom_site_occupancy",
    ]

    counts: dict[str, int] = {}
    for site in data["atom_sites"]:
        counts[site.symbol] = counts.get(site.symbol, 0) + 1
        label = f"{site.symbol}{counts[site.symbol]}"
        lines.append(
            f"{label} {site.symbol} {site.x:.6f} {site.y:.6f} {site.z:.6f} {site.occupancy:.6f}"
        )

    if data["reference"]:
        lines.extend(["", f"# Reference: {data['reference']}"])

    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")


def convert_tree(src_root: Path, dst_root: Path) -> tuple[int, int, list[tuple[str, str]]]:
    converted = 0
    failed = 0
    issues: list[tuple[str, str]] = []

    for src in src_root.rglob("*.str"):
        rel = src.relative_to(src_root).with_suffix(".cif")
        dst = dst_root / rel
        try:
            data = parse_str_file(src)
            write_cif(data, dst)
            converted += 1
        except Exception as exc:  # pragma: no cover - batch conversion should continue
            failed += 1
            issues.append((str(src), str(exc)))
    return converted, failed, issues


def write_report(dst_root: Path, converted: int, failed: int, issues: list[tuple[str, str]]) -> None:
    report = dst_root / "_conversion_report.csv"
    with report.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["status", "path", "detail"])
        writer.writerow(["summary", str(dst_root), f"converted={converted};failed={failed}"])
        for path, detail in issues:
            writer.writerow(["failed", path, detail])


def main() -> None:
    src_root = Path(r"D:\Users\oo\Desktop\GIT\xrd\Structures")
    dst_root = Path(r"D:\Users\oo\Desktop\GIT\xrd\Structures_cif")
    converted, failed, issues = convert_tree(src_root, dst_root)
    write_report(dst_root, converted, failed, issues)
    print(f"Converted: {converted}")
    print(f"Failed: {failed}")
    print(f"Output: {dst_root}")


if __name__ == "__main__":
    main()
