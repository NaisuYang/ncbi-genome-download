# NCBI基因组下载及更新

将NCBI真核基因组按照下面的分类进行下载

```shell
#2025-05-06 数量
fungi -ref 5055 -all 21435
viridiplantae -ref 2500 -all 6523
eukaryota-others -ref 792
metazoa-arthropoda -ref 4270 -all 7888
metazoa-chordata-aves -ref 1491 -all 2243
metazoa-chordata-others -ref 656
metazoa-chordata-actinopteri -ref 1733 -all 2922
metazoa-chordata-mammalia -ref 854 -all 4398
metazoa-others -ref 1280

#更新日志
fungi
Original: 13673
Deprecated: 1452
Updates: 9213
Now：21434

viridiplantae
Original: 1307
Deprecated: 469
Updates: 1662
Now：2500

metazoa-chordata-mammalia
Original: 803
Deprecated: 413
Updates: 464
Now：854

metazoa-arthropoda
Original: 2291
Deprecated: 626
Updates: 2603
Now：4268

metazoa-chordata-actinopteri
Original: 1003
Deprecated: 223
Updates: 953
Now：1733

metazoa-chordata-aves
Original: 798
Deprecated: 352
Updates: 1045
Now：1491
```

## 1. NCBI基因组下载

下载主要通过NCBI提供的命令行工具完成

### 获取name2id

```shell
#下载基因组信息
datasets summary genome taxon 'fungi' --reference --as-json-lines > fungi.json

#提取name2id
cat fungi.json | dataformat tsv genome --fields assminfo-paired-assm-accession,current-accession,organism-name | sed -e 's/^[[:space:]]*//' -e 's/GCF_[^[:space:]]*[[:space:]]*//g' | awk 'BEGIN {FS=OFS="\t"} NR==1 {print "Name\tGCA"; next} ($1 ~ /^GCA/) {gsub("\.", "_", $1);gsub(" ", "_", $2); print $2 "\t" $1}' > name2id.txt
```

### 提取GCA accession

```shell
awk -F'\t' 'NR > 1 {split($2, a, "_"); print a[1]"_"a[2]"."a[3]}' name2id.txt > gca_accession.txt
```

### 下载基因组

```shell
#获取基因组地址和MD5值
datasets download genome accession --inputfile gca_accession.txt --dehydrated --filename ncbi.zip
#解压到ncbi目录
unzip -d ncbi ncbi.zip
#下载基因组存放在data目录，不需要再建子目录
sed -i 's/data\/GCA_[^/]*\//data\//g' ncbi/ncbi_dataset/fetch.txt
#下载基因组
datasets rehydrate --gzip --directory ncbi
```

## 2. 基因组更新

### 获取目前基因组的文件的MD5值

```shell
#为了方便管理，所有的基因组文件都存放在分类目录下的GCA文件夹
cd GCA
md5sum *.fna > ../GCA.md5
```

### 获取最新基因组数据

```shell
datasets summary genome taxon 'fungi' --reference --as-json-lines | dataformat tsv genome --fields assminfo-paired-assm-accession,current-accession,organism-name | sed -e 's/^[[:space:]]*//' -e 's/GCF_[^[:space:]]*[[:space:]]*//g' | awk 'BEGIN {FS=OFS="\t"} NR==1 {print "Name\tGCA"; next} ($1 ~ /^GCA/) {gsub("\.", "_", $1);gsub(" ", "_", $2); print $2 "\t" $1}' > name2id.txt
awk -F'\t' 'NR > 1 {print $2}' name2id.txt > gca_accession.txt
datasets download genome accession --inputfile gca_accession.txt --dehydrated --filename ncbi.zip
unzip -d ncbi ncbi.zip
```

### 计算需要更新的基因组

```shell
python3 mobilome_check_genome_updates.py --gca_md5 GCA.md5 --ncbi_md5 ncbi/md5sum.txt --fetch_file ncbi/ncbi_dataset/fetch.txt
```

### 下载基因组

```shell
mv ncbi/ncbi_dataset/fetch.txt ncbi/ncbi_dataset/fetch.backup.txt
mv ncbi/ncbi_dataset/fetch.filters.txt  ncbi/ncbi_dataset/fetch.txt
sed -i 's/data\/GCA_[^/]*\//data\//g' ncbi/ncbi_dataset/fetch.txt
datasets rehydrate --gzip --directory ncbi
#批量解压
find ncbi/ncbi_dataset/data/ -name "*.gz" | xargs -I {} echo gunzip {} | parallel -j 10
#将下载好的基因组移动到GCA-updates
mkdir GCA-updates
mv ncbi/ncbi_dataset/data/*.fna GCA-updates/
ls GCA-updates/* | awk -F'[_.]' '{print "mv "$0" "$1"_"$2"_"$3".fna"}' > rename.sh
#检查名称是否都正确
column -t rename.sh  | less -S
bash rename.sh
```

### 下载失败处理

```shell
#解压数据后，解压失败的重新下载
ls ncbi/ncbi_dataset/data/*.gz | cut -d "/" -f4 | cut -d "." -f1 | grep -f /dev/stdin ncbi/ncbi_dataset/fetch.txt > ncbi/ncbi_dataset/tmp.txt
mv ncbi/ncbi_dataset/tmp.txt ncbi/ncbi_dataset/fetch.txt
rm ncbi/ncbi_dataset/data/*.gz
datasets rehydrate --gzip --directory ncbi
ls ncbi/ncbi_dataset/data/*.gz | xargs -I {} echo gunzip {} | parallel -j 10
mv ncbi/ncbi_dataset/data/*.fna GCA-updates/
ls GCA-updates/* | awk -F'[_.]' '{print "mv "$0" "$1"_"$2"_"$3".fna"}' > rename.sh
column -t rename.sh  | less -S
bash rename.sh
#获取未下载的基因组信息
ls GCA-updates/ | cut -d "/" -f4 | cut -d "_" -f1,2 | grep -vf /dev/stdin ncbi/ncbi_dataset/fetch.txt > ncbi/ncbi_dataset/tmp.txt
mv ncbi/ncbi_dataset/tmp.txt ncbi/ncbi_dataset/fetch.txt
datasets rehydrate --gzip --directory ncbi
```

### 删除过时的基因组

```shell
#创建存放过时的基因组文件夹
mkdir deprecated
#将fna文件移动到deprecated文件夹
awk '{print $2}' GCA.deprecated.md5 | xargs -I {} mv {} deprecated
awk -F'[ .]' '{print $3"*"}' GCA.deprecated.md5 | xargs -I {} sh -c 'rm -rf {}'
#除了fna文件外，删除所有文件
find GCA -type f ! -name "*.fna" -exec rm -fv {} \;
```

### 下载的基因组进行md5校验

```shell
cd GCA-updates
ls *.fna | xargs -I {} echo "md5sum {} >> ../GCA-updates.md5" | parallel -j 10
#比较md5值是否一致
#新的GCA.md5应该是GCA.exists.md5和ncbi/md5sum.updates.awk.txt合并
awk -F'[ ./_]' '{print $1"  "$6"_"$7"_"$8".fna"}' ncbi/md5sum.updates.txt > ncbi/md5sum.updates.awk.txt

cat GCA.exists.md5 ncbi/md5sum.updates.awk.txt | sort | uniq > GCA.md5

#实际校验的md5值应该为GCA.exists.md5和GCA-updates.md5合并
cat GCA.exists.md5 GCA-updates.md5 | sort | uniq > GCA.check.md5

#判断GCA.md5和GCA.check.md5内容是否一致
diff GCA.md5 GCA.check.md5
```

### 格式化基因组

```shell
#获取所有fna文件路径
find /home/bpool/storage/eukaryotes_genome/fungi/GCA -type f -name "*.fna" > GCA.list

#更新基因组获取GCA-updates
find /home/bpool/storage/eukaryotes_genome/fungi/GCA-updates -type f -name "*.fna" > GCA-updates.list

#批量格式化基因组
sbatch makeblastdb.slurm

#将格式化好的基因组转移到GCA完成基因组更新
mv GCA-updates/* GCA/
```

### makeblastdb.slurm

```shell
#!/bin/bash
#SBATCH --job-name=makeblastdb
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=5
#SBATCH --output=slurm-%A_%a.out
#SBATCH --array=1-21434%10000

CATEGORYDIR="/home/bpool/storage/eukaryotes_genome/fungi"
LOGDIR="$CATEGORYDIR/logs"
GENOME_DIR="$CATEGORYDIR/GCA"
mapfile -t GENOME_LIST < $CATEGORYDIR/GCA.list

# 获取任务ID
TASK_ID=$SLURM_ARRAY_TASK_ID
GENOME_FILE=${GENOME_LIST[$TASK_ID - 1]}

#检查文件是否存在
if [ ! -f "$GENOME_FILE" ]; then
   echo "Error: Genome file $GENOME_FILE not found"
   exit 1
fi

cd $GENOME_DIR
makeblastdb -in $(basename "$GENOME_FILE") -input_type fasta -title $(basename "$GENOME_FILE" .fna) -dbtype nucl -out $(basename "$GENOME_FILE" .fna) -logfile $LOGDIR/$(basename "$GENOME_FILE" .fna).makeblastdb.log
echo makeblastdb -in $(basename "$GENOME_FILE") -input_type fasta -title $(basename "$GENOME_FILE" .fna) -dbtype nucl -out $(basename "$GENOME_FILE" .fna) -logfile $LOGDIR/$(basename "$GENOME_FILE" .fna).makeblastdb.log  done! >> $LOGDIR/$(basename "$GENOME_FILE" .fna).makeblastdb.log
seqkit fx2tab -l -n -i $(basename "$GENOME_FILE") > $(basename "$GENOME_FILE").len
echo "seqkit fx2tab -l -n -i $(basename "$GENOME_FILE") > $(basename "$GENOME_FILE").len done!" >> $LOGDIR/$(basename "$GENOME_FILE" .fna).makeblastdb.log
samtools faidx $(basename "$GENOME_FILE")
echo "samtools faidx $(basename "$GENOME_FILE") done!" >> $LOGDIR/$(basename "$GENOME_FILE" .fna).makeblastdb.log
```

## 3. Others基因组下载

```shell
#eukaryota-others
cat fungi.gca_accession.txt metazoa.gca_accession.txt viridiplantae.gca_accession.txt > exclude.gca_accession.txt
awk 'NR==FNR{a[$0]; next} !($0 in a)' exclude.gca_accession.txt  eukaryota.gca_accession.txt > eukaryota-others.gca_accession.txt

#metazoa-others
cat arthropoda.gca_accession.txt chordata.gca_accession.txt > exclude.gca_accession.txt
awk 'NR==FNR{a[$0]; next} !($0 in a)' exclude.gca_accession.txt  metazoa.gca_accession.txt > metazoa-others.gca_accession.txt

#metazoa-chordata-others
cat actinopteri.gca_accession.txt aves.gca_accession.txt mammalia.gca_accession.txt > exclude.gca_accession.txt
awk 'NR==FNR{a[$0]; next} !($0 in a)' exclude.gca_accession.txt chordata.gca_accession.txt > chordata-others.gca_accession.txt
```

