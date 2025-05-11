#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File    :   mobilome_check_genome_updates.py
@Time    :   2025/05/04 17:49:28
@Author  :   Naisu Yang 
@Version :   1.0
@Contact :   3298990@qq.com
'''

# here put the import lib
import argparse
from pathlib import Path

def parse_md5(file_path):
    """解析md5文件，返回{md5: filename}的字典"""
    md5_dict = {}
    with open(file_path, 'r') as f:
        for line in f:
            md5, filename = line.strip().split()
            md5_dict[md5] = filename
    print(f'{Path(file_path).name} Lines: {len(md5_dict)}')
    return md5_dict

def find_deprecated(gca_md5, ncbi_md5):
    """找出在GCA中存在但在NCBI中不存在的记录"""
    deprecated = []
    exists = []
    for md5, filename in gca_md5.items():
        if md5 not in ncbi_md5:
            deprecated.append(f"{md5}  {filename}")
        else:
            exists.append(f"{md5}  {filename}")
    print(f'Deprecated Lines: {len(deprecated)}')
    print(f'Exists Lines: {len(exists)}')
    return deprecated,exists

def find_updates(gca_md5, ncbi_md5):
    """找出在NCBI中存在但在GCA中不存在的记录"""
    updates = []
    exists = []
    for md5, filename in ncbi_md5.items():
        if md5 not in gca_md5 and "GCA" in filename:
            updates.append(f"{md5}  {filename}")
        elif "GCA" in filename:
            exists.append(f"{md5}  {filename}")
    print(f'Updates Lines: {len(updates)}')
    print(f'Exists Lines: {len(exists)}')
    return updates,exists

def filter_fetch(fetch_file, update_files):
    """根据更新列表过滤fetch.txt文件"""
    filters = []
    with open(fetch_file, 'r') as fin:
        for line in fin:
            gca_accession = "GCA_" + line.split("GCA_")[1].split(".")[0]
            if any(gca_accession in item for item in update_files):
                filters.append(line)
    print(f'fetch update Lines: {len(filters)}')
    return filters


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Generate SLURM submission script for mobilome_tn_mining pipeline')

    parser = argparse.ArgumentParser(description="statistical analysis of mobilome_tn_mining results")
    #parser.add_argument('-d', "--results_dir", type=str, required=True, help="Path to the mobilome_tn_mining results directory")
    parser.add_argument("--gca_md5", type=str, required=True, help="Path to the mobilome_tn_mining results directory")
    parser.add_argument("--ncbi_md5", type=str, required=True, help="Path to the mobilome_tn_mining results directory")
    parser.add_argument("--fetch_file", type=str, required=True, help="Path to the mobilome_tn_mining results directory")
    args = parser.parse_args()
    
    gca_md5 = parse_md5(args.gca_md5)
    ncbi_md5 = parse_md5(args.ncbi_md5)
    #fetch_file = parse_md5(args.fetch_file)

    deprecated, exists = find_deprecated(gca_md5, ncbi_md5)
    output_dir = Path(args.gca_md5).absolute().parent
    with open(Path(output_dir,'GCA.deprecated.md5'), 'w') as f1, open(Path(output_dir,'GCA.exists.md5'), 'w') as f2:
        f1.write('\n'.join(deprecated) + '\n')
        f2.write('\n'.join(exists) + '\n')

    updates,exists = find_updates(gca_md5, ncbi_md5)
    output_dir = Path(args.ncbi_md5).absolute().parent
    with open(Path(output_dir,'md5sum.updates.txt'), 'w') as f1, open(Path(output_dir,'md5sum.exists.txt'), 'w') as f2:
        f1.write('\n'.join(updates) + '\n')
        f2.write('\n'.join(exists) + '\n')

    filters = filter_fetch(args.fetch_file, updates)
    with open(Path(Path(args.fetch_file).absolute().parent,'fetch.filters.txt'), 'w') as f:
        f.writelines(filters)

if __name__ == '__main__':
    main()