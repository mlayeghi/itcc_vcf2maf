#!/usr/bin/env python3

import math
import os.path
import psutil
import shutil
import subprocess

from pathlib import Path

from pedcan_vcf2maf import CONFIG


def is_gzipped(filepath: Path) -> bool:
    with open(filepath, "rb") as f:
        return f.read(2) == b"\x1f\x8b"


def is_text_vcf(filepath: Path) -> bool:
    try:
        with open(filepath, "rt", encoding="utf-8", errors="strict") as f:
            seen_fileformat = False

            for line in f:
                if line.startswith("##fileformat=VCF"):
                    seen_fileformat = True

                if line.startswith("#CHROM"):
                    return seen_fileformat  # must have fileformat first

                if not line.startswith("#"):
                    # We hit data before #CHROM → invalid VCF
                    return False

            return False  # EOF without #CHROM

    except (UnicodeDecodeError, OSError):
        return False


def unzipvcf(vcf_filepath: Path, tmp_dir: str) -> Path:
    unzipped_file = Path(tmp_dir) / vcf_filepath.with_suffix("").name

    if is_gzipped(filepath=vcf_filepath):
        with open(unzipped_file, "wb") as out:
            subprocess.run(["gunzip", "-c", vcf_filepath], stdout=out, check=True)
    elif is_text_vcf(filepath=vcf_filepath):
        shutil.copy(src=vcf_filepath, dst=unzipped_file)

    return unzipped_file


def filter_vcf(ref_fasta: Path, infile: Path) -> Path:
    filtered_vcf = infile.with_name(infile.stem + "_PASS.vcf")
    print("Filtering PASS variants...", flush=True)

    cmd = [
        "gatk",
        "SelectVariants",
        "-R", str(ref_fasta),
        "-V", str(infile),
        "--exclude-filtered",
        "-O", str(filtered_vcf)
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except FileNotFoundError:
        print("GATK executable not found in PATH", flush=True)
    except PermissionError:
        print("Permission denied on input/output files", flush=True)
    except subprocess.CalledProcessError as e:
        print("GATK failed with exit code:", e.returncode, flush=True)
        print("STDOUT:\n", e.stdout, flush=True)
        print("STDERR:\n", e.stderr, flush=True)
        raise

    print(f"Filtered VCF written to: {str(filtered_vcf)}", flush=True)
    return filtered_vcf


def get_tumor_id_from_filename(vcf_path: Path) -> str:
    suffix = ".purple.somatic.vcf.gz"
    if not vcf_path.name.endswith(suffix):
        raise ValueError(
            f"Unexpected filename: {vcf_path.name}\n"
            f"VCF files must end with {suffix}"
        )

    tumor_id = vcf_path.name.removesuffix(suffix)
    if not tumor_id:
        raise ValueError(
            f"Could not determine tumor sample ID from filename: {vcf_path.name}\n"
            f"VCF files should be named as <tumor_sample_id>{suffix}, where "
            f"the tumor sample ID matches one of the VCF sample columns."
        )

    return tumor_id


def get_sample_ids_from_vcf(infile: Path, tumor_id: str):
    """
    Extract normal and tumor sample IDs from a VCF file.

    Parameters
    ----------
    infile : Path
        Path to the VCF file (plain text, already unzipped).
    tumor_id : str
        Tumor sample ID derived from the original VCF filename.
        Expected to match one of the two VCF sample columns.

    Returns
    -------
    normal_id : str
        Normal sample ID (the sample column that's not the tumor ID; fallback: second-to-last column)
    tumor_id : str
        Tumor sample ID (the sample column that matches the input tumor_id; fallback: last column)
    """
    # Open file and read line by line
    with open(infile, "rt", encoding="utf-8", errors="strict") as f:
        for line in f:
            if line.startswith("#CHROM"):
                # Split header into columns
                columns = line.strip().split("\t")
                ncols_vcf = len(columns)

                if ncols_vcf != 11:
                    print(f"WARNING: Unexpected number of columns in VCF: {ncols_vcf}", flush=True)
                    raise ValueError(f"Wrong number of columns in VCF file: {infile}")

                # Extract sample IDs
                sample_ids = columns[-2:]
                if tumor_id not in sample_ids:
                    normal_id = sample_ids[0]  # second-to-last column
                    tumor_id = sample_ids[1]   # last column
                    print(
                        f"WARNING: Tumor sample ID from filename was not found in VCF sample columns. "
                        f"Falling back to the original column-order assumption: among the final two "
                        f"VCF sample columns, the second-to-last column is normal ({normal_id}) and "
                        f"the last column is tumor ({tumor_id}). VCF sample columns: {', '.join(sample_ids)}",
                        flush=True,
                    )
                    return normal_id, tumor_id

                normal_candidates = [sample_id for sample_id in sample_ids if sample_id != tumor_id]
                if len(normal_candidates) != 1:
                    raise ValueError(
                        f"Could not determine normal sample ID from VCF sample columns: "
                        f"{', '.join(sample_ids)}\n"
                        f"Expected exactly two VCF sample columns: one matching the tumour sample ID "
                        f"from the filename ({tumor_id}) and one normal sample column. Please check "
                        f"whether the VCF has duplicate sample IDs or more than two sample columns."
                    )

                normal_id = normal_candidates[0]

                print(f"Found normal sample: {normal_id}", flush=True)
                print(f"Found tumor sample: {tumor_id}", flush=True)

                return normal_id, tumor_id

    # If we reach here, #CHROM header was not found
    raise ValueError(f"No #CHROM header line found in {infile}")


def determine_vep_forks(mem_per_fork_gb: int = 18, system_reserve_gb: int = 2, cpu_reserve: int =1) -> str:
    # --- CPUs ---
    total_cpus = os.cpu_count()
    slurm_cpus = os.getenv("SLURM_CPUS_PER_TASK")
    if slurm_cpus:
        total_cpus = int(slurm_cpus)

    max_cpu_forks = max(total_cpus - cpu_reserve, 1)

    # --- Memory ---
    total_mem_gb = psutil.virtual_memory().total / (1024 ** 3)
    slurm_mem_node = os.getenv("SLURM_MEM_PER_NODE")
    if slurm_mem_node:
        total_mem_gb = int(slurm_mem_node) / 1024

    usable_mem = max(total_mem_gb - system_reserve_gb, 0)
    max_mem_forks = math.floor(usable_mem / mem_per_fork_gb)

    forks = min(max_cpu_forks, max_mem_forks)
    forks = max(forks, 1)

    return str(forks)

def run_vcf_2_maf_perl(ref_fasta: Path, vep_dir: Path, filtered_vcf: Path, og_vcf_path: Path,
                       normal_id, tumour_id, tmp_dir: str):
    # tmp_out_file = filtered_vcf.with_name(filtered_vcf.stem + ".maf")
    tmp_out_file = og_vcf_path.with_name(og_vcf_path.stem + "_pre_filter.maf")
    outfile = og_vcf_path.with_name(og_vcf_path.stem + ".maf")

    # Paths inside container
    vcf2maf_pl = Path("/opt/vcf2maf/vcf2maf.pl")
    vep_path = Path("/opt/vep/src/ensembl-vep/")
    custom_enst = Path("/opt/vcf2maf/data/isoform_overrides_uniprot")
    my_filter_vcf = vep_dir / "af-only-gnomad.hg38.vcf.gz"
    vep_data = vep_dir
    tmp_path = Path(tmp_dir)

    cmd_vcf2maf = [
        "perl", str(vcf2maf_pl),
        "--ncbi-build", "GRCh38",
        "--cache-version", "104",
        "--vep-data", str(vep_data),
        "--ref-fasta", str(ref_fasta),
        "--filter-vcf", str(my_filter_vcf),
        "--vep-path", str(vep_path),
        "--vep-forks", determine_vep_forks(),
        "--input-vcf", str(filtered_vcf),
        "--output-maf", str(tmp_out_file),
        "--vcf-tumor-id", tumour_id,
        "--tumor-id", tumour_id,
        "--vcf-normal-id", normal_id,
        "--normal-id", normal_id,
        "--tmp-dir", str(tmp_path),
        "--custom-enst", str(custom_enst)
    ]

    # Run vcf2maf.pl
    subprocess.run(cmd_vcf2maf, check=True)

    # filterMaf.pl step: cat outfile | filterMaf.pl > tmp.maf
    filter_maf_path = "/opt/cbioportalize/src/filterMaf.pl"
    tmp_maf = tmp_path / "tmp.maf"

    with open(tmp_maf, "w") as out_f, open(tmp_out_file, "r") as in_f:
        subprocess.run(
            ["perl", f"{filter_maf_path}"],
            stdin=in_f,
            stdout=out_f,
            check=True
        )

    # Replace original outfile with filtered MAF
    shutil.move(str(tmp_maf), str(outfile))

    # Print line count
    with open(outfile, "r") as f:
        n_lines = sum(1 for _ in f)
        print(f"Line count = {str(n_lines)}")

    return outfile


def process_vcf(ref_dir_dict: dict, vcf_path: Path, tmp_dir: str) -> Path:

    suffix = ".purple.somatic.vcf.gz"
    if not vcf_path.name.endswith(suffix):
        raise ValueError(
            f"Unexpected filename: {vcf_path.name}\n"
            f"VCF files must end with {suffix}"
        )

    ref_fasta = ref_dir_dict["genome"] / CONFIG["genome_fasta_file"]

    #Steps
    unzipped_vcf = unzipvcf(vcf_filepath=vcf_path, tmp_dir=tmp_dir)

    filtered_vcf = filter_vcf(ref_fasta=ref_fasta, infile=unzipped_vcf)

    tumor_id = get_tumor_id_from_filename(vcf_path=vcf_path)
    normal_id, tumor_id = get_sample_ids_from_vcf(infile=filtered_vcf, tumor_id=tumor_id)

    out_maf_file = run_vcf_2_maf_perl(ref_fasta=ref_fasta, vep_dir=ref_dir_dict["vep"], filtered_vcf=filtered_vcf,
                                      og_vcf_path=vcf_path, normal_id=normal_id, tumour_id=tumor_id, tmp_dir=tmp_dir)

    print(f"vcf2maf conversion complete: {str(out_maf_file)}", flush=True)

    return out_maf_file
