#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 27 23:11:19 2023

@author: huangpaveen
"""

import os
import re
from datetime import datetime


def read_file(path):
    with open(path, "r", encoding="utf-8-sig") as fr:
        return fr.readlines()
    
def recognize_normalized_date(text):
    date_pattern = r'(\d{2,4})-(\d{2})-(\d{2})'
    matches = re.findall(date_pattern, text)
    if matches:
        return matches[0] 
    return 

def extract_date(datetime_string):
    # This regex matches a date in the format YYYY-MM-DD that is followed by 'T'
    date_pattern = re.compile(r'\b(\d{2,4}-\d{2}-\d{2})T')
    match = date_pattern.search(datetime_string)
    return match.group(1) if match else None


def date_normalization(original_date, normalized_date, cat="DATE"):
    # This pattern matches dates in 'D/M/YYYY', 'D.M.YYYY', 'DDMMYYYY', and 'D.M.YY' formats
    date_pattern = r'(\d{1,2})[./](\d{1,2})[./](\d{2,4})|(\d{8})'
    match = re.match(date_pattern, original_date.replace(' ', ''))
    if cat == "TIME":
        tmp_list = original_date.split(" ")
        for tmp in tmp_list:
            match = re.match(date_pattern, tmp)
            if match:
                break
    if match:
        if match.group(4):
            year, month, day = match.group(4)[:4], match.group(4)[4:6], match.group(4)[6:]
        else:
            day, month, year = match.groups()[:3]
        
        day = day.zfill(2)
        month = month.zfill(2)
        if len(year) == 2:
            current_year = str(datetime.now().year)
            century = current_year[:2]
            year = century + year
        elif len(year) == 3 or len(year) == 1:
            return normalized_date
        
        time_recg = recognize_normalized_date(normalized_date)
        if time_recg:
            y_norm, m_norm, d_norm = time_recg
            if any([m_norm != month, d_norm != day, y_norm != year]):
                tmp_old = f"{y_norm}-{m_norm}-{d_norm}"
                tmp_new = f"{year}-{month}-{day}"
                normalized_date = normalized_date.replace(tmp_old, tmp_new)  
    return normalized_date


def time_normalization(original_string, generated_answer):
    # am_pm_time_match = re.search(r'(\d{1,2})[:.](\d{2})(am|pm)', original_string, re.IGNORECASE)
    am_pm_time_match = re.search(r'(\d{1,2})[:.](\d{2})\s*(am|pm)', original_string, re.IGNORECASE)
    if not am_pm_time_match:
        return generated_answer  # No AM/PM time found, return original answer

    # Extract the hours, minutes, and the AM/PM part
    hours, minutes, part_of_day = am_pm_time_match.groups()
    hours = int(hours)
    minutes = int(minutes)
    part_of_day = part_of_day.lower()

    # Convert hours to 24-hour format based on the AM/PM indicator
    if part_of_day == 'pm' and hours < 12:
        hours += 12
    elif part_of_day == 'am' and hours == 12:
        hours = 0

    # Format the hours and minutes into a 24-hour time format
    corrected_time = f"{hours:02d}:{minutes:02d}"

    # Replace the time in the generated answer with the corrected time
    corrected_answer = re.sub(r'T\d{2}:\d{2}', f'T{corrected_time}', generated_answer)

    return corrected_answer


if __name__ == "__main__":
    path = os.path.join(os.getcwd(),"Result")
    # path = os.path.join(os.getcwd(),"Result/val")
    answer = "answer_1701349994_1701423875_norm.txt"
    file_path = os.path.join(path, answer)
    save_path =  os.path.join(path, answer.replace(".txt", "_clean.txt"))
    
    lines = read_file(file_path)
    
    with open(save_path, 'w', encoding='utf-8') as file:
        for line in lines:
            # Split each line by tab character
            parts = line.strip().split('\t')
            if len(parts) == 6:
                fid, category, start_pos, end_pos, content, normalization = parts
                if "4:50pm 08.03.65" in content:
                    print()
                if category == "DATE":
                    normalization = date_normalization(content, normalization)
                elif category == "TIME":
                    time_date = extract_date(normalization)
                    if time_date:
                        time_date_corrected = date_normalization(content, time_date, "TIME")
                        normalization = normalization.replace(time_date, time_date_corrected)
                    normalization = time_normalization(content, normalization)
                file.write(f"{fid}\t{category}\t{start_pos}\t{end_pos}\t{content}\t{normalization}\n")
            else:
                fid, category, start_pos, end_pos, content = parts
                file.write(f"{fid}\t{category}\t{start_pos}\t{end_pos}\t{content}\n")
                
                
                


