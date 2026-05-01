from pathlib import Path
import shutil

from PyXplore import WPEM


def main() -> None:
    base = Path(r"D:\Users\oo\Desktop\GIT\xrd")
    fit_dir = base / "pyxplore_only_fit_316Ti-2"
    fit_dir.mkdir(parents=True, exist_ok=True)

    src_txt = base / "316Ti-2.txt"
    raw_csv = fit_dir / "raw_no_header.csv"
    with src_txt.open("r", encoding="utf-8", errors="ignore") as rf, raw_csv.open(
        "w", encoding="utf-8"
    ) as wf:
        for line in rf:
            s = line.strip()
            if not s or s.startswith("*"):
                continue
            parts = s.split()
            if len(parts) != 2:
                continue
            try:
                float(parts[0])
                float(parts[1])
            except ValueError:
                continue
            wf.write(parts[0] + "," + parts[1] + "\n")

    candidate_cifs = [
        ("peak0.csv", base / "Structures_cif" / "MetalsAlloysOxides" / "Fe-Austenite.cif"),
        ("peak1.csv", base / "Structures_cif" / "MetalsAlloysOxides" / "Cr23C6.cif"),
        ("peak2.csv", base / "Structures_cif" / "MetalsAlloysOxides" / "Ti-hcp.cif"),
    ]

    lattice_constants = []
    density_list = []
    root_hkl_fallbacks = {
        "peak1.csv": Path(r"D:\Cr23C6HKL.csv"),
        "peak2.csv": Path(r"D:\Ti-hcpHKL.csv"),
    }

    for peak_name, cif_path in candidate_cifs:
        if peak_name == "peak0.csv" and not (fit_dir / peak_name).exists():
            subdir = fit_dir / peak_name.replace(".csv", "")
            subdir.mkdir(parents=True, exist_ok=True)
            WPEM.CIFpreprocess(
                str(cif_path),
                wavelength="CuKa",
                two_theta_range=(10, 80),
                cal_extinction=True,
                relaxation=False,
                work_dir=str(subdir),
            )
            hkl_files = sorted((subdir / "output_xrd").glob("*HKL.csv"))
            if hkl_files:
                shutil.copyfile(hkl_files[0], fit_dir / peak_name)

        if peak_name in root_hkl_fallbacks and root_hkl_fallbacks[peak_name].exists():
            shutil.copyfile(root_hkl_fallbacks[peak_name], fit_dir / peak_name)

        latt, atoms, density = WPEM.CIFpreprocess(
            str(cif_path),
            wavelength="CuKa",
            two_theta_range=(10, 80),
            cal_extinction=True,
            relaxation=False,
            work_dir=str(fit_dir),
        )
        lattice_constants.append(latt)
        density_list.append(density)

    no_bac = base / "pyxplore_tf310_316Ti-2" / "ConvertedDocuments" / "no_bac_intensity.csv"
    bac = base / "pyxplore_tf310_316Ti-2" / "ConvertedDocuments" / "bac.csv"

    result = WPEM.XRDfit(
        wavelength=[1.540593, 1.544414],
        Var=137.67622893933344,
        Lattice_constants=lattice_constants,
        no_bac_intensity_file=str(no_bac),
        original_file=str(raw_csv),
        bacground_file=str(bac),
        density_list=density_list,
        two_theta_range=(10, 80),
        bta=0.8,
        bta_threshold=0.5,
        limit=0.0005,
        iter_limit=0.05,
        w_limit=1e-17,
        iter_max=1,
        lock_num=2,
        asy_C=0.5,
        s_angle=50,
        subset_number=9,
        low_bound=65,
        up_bound=80,
        InitializationEpoch=2,
        MODEL="ANALYSIS",
        Macromolecule=False,
        cpu=1,
        num=3,
        EXACT=False,
        Cu_tao=None,
        Ave_Waves=False,
        loadParams=False,
        ZeroShift=False,
        work_dir=str(fit_dir),
    )
    print("XRDfit result=", result)


if __name__ == "__main__":
    main()
