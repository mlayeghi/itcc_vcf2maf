#!/usr/bin/env python3

import argparse
import os
import sys
import tempfile

from config_loader import load_config
from scripts import common

repo_dir = os.path.dirname(os.path.realpath(__file__))
CONFIG = load_config(path=os.path.join(repo_dir, "config.json"))

print(CONFIG.keys())

def _get_arguments() -> tuple:
    parser = argparse.ArgumentParser(description='ITCC VCF to MAF converter.')
    parser.add_argument('-d', '--dir', dest="data_dir",
                        help='The directory to search for vcf and tsv files.',
                        default=os.getcwd(),
                        type=str)
    parser.add_argument('-r', '--ref_dir', dest="ref_dir",
                        help="The directory to use or store reference data.",
                        required=True,
                        type=str)
    parser.add_argument('-t', '--temp', dest="temp_space",
                        help="The temp space to use.",
                        required=False,
                        type=str)
    parser.add_argument('--dry-run', dest="dry_run", action='store_true',
                        help="Do not create files.")
    args = parser.parse_args()

    try:
        data_dir = common.ensure_directory(path_str=args.data_dir)
        ref_dir = common.ensure_directory(path_str=args.ref_dir)
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
        print(f"Reference directory ready: {ref_dir}")

    return data_dir, ref_dir, temp_space


def main():
    data_dir, ref_dir, temp_space = _get_arguments()

    tmp_dir_args = {}
    if temp_space:
        # Use user-provided temp space
        tmp_dir_args['dir'] = temp_space

    with tempfile.TemporaryDirectory(prefix="itcc_vcf2maf_", **tmp_dir_args) as tmp_dir_name:
        print(f"Created temporary directory: {tmp_dir_name}")
        ref_dir_dict = common.ensure_reference_data(ref_dir=ref_dir, config=CONFIG)
        stop = True
        # short_read.main(this_read1s=args.read1, this_read2s=args.read2, tmp_dir=tmp_dir_name, prefix=args.prefix,
        #                 token=args.token, email=args.email, save=args.save, om=args.om, v2=args.v2)


if __name__ == "__main__":
    main()
    exit(0)