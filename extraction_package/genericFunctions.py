"""
Copyright © 2023-2024 InferLink Corporation. All Rights Reserved.

Distribution authorized to U.S. Government only; Proprietary Information, September 22, 2023. Other requests for this document shall be referred to the DoD Controlling Office or the DoD SBIR/STTR Program Office.

This Data developed under a SBIR/STTR Contract No 140D0423C0093 is subject to SBIR/STTR Data Rights which allow for protection under DFARS 252.227-7018 (see Section 11.6, Technical Data Rights). 
"""

import json
import warnings
import re
import csv
import PyPDF2
from fuzzywuzzy import process
from settings import SYSTEM_SOURCE, VERSION_NUMBER, CDR_BEARER, CDR_ENDPOINT
from old_extraction_package_v2.ExtractPrompts import *
import logging
from collections import Counter
import requests

# Get logger
logger = logging.getLogger(__name__)

warnings.filterwarnings(action='ignore', category=UserWarning, module='openpyxl')

def download_document(doc_id, download_dir):
    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer '+ CDR_BEARER
    }

    url_pdf = f'{CDR_ENDPOINT}/docs/document/{doc_id}'
    url_meta = f'{CDR_ENDPOINT}/docs/document/meta/{doc_id}'
    # logger.debug(f"in download document CDR Bearer: {CDR_BEARER}")

    # Send the initial GET request
    response = requests.get(url_meta, headers=headers)
    logger.info(f"Meta doc status code: {response.status_code}")
    if response.status_code == 200:
        # Save the response content to a file
        resp_json = json.loads(response.content)
        title = resp_json['title']
        
        response = requests.get(url_pdf, headers=headers)

        if response.status_code == 200:    
            with open(f'{download_dir}{doc_id}_{title}.pdf', 'wb') as file:
                file.write(response.content)
            logger.info(f"Document downloaded and saved as '{title}.pdf'")
            return f"{doc_id}_{title}.pdf"
        else:
            logger.info(f"Failed to download document. Status code: {response.status_code}")
            return None
    else:
        logger.info(f"Failed to get meta data. Status code: {response.status_code}")
        logger.info(f"Response content: {response.content}")
        return None
      

def append_section_to_JSON(file_path, header_name, whole_section):
    logger.debug(f"Writing {header_name}")
    
    json_schema = whole_section
    # logger.debug(f"Json Schema before write: {json_schema}")
    with open(file_path, "w") as json_file:
        json.dump(convert_int_or_float(json_schema), json_file, indent=2)
        
def generate_sliding_windows(pages):
    # pages = get_pages_with_tables(filepath)
    
    if not pages:
        return []

    pages = sorted(pages)
    windows = []
    
    current_window = [pages[0]]
    
    for i in range(1, len(pages)):
        if pages[i] == current_window[-1] + 1:
            current_window.append(pages[i])
        else:
            windows.append(current_window)
            current_window = [pages[i]]
    
    # Append the last window
    windows.append(current_window)
    
    expanded_windows = []
    for window in windows:
        start = window[0] - 1
        end = window[-1] + 1
        if end < len(pages):
            expanded_windows.append(list(range(start, end+1)))
        else:
            expanded_windows.append(list(range(start, end)))
    
    return expanded_windows

def return_pages_of_text(windows, filepath):
    full_text = ""
    with open(filepath, 'rb') as file:
            
            # Create a PDF reader
            pdf = PyPDF2.PdfReader(file)
            
            # Iterate over each page
            for window in windows:
                for page_num in window:
                    if page_num < len(pdf.pages):
                        page = pdf.pages[page_num]
                        full_text += page.extract_text() + "\n" 
    return full_text

def convert_int_or_float(obj):
    if isinstance(obj, dict):
        return {key: convert_int_or_float(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_int_or_float(item) for item in obj]
    elif isinstance(obj, (int, float)):
        return obj
    elif isinstance(obj, str) and obj.isdigit():
        return int(obj)
    elif isinstance(obj, str) and obj.replace('.', '', 1).isdigit():
        return float(obj)
    return obj

def read_csv_to_dict(file_path):
    data_dict_list = []
    
    with open(file_path, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        
        for row in csv_reader:
            data_dict_list.append(dict(row))
    
    return data_dict_list


def find_best_match(input_str, list_to_match, threshold=75):
    # Get the best match and its score
    best_match, score = process.extractOne(input_str, list_to_match)

    # Check if the score is above the threshold
    if score >= threshold:
        return best_match
    else:
        return None
    
    
def add_extraction_dict(value, inner_json):
    logger.debug(f"In the inner dict function: {inner_json}")
    if not inner_json['normalized_uri']:
        inner_json.pop('normalized_uri')
        
        
    inner_json['observed_name'] = value
    inner_json['confidence'] = 1 
    inner_json['source'] = SYSTEM_SOURCE + " " + VERSION_NUMBER  
    logger.debug(f"after extraction_dict: {inner_json}")
    return inner_json


def string_in_page(pdf_path, target_string, check_pages):
    page_numbers = []
    # Open the PDF file in binary mode
    if not check_pages:
        return page_numbers

    with open(pdf_path, 'rb') as file:
        
        # Create a PDF reader
        pdf = PyPDF2.PdfReader(file)
        
        # Iterate over each page
        for page_num in check_pages:
            page = pdf.pages[page_num]
            text = page.extract_text()
            text_new = ' '.join(text.replace("\t", " ").split()).lower()
            # Check if target string is in the page's text
            if target_string.lower() in text_new:
                page_numbers.append(page_num) 
    logger.debug(f"In string in page: heres the number: {page_numbers}")     
    return page_numbers

def check_numbers(text_count, target_count):
    text_counter = Counter(text_count)
    target_counter = Counter(target_count)
    for num, count in target_counter.items():
        if text_counter[num] < count:
            return False
    return True

def extract_all_integers_in_page(pdf_path, target_list, check_pages):
    page_numbers = []
    # Open the PDF file in binary mode
    if not check_pages:
        return page_numbers

    with open(pdf_path, 'rb') as file:
        
        # Create a PDF reader
        pdf = PyPDF2.PdfReader(file)
        
        # Iterate over each page
        for page_num in check_pages:
            page = pdf.pages[page_num]
            text = page.extract_text()
            text_new = ' '.join(text.replace("\t", " ").split()).lower()
            integers_in_text = re.findall("[0-9]", text_new)
            # logger.debug(f"integers in text: {integers_in_text} & target_list {target_list}")
            if check_numbers(integers_in_text, target_list):
                page_numbers.append(page_num)

          
    return page_numbers

def find_correct_page(file_path, extractions, table_pages):
 
    target_strings = set()
    target_integers = []
    
    for inner_dict in extractions:
        for key, value in inner_dict.items():
            # logger.debug(f"key: {key}: {value}")
            if key != "commodity":
                
                if isinstance(value, str) and len((value)) > 0 and len(target_strings) < 6:
                    target_strings.add((value))
                    target_integers+= [i for i in re.sub(r'[^\d]', '', value)]
                    logger.debug(f"adding target integers: {target_integers}")
                elif isinstance(value, (int, float)) and len(target_integers) < 15:
                    # adding integers, first clean
                    target_integers += [i for i in re.sub(r'[^\d]', '', str(value))]
                
                
    logger.debug(f"target_strings: {target_strings} target_integers: {target_integers}")

    matching_pages = {}
    
    for string in target_strings:
        matching_pages[string] = string_in_page(file_path, string, table_pages)

    pages_with_integers = extract_all_integers_in_page(file_path, target_integers, table_pages)   
                
    logger.debug(f"Here are the papers: {matching_pages}, {pages_with_integers}")
    all_pages = sum(matching_pages.values(), []) + pages_with_integers
    page_counts = Counter(all_pages)
    logger.debug(f"page_counts: {page_counts}")
    # Find the page with the highest count
    most_common_page, most_common_count = page_counts.most_common(1)[0]
    
    logger.debug(f"Matching pages: {most_common_page}")
    
    return most_common_page
    

    
def check_instance(current_extraction, key, instance):
    # logger.debug(f"Previous value: {current_extraction[key]}")
    output_value = None
    
    if key in current_extraction:
        curr_value = current_extraction[key]
        logger.debug(f"Looking at key {key} : {curr_value}")
        
        ## want to test the current value or if its 0
        if isinstance(curr_value, str) and len(curr_value) == 0:
            ## in case we have an empty value should pop that value out
            logger.debug("The value is empty")
            output_value = None
        
        elif instance == float and isinstance(curr_value, str):
            # if its a float we want to change the string to the correct float value
            logger.debug(f"Original value: {curr_value} \n")
            
            curr_value = current_extraction[key]
            numeric_chars = re.findall(r'[\d.]+', curr_value)
            str_value = ''.join(numeric_chars)
        
            try:
                output_value = float(str_value)
                logger.debug(f"Updated value: {output_value}")
                
            except ValueError:
                logger.error(f"Get value error for {curr_value} instance {instance} \n")
                
        
        elif isinstance(curr_value, instance):
            # if it is the correct instance type
            logger.debug(f"MATCH: curr_value {curr_value} instance {instance} \n")
            if instance == list and len(current_extraction[key]) == 0:
                output_value = None
            else:
                output_value = current_extraction[key]
        else:
            try:
            # testing the current value as the instance
                output_value = instance(curr_value)
        
            except ValueError:
                logger.error(f"Get value error for {curr_value} instance {instance} \n")
    
    if output_value is None:
        current_extraction.pop(key)
    else:
        current_extraction[key] = output_value
    
    
    logger.debug(f"check_instance: Final cleaned instance {current_extraction} \n")
    return current_extraction
                