#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 21 22:51:24 2023

@author: huangpaveen
"""

import os
import numpy as np
import torch
import random

import data_forge as DataF

def set_torch_seed(seed=0):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benckmark = False
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)


def read_file(path):
    with open(path, "r", encoding="utf-8-sig") as fr:
        return fr.readlines()


def process_annotation_file(lines):
    """
    處理anwser.txt 標註檔案

    output:annotation dicitonary
    """
    print("process annotation file...")
    entity_dict = {}
    for line in lines:
        items = line.strip("\n").split("\t")
        if len(items) == 5:
            item_dict = {
                "phi": items[1],
                "st_idx": int(items[2]),
                "ed_idx": int(items[3]),
                "entity": items[4],
            }
        elif len(items) == 6:
            item_dict = {
                "phi": items[1],
                "st_idx": int(items[2]),
                "ed_idx": int(items[3]),
                "entity": items[4],
                "normalize_time": items[5],
            }
        if items[0] not in entity_dict:
            entity_dict[items[0]] = [item_dict]
        else:
            entity_dict[items[0]].append(item_dict)
    print("annotation file done")
    return entity_dict


def process_medical_report(txt_name, medical_report_folder, annos_dict, special_tokens_dict):
    """
    處理單個病理報告

    output : 處理完的 sequence pairs
    """
    file_name = txt_name + ".txt"
    sents = read_file(os.path.join(medical_report_folder, file_name))
    article = "".join(sents)

    item_idx, normalized_pairs = 0, []
    for w_idx, word in enumerate(article):
        
        if w_idx == annos_dict[txt_name][item_idx]["st_idx"]:
            phi_key = annos_dict[txt_name][item_idx]["phi"]
            phi_value = annos_dict[txt_name][item_idx]["entity"]
            if "normalize_time" in annos_dict[txt_name][item_idx]:
                normalized_pairs.append(f"{phi_key}:{phi_value}\t{annos_dict[txt_name][item_idx]['normalize_time']}\n")
            if item_idx == len(annos_dict[txt_name]) - 1:
                continue
            item_idx += 1
    return normalized_pairs



def append_length(line):
    length = len(line)
    current_content = line.strip()
    while len(current_content) < length:
        current_content += " "
    return current_content


def concatenate_validation(lines, max_length=256):
    concatenated_data = []
    initial_length = []

    for i in range(len(lines)):
        current_content = append_length(lines[i])
        initial_length.append(len(lines[i]))

        j = i + 1
        while j < len(lines):
            next_line = append_length(lines[j])
            new_content = current_content + next_line

            if len(new_content) < max_length:
                current_content = new_content
            else:
                break

            j += 1

        concatenated_data.append(current_content)

    return concatenated_data, initial_length


def process_valid_data(test_txts, out_file):
    with open(out_file, "w", encoding="utf-8") as fw:
        for txt in test_txts:
            m_report = read_file(txt)
            m_report_concatneated, initial_length = concatenate_validation(m_report, max_length=MaxLen)
            boundary = 0
            # temp = ''.join(m_report)
            fid = txt.split("/")[-1].replace(".txt", "")
            for (idx, sent), initial_length in zip(enumerate(m_report_concatneated), initial_length):
                if sent.replace(" ", "").replace("\n", "").replace("\t", "") != "":
                    sent = sent.replace("\t", " ")

                    fw.write(f"{fid}\t{boundary}\t{sent}\n")
                boundary += initial_length

def forge_duration_sample(num_samples):
    duration_samples = []
    samples, normalized_samples = DataF.generate_duration_samples(num_samples)
    for sample, norm in zip(samples, normalized_samples):
        duration_samples.append(f"DURATION:{sample}\t{norm}\n")
        
    return duration_samples
        

def generate_annotated_medical_report_parallel(
    anno_file_path, medical_report_folder, tsv_output_path, num_processes=4
):
    """
    呼叫上面的兩個function
    處理全部的病理報告和標記檔案

    output : 全部的 sequence pairs
    """
    anno_lines = read_file(anno_file_path)
    annos_dict = process_annotation_file(anno_lines)
    txt_names = list(annos_dict.keys())

    print("processing each medical file")

    all_seq_pairs = []
    for txt_name in txt_names:
        result_pairs = process_medical_report(txt_name, medical_report_folder, 
                                              annos_dict, special_tokens_dict)
        all_seq_pairs.extend(result_pairs)
    
    all_seq_pairs += forge_duration_sample(300)
    all_seq_pairs += DataF.generate_set_samples(300)
    all_seq_pairs = list(set(all_seq_pairs))
    print(all_seq_pairs[:10])
    print("All medical file done")
    print("write out to tsv format...")
    with open(tsv_output_path, "w", encoding="utf-8") as fw:
        for seq_pair in all_seq_pairs:
            fw.write(seq_pair)
    print("tsv format dataset done")
    return all_seq_pairs


if __name__ == "__main__":

    bos = "<|endoftext|>"
    eos = "<|END|>"
    pad = "<|pad|>"
    ner = "\n\n####\n\n"
    special_tokens_dict = {
        "bos_token": bos,
        "eos_token": eos,
        "pad_token": pad,
        "sep_token": ner,
    }

    MaxLen = 128
    PHINull = "PHI:Null"
    NormCat = ["TIME", "SET", "DATE", "DURATION"]


    """training data processing for task1"""
    set_torch_seed()
    path = os.path.join(os.getcwd(), "Data/First_Phase_Release(Correction)")
    report_folder = os.path.join(path, "First_Phase_Text_Dataset")
    anno_info_path = os.path.join(path, "answer.txt")
    file_name = f"train_phase1_{MaxLen}_task2.tsv"
    save_name = os.path.join(os.getcwd(), f"Data/{file_name}")
    results = generate_annotated_medical_report_parallel(anno_info_path, report_folder, save_name, num_processes=4)
    print("max length in dataset2:", max(len(s) for s in results))
    
    path = os.path.join(os.getcwd(), "Data/Second_Phase_Dataset")
    report_folder = os.path.join(path, "Second_Phase_Text_Dataset")
    anno_info_path = os.path.join(path, "answer.txt")
    file_name =  f"train_phase2_{MaxLen}_task2.tsv"
    save_name = os.path.join(os.getcwd(), f"Data/{file_name}")
    results = generate_annotated_medical_report_parallel(anno_info_path, report_folder, save_name, num_processes=4)
    print("max length in dataset2:", max(len(s) for s in results))
    
    # """validation data processing"""
    # path = os.path.join(os.getcwd(), "Data/First_Phase_Release(Correction)")
    # report_folder = os.path.join(path, "Validation_Release")
    # file_name = f"valid_phase1_{MaxLen}_repeat.tsv"
    # save_name = os.path.join(os.getcwd(), f"Data/{file_name}")

    # test_txts = list(map(lambda x: os.path.join(report_folder, x), os.listdir(report_folder)))
    # test_txts = sorted(test_txts)
    # valid_data = process_valid_data(test_txts, save_name)
