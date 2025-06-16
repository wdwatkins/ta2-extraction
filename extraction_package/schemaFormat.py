"""
Copyright © 2023-2024 InferLink Corporation. All Rights Reserved.

Distribution authorized to U.S. Government only; Proprietary Information, September 22, 2023. Other requests for this document shall be referred to the DoD Controlling Office or the DoD SBIR/STTR Program Office.

This Data developed under a SBIR/STTR Contract No 140D0423C0093 is subject to SBIR/STTR Data Rights which allow for protection under DFARS 252.227-7018 (see Section 11.6, Technical Data Rights). 
"""
from settings import VERSION_NUMBER, SYSTEM_SOURCE, CDR_ENDPOINT, MINMOD_URL
from extraction_package import genericFunctions as generic

def created_document_ref(record_id, title):
    return {
        "title": title,
        "doi": "",
        "authors": [],
        "year": "",
        "month": "",
        "volume": "",
        "issue": "",
        "description": "",
        "uri": f"{CDR_ENDPOINT}/docs/documents/{record_id}"
    }
            
            
def create_mineral_site(record_id):
    return {
        "source_id": f"{CDR_ENDPOINT}/docs/documents",
        "record_id": f"{record_id}",
        "name": "",
        "location_info": {
            "location": "",
            "crs": "",
            "country": "",
            "state_or_province": ""
        }
    }

        
def create_deposit_format():
    return """
        {"deposit_type": []
        }
        """
        
def create_deposit_format_correct():
    return """
        {
        "deposit_type": {
            "observed text": f"{MINMOD_URL}/deposit_id",  
            "observed text" : f"{MINMOD_URL}/deposit_id",
            "observed text": ""
        }
        }
        """
        

def create_inventory_format(commodities_dict, commodity, document_dict):
    doc_month = document_dict.get('month', '')
    doc_year = document_dict.get('year', '')
    doc_date = ''
    if doc_month and doc_year:
        doc_date = f"{doc_year}-{doc_month}"
    
    commodity_dict = {
                  "observed_name": commodity,
                  "confidence": 1,
                  "source": SYSTEM_SOURCE + " " + VERSION_NUMBER}
    
    found_value = generic.find_best_match(commodity, commodities_dict.keys()) 
    # print(f"Found commodity: {found_value}")
    if found_value in commodities_dict:
        # print(f"found value in dict: {commodities_dict[found_value]}")
        norm_uri =  f"{MINMOD_URL}/" + commodities_dict[found_value]
        commodity_dict["normalized_uri"] = norm_uri
        
    format = {
    "commodity": commodity_dict,
    "category": "",
    "material_form":"",
    "ore": {
        "ore_unit": "",
        "value": ""
    },
    "grade": {
        "grade_unit": "",
        "grade_value": ""
    },
    "cutoff_grade": {
        "grade_unit": "",
        "grade_value": ""
    },
    "contained_metal": "", 
    "reference": {
        "document": document_dict,
    },
    "date": doc_date,
    "zone": "",
    }

    if doc_date:
        return format

    else: 
        format.pop('date')
        return format