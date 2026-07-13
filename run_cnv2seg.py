#!/usr/bin/env python3

import argparse
import os
import tempfile

from config_loader import load_config
from pathlib import Path
from scripts import common, search, cbio_release

repo_dir = os.path.dirname(os.path.realpath(__file__))
repo_path = Path(repo_dir)
CONFIG = load_config(path=os.path.join(repo_dir, "config.json"))


def _get_arguments() -> tuple:
    parser = argparse.ArgumentParser(description='ITCC VCF2MAF converter.')
    parser.add_argument('-d', '--dir', dest="data_dir",
                        help='The directory to search for vcf and tsv files. '
                             'MAF and SEG files will be written beside appropriate files.',
                        default=os.getcwd(),
                        type=str)
    parser.add_argument('-t', '--temp', dest="temp_space",
                        help="The temp space to use.",
                        required=False,
                        type=str)
    parser.add_argument('-o', '--out_dir', dest="out_dir",
                        help='The directory to write output files to.',
                        default=os.getcwd(),
                        type=str)
    args = parser.parse_args()

    try:
        data_dir = common.ensure_directory(path_str=args.data_dir)
        out_dir = common.ensure_directory(path_str=args.out_dir)
        # Use user-provided temp space if given, else None
        if args.temp_space:
            temp_space = common.ensure_directory(path_str=args.temp_space)
        else:
            temp_space = None
    except ValueError as e:
        print(f"Invalid input: {e}")
        exit(1)
    except FileNotFoundError as e:
        print(f"Parent directory missing: {e}")
        exit(1)
    except PermissionError as e:
        print(f"Permission denied: {e}")
        exit(1)
    except NotADirectoryError as e:
        print(f"Path conflict: {e}")
        exit(1)
    except OSError as e:
        print(f"OS error: {e}")
        exit(1)
    else:
        print(f"Data directory ready: {data_dir}")

    return data_dir, temp_space, out_dir


def main():
    data_dir, tmp_dir, out_dir = _get_arguments()

    output_dir=Path(out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    tmp_dir_args = {}
    if tmp_dir:
        # Use user-provided temp space
        tmp_dir_args['dir'] = tmp_dir

    with tempfile.TemporaryDirectory(prefix="itcc_vcf2maf_", **tmp_dir_args) as tmp_dir_name:
        print(f"Created temporary directory: {tmp_dir_name}")
        ref_dir_dict = common.ensure_reference_data(config=CONFIG)
        maf_files, seg_files = search.searcher(ref_dir_dict=ref_dir_dict, search_dir=data_dir, tmp_dir=tmp_dir_name, out_type='seg')

        print(f"Processing {len(seg_files)} SEG files...")
        cbio_release._merge_seg(seg_files, output_dir / "data_seg.seg")


if __name__ == "__main__":
    main()
    print("Done!")
    exit(0)