#!/usr/bin/env python3

import os
import requests
import shutil
import subprocess
import sys
import tarfile

from email.utils import formatdate
from pathlib import Path


def ensure_directory(path_str: str) -> Path:
    """
    Create a directory if it does not exist.
    Verifies parent write permissions before creation.

    Returns:
        Path object of the directory.

    Raises:
        ValueError: If path string is invalid.
        PermissionError: If insufficient permissions.
        NotADirectoryError: If path exists and is not a directory.
        OSError: For other OS-related errors.
    """

    if not path_str or not path_str.strip():
        raise ValueError(f"Path must be a non-empty string.  Given {path_str}")

    path = Path(path_str).expanduser().resolve()

    # If path already exists
    if path.exists():
        if path.is_dir():
            return path
        else:
            raise NotADirectoryError(f"{path} exists and is not a directory.")

    parent = path.parent

    # Ensure parent exists
    if not parent.exists():
        raise FileNotFoundError(f"Parent directory does not exist: {parent}")

    # Check write and execute permissions on parent
    if not os.access(parent, os.W_OK | os.X_OK):
        raise PermissionError(f"No permission to create directory in: {parent}")

    # Attempt creation (still must handle race conditions)
    try:
        path.mkdir(parents=False, exist_ok=False)
    except Exception as e:
        raise OSError(f"Failed to create directory '{path}': {e}")

    return path


def ensure_gatk_reference(ref_fasta: Path):
    dict_file = ref_fasta.with_suffix(".dict")
    fai_file = Path(str(ref_fasta) + ".fai")

    if not dict_file.exists():
        subprocess.run(
            ["gatk", "CreateSequenceDictionary",
             "-R", str(ref_fasta),
             "-O", str(dict_file)],
            check=True
        )

    if not fai_file.exists():
        subprocess.run(
            ["samtools", "faidx", str(ref_fasta)],
            check=True
        )


def ensure_reference_data(config: dict) -> dict:
    """
    Ensure reference genome and VEP cache exist inside ref_dir.
    Base directory within the container will be called /resources.

    Returns:
        dict with paths: {"genome": Path, "vep": Path}
    """

    base = Path("/resources").expanduser().resolve()
    if sys.platform == "darwin":
        base = Path("/Users/scottdavidson/Documents/PycharmProjects/itcc_vcf2maf/test_ref_dir").expanduser().resolve()
    genome_dir = base / "genome"

    # Ensure base exists
    base.mkdir(parents=True, exist_ok=True)
    if not os.path.isdir(base):
        raise NotADirectoryError(f"resource directory does not exist: {base}")
    if not os.access(base, os.W_OK | os.X_OK):
        raise PermissionError(f"ref_dir not writable: {base}")

    # ---- Genome ----
    genome_fasta_url = config["genome_fasta_url"]

    genome_dir.mkdir(parents=True, exist_ok=True)
    genome_fasta = genome_dir / config["genome_fasta_file"]

    genome_sentinel = genome_dir / ".genome_complete"

    if genome_sentinel.exists() and genome_fasta.exists():
        print("Reference genome found. Reusing.")
    else:
        print("Reference genome missing. Downloading...")
        download_if_needed(genome_fasta_url, genome_fasta)
        ensure_gatk_reference(ref_fasta=genome_fasta)
        print("Reference genome setup complete.")

    # ---- VEP ----
    vep_dir = base / "vep"
    vep_cache_url = config["vep_cache_url"]
    vep_tar = vep_dir / config["vep_cache_tarfile"]
    vep_gnomad_vcf_url = config["gnomad_vcf"]
    vep_gnomad_vcf_tbi_url = config["gnomad_vcf_tbi"]
    vep_gnomad_vcf = vep_dir / config["gnomad_vcf_file"]
    vep_gnomad_vcf_tbi = vep_dir /config["gnomad_vcf_tbi_file"]
    vep_sentinel = vep_dir / ".vep_complete"

    if vep_sentinel.exists():
        print("VEP cache found. Reusing.")
    else:
        print("VEP cache missing. Downloading...")
        download_if_needed(url=vep_gnomad_vcf_url, dest=vep_gnomad_vcf)
        download_if_needed(url=vep_gnomad_vcf_tbi_url, dest=vep_gnomad_vcf_tbi)
        if download_if_needed(vep_cache_url, vep_tar):
            with tarfile.open(vep_tar, "r:gz") as tar:
                tar.extractall(path=vep_dir)

        print(f"VEP cache installed at {vep_dir}")

        vep_sentinel.touch()
        print("VEP cache setup complete.")

    return {
        "genome": genome_dir,
        "vep": vep_dir
    }




def download_if_needed(url: str, dest: Path) -> bool:
    """
    Download a file from HTTP, HTTPS, or FTP if it doesn't exist locally.
    Overwrites if the remote file is newer than local copy.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)

    headers = {}
    if dest.exists():
        # Use If-Modified-Since header
        headers["If-Modified-Since"] = \
            formatdate(dest.stat().st_mtime, usegmt=True)

    response = requests.get(url, headers=headers, stream=True)

    if response.status_code == 304:
        print("File is up to date.")
        return False

    response.raise_for_status()

    tmp_file = dest.with_suffix(".tmp")
    print(f"Downloading: {url} -> {dest}")

    with tmp_file.open("wb") as f:
        shutil.copyfileobj(response.raw, f)

    tmp_file.replace(dest)
    print(f"Downloaded: {dest}")
    return True
