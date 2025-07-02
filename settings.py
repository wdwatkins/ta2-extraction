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
from pydantic_settings import BaseSettings
import os
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") # For OpenAI
OPENAI_AZURE_ENDPOINT = os.getenv("OPENAI_AZURE_ENDPOINT", None)
OPENAI_AZURE_API_VERSION = os.getenv("OPENAI_AZURE_API_VERSION")
CDR_BEARER = os.getenv("CDR_BEARER")
CDR_ENDPOINT = os.getenv("CDR_ENDPOINT")
CALLBACK_URL= os.getenv("CALLBACK_URL")
REGISTRATION_SECRET = os.getenv("REGISTRATION_SECRET")
WORKING_DIR = os.getenv("WORKING_DIR", "/app/")
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

#TODO: all files should either use this or the variables above
# they are duplicative.  This class is only used in server.py
class Settings(BaseSettings):
    # TO BE CHANGED BY TA3-4 system
    system_name: str = "inferlink_extraction"
    system_version: str = "0.0.1"
    ml_model_name: str = "xcorp_docs_model"
    ml_model_version: str = "0.0.1"

    # Local port to run on
    local_port: int = 80
    cdr_api_token: str
    # To be filled in programmatically via ngrok below.
    callback_url: str = ""
    # Secret string used for signature verification on callback.  Changed by TA3-4 system.
    registration_secret: str = "mysecret"

    # To be provided to TA3-4 system by CDR admin
    user_api_token: str = ""
    cdr_host: str = "https://api.cdr.land"
    admin_cdr_host: str = "https://admin.cdr.land"
    openai_azure_endpoint: str = ""
    openai_azure_api_version: str = "2023-05-15"
    openai_api_key: str = ""
    minmod_endpoint: str = "https://minmod.isi.edu/api"
    minmod_user: str = ""
    minmod_token: str = ""
    working_dir: str = "/app/"
    callback_url: str = "extract.dev-minmod.chs.usgs.gov/hook"
    # For local development
    # cdr_host: str = "http://0.0.0.0:8333"
    # admin_cdr_host: str = "http://0.0.0.0:3333"

    # To be filled in programmatically after registration process below.  Needed to remove registration.
    registration_id: str = ""

    class Config:
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = "utf-8"

app_settings = Settings()