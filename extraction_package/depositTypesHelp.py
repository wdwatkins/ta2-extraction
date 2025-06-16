"""
Copyright © 2023-2024 InferLink Corporation. All Rights Reserved.

Distribution authorized to U.S. Government only; Proprietary Information, September 22, 2023. Other requests for this document shall be referred to the DoD Controlling Office or the DoD SBIR/STTR Program Office.

This Data developed under a SBIR/STTR Contract No 140D0423C0093 is subject to SBIR/STTR Data Rights which allow for protection under DFARS 252.227-7018 (see Section 11.6, Technical Data Rights). 
"""
import warnings
import logging
import extraction_package.genericFunctions as generic
import extraction_package.LLMFunctions as llm
import extraction_package.LLMmodels as model
import extraction_package.extractionPrompts as prompt


from settings import VERSION_NUMBER, SYSTEM_SOURCE, MINI_MODEL, STRUCTURE_MODEL, MINMOD_URL, WORKING_DIR
# Ignore the specific UserWarning from openpyxl
warnings.filterwarnings(action='ignore', category=UserWarning, module='openpyxl')

logger = logging.getLogger(__name__)

def create_deposit_types(filepath, deposit_pages):
    logger.info(f"Getting started on deposit type")
    deposit_window = generic.generate_sliding_windows(deposit_pages)
    minmod_deposit_types = generic.read_csv_to_dict(WORKING_DIR + "/codes/minmod_deposit_types.csv")
    deposit_id = {}
    for key in minmod_deposit_types:
        deposit_id[key['Deposit type']] = key['Minmod ID']
        
    full_text = generic.return_pages_of_text(deposit_window, filepath)
    deposits = llm.get_gpt_response(prompt.find_deposit_types + full_text, STRUCTURE_MODEL, model.DepositTypes.model_json_schema())

    logger.debug(f"Here are the deposit types: {deposits}")
    deposit_types_json = format_deposit_candidates(deposits, deposit_id) 
        
    logger.info(f" Final Formatted Deposit Type: {deposit_types_json} \n")

        
    return deposit_types_json


def format_deposit_candidates(deposit_list, minmod_deposits):
    deposit_type_candidate = { "deposit_type_candidate": []}
    logger.debug(f'minmod_deposit_type {minmod_deposits}')
    
    for dep in deposit_list['deposits']:
        logger.debug(f"Looking at deposit: {dep}")
        inner_dict = {}
        inner_dict["observed_name"] = dep
        normalized_value = generic.find_best_match(dep, minmod_deposits.keys())
        if normalized_value in minmod_deposits:
            inner_dict["normalized_uri"] = MINMOD_URL + minmod_deposits[normalized_value]
   
        inner_dict["source"] =  SYSTEM_SOURCE + " "+ VERSION_NUMBER
        inner_dict["confidence"] = 1/len(deposit_list['deposits']) 
        if inner_dict['confidence'] == 1:
            inner_dict['confidence'] = 0.99
        deposit_type_candidate['deposit_type_candidate'].append(inner_dict)
    
        
        logger.debug(f'deposit type candidate {deposit_type_candidate}')    
            
    
    
    return deposit_type_candidate