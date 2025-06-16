
import pickle
import pandas as pd
import requests
import json
import os
import urllib.parse
import httpx
import time
from pydantic import BaseModel, Field
import openai
from typing import List, Optional
from settings import OPENAI_API_KEY, WORKING_DIR
import warnings
import requests
import json
import csv
from enum import Enum
import PyPDF2
from tenacity import retry, retry_if_result, stop_after_attempt, wait_fixed
from requests.exceptions import ConnectionError
from typing import List, Type, TypeVar, Dict

# Define a generic type for Enum
T = TypeVar('T', bound=Enum)


def create_enum_from_csv(csv_file: str, enum_name: str, key1: str, key2: str) -> Enum:
    df = pd.read_csv(csv_file)
    if key2:
        values = df[key1].tolist() + df[key2].tolist()
    else:
        values = df[key1].tolist()
    return Enum(enum_name, {value.upper().replace(' ', '_'): value for value in values})

UnitEnum = create_enum_from_csv(f'{WORKING_DIR}/codes/minmod_units.csv', 'UnitEnum', 'unit name', 'unit aliases' )
CompoundEnum = create_enum_from_csv(f'{WORKING_DIR}/codes/material_form.csv', 'CompoundEnum', 'name', 'formula' )
CommoditiesEnum =create_enum_from_csv(f'{WORKING_DIR}/codes/minmod_commodities.csv', 'CommoditiesEnum', 'CommodityinMRDS', '')
CountryEnum = create_enum_from_csv(f'{WORKING_DIR}/codes/country.csv', 'CountryEnum','name', 'iso3')
StateProvinceEnum = create_enum_from_csv(f'{WORKING_DIR}/codes/state_or_province.csv', 'StateProvinceEnum', 'name', '')
CRSEnum = create_enum_from_csv(f'{WORKING_DIR}/codes/epsg.csv', 'CRSEnum', 'name', '')
DepositEnum = create_enum_from_csv(f'{WORKING_DIR}/codes/minmod_deposit_types.csv', 'DepositEnum', 'Deposit type', '')



class DepositTypes(BaseModel):
    deposits: list[DepositEnum] = Field(description="The list of acceptable deposit types found in the text")



class pageClassifier(BaseModel):
    isTable: bool = Field(Description="Boolean that flages whether or not there is a table on this page")
    isDepositType: bool = Field(Description="Boolean that denotes if we have found the deposit types section within the document")
    isTOC: bool = Field(Description="Boolean that denotes if we have found text that has a Table of Contents structure, which typically has page numbers, headers, and sections of the documents.")

class DocRefandLocationInfo(BaseModel):
    name: str = Field(Descprtion = "Give the name of the physical mining site which can be different than the project")
    location: str = Field(Description="geographic coordinates using latitude and longitude that will then be converted to geometry point structure using WGS84 standard. For one set of latitude, longitude coordinates the format looks like: POINT(long1 lat1). If there are multiple points the format will look like: MULTIPOINT(long1 lat1,long2 lat2, ..). Latitude should be between (-90 and +90) and Longitude should be between (-180 and +180) with only numeric information. If there is no location information or if the correct conversions cannot be made replace the value as empty strings")
    crs: CRSEnum = Field(Description="the geometry point standard that the above location is in")
    country: List[CountryEnum] = Field(Description=" List of extracted countries name that the mining site is physically located in") 
    state_or_province: List[StateProvinceEnum] = Field(Description= "List of extracted state or province names that the mining site is physically located in") 
    authors: List[str] = Field(Description="list of author names (ignore professional titles). Note authors can be idenfitied by key words such as authors or prepared by. Do not return company names.") 
    month: str = Field(Description="Month the document was published. Should be in mm format")
    year: str = Field(Description="Year the document was published. Should be in yyyy format")
    volume: str= Field(Description="Volume of the document")
    issue: str= Field(Description="Issue name of the document")
    description: str = Field(Description="One sentence description of the document")
    
## pydantic for the mineral inventory 
class CategoryEnum(str, Enum):
    inferred = "inferred"
    indicated = "indicated"
    measured = "measured"
    probable = "probable"
    proven = "proven"
    proven_plus_probable = "proven+probable"
    inferred_plus_indicated = "inferred+indicated"
    inferred_plus_measured = "inferred+measured"
    measured_plus_indicated = "measured+indicated"

class CommoditiesCategories(BaseModel):
    commodities: list[CommoditiesEnum] = Field(description = "The list of commodities found in the tables")
    categories: list[CategoryEnum] = Field(description = "The list of categories found in the tables")

class RelevantTable(BaseModel):
    tableName: str = Field(description="Name of the table in the text")
    tableYear: str = Field(description="Year the table was created for in format: yyyy")
    commodities: list[CommoditiesEnum] = Field(description = "The list of commodities found in the tables")

class RelevantTableSchema(BaseModel):
    tables: List[RelevantTable] = Field(description="A list of dictionaries that store all relevant Tables found in the text")

class MineralExtractionRow(BaseModel):
    tableName: str = Field(description="Name of the table in the text")
    commodity: CommoditiesEnum = Field(description="The commodity of interest for this row and extraction")
    category: CategoryEnum = Field(description="The category of the mineral extraction.")
    zone: Optional[str] = Field(description = "the named area where the commodity resources were extracted from (Note: Do not include any Total values).")
    chemical_compound: CompoundEnum = Field(description="The compound form the commodity was presented in. A compound is a mix of two or more elements. Only return compounds.")
    cut_off_value: Optional[str] = Field(description="The amount of the cutoff value.")
    cut_off_unit: Optional[UnitEnum] = Field(description="The unit of the cutoff value.")
    tonnage_value: float = Field(description="The given tonnage amount for the resource")
    tonnage_unit: UnitEnum = Field(description="The unit of the tonnage value.")
    grade_value: str = Field(description="The grade value")
    grade_unit: UnitEnum = Field(description="The unit of the grade value.")

class MineralExtractionSchema(BaseModel):
    extractions: List[MineralExtractionRow] = Field(description="A dictionary where keys are extraction identifiers and values are lists of MineralExtractionRow")
