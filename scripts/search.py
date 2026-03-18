#!/usr/bin/env python3

import os

from pathlib import Path

from scripts import purple_cnv2seg, vcf2maf


def searcher(ref_dir_dict: dict, search_dir: Path, tmp_dir: str) -> tuple:
    maf_files = []
    seg_files = []
    for root, dirs, files in os.walk(search_dir, topdown=True,followlinks=False):
        root_path = Path(root).expanduser().resolve()
        for file in files:
            if not file.endswith((".purple.cnv.somatic.tsv", "purple.somatic.vcf.gz")):
                continue
            # So we have one of two required types
            file_path = root_path / file
            if file.endswith(".purple.cnv.somatic.tsv"):
                print(f"About to process purple: {str(search_dir)}")
                this_seq_file = purple_cnv2seg.process_purple(tsv_file=file_path)
                seg_files.append(this_seq_file)

            if file.endswith(".purple.somatic.vcf.gz"):
                print(f"About to process vcf: {str(search_dir)}")
                this_maf_file = vcf2maf.process_vcf(ref_dir_dict=ref_dir_dict, vcf_path=file_path, tmp_dir=tmp_dir)
                maf_files.append(this_maf_file)

    return maf_files, seg_files
