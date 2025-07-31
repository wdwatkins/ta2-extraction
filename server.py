import argparse
import atexit
import hashlib
import hmac
import os
from fastapi.security import APIKeyHeader
import httpx
import ssl
import certifi
import datetime as date
import uvicorn
import logging
from cdr_schemas.events import Event
from fastapi import (BackgroundTasks, Depends, FastAPI, HTTPException, Request,
                     status)
from settings import app_settings
from minmodapi import MinModAPI, replace_site
from cdr_schemas.document import Document
import sys
sys.path.append(os.path.abspath('/home/ubuntu/ta2-extraction'))

import extraction_package.genericFunctions as generic
import extraction_package.pipeline as extract 
from dotenv import load_dotenv

logging.basicConfig(level=app_settings.log_level)
logger = logging.getLogger(__name__)

# Specify the path to the .env file
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), './.env'))

# Load the .env file
load_dotenv(dotenv_path)

parser = argparse.ArgumentParser()
args = parser.parse_args()

print("Trying to log in")
minmod_api=MinModAPI(app_settings.minmod_endpoint)
minmod_api.login(app_settings.minmod_user, app_settings.minmod_token)
print("Logged into minmod API: ",minmod_api.whoami())

# Get ngrok to give us an endpoint
#listener = ngrok.forward(app_settings.local_port, authtoken_from_env=True)
#app_settings.callback_url = listener.url() + "/hook"

def clean_up():
    # delete our registered system at CDR on program end
    headers = {'Authorization': f'Bearer {app_settings.cdr_bearer}'}
    ctx = ssl.create_default_context(
        cafile=os.environ.get("SSL_CERT_FILE", certifi.where())
        )
    client = httpx.Client(follow_redirects=True, verify = ctx)
    client.delete(f"{app_settings.cdr_host}/user/me/register/{app_settings.registration_id}", headers=headers)


# register clean_up
atexit.register(clean_up)
app = FastAPI()


async def event_handler(evt: Event):
    print(f"Getting the event at: {date.datetime.now()}")
    try:
        match evt:
            case Event(event="ping"):
                print("Received PING!")
            case Event(event="document.process"):
                print("Received document process event!")
                print(evt.payload)
                document = Document(**evt.payload)
                download_link = f"https://docs.polymer.rocks/cdr/download/{document.id}"
                print(download_link)
                #count, belowLimit = minmod_api.increment()
                
                    
                if True:                
                    record_id = document.id
                    # print(f"Looking at record_id: {record_id}")
                    ifexists = minmod_api.has_site(record_id)
                    
                    logger.info(f"Record ID: exists in CDR: {ifexists}")
                    download_dir = "/app/reports/"
                    output_folder_path = "/app/output/"
                    file_name = None
                    
                    if not ifexists:
                        file_name = generic.download_document(record_id, download_dir)
                        logger.info(f"Finished Downloading: {file_name}")
                    
                    if file_name is not None:
                        logger.info(f"Going to start extracting: {file_name}")
                        json_output = extract.run(download_dir, file_name, output_folder_path)
                        logger.debug(f"Json output: {json_output}")
                        logger.info("Completed Extraction")
                        try:
                            logger.debug("Attempting upsert to minmod")
                            for item in json_output:
                                item['source_id'] = "https://api.cdr.land/v1/docs/documents" # hard code for now to be consistent with USC deployment
                                logger.debug("Note hard-coded source_id field")
                                logger.debug(f"mineral site json: {item}")
                                upsert_response = minmod_api.upsert_mineral_site(item, apply_update=replace_site)
                                logger.debug("Minmod response to upsert: %s", upsert_response)
                        except Exception as e:
                            logger.warning(f"Error from Minmod: {e}")
                        
                        
                        download_file_path = os.path.join(download_dir, file_name)
                        
                        if os.path.exists(download_file_path):
                            try:
                                os.remove(download_file_path)
                            except:
                                print("Couldn't delete file")
                                
                        try:
                            for filename in os.listdir(output_folder_path):
                                file_path = os.path.join(output_folder_path, filename)
                                if os.path.isfile(file_path):
                                    os.remove(file_path)
                                    # print(f"Successfully deleted {filename} from {output_folder_path}")
                        except Exception as e:
                            print(f"Error deleting files in {output_folder_path}: {e}")
                        
                    else:
                        print("Did not extract file")                               
                    
            case _:
                print("Nothing to do for event: %s", evt)

    except Exception:
        print("background processing event: %s", evt)
        raise

cdr_signiture = APIKeyHeader(name="x-cdr-signature-256")


async def verify_signature(request: Request, signature_header: str = Depends(cdr_signiture)):

    payload_body = await request.body()
    if not signature_header:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="x-hub-signature-256 header is missing!")

    hash_object = hmac.new(app_settings.registration_secret.encode(
        "utf-8"), msg=payload_body, digestmod=hashlib.sha256)
    expected_signature = hash_object.hexdigest()
    if not hmac.compare_digest(expected_signature, signature_header):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Request signatures didn't match!")

    return True


@app.post("/hook")
async def hook(
    evt: Event,
    background_tasks: BackgroundTasks,
    request: Request,
    verified_signature: bool = Depends(verify_signature),
):
    """Our main entry point for CDR calls"""

    background_tasks.add_task(event_handler, evt)
    return {"ok": "success"}


def run():
    """Run our web hook"""
    uvicorn.run("__main__:app", host="0.0.0.0",
                port=app_settings.local_port, reload=False)

def register_system():
    """Register our system to the CDR using the app_settings"""
    global app_settings
    headers = {'Authorization': f'Bearer {app_settings.cdr_bearer}'}
    # print(headers)
    registration = {
        "name": app_settings.system_name,
        "version": app_settings.system_version,
        "callback_url": app_settings.callback_url,
        "webhook_secret": app_settings.registration_secret,
        # Leave blank if callback url has no auth requirement
        "auth_header": "",
        "auth_token": app_settings.registration_secret,
        # Registers for ALL events
        "events": ["document.process", "ping"]

    }
    ctx = ssl.create_default_context(
        cafile=os.environ.get("SSL_CERT_FILE", certifi.where())
        )
    client = httpx.Client(follow_redirects=True, verify = ctx)

    r = client.post(f"{app_settings.cdr_host}/user/me/register",
                    json=registration, headers=headers)
    
    # Log our registration_id such we can delete it when we close the program.
    print(f"register system r: {r}")
    app_settings.registration_id = r.json()["id"]

if __name__ == "__main__":
    ## Only have to register your system once
    register_system()
    run()
