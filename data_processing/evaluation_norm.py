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

def evaluate_performance(pred_data, true_data, target_categories):
    tp, fp, fn = 0, 0, 0
    false_positives, false_negatives, true_positives = [], [], []

    pred_dict_norm = {(d[0], int(d[2]), int(d[3]), d[5] if len(d) > 5 else None): d for d in pred_data if d[1] in target_categories}
    true_dict_norm = {(d[0], int(d[2]), int(d[3]), d[5] if len(d) > 5 else None): d for d in true_data if d[1] in target_categories}
    true_dict = {(d[0], int(d[2]), int(d[3])): d for d in true_data if d[1] in target_categories}
    pred_dict = {(d[0], int(d[2]), int(d[3])): d for d in pred_data if d[1] in target_categories}
    true_start_dict = {(d[0], int(d[2])): d for d in true_data if d[1] in target_categories}
    pred_start_dict = {(d[0], int(d[2])): d for d in pred_data if d[1] in target_categories}
    
    
    for key, prediction in pred_dict_norm.items():
        if key not in true_dict_norm:
            fp += 1
            if key[:3] in true_dict:
                false_positives.append(prediction + ["norm wrong", true_dict[key[:3]][5]])
            elif (key[0], key[1]) in true_start_dict:
                false_positives.append(prediction + ["pred wrong", true_start_dict[(key[0],key[1])][4]])
            else:
                false_positives.append(prediction + ["not in answer", " "])
        else:
            tp += 1
            true_positives.append(prediction)

    for key, answer in true_dict_norm.items():
        if key not in pred_dict_norm:
            fn += 1
            if key[:3] in pred_dict:
                false_negatives.append(answer+ ["norm wrong", pred_dict[key[:3]][5]])
            elif (key[0], key[1]) in pred_start_dict:
                false_negatives.append(answer+["pred wrong", pred_start_dict[(key[0],key[1])][4]])
            else:
                false_negatives.append(answer + ["not predicted", " "])

    precision = tp / (tp + fp) if tp + fp > 0 else 0
    recall = tp / (tp + fn) if tp + fn > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if precision + recall > 0 else 0
    return precision, recall, f1, false_positives, false_negatives, true_positives

if __name__ == "__main__":
    target_categories = ["TIME", "DURATION", "SET", "DATE"]
    # Load the datasets
    path = os.path.join(os.getcwd(), "Result/val")
    answer_name = "answer_1701349994_1701423875_norm_clean.txt"    
    time = answer_name[7:17]
    file_prediction_path = os.path.join(path, answer_name)
    file_ground_path = os.path.join(path, "answer_val_phase1.txt")
    
    predictions = load_data(file_prediction_path)
    ground_truth = load_data(file_ground_path)

    precision, recall, f1, false_positives, false_negatives, true_positives = evaluate_performance(predictions, ground_truth, target_categories)

    fp_df = pd.DataFrame(false_positives, columns=["file_name", "pred_category", "start_pos", "end_pos", 
                                      "pred_content", "pred_norm", "error", " gt"])
    fn_df = pd.DataFrame(false_negatives, columns=["file_name", "gt_category", "start_pos", "end_pos", 
                                      "gt_content", "gt_norm_time", "error", "pred"])
    tp_df = pd.DataFrame(true_positives, columns=["file_name", "pred_category", "start_pos", "end_pos", 
                                      "pred_content", "pred_norm"])
    
    
    fp_df.to_excel(os.path.join(path, f'false_positives_{time}_norm.xlsx'), index=False)
    fn_df.to_excel(os.path.join(path, f'false_negatives_{time}_norm.xlsx'),index=False)
    tp_df.to_excel(os.path.join(path, f'true_positives_{time}_norm.xlsx'),index=False)
    
    # Print the results
    print(f"Precision: {precision:.2f}, Recall: {recall:.2f}, F1 Score: {f1:.2f}")
    # Optionally, print the error analysis details
    # print("False Positives:", false_positives)
    # print("False Negatives:", false_negatives)
    # print("True Positives:", true_positives)


