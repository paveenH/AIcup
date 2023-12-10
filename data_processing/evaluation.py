#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 14 16:35:43 2023

@author: huangpaveen
"""

import os
import pandas as pd

def load_data(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            parts = line.strip().split('\t')
            if len(parts) < 5:  # Skip incomplete lines
                continue
            data.append(parts)
    return data

def add_error_info(record, error, tp=None, has_time=True):
    if tp is None:
        tp = "no value"
    if has_time:
        return record + [tp, error]
    return record + ["no time", tp, error]

def evaluate_performance(pred_data, true_data):
    tp, fp, fn = 0, 0, 0
    false_positives = []
    false_negatives = []
    true_positives = []

    pred_dict = {(d[0], int(d[2]), int(d[3])): d for d in pred_data}
    true_dict = {(d[0], int(d[2]), int(d[3])): d for d in true_data}

    for key, prediction in pred_dict.items():
        prediction_type = prediction[1]
        has_time = len(prediction) == 6

        if key not in true_dict:
            fp += 1
            false_positives.append(add_error_info(prediction, "not in answer", None, has_time))
        else:
            true_type = true_dict[key][1]
            if prediction_type != true_type:
                fp += 1
                false_positives.append(add_error_info(prediction, "type wrong", true_type, has_time))
            else:
                tp += 1
                true_positives.append(prediction)

    for key, answer in true_dict.items():
        answer_type = answer[1]
        has_time = len(answer) == 6

        if key not in pred_dict:
            fn += 1
            false_negatives.append(add_error_info(answer, "not predicted", None, has_time))
        else:
            prediction_type = pred_dict[key][1]
            if prediction_type != answer_type:
                false_negatives.append(add_error_info(answer, "type wrong", prediction_type, has_time))

    precision = tp / (tp + fp) if tp + fp > 0 else 0
    recall = tp / (tp + fn) if tp + fn > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if precision + recall > 0 else 0
    
    return precision, recall, f1, false_positives, false_negatives, true_positives


def evaluate_macro_f1(pred_data, true_data):
    def add_error_info(data, error_type, mismatch_type=None, has_time=False):
        return data + [error_type, mismatch_type] if has_time else data + [error_type, mismatch_type, None]

    # Initialize counters for each category
    category_stats = {}

    # Convert data to dictionaries for easier access
    pred_dict = {(d[0], int(d[2]), int(d[3])): d for d in pred_data}
    true_dict = {(d[0], int(d[2]), int(d[3])): d for d in true_data}

    # Process predictions
    for key, prediction in pred_dict.items():
        prediction_type = prediction[1]

        # Initialize stats for new category
        if prediction_type not in category_stats:
            category_stats[prediction_type] = {"tp": 0, "fp": 0, "fn": 0}

        if key not in true_dict:
            category_stats[prediction_type]["fp"] += 1
        else:
            true_type = true_dict[key][1]
            if prediction_type != true_type:
                category_stats[prediction_type]["fp"] += 1
            else:
                category_stats[prediction_type]["tp"] += 1

    # Process true values for false negatives
    for key, answer in true_dict.items():
        answer_type = answer[1]

        # Initialize stats for new category
        if answer_type not in category_stats:
            category_stats[answer_type] = {"tp": 0, "fp": 0, "fn": 0}

        if key not in pred_dict:
            category_stats[answer_type]["fn"] += 1
        else:
            prediction_type = pred_dict[key][1]
            if prediction_type != answer_type:
                category_stats[answer_type]["fn"] += 1

    # Calculate F1 score for each category
    category_f1_scores = {}
    for category, stats in category_stats.items():
        tp, fp, fn = stats["tp"], stats["fp"], stats["fn"]
        precision = tp / (tp + fp) if tp + fp > 0 else 0
        recall = tp / (tp + fn) if tp + fn > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if precision + recall > 0 else 0
        category_f1_scores[category] = f1

    # Calculate macro-F1 score
    macro_f1 = sum(category_f1_scores.values()) / len(category_f1_scores) if category_f1_scores else 0

    return macro_f1, category_f1_scores


def print_results(file_path, false_positives, false_negatives):
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write("False Positives:\n")
        for item in false_positives:
            file.write(str(item) + '\n')
        file.write("\nFalse Negatives:\n")
        for item in false_negatives:
            file.write(str(item) + '\n')
        

if __name__ == "__main__":
    # Load the generated answers and the standard answers
    path = os.path.join(os.getcwd(), "Result/val")
    time = "1701181213_1701317300"
    pred_data = load_data(os.path.join(path, f"answer_{time}.txt"))
    true_data = load_data(os.path.join(path, "answer_val_phase1.txt"))


    # Evaluation 1
    precision, recall, f1, fp, fn, tp = evaluate_performance(pred_data, true_data)
    print(f"Precision: {precision}, Recall: {recall}, F1-Measure: {f1}")
    
    macro_f1, category_f1_scores = evaluate_macro_f1(pred_data, true_data)
    print(f"macro f1: {macro_f1}")
    
    # 转换列表为 DataFrame
    fp_df = pd.DataFrame(fp, columns=["file_name", "pred_category", "start_pos", "end_pos", 
                                      "pred_content", "pred_norm_time", "gt_content", "error"])
    fn_df = pd.DataFrame(fn, columns=["file_name", "gt_category", "start_pos", "end_pos", 
                                      "gt_content", "gt_norm_time", "pred_content", "error"])
    tp_df = pd.DataFrame(tp, columns=["file_name", "pred_category", "start_pos", "end_pos", 
                                      "pred_content"])
    
    
    fp_df.to_excel(os.path.join(path, f'false_positives_{time}.xlsx'), index=False)
    fn_df.to_excel(os.path.join(path, f'false_negatives_{time}.xlsx'),index=False)
    tp_df.to_excel(os.path.join(path, f'true_positives_{time}.xlsx'),index=False)
                                
