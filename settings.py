"""
Copyright © 2023-2024 InferLink Corporation. All Rights Reserved.

Distribution authorized to U.S. Government only; Proprietary Information, September 22, 2023. Other requests for this document shall be referred to the DoD Controlling Office or the DoD SBIR/STTR Program Office.

This Data developed under a SBIR/STTR Contract No 140D0423C0093 is subject to SBIR/STTR Data Rights which allow for protection under DFARS 252.227-7018 (see Section 11.6, Technical Data Rights). 
"""
"""
Settings File to place API_key or any other variables that will change between users. It also allows us to change
easier across all files as well. 
    
"""
from dotenv import load_dotenv
import os
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") # For OpenAI
OPENAI_AZURE_ENDPOINT = os.getenv("OPENAI_AZURE_ENDPOINT", None)
OPENAI_AZURE_API_VERSION = os.getenv("OPENAI_AZURE_API_VERSION")
CDR_BEARER = os.getenv("CDR_BEARER")
CDR_ENDPOINT = os.getenv("CDR_ENDPOINT")
WORKING_DIR = os.path.expanduser("~/ta2-extraction")
# print(API_KEY, WORKING_DIR, CDR_BEARER)
MODEL_TYPE = "gpt-4o"
LIBRARY_ID = "4530692"
LIBRARY_TYPE = "group"
CATEGORY_VALUES = ["inferred", "indicated","measured", "probable", 
                "proven", "proven+probable", "inferred+indicated", "inferred+measured",
                "measured+indicated"]
MINMOD_URL = "https://minmod.isi.edu/resource/"
VERSION_NUMBER = "v3"
SYSTEM_SOURCE = "Inferlink Extraction"
STRUCTURE_MODEL = "gpt-4o-2024-08-06"
MINI_MODEL = "gpt-4o-mini"