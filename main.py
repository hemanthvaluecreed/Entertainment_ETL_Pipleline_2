from extract import extract_show_data
from transform import transform
from load import load_all
from validate import run_validation

from logger.loggerConfig import logger


def main():

    logger.info("========== PIPELINE STARTED ==========")

    try:

        # 1. EXTRACTION

        logger.info("EXTRACTION STARTED")

        extract_show_data()

        logger.info("EXTRACTION COMPLETED")
        # 2. TRANSFORMATION
        logger.info("TRANSFORMATION STARTED")

        transform()

        logger.info("TRANSFORMATION COMPLETED")
        # 3. DATABASE LOAD
        logger.info("DATABASE LOAD STARTED")

        load_all()

        logger.info("DATABASE LOAD COMPLETED")

        # 4. VALIDATION
        logger.info("VALIDATION STARTED")

        run_validation()

        logger.info("VALIDATION COMPLETED")


        logger.info("========== PIPELINE COMPLETED ==========")


    except Exception:

        logger.exception(
            "========== PIPELINE FAILED =========="
        )

        raise


if __name__ == "__main__":
    main()