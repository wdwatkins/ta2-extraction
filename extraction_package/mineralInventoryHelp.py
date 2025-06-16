"""
Copyright © 2023-2024 InferLink Corporation. All Rights Reserved.

Distribution authorized to U.S. Government only; Proprietary Information, September 22, 2023. Other requests for this document shall be referred to the DoD Controlling Office or the DoD SBIR/STTR Program Office.

This Data developed under a SBIR/STTR Contract No 140D0423C0093 is subject to SBIR/STTR Data Rights which allow for protection under DFARS 252.227-7018 (see Section 11.6, Technical Data Rights). 
"""
import warnings
import requests
import copy
import logging
from settings import CATEGORY_VALUES,  MINMOD_URL, STRUCTURE_MODEL, WORKING_DIR

import extraction_package.schemaFormat as schemas
import extraction_package.genericFunctions as generic
import extraction_package.LLMFunctions as llm
import extraction_package.extractionPrompts as prompts
import extraction_package.LLMmodels as model



# Ignore the specific UserWarning from openpyxl
warnings.filterwarnings(action='ignore', category=UserWarning, module='openpyxl')

logger = logging.getLogger(__name__)



def create_mineral_inventory(file_path, document_dict, table_pages):
    
    commodities, correct_units = create_minmod_dict()
    mineral_inventory_json = {"mineral_inventory":[]}
    table_window = generic.generate_sliding_windows(table_pages)
    full_text = generic.return_pages_of_text(table_window, file_path)
    try:
        doc_year = int(document_dict['year'])
    except:
        # if no doc year just set to 0 so all tables are larger than this
        doc_year = 0

    ## first call and do the extractions & then develop the format
    tables = llm.get_gpt_response(prompts.find_relevant_table_instructions + full_text, STRUCTURE_MODEL, model.RelevantTableSchema.model_json_schema())
    logger.debug(f"Here are the tables: {tables}")
    
    
    for table in tables['tables']:
        logger.debug(f"Looking at table: {table} vs {doc_year}\n")
        try:
            table_year = int(table['tableYear'])
        except (ValueError, TypeError, KeyError):
            table_year = None
            
        if table_year is None or table_year + 3 >= doc_year:
            logger.debug(f"Looking at table: {table['tableName']}")
            resp = llm.get_gpt_response(prompts.extract_rows_from_tables.replace("__TABLE_NAME__", table['tableName']).replace("__COMMODITY_LIST__", str(table['commodities'])) + full_text, STRUCTURE_MODEL, model.MineralExtractionSchema.model_json_schema())
            logger.debug(f'here is the resp: {resp} \n')
            this_table_page = generic.find_correct_page(file_path, resp['extractions'], table_pages)
            logger.debug(f"Table can be found on page: {this_table_page} ")
            ## clean up values and then add to mineral_inventory_json
            ## check the overal windows to see where this table Name is. 
            for output in resp['extractions']:
                commodity = output['commodity'].lower()
                logger.debug(f"Looking at commodity: {commodity}")
                inventory_format = schemas.create_inventory_format(commodities, commodity, document_dict)
                cleaned = create_mineral_inventory_json(output, inventory_format, correct_units, file_path, this_table_page)
                logger.info(f"Cleaned output: {cleaned}")
                mineral_inventory_json["mineral_inventory"].append(cleaned)
                
   
        logger.debug(f"Here is the mineral inventory json: \n {mineral_inventory_json}")

    return mineral_inventory_json

def clean_commodities(commodity_list, acceptable_commodities):
    final_list = []
    for comm in commodity_list:
        if comm in acceptable_commodities:
            final_list.append(comm)
            
    return final_list
    



def create_mineral_inventory_json(extraction_dict, inventory_format, unit_dict, file_path, this_table_page):
    current_inventory_format = copy.deepcopy(inventory_format)
    logger.debug(f"Extraction dict passed: {extraction_dict}")
    
    for key, value in extraction_dict.items():
       
        
        if not isinstance(value, str):
            value = str(value)
            if value.lower() == "none":
                value = ''
        
        if 'category' in key:
            current_inventory_format = check_category(current_inventory_format, MINMOD_URL, value)
            
        elif 'zone' in key:
            ## cannot have an empty zone
            if value:
                current_inventory_format['zone'] = value.lower()
            else: current_inventory_format.pop('zone')
            
        elif 'chemical' in key:
            current_inventory_format = check_material_form(current_inventory_format, MINMOD_URL, value)
        
        elif 'cut' in key.lower() and 'unit' not in key.lower():
            current_inventory_format['cutoff_grade']['grade_value'] = value.lower()
            current_inventory_format['cutoff_grade'] = generic.check_instance(current_extraction=current_inventory_format['cutoff_grade'], key = 'grade_value', instance=float)
                                    
        elif 'cut' in key.lower() and 'unit' in key.lower():
            current_inventory_format = check_cutoff_grade_unit(current_inventory_format, value, unit_dict)
            
        elif 'tonnage' in key.lower() and 'unit' not in key.lower():
            value = value.replace(",", "")
            current_inventory_format['ore']['value'] = value.lower()
            current_inventory_format['ore'] = generic.check_instance(current_extraction=current_inventory_format['ore'], key = 'value', instance=float)
            
            
        elif 'tonnage' in key.lower() and 'unit' in key.lower():
           
            current_inventory_format = check_tonnage_unit(current_inventory_format, value, unit_dict)

        elif 'grade' in key.lower() and 'unit' in key.lower():
            if value == "":
                current_inventory_format['grade'].pop('grade_unit')
            else:
                current_inventory_format['grade']['grade_unit'] = {}
                current_inventory_format['grade']['grade_unit']['normalized_uri'] = ""
                grade_unit_list = list(unit_dict.keys())
                
                if value == "%":
                    current_inventory_format['grade']['grade_unit']['normalized_uri'] = MINMOD_URL + unit_dict['percent'] 
                else:
                    found_value = generic.find_best_match(value, grade_unit_list) 
                    if found_value is not None:
                        current_inventory_format['grade']['grade_unit']['normalized_uri'] = MINMOD_URL + unit_dict[found_value]           
                
                current_inventory_format['grade']['grade_unit'] = generic.add_extraction_dict(value, current_inventory_format['grade']['grade_unit'])
                
        elif 'grade' in key.lower() and 'unit' not in key.lower():
            
            current_inventory_format['grade']['grade_value'] = validate_grade_value(value, unit=current_inventory_format['grade']['grade_unit'])
            current_inventory_format['grade'] = generic.check_instance(current_extraction=current_inventory_format['grade'], key = 'grade_value', instance=float)
            
        elif 'table' in key.lower():
            ## update to also look for category and tonnage_value
            if this_table_page:
                current_inventory_format['reference']['page_info']= []
                current_inventory_format['reference']['page_info'].append({'page': this_table_page})
            logger.debug("ended table")       
            
        logger.debug(f"Finished key: {key}")
        
    current_inventory_format = check_empty_headers_add_contained_metal(current_inventory_format)        
        
    return current_inventory_format


def validate_grade_value(value, unit=None):
    try:
        # Convert to float
        numeric_value = float(value)
        
        if (0 <= numeric_value <= 1) or (numeric_value.is_integer() and numeric_value < 100):
            if unit and unit.lower() == "percentage" and numeric_value > 1:
                return "" 
            return value.lower()
    except ValueError:
        pass

    return "" 

def check_cutoff_grade_unit(curr_json, value, unit_dict):
    ## need to change the method of doing this as well for doing the unit to follow new schema
    
    if value.strip() == "":
        # logger.debug("No cutoff_grade")
        curr_json['cutoff_grade'].pop('grade_unit')
        
    else:
        curr_json['cutoff_grade']['grade_unit'] = {}
        curr_json['cutoff_grade']['grade_unit']['normalized_uri'] = ""
        
        if value == '%':
            curr_json['cutoff_grade']['grade_unit']['normalized_uri'] = MINMOD_URL + unit_dict['percent']
        
        elif value:
            grade_unit_list = list(unit_dict.keys())
            found_value = generic.find_best_match(value, grade_unit_list)

            # logger.debug(f"found_value: {found_value}")
            if found_value is not None:
                # can check of the new new format
                curr_json['cutoff_grade']['grade_unit']['normalized_uri'] = MINMOD_URL + unit_dict[found_value]
        
        # logger.debug(f"check cutoff grade Current json: {curr_json['cutoff_grade']}")
        curr_json['cutoff_grade']['grade_unit'] = generic.add_extraction_dict(value, curr_json['cutoff_grade']['grade_unit'])
         
    return curr_json




def check_tonnage_unit(curr_json, value, unit_dict):
    kt_values = ["k","kt", "000s tonnes", "thousand tonnes", "thousands", "000s" , "000 tonnes", "ktonnes"]
    grade_unit_list = list(unit_dict.keys())
    curr_json['ore']['ore_unit'] = {}
    curr_json['ore']['ore_unit']['normalized_uri'] = ""
    
    if value == "":
        curr_json['ore'].pop('ore_unit')
    else:
        
        if value.lower() in kt_values:
                if curr_json['ore']['value']: 
                    try:
                        float_val = float(curr_json['ore']['value']) * 1000
                        curr_json['ore']['value'] =  float_val
                        curr_json['ore']['ore_unit']['normalized_uri'] = MINMOD_URL + unit_dict["tonnes"]
                        
                    except ValueError:
                        logger.error(f"Got Type Error for : {curr_json['ore']['value']}")
                        
        else:
            found_value = generic.find_best_match(value, grade_unit_list)
            if found_value is not None:
                # logger.debug(f"Found match value for ore_unit {found_value}")
                curr_json['ore']['ore_unit']['normalized_uri'] = MINMOD_URL + unit_dict[found_value]
        
        curr_json['ore']['ore_unit'] = generic.add_extraction_dict(value, curr_json['ore']['ore_unit'])
            
                
    return curr_json

def check_category(current_json, MINMOD_URL, value):
    ## update categories
    current_json['category'] = []
                     
    if value.lower() in CATEGORY_VALUES:
        if "+" in value.lower():
            new_vals = value.lower().split("+")
            for val in new_vals:
                inner_dict = {"normalized_uri": MINMOD_URL + val.capitalize()}
                inner_dict = generic.add_extraction_dict(value, inner_dict)
                current_json['category'].append(inner_dict)
        else:
            inner_dict = {"normalized_uri": MINMOD_URL + value.capitalize()}
            inner_dict = generic.add_extraction_dict(value, inner_dict)
            current_json['category'].append(inner_dict)
            
    
    return current_json


def create_minmod_dict():
    minmod_commodities = generic.read_csv_to_dict(f"{WORKING_DIR}/codes/minmod_commodities.csv")
    commodities = {}
    for key in minmod_commodities:
        commodities[key['CommodityinGeoKb'].lower()] = key['minmod_id']
        
    minmod_units = generic.read_csv_to_dict(f"{WORKING_DIR}/codes/minmod_units.csv")
    correct_units = {}
    for key in minmod_units:
        correct_units[key['unit name']] = key['minmod_id']
        correct_units[key['unit aliases']] = key['minmod_id']

    return commodities, correct_units


def check_empty_headers_add_contained_metal(extraction):
    keys_to_check = ["ore", "grade", "cutoff_grade"]
    logger.debug(f"Starting extraction for check empty & add {extraction}")
    
    for key in keys_to_check:
        logger.debug(f"Checking key {key} with values {extraction[key]}")
        if not extraction[key]:
            logger.debug("Going to pop it")
            extraction.pop(key)
            logger.debug("Currently this value is empty")
            
    # logger.debug(f"Already checked all keys: extraction now: {extraction}")
    
    if extraction.get("ore", {}).get("value", None):
        value = extraction["ore"]["value"]
    else: value = None

    
    if extraction.get("grade", {}).get("grade_value", None):
        grade_value = extraction["grade"]["grade_value"]
    else: grade_value = None 
    
    if  value and grade_value:
        try:
            extraction["contained_metal"] = round(value*(grade_value/100), 4)
        except ValueError:
            logger.error(f"Get ValueError in check empty headers for value: {value} or grade_value {grade_value}")
            extraction.pop("contained_metal")
    else:
        extraction.pop("contained_metal")
        
    # logger.debug(f"Here is the extraction post contained metal: {extraction}")
    return extraction


def check_material_form(curr_json, MINMOD_URL, value):
    if len(value) == 0:
        curr_json.pop('material_form')
        return curr_json
    
    curr_json['material_form'] = {"normalized_uri": ""}
    
    # logger.debug(f"Here is curr_json {curr_json}")
    material_form_picklist = generic.read_csv_to_dict(f"{WORKING_DIR}/codes/material_form.csv")
    
    options = {}
    for item in material_form_picklist:
        options[item['name']] = item['id']
        options[item['formula']] = item['id']
        
    found_value = generic.find_best_match(value, list(options.keys()))
    if found_value is not None:
        logger.debug(f"Found match value for material_form {found_value}")
        curr_json['material_form']['normalized_uri'] = MINMOD_URL + options[found_value]
        
    curr_json['material_form'] = generic.add_extraction_dict(value, curr_json['material_form'])
    
    # logger.debug(f"Here is the curr_json in the file: {curr_json}")
    
    return curr_json
    
def post_process(curr_json):
    inner_list = curr_json['mineral_inventory']
    
    for inner_dict in inner_list:
        # Check if 'material_form' is an empty string and remove it
        if inner_dict.get('material_form') == "":
            inner_dict.pop('material_form', None)
        
        if 'zone' in inner_dict and not isinstance(inner_dict['zone'], str):
            inner_dict['zone'] = str(inner_dict['zone'])
        
        # Process each key in the inner dictionary
        for key in inner_dict:
            # Process 'ore', 'grade', and 'cutoff_grade'
            if key in ['ore', 'grade', 'cutoff_grade']:
                new_dict = {}
                for inner_key in inner_dict[key]:
                    new_dict['unit'] = {}
                    new_dict['value'] = {}
                    
                    # Extract 'unit' and 'value' if they exist in the inner key
                    if 'unit' in inner_key:
                        new_dict['unit'] = inner_dict[key][inner_key]
                    if 'value' in inner_key:
                        new_dict['value'] = inner_dict[key][inner_key]

               
               
                if not new_dict['unit']:
                    new_dict.pop('unit')
                if not new_dict['value']:
                    new_dict.pop('value')
             
                inner_dict[key] = new_dict

           
            for nested_key, nested_value in inner_dict.items():
                if isinstance(nested_value, dict): 
                    for sub_key in nested_value:
                        if sub_key == 'observed_name':
                            nested_value[sub_key] = str(nested_value[sub_key])
                            if nested_value[sub_key] == "":
                                nested_value.pop(sub_key)
                        if sub_key == 'normalized_uri':
                            nested_value[sub_key] = str(nested_value[sub_key])
                            

    return curr_json