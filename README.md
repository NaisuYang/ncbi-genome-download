```shell
#获取name2id
datasets summary genome taxon 'mammalia' --reference --as-json-lines | dataformat tsv genome --fields assminfo-paired-assm-accession,current-accession,organism-name | sed -e 's/^[[:space:]]*//' -e 's/GCF_[^[:space:]]*[[:space:]]*//g' | awk 'BEGIN {FS=OFS="\t"} NR==1 {print "Name\tGCA"; next} {gsub(" ", "_", $2); print $2 "\t" $1}' > name2id.txt

#提取GCA accession
awk -F'\t' 'NR > 1 {print $2}' name2id.txt > gca_accession.txt


datasets download genome accession --inputfile gca_accession.txt --dehydrated --filename genome.zip

unzip -d genome genome.zip

# 修改下载路径
sed -i 's/data\/GCA_[^/]*\//data\//g' genome/ncbi_dataset/fetch.txt


datasets rehydrate --gzip --directory ncbi
```

