#!/bin/bash

# finds all maf and seg files in current directory and subdirectories
# converts these maf and seg files into a minimal cbio release

#usage: bash make_cbio_release <release_id>
# E.g.: bash make_cbio_release test_oncoanalyzer

set -e
set -o pipefail

[[ $# != 1 ]] && echo "provide release id." && exit 1

###MAF files
# assuming all maf files have same columns in their headers
no_header_lines=2

find "in_data/" -name "*.maf" > maf_files.lst
echo "processing $(cat maf_files.lst | wc -l) MAF files..."


head -n $no_header_lines $(head -1 maf_files.lst) > data_mutation.maf
while read maffile; do
    tail -n +$(echo " $no_header_lines + 1" | bc) $maffile >> data_mutation.maf
done < maf_files.lst

echo "Done merging maf files."
wc -l data_mutation.maf

#meta file for maf
sed "s/STABLE_ID_PLACEHOLDER/$1/g" templates/meta_mutation_template.txt > meta_mutation.txt


###SEG
find "in_data/" -name "*.seg"  > seg_files.lst
no_header_lines=1
echo "processing $(cat seg_files.lst | wc -l) SEG files..."

#head -n $no_header_lines $(head -1 seg_files.lst) > data_seg.seg
printf "ID\tchrom\tloc.start\tloc.end\tnum.mark\tseg.mean\n" > data_seg.seg

while read segfile; do
    tail -n +$(echo " $no_header_lines + 1" | bc) $segfile >> data_seg.seg
done < seg_files.lst

echo "Done merging seg files."
wc -l data_seg.seg

#meta
sed "s/STABLE_ID_PLACEHOLDER/$1/g" templates/meta_seg_template.txt > meta_seg.txt

### clinical data
# clinical_patient
# Note: for now just parsing patients from seg file sample id column

cp templates/data_clinical_patient_template.txt data_clinical_patient.txt
while IFS=$'\t' read -r patient sample; do
    printf '%s\t%s\t%s\t%s\t%s\n' "1" "female" "40" "0:LIVING" "$patient" >> data_clinical_patient.txt
done < in_data/clinical/patients_samples.tsv

# keep only unique rows
awk '!seen[$0]++' data_clinical_patient.txt > tmp && mv tmp data_clinical_patient.txt
wc -l data_clinical_patient.txt



sed "s/STABLE_ID_PLACEHOLDER/$1/g" templates/meta_clinical_patient_template.txt > meta_clinical_patient.txt
wc -l meta_clinical_patient.txt

# clinical_sample
# note: for now just parsins samples from maf file

cp templates/data_clinical_sample_template.txt data_clinical_sample.txt


sampletype="Primary"
while IFS=$'\t' read -r patient sample; do
    printf '%s\t%s\n' "$sample" "$patient" >> data_clinical_sample.txt
done < in_data/clinical/patients_samples.tsv
wc -l data_clinical_sample.txt

sed "s/STABLE_ID_PLACEHOLDER/$1/g" templates/meta_clinical_sample_template.txt > meta_clinical_sample.txt
#meta_study.txt
sed "s/STABLE_ID_PLACEHOLDER/$1/g"  templates/meta_study_template.txt > meta_study.txt
wc -l meta_study.txt

# cancer type
cp -v templates/cancer_type_template.txt cancer_type.txt
cp -v templates/meta_cancer_type_template.txt meta_cancer_type.txt


#case lists
mkdir -p case_lists
sed "s/STABLE_ID_PLACEHOLDER/$1/g" templates/cases_sequenced_template.txt > case_lists/cases_sequenced.txt
truncate -s -1 case_lists/cases_sequenced.txt
awk '{print $NF}' in_data/clinical/patients_samples.tsv | tail -n +2 |  tr "\n" "\t" >> case_lists/cases_sequenced.txt
truncate -s -1 case_lists/cases_sequenced.txt

echo "Done!"
rm *.lst

