#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 26 10:10:24 2023

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

    bounary, item_idx, temp_seq, seq_pairs = 0, 0, "", []
    new_line_idx = 0
    for w_idx, word in enumerate(article):
        if word == "\n":
            new_line_idx = w_idx + 1
            if article[bounary:new_line_idx] == "\n":
                bounary = new_line_idx
                continue
            if temp_seq == "":
                temp_seq = PHINull
            sentence = article[bounary:new_line_idx].strip().replace("\t", " ")
            temp_seq = temp_seq.strip("++")
            seq_pair = f"{txt_name}\t{bounary}\t{sentence}\t{temp_seq}\n"
            bounary = new_line_idx
            seq_pairs.append(seq_pair)
            temp_seq = ""
        if w_idx == annos_dict[txt_name][item_idx]["st_idx"]:
            phi_key = annos_dict[txt_name][item_idx]["phi"]
            phi_value = annos_dict[txt_name][item_idx]["entity"]
            # if "normalize_time" in annos_dict[txt_name][item_idx]:
            #     temp_seq += f"{phi_key}:{phi_value}=>{annos_dict[txt_name][item_idx]['normalize_time']}++
            # else:
            temp_seq += f"{phi_key}:{phi_value}++"
            if item_idx == len(annos_dict[txt_name]) - 1:
                continue
            item_idx += 1
    return seq_pairs


def sliding_window(fid, start_pos, content, label, max_len=128, overlap=50):
    """
    切分長句
    """
    splited_pairs = []
    stride = max_len - overlap
    label_infos = DataF.extract_label_info(label)
    for i in range(0, len(content), stride):
        window = content[i : i + max_len]
        window_start_pos = int(start_pos) + i
        window_label = ""

        if label == PHINull:
            window_label = PHINull
        else:
            for label_info in label_infos:
                category, label_content, label_norm = label_info
                # 如果窗口中包含了这个label的内容，则将其加入到label中
                if label_content in window:
                    label_content += label_norm if label_norm else ""
                    window_label += f"{category}:{label_content}++"
        # 删除最后一个换行符
        window_label = window_label[:-2] if window_label != PHINull else window_label
        if not window_label:
            window_label = PHINull

        splited_line = f"{fid}\t{window_start_pos}\t{window}\t{window_label}\n"
        if splited_line not in splited_pairs:
            splited_pairs.append(splited_line)

        """sample enhancement"""
        splited_pairs += small_sample_enhancement(fid, window_start_pos, window, window_label)

    return splited_pairs


def small_sample_enhancement(file_id, start_pos, current_content, current_label):
    enhanced_samples = []
    label_infos = DataF.extract_label_info(current_label)
    for cat, label_content, label_norm in label_infos:
        if cat == "PHONE":
            enhanced_samples += DataF.enhance_phone_number(
                file_id, start_pos, current_content, current_label, label_content, num_samples=50
            )
        elif cat == "COUNTRY":
            enhanced_samples += DataF.enhance_country(
                file_id, start_pos, current_content, current_label, label_content, num_samples=80
            )
        elif cat == "LOCATION-OTHER":
            enhanced_samples += DataF.enhance_location_other(
                file_id, start_pos, current_content, current_label, label_content, num_samples=80
            )
        elif cat == "DURATION":
            enhanced_samples += DataF.enhance_duration_and_normalized(
                file_id,
                start_pos,
                current_content,
                current_label,
                label_content,
                label_norm,
                num_samples=80,
                normalize=False,
            )
        elif cat == "ORGANIZATION":
            enhanced_samples += DataF.enhance_organization(
                file_id, start_pos, current_content, current_label, label_content, num_samples=30
            )
        elif cat == "SET":
            enhanced_samples += DataF.enhance_set(
                file_id, start_pos, current_content, current_label, num_samples=50
            )

    return list(set(enhanced_samples))


def concatenate_and_slice_sentences(lines, max_length=256, data_type = "original"):
    """
    拼接短句，切分長句
    """
    concatenated_data = []
    for i in range(len(lines)):
        if lines[i].isspace():
            continue
        current_file_id, current_start_pos, current_content, current_label = lines[i].strip().split("\t")
        
        """long sentences processing"""
        if data_type == "sliced" and len(current_content) > max_length*2:
            splited_pairs = sliding_window(
                current_file_id,
                current_start_pos,
                current_content,
                current_label,
                max_len=MaxLen*2,
                overlap=30,
            )
            concatenated_data += splited_pairs 
                 
        
        """add priginal sentences"""
        if data_type == "original":
            concatenated_data.append(lines[i])
            concatenated_data += small_sample_enhancement(current_file_id, current_start_pos, current_content, current_label)

        """short sentences processing"""
        if data_type == "spliced" and len(current_content) <= max_length:
            labels_list = [current_label]
            j = i + 1
            flag = 0
            while j < len(lines):
                if lines[j].isspace():
                    continue
                next_file_id, next_start_pos, next_content, next_label = lines[j].strip().split("\t")
                current_position = int(current_start_pos) + len(current_content)
                if int(next_start_pos) < current_position:
                    print("[ERROR]indexs inversion")
                while int(next_start_pos) > current_position:
                    current_content += " "
                    current_position += 1
                new_content = current_content + next_content
                if len(new_content) < max_length:
                    current_content = new_content
                    flag = 1
                    if next_label != PHINull:
                        labels_list.append(next_label)
                else:
                    break
                j += 1
            # label concatnation
            if len(set(labels_list)) == 1 and PHINull in labels_list:
                final_label = PHINull
            else:
                final_label = "++".join(filter(lambda x: x != PHINull, labels_list))

            seq_pair = f"{current_file_id}\t{current_start_pos}\t{current_content}\t{final_label}\n"
            if flag and seq_pair not in concatenated_data:
                concatenated_data.append(seq_pair)
                enhenced_pairs = small_sample_enhancement(
                    current_file_id, current_start_pos, current_content, final_label
                    )
                if enhenced_pairs:
                    concatenated_data.extend(enhenced_pairs)
        

    return concatenated_data


def append_length(line):
    length = len(line)
    current_content = line.replace("\t", " ").replace("\n", " ")
    # current_content = line.strip()
    while len(current_content) < length:
        current_content += " "
    return current_content


def validation_segment(sentence, max_length=256, overlap=30):
    """
    将长句子切分为多个段落，每个段落长度不超过 max_length，且段落之间有 overlap 字符的重合。
    """
    segments = []
    stride = max_length - overlap  # 实际滑动步长
    i = 0

    while i < len(sentence):
        segment = sentence[i:i + max_length]
        segments.append(segment)
        i += stride

    return segments



def concatenate_validation(lines, max_length=256, dtype="original"):
    concatenated_data = []
    for i in range(len(lines)):    
        # current_content = lines[i]
        current_content = append_length(lines[i])
        
        # long sentence segment
        if len(lines[i])>max_length and dtype == "sliced":
            concatenated_data += validation_segment(lines[i], max_length, 30)
            continue
        
        elif dtype == "spliced":
            if len (lines[i])>max_length:
                # to keep boundry with original 
                concatenated_data.append("")
        # short sentence concatnation
            else:  
                j = i + 1
                flag = 0
                while j < len(lines):
                    next_line = append_length(lines[j])
                    # next_line = lines[j]
                    new_content = current_content + next_line
                    if len(new_content) < max_length:
                        current_content = new_content
                        flag = 1
                    else:
                        break
                    j += 1
                
                if flag:
                    concatenated_data.append(current_content)
                else:
                    concatenated_data.append("")
            
    return concatenated_data


def find_position(sentence, article, nums=3):
    i = 0
    while sentence[i:] not in article:
        i += 1
    return sentence[i:]
        

def process_valid_data(test_txts, out_file):
    out_file_original = out_file.replace('.tsv', '_original.tsv')
    out_file_spliced = out_file.replace('.tsv', '_spliced.tsv')
    out_file_sliced = out_file.replace('.tsv', '_sliced.tsv')
    
    with open(out_file_original, "w", encoding="utf-8") as fw_org, \
        open(out_file_spliced, "w", encoding="utf-8") as fw_spl, \
            open(out_file_sliced, "w", encoding="utf-8") as fw_slc:
        
        for txt in test_txts:
            m_report = read_file(txt)
            article = "".join(m_report)
            m_report_spliced = concatenate_validation(m_report, MaxLen, "spliced")
            m_report_sliced = concatenate_validation(m_report, MaxLen*2, "sliced")
            fid = txt.split("/")[-1].replace(".txt", "")
       
            boundary = 0
            for sent_org, sent_spl in zip(m_report, m_report_spliced):
                if sent_org.replace(" ", "").replace("\n", "").replace("\t", "") != "":
                    sent_org = sent_org.replace("\t", " ").replace("\n", " ")
                    fw_org.write(f"{fid}\t{boundary}\t{sent_org}\n") 
                if sent_spl.replace(" ", "").replace("\n", "").replace("\t", "") != "":
                    sent_spl = sent_spl.replace("\t", " ").replace("\n", " ") 
                    fw_spl.write(f"{fid}\t{boundary}\t{sent_spl}\n") 
                boundary += len(sent_org)
            
            for sent_slc in m_report_sliced:
                if sent_slc.replace(" ", "").replace("\n", "").replace("\t", "") != "":
                    sent_slc = sent_slc.replace("\t", " ").replace("\n", " ").strip()
                    position = article.find(sent_slc)
                    if position == -1:
                        sent_slc = find_position(sent_slc, article, nums=3)
                        position = article.find(sent_slc)
                        if position == -1:
                            print("[ERROR] Not in article:", sent_slc)
                    fw_slc.write(f"{fid}\t{position}\t{sent_slc}\n") 


def generate_annotated_medical_report_parallel(
    anno_file_path, medical_report_folder, tsv_output_path, dtype, sample, num_processes=4
):
    """
    呼叫上面的兩個function
    處理全部的病理報告和標記檔案

    output : 全部的 sequence pairs
    """
    anno_lines = read_file(anno_file_path)
    annos_dict = process_annotation_file(anno_lines)
    txt_names = list(annos_dict.keys())
    
    # rename savename
    train_file_name = tsv_output_path.replace(".tsv", "_train.tsv")
    test_file_name = tsv_output_path.replace(".tsv", "_test.tsv")
      
    # sample test files
    random_seed = 1025
    random.seed(random_seed)
    test_file_ids = random.sample(txt_names, int(0.1 * len(txt_names)))
    train_file_ids = [fid for fid in txt_names if fid not in test_file_ids]

    """Training data"""
    print("processing each medical file")
    all_seq_pairs = []
    for txt_name in train_file_ids:
        result_pairs = process_medical_report(
            txt_name, medical_report_folder, annos_dict, special_tokens_dict
        )
        concatenated_pairs = concatenate_and_slice_sentences(result_pairs, MaxLen, dtype)
        all_seq_pairs.extend(concatenated_pairs)
    
    print(f"max length in dataset-{dtype} training:", max(len(s) for s in all_seq_pairs))
    print("All traiing medical file done")
    with open(train_file_name, "w", encoding="utf-8") as fw:
        for seq_pair in all_seq_pairs:
            fw.write(seq_pair)
    print("Training tsv format dataset done")
    
    
    """Testing data"""
    all_seq_pairs = []
    for txt_name in test_file_ids:
        result_pairs = process_medical_report(
            txt_name, medical_report_folder, annos_dict, special_tokens_dict
        )
        concatenated_pairs = concatenate_and_slice_sentences(result_pairs, MaxLen, dtype)
        all_seq_pairs.extend(concatenated_pairs)
        
    print(f"max length in dataset1-{dtype} training:", max(len(s) for s in all_seq_pairs))
    print("All testing medical file done")
    with open(test_file_name, "w", encoding="utf-8") as fw:
        for seq_pair in all_seq_pairs:
            fw.write(seq_pair)
    print("Testing tsv format dataset done")
    

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
    Types = ["original", "sliced", "spliced"]


    # """training data processing for task1"""
    # set_torch_seed()
    # path = os.path.join(os.getcwd(), "Data/First_Phase_Release(Correction)")
    # report_folder = os.path.join(path, "First_Phase_Text_Dataset")
    # anno_info_path = os.path.join(path, "answer.txt")
    
    # for dtype in Types:
    #     sample = True
    #     file_name = f"train_phase1_v8_{dtype}.tsv"
    #     save_name = os.path.join(os.getcwd(), f"Data/{file_name}")
    #     generate_annotated_medical_report_parallel(anno_info_path, report_folder, 
    #                                                 save_name, dtype, sample, 
    #                                                 num_processes=4)
    #     sample = False
        
    # path = os.path.join(os.getcwd(), "Data/Second_Phase_Dataset")
    # report_folder = os.path.join(path, "Second_Phase_Text_Dataset")
    # anno_info_path = os.path.join(path, "answer.txt")
    # for dtype in Types:
    #     sample = True
    #     file_name =  f"train_phase2_v8_{dtype}.tsv"
    #     save_name = os.path.join(os.getcwd(), f"Data/{file_name}")
    #     generate_annotated_medical_report_parallel(anno_info_path, report_folder, 
    #                                                 save_name, dtype, sample, 
    #                                                 num_processes=4)
    #     sample = False
        
    
    # """validation data processing"""
    # path = os.path.join(os.getcwd(), "Data/First_Phase_Release(Correction)")
    # report_folder = os.path.join(path, "Validation_Release")
    # file_name = "valid_phase1_v8.tsv"
    # save_name = os.path.join(os.getcwd(), f"Data/{file_name}")

    # test_txts = list(map(lambda x: os.path.join(report_folder, x), os.listdir(report_folder)))
    # test_txts = sorted(test_txts)
    # valid_data = process_valid_data(test_txts, save_name)
    
    """final data processing"""
    path = os.path.join(os.getcwd(), "Data/opendid_test")
    report_folder = os.path.join(path, "opendid_test")
    file_name = "final.tsv"
    save_name = os.path.join(os.getcwd(), f"Data/{file_name}")

    test_txts = list(map(lambda x: os.path.join(report_folder, x), os.listdir(report_folder)))
    test_txts = sorted(test_txts)
    valid_data = process_valid_data(test_txts, save_name)
    
   
    
