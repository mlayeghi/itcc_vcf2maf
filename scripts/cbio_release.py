#!/usr/bin/env python3

import shutil
from pathlib import Path


def _merge_maf(maf_files: list[Path], output_file: Path) -> None:
    no_header_lines = 2

    with output_file.open("w") as out:
        # Write header from first file
        with maf_files[0].open() as f:
            for _ in range(no_header_lines):
                out.write(f.readline())

        # Append remaining lines from all files
        for maf in maf_files:
            with maf.open() as f:
                for i, line in enumerate(f):
                    if i >= no_header_lines:
                        out.write(line)


def _merge_seg(seg_files: list[Path], output_file: Path) -> None:
    no_header_lines = 1

    with output_file.open("w") as out:
        out.write("ID\tchrom\tloc.start\tloc.end\tnum.mark\tseg.mean\n")

        for seg in seg_files:
            with seg.open() as f:
                for i, line in enumerate(f):
                    if i >= no_header_lines:
                        out.write(line)


def _replace_placeholder(template: Path, output: Path, release_id: str):
    text = template.read_text()
    text = text.replace("STABLE_ID_PLACEHOLDER", release_id)
    output.write_text(text)


def _write_meta_files(release_id: str, templates_dir: Path, output_dir: Path):
    replacements = {
        "meta_mutation_template.txt": "meta_mutation.txt",
        "meta_seg_template.txt": "meta_seg.txt",
        "meta_clinical_patient_template.txt": "meta_clinical_patient.txt",
        "meta_clinical_sample_template.txt": "meta_clinical_sample.txt",
        "meta_study_template.txt": "meta_study.txt",
    }

    for template_name, out_name in replacements.items():
        _replace_placeholder(
            templates_dir / template_name,
            output_dir / out_name,
            release_id,
        )

    # direct copies
    shutil.copy(
        templates_dir / "cancer_type_template.txt",
        output_dir / "cancer_type.txt",
    )
    shutil.copy(
        templates_dir / "meta_cancer_type_template.txt",
        output_dir / "meta_cancer_type.txt",
    )


def _write_clinical_files(
    clinical_tsv: Path,
    templates_dir: Path,
    output_dir: Path,
):
    patient_template = templates_dir / "data_clinical_patient_template.txt"
    sample_template = templates_dir / "data_clinical_sample_template.txt"

    patient_out = output_dir / "data_clinical_patient.txt"
    sample_out = output_dir / "data_clinical_sample.txt"

    shutil.copy(patient_template, patient_out)
    shutil.copy(sample_template, sample_out)

    seen = set()

    with clinical_tsv.open() as f:
        header = next(f)
        for line in f:
            patient, sample = line.strip().split("\t")[:2]

            patient_row = f"1\tfemale\t40\t0:LIVING\t{patient}\n"
            if patient_row not in seen:
                with patient_out.open("a") as p:
                    p.write(patient_row)
                seen.add(patient_row)

            with sample_out.open("a") as s:
                s.write(f"{sample}\t{patient}\n")


def _write_case_lists(
    release_id: str,
    clinical_tsv: Path,
    templates_dir: Path,
    output_dir: Path,
):
    case_dir = output_dir / "case_lists"
    case_dir.mkdir(exist_ok=True)

    template = templates_dir / "cases_sequenced_template.txt"
    case_out = case_dir / "cases_sequenced.txt"

    text = template.read_text().replace("STABLE_ID_PLACEHOLDER", release_id)
    case_out.write_text(text.rstrip())

    samples = []
    with clinical_tsv.open() as f:
        next(f)
        for line in f:
            samples.append(line.strip().split("\t")[-1])

    with case_out.open("a") as f:
        f.write("\t" + "\t".join(samples))


def make_cbio_release(
    release_id: str,
    maf_files: list[Path],
    seg_files: list[Path],
    templates_dir: Path,
    clinical_tsv: Path,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Processing {len(maf_files)} MAF files...")
    _merge_maf(maf_files, output_dir / "data_mutation.maf")

    print(f"Processing {len(seg_files)} SEG files...")
    _merge_seg(seg_files, output_dir / "data_seg.seg")

    _write_meta_files(release_id, templates_dir, output_dir)
    _write_clinical_files(clinical_tsv, templates_dir, output_dir)
    _write_case_lists(release_id, clinical_tsv, templates_dir, output_dir)
