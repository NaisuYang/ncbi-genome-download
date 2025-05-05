# NCBI基因组下载及更新

将NCBI真核基因组按照下面的分类进行下载

```shell
fungi
viridiplantae
eukaryota-others 
metazoa-arthropoda
metazoa-chordata-aves
metazoa-chordata-others
metazoa-chordata-actinopteri
metazoa-chordata-mammalia
metazoa-others    
```

## 1. NCBI基因组下载

下载主要通过NCBI提供的命令行工具完成

### 获取name2id

```shell
datasets summary genome taxon 'fungi' --reference --as-json-lines | dataformat tsv genome --fields assminfo-paired-assm-accession,current-accession,organism-name | sed -e 's/^[[:space:]]*//' -e 's/GCF_[^[:space:]]*[[:space:]]*//g' | awk 'BEGIN {FS=OFS="\t"} NR==1 {print "Name\tGCA"; next} {gsub(" ", "_", $2); print $2 "\t" $1}' > name2id.txt
```

### 提取GCA accession

```shell
awk -F'\t' 'NR > 1 {print $2}' name2id.txt > gca_accession.txt
```

### 下载基因组

```shell
datasets download genome accession --inputfile gca_accession.txt --dehydrated --filename ncbi.zip
unzip -d ncbi ncbi.zip
#下载基因组存放在data目录，不需要再建子目录
sed -i 's/data\/GCA_[^/]*\//data\//g' genome/ncbi_dataset/fetch.txt
datasets rehydrate --gzip --directory ncbi
```

## 2. 基因组更新

### 获取目前基因组的文件的MD5值

```shell
#为了方便管理，所有的基因组文件都存放在分类目录下的GCA文件夹
md5sum GCA/*.fna > GCA.md5
```

### 获取最新基因组数据

```shell
datasets summary genome taxon 'fungi' --reference --as-json-lines | dataformat tsv genome --fields assminfo-paired-assm-accession,current-accession,organism-name | sed -e 's/^[[:space:]]*//' -e 's/GCF_[^[:space:]]*[[:space:]]*//g' | awk 'BEGIN {FS=OFS="\t"} NR==1 {print "Name\tGCA"; next} {gsub(" ", "_", $2); print $2 "\t" $1}' > name2id.txt
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
#将下载好的基因组移动到GCA-updates
mkdir GCA-updates
mv ncbi/ncbi_dataset/data/*.fna GCA-updates/
ls GCA-updates/* | awk -F'[_.]' '{print "mv "$0" "$1"_"$2"_"$3".fna"}' > rename.sh
```

### 下载失败处理

```shell
#解压数据后，解压失败的重新下载
ls ncbi/ncbi_dataset/data/*.gz | cut -d "/" -f3 | cut -d "." -f1 | grep -f /dev/stdin ncbi_dataset/tmp.txt
mv ncbi_dataset/tmp.txt ncbi_dataset/fetch.txt
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
md5sum * > ../GCA-updates.md5
#比较md5值是否一致
#新的GCA.md5应该是GCA.exists.md5和ncbi/md5sum.updates.awk.txt合并
awk -F'[ ./_]' '{print $1,$6"_"$7"_"$8".fna"}' ncbi/md5sum.updates.txt > ncbi/md5sum.updates.awk.txt
cat GCA.exists.md5 ncbi/md5sum.updates.awk.txt | sort | uniq > GCA.md5

#实际校验的md5值应该为GCA.exists.md5和GCA-updates.md5合并
cat GCA.exists.md5 GCA-updates.md5 | sort | uniq > GCA.check.md5

#判断GCA.md5和GCA.check.md5内容是否一致
diff GCA.md5 GCA.check.md5
```



### 文件重命名

```shell
awk -F'[/.]' '{print "mv "$3".fna "$3"_"$4".fna"}' ../ncbi/md5sum.exists.txt | bash

#awk -F'[/.]' '{print "mv "$3".fna "$3"_"$4".fna"}' ../ncbi/md5sum.exists.txt | bash
```



```shell
mv ncbi/ncbi_dataset/data/*.fna GCA-update/

awk -F'[ /._]' '{print $1"  "$4"_"$5"_"$6".fna"}' GCA-update1.md5
awk -F'[ /]' '{print $1,$6}' ncbi/md5sum.update.txt > GCA-update.md5
```

