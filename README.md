# ITCC VCF2MAF

**Converts the output of the [Oncoanalyser](https://nf-co.re/oncoanalyser/2.3.0/) pipeline into file formats ready for the ITCC cBioPortal instance**

---

## Requirements

Provided in container form, so the ability to run Docker, Singularity or Apptainer is required.

### Minimum System Requirements

- **CPUs:** 16
- **Memory:** 32 GB RAM
- **Disk:** 100 GB+ free space
- **Singularity** or **Docker** or **Apptainer**

Tested on a high performance cluster using slurm scheduler, with these requirements and Singularity version 3.11.3.
Compute node requires internet access to download the reference data on first use.

---

## Usage
The container can be pulled from [Dockerhub](https://hub.docker.com/r/shlienteam/itcc_vcf2maf).
```
singularity pull itcc_vcf2maf_1_0_0.sif docker://shlienteam/itcc_vcf2maf:1.0.0
singularity exec \
-B /path/to/mount/whole/filesystem \
-B /your/path/to/reference/dir:/resources \
/path/to/your/singularity/image/cache/itcc_vcf2maf_1_0_0.sif \
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
Given here as `/your/path/to/reference/dir`, this will be used to store the reference files and vep database required by the pipeline for the first run, and future runs if given a non-temporary directory.
```
Contents of your reference directory will look like this:
 .
 |-genome
 |---GRCh38_masked_exclusions_alts_hlas.dict
 |---GRCh38_masked_exclusions_alts_hlas.fasta
 |---GRCh38_masked_exclusions_alts_hlas.fasta.fai
 |-vep
 |---af-only-gnomad.hg38.vcf.gz
 |---af-only-gnomad.hg38.vcf.gz.tbi
 |---homo_sapiens
 |-----104_GRCh38
```
If you don't have access to the internet from the container, you can download and format the resource directory by downloading these files:
```
genome directory
https://pub-cf6ba01919994c3cbd354659947f74d8.r2.dev/genomes/GRCh38_hmf/25.1/GRCh38_masked_exclusions_alts_hlas.fasta

vep directory
https://storage.googleapis.com/gcp-public-data--broad-references/hg38/v0/somatic-hg38/af-only-gnomad.hg38.vcf.gz
https://storage.googleapis.com/gcp-public-data--broad-references/hg38/v0/somatic-hg38/af-only-gnomad.hg38.vcf.gz.tbi
https://ftp.ensembl.org/pub/release-104/variation/vep/homo_sapiens_vep_104_GRCh38.tar.gz

tar -xvf homo_sapiens_vep_104_GRCh38.tar.gz
```

### pedcan_vcf2maf.py options
1. The `-t` option allows a user specified temporary directory to be given to allow clean up
2. The `-d` option provides the directory that you wanted scanned and process for files matching `.purple.cnv.somatic.tsv` or  `.sage.somatic.vcf.gz`.
2. The `-r` option requests a user specified release id for running the pipeline.
3. The `-p` option is for the user to provide a TSV file that contains two columns of data with a header line.

Example patient sample tsv file to give with the `-p` flag.

| patient_id | sample_id |
|------------|-----------|
| patient 1  | sample 1  |
| patient 2  | sample 2  |

---

## Example Command

```
singularity exec -e -B /your/path/to/reference/dir:/resources \
/path/to/your/singularity/image/cache/itcc_vcf2maf_1_0_0.sif \
python /opt/itcc_vcf2maf/pedcan_vcf2maf.py \
-d /your/path/to/data/dir \
-p /your/path/to/pat_sam.tsv \
-r testing_OA
```

---

## Contact

```
Contact:
- Mehdi Layeghifard <mehdi.layeghifard@sickkids.ca>
```