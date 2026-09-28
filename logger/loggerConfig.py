import logging 
from pathlib import Path

BASE_DIR= Path(__file__).resolve().parent
filename = BASE_DIR/'logger.log'
print(filename.resolve())

logging.basicConfig(level=logging.INFO,filename=filename,filemode='w',
            format='%(asctime)s| %(name)s | %(module)s | %(levelname)s | %(message)s')

logger = logging.getLogger("Entertainment-ETL")