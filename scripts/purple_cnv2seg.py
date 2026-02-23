#!/usr/bin/env python3

import numpy as np
import pandas as pd

from pathlib import Path


def process_purple(tsv_file: Path) -> Path:
    # Derive output path and sample name
    suffix = ".purple.cnv.somatic.tsv"
    if not tsv_file.name.endswith(suffix):
        raise ValueError(f"Unexpected filename: {tsv_file.name}")

    sample = tsv_file.name.removesuffix(suffix)
    output_path = tsv_file.parent / f"{sample}.seg"

    # Load the TSV
    df = pd.read_csv(filepath_or_buffer=tsv_file, sep="\t")

    # Remove the "chr" prefix
    df["Chromosome"] = df.iloc[:, 0].astype(str).str.removeprefix("chr")

    # Extract required columns
    seg = pd.DataFrame({"Sample": sample, "Chromosome": df["Chromosome"], "Start": df.iloc[:, 1],
                        "End": df.iloc[:, 2], "Num_Probes": df.iloc[:, 10], })

    # Compute log2(copy_number/2) with zero-handling
    copy_number = df.iloc[:, 3].astype(float)
    # Treat negative CN as zero
    copy_number = copy_number.clip(lower=0)
    # Default value for CN == 0
    seg["Segment_Mean"] = -10.0
    # Compute log2 only for positive CN
    mask = copy_number > 0
    seg.loc[mask, "Segment_Mean"] = np.log2(copy_number[mask] / 2)

    # Write the SEG file
    seg.to_csv(output_path, sep="\t", index=False)
    print(f"Written SEG file to {output_path}", flush=True)

    return output_path