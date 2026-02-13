#!/usr/bin/env python3

import os
import requests
import shutil
import subprocess
import tarfile

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


def ensure_reference_data(ref_dir: str, config: dict) -> dict:
    """
    Ensure reference genome and VEP cache exist inside ref_dir.

    Returns:
        dict with paths: {"genome": Path, "vep": Path}
    """

    base = Path(ref_dir).expanduser().resolve()
    genome_dir = base / "genome"

    # Ensure base exists
    base.mkdir(parents=True, exist_ok=True)

    if not os.access(base, os.W_OK | os.X_OK):
        raise PermissionError(f"ref_dir not writable: {base}")

    # ---- Genome ----
    genome_url = config["genome_url"]

    genome_dir.mkdir(parents=True, exist_ok=True)
    genome_fasta = genome_dir / config["genome_file"]

    if genome_fasta.exists():
        print("Reference genome found. Reusing.")
    else:
        print("Reference genome missing. Downloading...")
        download_if_needed(genome_url, genome_fasta)
        subprocess.run(["samtools", "faidx", str(genome_fasta)], check=True)
        print("Reference genome setup complete.")

    # ---- VEP ----
    vep_dir = base / "vep"
    vep_cache_url = config["vep_cache_url"]
    vep_tar = vep_dir / config["vep_cache_tarfile"]
    vep_sentinel = vep_dir / ".vep_complete"

    if vep_sentinel.exists():
        print("VEP cache found. Reusing.")
    else:
        print("VEP cache missing. Downloading...")
        download_if_needed(vep_cache_url, vep_tar)
        with tarfile.open(vep_tar, "r:gz") as tar:
            tar.extractall(path=vep_dir)

        print(f"VEP cache installed at {vep_dir}")

        vep_sentinel.touch()
        print("VEP cache setup complete.")

    return {
        "genome": genome_dir,
        "vep": vep_dir
    }


def download_if_needed(url: str, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)

    headers = {}
    if dest.exists():
        # Use If-Modified-Since header
        headers["If-Modified-Since"] = \
            requests.utils.formatdate(dest.stat().st_mtime, usegmt=True)

    response = requests.get(url, headers=headers, stream=True)

    if response.status_code == 304:
        print("File is up to date.")
        return

    response.raise_for_status()

    tmp_file = dest.with_suffix(".tmp")

    with tmp_file.open("wb") as f:
        shutil.copyfileobj(response.raw, f)

    tmp_file.replace(dest)
    print(f"Downloaded: {dest}")
