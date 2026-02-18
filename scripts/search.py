#!/usr/bin/env python3

import os

from pathlib import Path

from scripts import purple_cnv2seg
from scripts import vcf2maf


def searcher(search_dir: Path, tmp_dir: str) -> tuple:
    maf_files = []
    seg_files = []
    for root, dirs, files in os.walk(search_dir, topdown=True,followlinks=False):
        root_path = Path(root).expanduser().resolve()
        for file in files:
            if not file.endswith((".purple.cnv.somatic.tsv", ".sage.somatic.vcf.gz")):
                continue
            # So we have one of two required types
            file_path = root_path / file
            if file.endswith(".purple.cnv.somatic.tsv"):
                this_seq_file = purple_cnv2seg.process_purple(tsv_file=file_path)
                seg_files.append(this_seq_file)

            if file.endswith(".sage.somatic.vcf.gz"):
                this_maf_file = vcf2maf.process_sage(vcf_path=file_path, tmp_dir=tmp_dir)
                maf_files.append(this_maf_file)

    return maf_files, seg_files
