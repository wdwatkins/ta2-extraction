"""
Copyright © 2023-2024 InferLink Corporation. All Rights Reserved.

Distribution authorized to U.S. Government only; Proprietary Information, September 22, 2023. Other requests for this document shall be referred to the DoD Controlling Office or the DoD SBIR/STTR Program Office.

This Data developed under a SBIR/STTR Contract No 140D0423C0093 is subject to SBIR/STTR Data Rights which allow for protection under DFARS 252.227-7018 (see Section 11.6, Technical Data Rights). 
"""
import json
import openai
from typing import List
from settings import OPENAI_API_KEY, OPENAI_AZURE_ENDPOINT, OPENAI_AZURE_API_VERSION
import requests
import json
from enum import Enum
import PyPDF2
from typing import List, Type, TypeVar
import extraction_package.extractionPrompts as prompts
import extraction_package.LLMmodels as model
from settings import MINI_MODEL
import logging


logger = logging.getLogger(__name__)
# Define a generic type for Enum
T = TypeVar('T', bound=Enum)

def openai_authenticate():
    logger.debug("AZURE_ENDPOINT: %s", OPENAI_AZURE_ENDPOINT)
    if OPENAI_AZURE_ENDPOINT is not None:
        openai.azure_endpoint = OPENAI_AZURE_ENDPOINT
        openai.api_version = OPENAI_AZURE_API_VERSION
        logger.info(f"Using Azure OpenAI with endpoint: {OPENAI_AZURE_ENDPOINT} and version: {OPENAI_AZURE_API_VERSION}")
    else: 
        logger.info("Using OpenAI API without Azure configuration")
    client = openai.OpenAI(api_key = OPENAI_API_KEY)
    logger.debug("Client values: %s", client)
    return client

def get_gpt_response(prompt, model_type, schema_format):
    # logger.debug(f'Here is the prompt: {prompt} \n\n')
    # logger.debug(f"schema: {schema_format}\n\n")
    client = openai_authenticate()
    completion = client.beta.chat.completions.parse(
    model= model_type,
    messages=[
        {"role": "system", "content": """You are a geology expert and you are very good in understanding mining reports, which is attached.
"""},
        {"role": "user", "content": prompt },
    ],
    response_format={
            "type": "json_schema",
            "json_schema": {"name": "JSONSCHEMA","schema": schema_format}
    },
)
    # logger.debug("API response:", completion)
    
    try:
        content = completion.choices[0].message.content
        # Parse the JSON content if needed
        parsed_content = json.loads(content)
        return parsed_content
    except (TypeError, KeyError, IndexError, json.JSONDecodeError) as e:
        logger.debug("Error extracting or parsing response content:", e)
        return None

def clean_list_by_enum(values: List[str], enum_cls: Type[T]) -> List[str]:
    valid_values = {e.value for e in enum_cls}
    return [value for value in values if value in valid_values]

def get_pages_with_tables(filepath):
    table_pages = []
    deposit_pages = []
    TOC_pages = []
    with open(filepath, 'rb') as file:
        
        # Create a PDF reader
        pdf = PyPDF2.PdfReader(file)
        
        # Iterate over each page
        for page_num in range(0, len(pdf.pages)):
            logger.debug(f"Looking at page: {page_num}")
            page = pdf.pages[page_num]
            text = page.extract_text()
            resp = get_gpt_response(prompts.classifier_prompt + text, MINI_MODEL, model.pageClassifier.model_json_schema())

            logger.debug(f"Here is the response: {resp}\n")
            if resp['isTable']:
                table_pages.append(page_num)
            if resp['isDepositType']:
                deposit_pages.append(page_num)
            if resp['isTOC']:
                TOC_pages.append(page_num)

            logger.debug(f"Counts: table: {len(table_pages)} Deposit Type {len(deposit_pages)} \n\n")
    
    table_pages = [page for page in table_pages if page not in TOC_pages]
    deposit_pages = [page for page in deposit_pages if page not in TOC_pages]
    
    
    return table_pages, deposit_pages, TOC_pages