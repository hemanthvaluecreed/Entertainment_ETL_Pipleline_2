import requests
import random
import time
from pathlib import Path
import json
from logger.loggerConfig import logger

session = requests.Session()

#user-agent lets the server know who are requesting the resources
#requesting the resources to be in json format
session.headers.update({"User-Agent":"Entertainment_ETL_Pipeline/2.0","Accept":'Application/json'})

def requests_with_retrys(url, max_attempts=3, params=None):
    retryable_response_codes = [429, 500, 502, 503]

    for attempt in range(1,max_attempts + 1):
        try:
            logger.info('Requesting the page with params %s | Attempt %d/%d',params,attempt,max_attempts)
            response = session.get(url,params=params,timeout=(10, 10))

            #404 reponse marks the pagination completion in TvMaze api
            if response.status_code == 404:
                logger.info("HTTp 404 occurred | No more pages available")
                return response

            if response.status_code in retryable_response_codes:
                wait_time = 0
                if attempt == max_attempts:
                    logger.warning("Max tries reached | unable to retry")
                    response.raise_for_status()

                else:
                    retry = response.headers.get("Retry-After", 2)
                    if retry:
                        try:
                            wait_time = float(retry)

                        except ValueError:
                            logger.warning("Value error occurred while converting retry value")
                            wait_time = random.uniform(0, 1) + 2 ** attempt

                    else:
                        wait_time = random.uniform(0, 1) + 2 ** attempt

                logger.info("Request failed | retrying %d/%d after %.2f seconds",attempt, max_attempts, wait_time)

                time.sleep(wait_time)
                continue

            response.raise_for_status()
            return response
        
        #handling multiple exceptions
        except requests.exceptions.Timeout as e:
            if attempt == max_attempts:
                logger.warning("Request timeout | Maximum attempts reached")
                raise RuntimeError(f"Request timed out after {max_attempts} attempts") from e
            else:
                wait_time = random.uniform(0, 1) + 2 ** attempt
                logger.warning("Request/Connection timeout | retrying after %.2f seconds",wait_time)
                time.sleep(wait_time)

        except requests.exceptions.ConnectionError as e:
            if attempt == max_attempts:
                logger.error("Connection error | Maximum attempts reached")
                raise RuntimeError(f"Connection failed after {max_attempts} attempts") from e

            wait_time = random.uniform( 0,1) + 2 ** (attempt - 1)
            logger.warning("Connection error | Attempt %d/%d | ""Retrying after %.2f seconds",
                attempt,max_attempts,wait_time)

            time.sleep(wait_time)

        except requests.exceptions.HTTPError as e:
            logger.error("HTTP request failed | Status code: %s | Error: %s", response.status_code,e)
            raise

        except requests.exceptions.RequestException as e:
            logger.error("Request failed | Error: %s",e)
            raise


def extract_show_data():
    logger.info('Extraction started')
    url = "https://api.tvmaze.com/shows"
    max_attempts = 3
    page_Num = 0
    total_records = 0

    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True,exist_ok=True)

    while True:
        params = {"page": page_Num}
        try:
            response = requests_with_retrys(url,max_attempts,params=params)

            if response.status_code == 404:
                logger.info("Pagination completed || Last successful page: %d",page_Num)
                break

            data = response.json()
            records_count = len(data)
            raw_file = raw_dir / f"shows__{page_Num:03d}.json"

            with open(raw_file,"w",encoding="utf-8") as file:
                json.dump(data,file,indent=3)#creating a raw json files

            page_Num += 1
            total_records += records_count
            logger.info('Raw file created successfully | Pages created: %d | Records added: %d | Total Records: %d',
                   page_Num,records_count,total_records )

        except RuntimeError as e:
            logger.warning("Unexpected error occurred at page: %d",page_Num)
            raise

        except Exception as e:
            logger.warning("Unexpected error occurred at page: %d",page_Num)
            raise

    logger.info("Extraction completed | total pages extracted: %d | total records extracted: %d",page_Num,total_records)

