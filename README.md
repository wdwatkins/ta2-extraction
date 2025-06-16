# README for Extraction Package
This code is a part of the TA2 project for USGS. This is the package that works to extract information from Mining Reports to gather deposit types, mineral inventory, mining report reference, and mining site information to create a larger Database. The most up to date package is stored in ./extraction_package. 

## Installation (requires python >3.12 and pip)
1. Create virtual environment (python, anaconda, etc.)
2. In the project root: `pip install -r requirements.txt`

## How to run Docker Image
1. Clone the Repository: `git clone git@github.com:DARPA-CRITICALMAAS/ta2-extraction.git `
2. Create a .env file with at least `OPENAI_API_KEY`, `CDR_ENDPOINT` and `CDR_BEARER` (for Polymer authenetication). `OPENAI_AZURE_ENDPOINT` and `OPENAI_AZURE_API_VERSION` are needed if you are using Azure OpenAI. 
3. Fill out any necessary variables in the settings.py
4. Build the Docker Image: `docker build -t -my-extraction-app .`
5. Running the Docker Container: 
``` 
    docker run \
    -v /path/to/stored/reports/ta2-extraction/reports:/app/reports \
    -v /path/to/stored/reports/ta2-extraction/output:/app/output \
    my-extraction-app \
    python -m extraction_package.pipeline \
    --pdf_p "/app/reports/" \
    --pdf_name "FileName.pdf" \
    --output_path "/app/output/"
```

**Note**: Make sure the the directories are for saving the output and finding the reports are correctly named. This will only run one file at a time. --pdf_p: the pathway to where reports are stored. --pdf_name: is the name of the file that you want to extract from. --output_path: folder directory where you want to store the output.

## Extraction Package Directory 
Note all loggers should be name similar to the file. Note that the documents you want to process should also already be downloaded locally. 

Updated Jan 2025.

extraction_package/ \
|    |---- \_\_init\_\_ \
|    |---- pipeline.py : the main driver of the code \
|       |---- genericFunctions: all generalized functions that do not just relate to a single section \
|       |---- mineralInventoryHelp: code to generate the Mineral Inventory \
|       |---- documentRefHelp: Code to generate the Mineral Site and document reference information \
|       |---- LLMFunctions: all code that relates to call the LLM that is used \
|       |---- LLMModels: all formats for structured outputs \
|       |---- depositTypesHelp : the code given to derive the deposit type candidates \
|       |---- extractionPrompts: all prompts used \
|       |---- schemaFormats: all the formats that match the schema derived by the larger TA2 team 



### Description of Variables
* **file_name**: the filename of the pdf that you want to extract from. Expectation is that the file_name has the record_id in part of the name. 
* **folderpath**: folderpath to the where the report pdf is stored 
* **output_path**: output folder path where you want the mineral inventory extraction json to be outputted to.


### How to run One File
0. Make sure all variables in the .env are correctly formatted (ie API key and CDR Bearer)
1. Create virtual environment
2. Install required dependencies: `pip install -r requirements.txt`
3. Run Pipeline for one File which must already be downloaded locally. At the top of the ta2-extraction directory Run
 `python -m extraction_package.pipeline --pdf_p "/path/to/reports/" --pdf_name "FileName.pdf" --output_path "/path/to/stored/output/"`

## CDR Polymer process
1. Log in to the CDR: https://auth.polymer.rocks/
2. Upload a document by hitting the CDR dropdown in top right corner 
3. Insert document name and information.
4. Hit upload
5. Once upload completes, go to the file
6. Hit the process button to initate the extraction of the document


## Version Control
### Current Version 3.0
Major Changes
- Removal of assistants to use a more generic model for longevity
- change approach of how to get page number
- utilization of structured outputs and openAI improvements for models 4o
- Working on adding a filtered extraction 
- updates to the schema

### Previous Version 2.0: extraction_package
Major Changes
- LARGE overhaul to make code more scalable, readable, & all MPG's standards
- add logging, more try catch
- modularize the code into separate files

### Past version explanations
1.2 Changes for 9 month, pushed to main DATE
reference : https://platform.openai.com/docs/assistants/tools/file-search
- Removed the need to look at total for categories or for zones
- Using gpt-4-Turbo
- updates to assistants v2 which includes JSON return
- add a separate check for just tonnage or units using chat GPT
- utilizing tenacity for any run status failures/errors
- Changing the author prompts
- Updating how we get pages by looking for key words


1.1 Change to the extraction clean-up
    - adding the instance check & removal of keys
    - new unit keys were added
    - this was used for cobalt
    - errors: not picking up all the rows, schema errors with removal of keys
1.0 Initial Prompts
    - this was done for copper & nickel & zinc


### OLD Extraction Package Directory v1
extraction_package/ \
|    |---- \_\_init\_\_ \
| |---- extraction_pipeline : the main driver of the code \
|    |---- extraction_functions : stores all the functions needed to help the pipeline code \
|    |---- prompts: all prompts used \
|    |---- schema_formats: all the formats that match the schema derived by the larger TA2 team 
