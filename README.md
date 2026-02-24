# ITCC VCF2MAF

**Converts the output of the [Oncoanalyser](https://nf-co.re/oncoanalyser/2.3.0/) pipeline into file formats ready for the ITCC cBioPortal instance**

---

## Requirements

## Minimum Requirements

- **CPUs:** 16
- **Memory:** 32 GB RAM
- **Disk:** 100 GB+ free space

Tested on a high performance cluster using slurm scheduler, with these requirements and Singularity/3.11.3.
Compute node requires internet access to download the reference data on first use.
---

## Usage

```
singularity exec \
-B /your/path/to/reference/dir:/resources \
/path/to/your/singularity/image/cache/itcc_vcf2maf.sif \
python /opt/itcc_vcf2maf/pedcan_vcf2maf.py -h

usage: pedcan_vcf2maf.py [-h] [-d DATA_DIR] -r RELEASE_ID -p PAT_SAM [-t TEMP_SPACE] [--dry-run]

ITCC VCF to MAF converter.

options:
  -h, --help            show this help message and exit
  -d DATA_DIR, --dir DATA_DIR
                        The directory to search for vcf and tsv files.
  -r RELEASE_ID, --release_id RELEASE_ID
                        The release id to annotate cbioportal output with.
  -p PAT_SAM, --pat_sam PAT_SAM
                        A TSV file with two columns, patient_id and sample_id.
  -t TEMP_SPACE, --temp TEMP_SPACE
                        The temp space to use.
```
### Singularity options
Given here as `/your/path/to/reference/dir`, this will be used to store the reference files required by the pipeline for the run, and future runs if given a non-temporary directory.

### pedcan_vcf2maf.py options
1. The `-t` option allows a user specified temporary directory to be given to allow clean up
2. The `-d` option provides the directory that you wanted scanned and process for files matching `.purple.cnv.somatic.tsv` or  `.sage.somatic.vcf.gz`.
2. The `-r` option requests a user specified release id for running the pipeline.
3. The `-p` option is for the user to provide a TSV file that contains two columns of data with a header line.

| patient_id | sample_id |
|------------|-----------|
| patient 1  | sample 1  |
| patient 2  | sample 2  |

---

## Example Command

```
singularity exec -e -B /your/path/to/reference/dir:/resources \
/path/to/your/singularity/image/cache/itcc_vcf2maf.sif \
python /opt/itcc_vcf2maf/pedcan_vcf2maf.py \
-d /your/path/to/data/dir \
-p /your/path/to/pat_sam.tsv \
-r testing_OA
```

---

## Contact

```
Contact:
- Scott Davidson <scott.davidson@sickkids.ca>
```