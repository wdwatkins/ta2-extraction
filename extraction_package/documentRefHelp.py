import logging
import warnings
import extraction_package.extractionPrompts as prompts
import extraction_package.LLMmodels as model
import extraction_package.LLMFunctions as llmFunc
import extraction_package.genericFunctions as generic
import extraction_package.schemaFormat as schema
import re
import pandas as pd
from settings import MINI_MODEL, STRUCTURE_MODEL, MINMOD_URL, VERSION_NUMBER, SYSTEM_SOURCE, WORKING_DIR



# Get the logger specified in the file
logger = logging.getLogger(__name__)

# Ignore the specific UserWarning from openpyxl
warnings.filterwarnings(action='ignore', category=UserWarning, module='openpyxl')


def extractDocRefandMineralSite(TOC_pages, filepath, record_id, title):
    logger.debug("In the extract Doc Ref and Mineral Site")
    
    
    first_ten_not_TOC = []
    current_number = 0
    while len(first_ten_not_TOC) < 10:
        if first_ten_not_TOC not in TOC_pages:
            first_ten_not_TOC.append(current_number)
        current_number += 1

    first_10_pg = generic.return_pages_of_text([first_ten_not_TOC], filepath)

    resp = llmFunc.get_gpt_response(prompts.DocRefprompt + first_10_pg, MINI_MODEL, model.DocRefandLocationInfo.model_json_schema())
    
    document_ref, mineral_site = generateReferenceAndSite(resp, record_id, title)
    
    return document_ref, mineral_site


def generateReferenceAndSite(response, record_id, title):
    document_ref_schema = schema.created_document_ref(record_id, title)
    mineral_site_schema = schema.create_mineral_site(record_id)
    
    
    document_ref = clean_keys(document_ref_schema, response)
    mineral_site = clean_keys(mineral_site_schema, response)
    mineral_site = normalize_mineral_site(mineral_site)
    logger.debug(f"Returning the dictionary like: \n {document_ref}\n{mineral_site}")
    
    return document_ref, mineral_site

def clean_keys(original_dict, response):
    logger.debug("Cleanning the keys: ")
    logger.debug(f"Starting the dictionary like: \n {original_dict}\n response:\n{response}")
    output_dict = {}
    for key in original_dict.keys():
        logger.debug(f'Looking at key: {key}')
        
        if isinstance(original_dict[key], dict):
            # to get the nested key
            output_dict[key] = {}
            logger.debug(f"cleaning the key: {key}")
            for inner_key in original_dict[key]:
                if inner_key in response:
                    if len(str(response[inner_key])) > 0:
                        output_dict[key][inner_key] = response[inner_key]
                   
        elif isinstance(original_dict[key], (str, list)) and key in response:
            if len(str(response[key])) > 0:
                output_dict[key] = response[key]
                
        elif isinstance(original_dict[key], (str, list)) and len(original_dict[key]) > 0:
            output_dict[key] = original_dict[key]
            
      
    return output_dict
                    
def normalize_mineral_site(dictionary):
    logger.debug("Normalizing the values")
    drop_location = False
    
    for key, new_value in dictionary["location_info"].items():
        logger.debug(f"Normalizing the key: {key}: {new_value}")
        if key == 'crs':
            minmod_epsg = generic.read_csv_to_dict(f"{WORKING_DIR}/codes/epsg.csv")
            epsg_dict = {item['name']: item['minmod_id'] for item in minmod_epsg}
            logger.debug(f'epsg: {epsg_dict}')
            normalized_value = generic.find_best_match(new_value, list(epsg_dict.keys()), threshold=75)
            
            logger.debug(f"normalized: {normalized_value}")
            dictionary["location_info"][key] = {'normalized_uri': MINMOD_URL + epsg_dict[normalized_value]}
            dictionary["location_info"][key] = generic.add_extraction_dict(new_value, dictionary["location_info"][key] )
                       
        if key == 'country':
            # need to cycle through and send the list of countries
            country_temp = []
            dictionary["location_info"][key] = []
            logger.debug(f"List of countries: {new_value}")
            for inner_value in new_value:
                logger.debug(f"Looking at the countries: appending value: {inner_value}")        
                output, noramlized_country = add_country_or_state("country.csv", key, inner_value, None)
                dictionary["location_info"][key].append(output)
                if noramlized_country:
                    country_temp.append(noramlized_country)
            logger.debug(f"normalized_country: {country_temp}")
                
        if key == 'state_or_province':
            logger.debug(f"List of state_or_province: {new_value}")
            dictionary["location_info"][key] = []
            for inner_value in new_value:
                logger.debug(f"inner value: {inner_value}")
                output, _ = add_country_or_state("state_or_province.csv", key, inner_value, country_temp)
                dictionary["location_info"][key].append(output)
                
        if key == 'location':
            if isinstance(dictionary['location_info'][key], str) and is_valid_point(dictionary['location_info'][key]):
                drop_location = False
            else:
                drop_location = True

        logger.debug(f"Outputed dictionary: {dictionary}")
        
    if drop_location:
        logger.debug("Must drop location")
        dictionary['location_info'].pop('location')  
        
    return dictionary                    



def add_country_or_state(code_name, new_key, new_value, country_list):
    minmod_code = generic.read_csv_to_dict(f"{WORKING_DIR}/codes/{code_name}")
    
    df = pd.DataFrame(minmod_code)
    df.columns = df.columns.str.strip().str.replace('\ufeff', '')
    
    
    json_str = {'normalized_uri': ""}
    
    logger.info(f"Current: {json_str}, new_key {new_key}")
 
        
    normalized_value = generic.find_best_match(new_value, df['name'].tolist(), threshold=75)
    
    if normalized_value:
        logger.info(f"Normalized value {normalized_value}")
        result = df[df['name'] == normalized_value]
        m,_ = result.shape
        if m == 1:
             json_str['normalized_uri'] = MINMOD_URL + result['minmod_id'].values[0]
        else:
            new_result = result[result['country_name'].isin(country_list)]
            if not new_result.empty: 
                if not new_result.empty:
                    for country in country_list:
                        match = new_result[new_result['country_name'] == country]
                        if not match.empty:
                            json_str['normalized_uri'] = MINMOD_URL + match['minmod_id'].values[0]
                            break
            
    
    json_str = generic.add_extraction_dict(new_value, json_str)
    logger.debug(f"Output json string: {json_str}")
    return json_str, normalized_value
    

def is_valid_point(s):
    ## used to check if there is anything besides numbers between the ()
    pattern = r"\w+\((-?\d+(\.\d+)?\s-?\d+(\.\d+)?)\)"
    match = re.search(pattern, s)
    
    # Return True if a match is found, False otherwise
    number_bool = match is not None
    matches = re.findall(r'[-\d.]+', s)

    correct_val = False
    if len(matches) == 2:
        longitude = float(matches[0])
        latitude = float(matches[1])

        # Check the conditions
        if -180 <= longitude <= 180 and -90 <= latitude <= 90:
            correct_val = True
    
    return number_bool and correct_val
    
    