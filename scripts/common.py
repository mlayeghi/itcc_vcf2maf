#!/usr/bin/env python3

import os
import requests
import shutil
import subprocess
import tarfile
import time

from pathlib import Path
import urllib.request


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


def ensure_reference_data(config: dict) -> dict:
    """
    Ensure reference genome and VEP cache exist inside ref_dir.
    Base directory within the container will be called /resources.

    Returns:
        dict with paths: {"genome": Path, "vep": Path}
    """

    base = Path("/resources").expanduser().resolve()
    genome_dir = base / "genome"

    # Ensure base exists
    base.mkdir(parents=True, exist_ok=True)
    if not os.path.isdir(base):
        raise NotADirectoryError(f"resource directory does not exist: {base}")
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
    """
    Download a file from HTTP, HTTPS, or FTP if it doesn't exist locally.
    Overwrites if the remote file is newer than local copy.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Check if file exists and compare last-modified time
    if dest.exists():
        try:
            req = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(req) as response:
                remote_mtime = response.headers.get("Last-Modified")
                if remote_mtime:
                    # Convert remote Last-Modified to timestamp
                    remote_ts = time.mktime(
                        time.strptime(remote_mtime, "%a, %d %b %Y %H:%M:%S %Z")
                    )
                    local_ts = dest.stat().st_mtime
                    if local_ts >= remote_ts:
                        print("File is up to date.")
                        return
        except Exception:
            # Some FTP servers don’t provide HEAD or Last-Modified
            pass

    tmp_file = dest.with_suffix(".tmp")
    print(f"Downloading: {url} -> {dest}")

    # Download
    with urllib.request.urlopen(url) as response, tmp_file.open("wb") as out_file:
        shutil.copyfileobj(response, out_file)

    tmp_file.replace(dest)
    print(f"Downloaded: {dest}")
