#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 30 17:17:28 2023

@author: huangpaveen
"""

import re 

PhiCategory = [
    "PATIENT", "DOCTOR", "USERNAME", "PROFESSION", "ROOM", "DEPARTMENT", "HOSPITAL",
    "ORGANIZATION", "STREET", "CITY", "STATE", "COUNTRY", "ZIP", "LOCATION-OTHER",
    "AGE", "DATE", "TIME", "DURATION", "SET", "PHONE", "FAX", "EMAIL", "URL",
    "IPADDR", "SSN", "MEDICALRECORD", "HEALTHPLAN", "ACCOUNT", "LICENSE", "VEHICLE",
    "DEVICE", "BIOID", "IDNUM"
]

HOSPITALKey = ["HOSPITAL", "SERVICE", "CAMPUS", "CENTRE"]
ORGANIZATIONKey = ["Inc", "Corporation"]
PATIENTKey = ["PANCREAS", "Vessels", "HOOKWIRE", "SGP", "IMMUNOSTAINS", "Vessels", "HARTMANN"]

CommonCountry = ['United States', 'United Kingdom', 'South Korea', 'Saudi Arabia',
                  'South Africa','United Arab Emirates','South Africa','New Zealand']

def extract_label_info(label):
    """
    get label information from label string
    """
    pattern = r"([A-Z-]+):([^\n=>]+)(=>[^\n]+)?"
    # label_parts = label.split("\\n")
    label_parts = label.split("++")
    extracted_info = []

    for part in label_parts:
        matches = re.findall(pattern, part)
        for match in matches:
            category, content, norm = match
            extracted_info.append((category, content.strip(), norm.strip()))
    return extracted_info


"""Remedy1: Limit label length and constrain label content"""
def is_valid_label(label_cat, label_content):
    validation_rules = {
        "AGE": lambda x: False if len(x) > 3 or any(c.isalpha() for c in x) or int(x) > 110 else True,
        "DATE": lambda x: len(x) > 2,
        "DEPARTMENT": lambda x: len(x) > 2,
        "DOCTOR": lambda x: False if any(c.isdigit() for c in x) or x == "eh" else True,
        "DURATION": lambda x: any(term in x.lower() for term in ["day", "week", "month", "year", "dy", "wk", "mth", "yr"]),
        "HOSPITAL": lambda x: len(x) >= 4 and len(x.split(" ")) > 1,
        "IDNUM": lambda x: len(x) > 4,
        "ORGANIZATION": lambda x: len(x) >= 5,
        # "PATIENT": lambda x: False if any(c.isdigit() for c in x) else True,
        "PATIENT": lambda x: False if any(c.isdigit() for c in x) or any(keyword in x for keyword in PATIENTKey) else True,
        "PHONE": lambda x: len(x) == 8 or len(x) == 9,
        "STREET": lambda x: "BOX".lower() not in x.lower(),
        "TIME": lambda x: len(x) > 4,
        "ZIP": lambda x: len(x) == 4
    }
    
    if label_cat not in PhiCategory:
        return False
    
    if label_cat != "HOSPITAL" and "Hospital".lower() in label_content.lower():
        return False
    
    if label_cat not in ["AGE"] and len(label_content) == 1:
        return False

    return validation_rules.get(label_cat, lambda x: True)(label_content)

def label_clean(label_info):
    label_cat, label_content, _ = label_info
    if is_valid_label(label_cat, label_content):
        return label_info

"""Remedy2: Complete content by regulation"""

def complete_hospital(sentence, partial_name):
    for key in HOSPITALKey:
        if key in sentence and key not in partial_name:
            pattern = r"\b" + re.escape(partial_name) + r".*?\b(?:" + "|".join(HOSPITALKey) + r")\b"
            match = re.search(pattern, sentence)

            if not match:
                pattern = r"\b" + re.escape(partial_name) + r".*?\b(?:HEALTH)\b"
                match = re.search(pattern, sentence)

            if not match:
                partial_name = partial_name.split(" ")[0]
                pattern = r"\b" + re.escape(partial_name) + r".*?\b(?:" + "|".join(HOSPITALKey) + r")\b"
                match = re.search(pattern, sentence)

            return match.group(0) if match else partial_name

    return partial_name


def complete_time_v1(sentence, partial_time):
    time_patterns = [
        r"\b(\d{1,2}:\d{2}[ap]m\s+on\s+\d{1,2}[./]\d{1,2}[./]\d{2,4})\b",
        r"(\d{1,2}[:.]\d{2}[ap]m\s+(?:on\s+|at\s+)?\d{1,2}[./]\d{1,2}[./]\d{2,4})"
    ]

    for pattern in time_patterns:
        match = re.search(pattern, sentence)
        if match:
            return match.group(1)

    return partial_time


def complete_time_v2(sentence, partial_time):
    # Check if the partial_time follows the pattern "TIME:DD/MM/YYYY"
    date_pattern = r"(\d{2}/\d{2}/\d{4})"
    date_match = re.search(date_pattern, partial_time)

    if date_match:
        # Extract the date from the partial_time
        date = date_match.group(1)
        # Create a pattern to match the full time based on the extracted date
        # The pattern looks for "at" or "on" followed by the time hh:mm
        full_time_pattern = re.escape(date) + r'\s+(at|on)\s+(\d{1,2}:\d{1,2})'
        full_time_match = re.search(full_time_pattern, sentence)

        if full_time_match:
            # Construct the full time string
            full_time_str = date + " " + full_time_match.group(1) + " " + full_time_match.group(2)
            return full_time_str

    # If no full time match is found, return the original partial_time
    return partial_time


def complete_organization(sentence, partial_name):
    for key in ORGANIZATIONKey:
        if key in sentence and key not in partial_name:
            # 构建正则表达式以匹配完整的组织名称
            pattern = r"\b" + re.escape(partial_name) + r".*?\b(?:" + "|".join(ORGANIZATIONKey) + r")\b"
            match = re.search(pattern, sentence)

            if not match:
                # 如果没有匹配，尝试只用 partial_name 的第一个词
                partial_name_first_word = partial_name.split(" ")[0]
                pattern = r"\b" + re.escape(partial_name_first_word) + r".*?\b(?:" + "|".join(ORGANIZATIONKey) + r")\b"
                match = re.search(pattern, sentence)

            return match.group(0) if match else partial_name

    return partial_name


def complete_patient(sentence, partial_word):
    # Create a pattern that matches the partial_word followed by any word characters until a space or end of string
    pattern = re.escape(partial_word) + r'\w*'
    match = re.search(pattern, sentence)
    return match.group(0) if match else partial_word

    
def content_revision(sentence, label_info):
    label_cat, label_content, _ = label_info

    if label_cat == "HOSPITAL":
        label_content = complete_hospital(sentence, label_content)
    elif label_cat == "TIME":
        label_content = complete_time_v1(sentence, label_content)
        label_content = complete_time_v2(sentence, label_content)
    elif label_cat == "PATIENT":
        label_content = complete_patient(sentence, label_content)
    elif label_cat == "ORGANIZATION":
        label_content = complete_organization(sentence, label_content)
    return (label_cat, label_content, "")


"""Remedy3: Detect content from sentence"""
def duration_detection(sentence):
    # Compile a regular expression pattern to match durations in the sentence
    duration_pattern = re.compile(
        r"(\b\d{1,2}-\d{1,2}\s*|\b\d+\s*)(day|week|month|year|dy|wk|mth|yr)s?\b(?!\s*old)", 
        re.IGNORECASE
    )

    matches = duration_pattern.findall(sentence)
    durations = []
    for match in matches:
        full_match = "".join(match).strip()
        age_pattern = r"\b" + re.escape(match[0]) + r"\s*" + re.escape(match[1]) + r"\s*old\b"
        if not re.search(age_pattern, sentence, re.IGNORECASE):
            durations.append(full_match)

    if durations:
        nums = re.findall(r"\b\d+\b", durations[0])
        if nums and int(nums[0]) <= 20:
            return durations[0]

def location_other_detection(sentence):
    # pattern = r"(P\.O\. BOX \d+|PO BOX \d+)"
    pattern = r"(P\.O\.\s+BOX \d+|PO\s+BOX \d+)"
    matches = re.findall(pattern, sentence, re.IGNORECASE)
    
    return matches[0] if matches else None

def country_detection(sentence):
    # 创建正则表达式模式以匹配国家列表中的任何国家名
    pattern = r'\b(?:' + '|'.join(re.escape(country) for country in CommonCountry) + r')\b'
    # 使用 re.IGNORECASE 使匹配对大小写不敏感
    matches = re.findall(pattern, sentence, re.IGNORECASE)
    
    return matches[0] if matches else None


def age_in_date_detection(sentence, infos):
    age = None
    if "Page: 2" in sentence:
        sentence = sentence.replace("Page: 2", "")
    if "DATE:" in infos and "AGE:" in infos:
        labels = extract_label_info(infos)
        for label in labels:
            cat, content, _ = label
            if cat == "DATE":
                sentence = sentence.replace(content, "")
            if cat == "AGE":
                age = content
        if age and age not in sentence:
            if "++AGE:" in infos:
                infos = infos.replace(f"++AGE:{age}", "")
            elif "AGE:" in infos:
                infos = infos.replace(f"AGE:{age}", "")
    return infos


def detection(sentence, infos):
    #duration detection
    duration = duration_detection(sentence)
    if duration:
        if duration + "s" in sentence:
            duration += "s"
        infos += f"++DURATION:{duration}"
    # location detection
    location_other = location_other_detection(sentence)
    if location_other:
        infos += f"++LOCATION-OTHER:{location_other}"
    # country detection
    country = country_detection(sentence)
    if country:
        infos += f"++COUNTRY:{country}"
    # age in date detection
    infos = age_in_date_detection(sentence, infos)
    return infos
    

"""Remedy4: Revise ORGANIZATION over recall"""
def entry_clean(entry):
    exclusion_list = ["Corporation", "Inc", "Company", "Companies", "Energy", "Power"]
    time_list = ["at", "on", "am", "pm", ":"]
    if "ORGANIZATION" in entry["output"] and not any(term in entry["output"] for term in exclusion_list):
        entry["count"] -= 1
    if "DATE" in entry["output"] and  any(term in entry["output"] for term in time_list):
        entry["count"] -= 1
    return entry if entry["count"] > 0 else None

if __name__ == "__main__":
    is_valid_label("DURATION", "18 months")