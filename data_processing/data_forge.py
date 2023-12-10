#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 20 13:39:42 2023

@author: huangpaveen
"""

import random
import re
from num2words import num2words


def calculate_range_mean(quantity, range_num):
    """
    Duration range normalization
    """
    if range_num % 2 == 0:
        mean = quantity + range_num // 2
    else:
        mean = quantity + (range_num / 2)

    return round(mean, 1) if range_num % 2 != 0 else mean


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


def check_label(sentence, label_infos):
    """
    check if label contents in nosied sentence
    """
    for _, label, _ in label_infos:
        if label not in sentence:
            return False
    return True


def add_random_noise(sentence, label_infos):
    """
    Add random noise between words in a sentence.
    """
    words = sentence.split(" ")
    add_times = int(len(words) * 0.15)  # Calculate based on the number of words

    for _ in range(add_times):
        insertion_index = random.randint(0, len(words) - 1)
        words.insert(insertion_index, "[ADDED NOISE]")

        temp_sentence = " ".join(words)
        if check_label(temp_sentence, label_infos):
            sentence = temp_sentence

    return sentence


def delete_random_part(sentence, label_infos):
    """
    Delete random words from a sentence.
    """
    words = sentence.split(" ")
    deletion_length = int(len(words) * 0.15)  # Calculate based on the number of words

    for _ in range(deletion_length):
        if len(words) <= 1:  # Prevent deleting all words
            break

        del_index = random.randint(0, len(words) - 1)
        temp_words = words[:del_index] + words[del_index + 1:]
        temp_sentence = " ".join(temp_words)

        if check_label(temp_sentence, label_infos):
            words = temp_words  

    return " ".join(words)


def get_noised_samples(file_id, start_pos, current_content, current_label, noised_samples):
    """
    get noised samples
    """
    label_infos = extract_label_info(current_label)
    enhanced_samples = []
    for _ in range(noised_samples // 2):
        added_content = add_random_noise(current_content, label_infos)
        enhanced_samples.append(f"{file_id}\t{start_pos}\t{added_content}\t{current_label}\n")
        deleted_content = delete_random_part(current_content, label_infos)
        enhanced_samples.append(f"{file_id}\t{start_pos}\t{deleted_content}\t{current_label}\n")
    return enhanced_samples


def generate_phone_numbers(num_samples=300):
    """
    Generate a list of Australian phone numbers for the 'PHONE' category
    """
    phone_numbers = []
    for _ in range(num_samples):
        # Generate two groups of four digits each
        part_one = "".join(random.choice("123456789") for _ in range(4))
        part_two = "".join(random.choice("123456789") for _ in range(4))
        number = part_one + " " + part_two if random.choice([True, False]) else part_one + part_two
        phone_numbers.append(number)

    return phone_numbers


def generate_po_boxes(num_samples=100):
    """
    generate po box numbers
    """
    po_boxes = []
    for _ in range(num_samples // 2):
        box_number = random.randint(1, 10000)  # 随机生成一个数字，作为信箱号
        po_box = f"P.O. BOX {box_number}"
        po_boxes.append(po_box)
    for _ in range(num_samples // 2):
        box_number = random.randint(1, 10000)  # 随机生成一个数字，作为信箱号
        po_box = f"PO BOX {box_number}"
        po_boxes.append(po_box)
    return po_boxes


def generate_duration_samples(num_samples=50):
    """
    generate duration samples
    """
    units = ["day", "week", "month", "year"]
    normalized_units = {"day": "D", "week": "W", "month": "M", "year": "Y"}
    abbreviations = {"day": "dy", "week": "wk", "month": "mth", "year": "yr"}

    samples = []
    normalized_samples = []

    for _ in range(num_samples // 8):
        quantity = random.randint(1, 50)  # Assuming you want durations from 1 to 10
        range_num = random.randint(1, 5)
        unit = random.choice(units)
        num_word = num2words(quantity)
        tmps = []
        tmps_range = []
        word_full = f"{num_word} {unit}"
        num_full = f"{quantity} {unit}"
        num_abbr = f"{quantity} {abbreviations[unit]}"
        range_num_full = f"{quantity}-{quantity+range_num} {unit}"
        range_num_abbr = f"{quantity}-{quantity+range_num} {abbreviations[unit]}"
        if quantity == 1:
            tmps += [word_full, num_full, num_abbr]
            tmps_range += [range_num_full, range_num_abbr]
        elif quantity > 1 and quantity <= 10:
            tmps += [word_full, num_full, num_abbr]
            tmps_range += [range_num_full, range_num_abbr]
            tmps += [word_full + "s", num_full + "s", num_abbr + "s"]
            tmps_range += [range_num_full + "s", range_num_abbr + "s"]
        elif quantity > 10:
            tmps += [num_full, num_abbr]
            tmps_range += [range_num_full, range_num_abbr]
            tmps += [num_full + "s", num_abbr + "s"]
            tmps_range += range_num_full + "s", range_num_abbr + "s"

        # Generate normalized form
        normalized = f"P{quantity}{normalized_units[unit]}"
        range_mean = calculate_range_mean(quantity, range_num)
        normalized_range = f"P{range_mean}{normalized_units[unit]}"
        normalized_samples += [normalized] * len(tmps)
        normalized_samples += [normalized_range] * len(tmps_range)
        samples += tmps
        samples += tmps_range

    return samples, normalized_samples


def generate_set_samples(num_samples=100):
    # 定义频率和其标准化形式的映射
    frequency_map = {
        "once": "R1",
        "twice": "R2",
        "three times": "R3",
        "four times": "R4",
        "five times": "R5",
        "six times": "R6",
        "seven times": "R7",
        "eight times": "R8",
        "nine times": "R9",
        "ten times": "R10",
        # 更多频率和对应标准化形式可以根据需要添加
    }

    set_samples = []
    for _ in range(num_samples):
        # 从映射中随机选择一个频率及其标准化形式
        freq_word, normalized_freq = random.choice(list(frequency_map.items()))

        # 构建样本
        sample = f"SET:{freq_word} => {normalized_freq}\n"
        set_samples.append(sample)
    return set_samples



def generate_countries():
    """
    get normal countries list
    """
    return [
        "United States", "Canada", "Germany", "France", "China", "Japan", "United Kingdom", 
        "India", "Brazil", "South Africa", "Indonesia", "Pakistan", "Nigeria", "Bangladesh", 
        "Russia", "Mexico", "Ethiopia", "Philippines", "Egypt", "Vietnam", 
        "Democratic Republic of Congo", "Turkey", "Iran", "Thailand", "Italy", 
        "Tanzania", "Myanmar", "Kenya", "South Korea", "Colombia", "Spain", "Uganda", 
        "Argentina", "Algeria", "Sudan", "Ukraine", "Iraq", "Afghanistan", "Poland",
        "Morocco", "Saudi Arabia", "Uzbekistan", "Peru", "Angola", "Malaysia", "Mozambique", 
        "Ghana", "Yemen", "Nepal", "Venezuela", "American"]


def generate_organization_names(num_samples=100):
    """
    fake company names
    """
    name_components = [
        "Global", "United", "American", "Pacific", "National", "Enterprise",
        "International", "Tech", "Innovations", "Solutions", "Media",
        "Industries", "Motors", "Electric", "Software", "Networks",
        "Communications",  "Insurance", "Pharmaceuticals", "Corporation",
        "Group", "Holdings",  "Systems", "Materials", "Properties", "Healthcare",
        "Financial" ]
    company_types = ["Inc", "LLC", "Group", "Ltd", "Corporation", "Co", "PLC", "GmbH"]

    # Generate random organization names
    organization_names = []
    for _ in range(num_samples):
        name = " ".join(random.sample(name_components, random.randint(1, 3)))  
        company_type = random.choice(company_types)
        organization_name = f"{name} {company_type}"
        organization_names.append(organization_name)

    return organization_names


def enhance_phone_number(file_id, start_pos, current_content, current_label, label_content, num_samples=300):
    """
    enhance phone samples by random noise and fake samples
    """
    enhanced_samples = []
    noised_samples = int(num_samples * 0.2)
    generagted_samples = int(num_samples * 0.8)

    # add random noise
    enhanced_samples += get_noised_samples(
        file_id, start_pos, current_content, current_label, noised_samples // 2
    )

    # generate forged samples
    original_number = label_content
    generated_numbers = generate_phone_numbers(generagted_samples)
    for new_number in generated_numbers:
        new_content = current_content.replace(original_number, new_number)
        new_label = current_label.replace(original_number, new_number)
        generated_pair = f"{file_id}\t{start_pos}\t{new_content}\t{new_label}\n"
        enhanced_samples.append(generated_pair)
    return enhanced_samples


def enhance_country(file_id, start_pos, current_content, current_label, label_content, num_samples=500):
    """
    enhance country samples by random noise and fake samples
    """
    enhanced_samples = []
    country_list = generate_countries()
    # count number of samples
    num_noised = int(num_samples * 0.4)
    num_generated = num_samples - num_noised
    num_repeat = num_generated // len(country_list)

    # add random noise
    enhanced_samples += get_noised_samples(file_id, start_pos, current_content, current_label, num_noised)

    original_country = label_content
    for new_country in country_list:
        # replace original country
        new_content = current_content.replace(original_country, new_country)
        new_label = current_label.replace(original_country, new_country)
        enhanced_samples.append(f"{file_id}\t{start_pos}\t{new_content}\t{new_label}\n")
        # generate noise samples after replacement
        enhanced_samples += get_noised_samples(file_id, start_pos, new_content, new_label, num_repeat)

    return enhanced_samples


def enhance_location_other(
    file_id, start_pos, current_content, current_label, label_content, num_samples=300
):
    """
    enhance location_other samples by random noise and fake samples
    """
    enhanced_samples = []
    original_location = label_content
    if (
        "box" in original_location.lower()
        or "po" in original_location.lower()
        or "p.o." in original_location.lower()
    ):
        generation_samples = int(num_samples * 0.5)
        num_samples -= generation_samples
        location_other_list = generate_po_boxes(generation_samples)
        for new_location in location_other_list:
            new_content = current_content.replace(original_location, new_location)
            new_label = current_label.replace(original_location, new_location)
            generated_pair = f"{file_id}\t{start_pos}\t{new_content}\t{new_label}\n"
            enhanced_samples.append(generated_pair)

    enhanced_samples += get_noised_samples(file_id, start_pos, current_content, current_label, num_samples)

    return enhanced_samples


def enhance_duration_and_normalized(
    file_id,
    start_pos,
    current_content,
    current_label,
    label_content,
    label_norm,
    num_samples=100,
    normalize=False,
):
    """
    enhance duration samples and normalized samples by random noise and fake samples
    """
    enhanced_samples = []
    generated_samples = int(num_samples * 0.7)
    noised_samples = num_samples - generated_samples
    # add noise or delete scocasticly
    enhanced_samples += get_noised_samples(
        file_id, start_pos, current_content, current_label, noised_samples
    )

    # generate fake duration
    samples, normalized_samples = generate_duration_samples(generated_samples)
    original_duration = label_content
    original_duration_norm = label_norm

    for duration, normalized_duration in zip(samples, normalized_samples):
        new_content = current_content.replace(original_duration, duration)
        new_label = current_label.replace(original_duration, duration)
        if normalize:
            new_label = new_label.replace(original_duration_norm, "=>" + normalized_duration)
        new_entry = f"{file_id}\t{start_pos}\t{new_content}\t{new_label}\n"
        enhanced_samples.append(new_entry)

    return enhanced_samples


def enhance_organization(file_id, start_pos, current_content, current_label, label_content, num_samples=50):
    """
    enhance organization samples and normalized samples by random noise and fake samples
    """
    enhanced_samples = []
    generation_samples = int(num_samples * 0.5)
    noised_samples = num_samples - generation_samples
    # add random noise
    enhanced_samples += get_noised_samples(
        file_id, start_pos, current_content, current_label, noised_samples
    )

    # generate samples
    original_organization = label_content
    organization_list = generate_organization_names(generation_samples)
    for new_organization in organization_list:
        new_content = current_content.replace(original_organization, new_organization)
        new_label = current_label.replace(original_organization, new_organization)
        generated_pair = f"{file_id}\t{start_pos}\t{new_content}\t{new_label}\n"
        enhanced_samples.append(generated_pair)
    return enhanced_samples


def enhance_set(file_id, start_pos, current_content, current_label, num_samples=20):
    """
    enhance set samples and normalized samples by random noise
    """
    enhanced_samples = get_noised_samples(file_id, start_pos, current_content, current_label, num_samples)
    return enhanced_samples
