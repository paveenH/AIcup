#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 17 21:14:11 2023

@author: huangpaveen
"""

import re
import os
import data_forge as DataF
import remedy as RM
import json

PhiCategory = [
    "PATIENT", "DOCTOR", "USERNAME", "PROFESSION", "ROOM", "DEPARTMENT", "HOSPITAL",
    "ORGANIZATION", "STREET", "CITY", "STATE", "COUNTRY", "ZIP", "LOCATION-OTHER",
    "AGE", "DATE", "TIME", "DURATION", "SET", "PHONE", "FAX", "EMAIL", "URL",
    "IPADDR", "SSN", "MEDICALRECORD", "HEALTHPLAN", "ACCOUNT", "LICENSE", "VEHICLE",
    "DEVICE", "BIOID", "IDNUM"
]


def read_file(path):
    with open(path, "r", encoding="utf-8-sig") as fr:
        return fr.readlines()


"""Get and clean label information"""

def get_anno_format(sentence, infos, boundary):
    # Initialize the list to store annotations
    anno_list = []
    boundary = int(boundary)
    
    # label dectction
    infos = RM.detection(sentence, infos)

    # Extract label information and clean it
    label_infos = DataF.extract_label_info(infos)
    phi_dict = {}

    for label_info in label_infos:        
        # label clean
        if len(label_info) >= 2:
            cleaned_label = RM.label_clean(label_info)
            if cleaned_label:
                revised_label = RM.content_revision(sentence, cleaned_label)
                if revised_label[0] not in phi_dict:
                    phi_dict[revised_label[1]] = revised_label[0].strip()
                    
        # if len(label_info) >= 2:
        #     phi_dict[label_info[0]] = label_info[1].strip()

    # Find matches in the sentence and add to annotations
    for phi_value, phi_key in phi_dict.items():
        try:
            matches = [(m.start(), m.end()) for m in re.finditer(re.escape(phi_value), sentence)]
        except re.error:
            continue

        for start, end in matches:
            if start == end:
                continue
            # if phi_value == "eh":
            #     print()
            item_dict = {
                "phi": phi_key,
                "st_idx": start + boundary,
                "ed_idx": end + boundary,
                "entity": phi_value,
            }
            anno_list.append(item_dict)

    return anno_list


"""Construct vote dict"""


def construct_output_dict(outputs):
    # 用于存储每个键的出现次数和对应的输出行
    output_dict = {}

    for output in outputs:
        parts = output.split("\t")
        if len(parts) < 5:
            continue
        key = (parts[0], parts[1], parts[2], parts[3])
        if key not in output_dict:
            output_dict[key] = {"count": 1, "output": output}
        else:
            output_dict[key]["count"] += 1
    return output_dict


def organize_by_start_pos(output_dict):
    start_pos_dict = {}
    for key, value in output_dict.items():
        k = (key[0], key[2])
        if k not in start_pos_dict:
            start_pos_dict[k] = []
        start_pos_dict[k].append(value)

    return start_pos_dict


def organize_by_max_end_pos(output_dict):
    max_end_pos_dict = {}
    for key, value_list in output_dict.items():
        file_id = key[0]
        # 找到最大的end_pos
        max_end_pos = max(value["output"].split("\t")[3] for value in value_list)

        new_key = (file_id, max_end_pos)
        if new_key not in max_end_pos_dict:
            max_end_pos_dict[new_key] = []

        max_end_pos_dict[new_key].extend(value_list)

    return max_end_pos_dict


def select_best_output(start_pos_dict):
    best_output_dict = {}

    for start_pos, entries in start_pos_dict.items():
        # entry clean
        if len(entries) == 1:
            entry = RM.entry_clean(entries[0])
            if entry:
                best_output_dict[start_pos] = entry["output"]
            continue
            # best_output_dict[start_pos] = entries[0]["output"]
            # continue
        best_entry = None
        for entry in entries:
            # entry clean
            entry = RM.entry_clean(entry)
            if not entry:
                continue
            if best_entry is None:
                best_entry = entry
            elif entry["count"] > best_entry["count"] or (
                entry["count"] == best_entry["count"] and len(entry["output"]) > len(best_entry["output"])
            ):
                best_entry = entry
            elif entry["count"] == best_entry["count"] and len(entry["output"]) == len(best_entry["output"]):
                if "TIME" in entry["output"] and "DATE" in best_entry["output"]:
                    best_entry = entry
                elif "TIME" not in best_entry["output"]:
                    print("[WARNING] Undecided", entries)
                    break

        if best_entry:
            best_output_dict[start_pos] = best_entry["output"]

    return best_output_dict


def write_to_file(best_output_dict, output_file):
    # 将字典按照文件名和起始位置排序
    sorted_items = sorted(best_output_dict.items(), key=lambda x: (x[0][0], int(x[0][1])))

    with open(output_file, "w", encoding="utf-8") as file:
        for key, value in sorted_items:
            file.write(value + "\n")


if __name__ == "__main__":

    total = []
    outputs = []
    total_time = []

    
    # name_list = ["prediction_1701317300.txt", "prediction_1701181213.txt"]
    name_list = ["prediction_1701181213.txt", "prediction_1701317300.txt"]
    # name_list = ["prediction_1701068438.txt"] # flant5-base-LoRA 
    # name_list =["prediction_1701349994.txt"] # flant5-large-LoRA ✔
    # name_list = ["prediction_1701317300.txt"] # flant5-large ✔
    
    # name_list = ["prediction_1701423875.txt"] #  pythia 160m frz ✔
    # name_list = ["prediction_1701407216.txt"] # pythia 160m v5
    # name_list = ["prediction_1701181213.txt"] # pythia 160m v3  
    # name_list = ["prediction_1701158435.txt"] # pythia 70m v3
    
    for name in name_list:
        time = name[11:-4]
        path = os.path.join(os.getcwd(), "Result/val")
        # path = os.path.join(os.getcwd(), "Result")
        pred_path = os.path.join(path, name)
        lines = read_file(pred_path)
        total += lines
        total_time.append(time)

    out_time = "_".join(total_time)

    output_path = os.path.join(path, f"answer_{out_time}.txt")
    dict_path = os.path.join(path, f"dict_{out_time}.json")

    for line in total:
        if len(line.strip().split("\t")) != 4:
            # print("[WARNING]No prediction: ", line)
            continue
        fid, idx, content, prediction = line.strip().split("\t")
        # if fid != "1001":
        #     continue
        annotations = get_anno_format(content, prediction, idx)
        for annotation in annotations:
            outputs.append(
                f'{fid}\t{annotation["phi"]}\t{annotation["st_idx"]}\t{annotation["ed_idx"]}\t{annotation["entity"]}'
            )

    output_dict = construct_output_dict(outputs)
    start_pos_dict = organize_by_start_pos(output_dict)
    pos_dict = organize_by_max_end_pos(start_pos_dict)
    best_output_dict = select_best_output(pos_dict)

    write_to_file(best_output_dict, output_path)
    
    json_compatible_dict = {str(k): v for k, v in pos_dict.items()}
    with open(dict_path, 'w', encoding='utf-8') as f:
        json.dump(json_compatible_dict, f, ensure_ascii=False, indent=4)

    print(out_time)
