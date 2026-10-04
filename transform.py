import json
from pathlib import Path
import pandas as pd
from logger.loggerConfig import logger



#loading raw data
def load_raw_data(raw_dir="data/raw"):
    """
    Read all extracted TVMaze JSON files and combine
    their records into one Python list.
    """
    raw_dir = Path(raw_dir)
    #finds all the files having name with given pattern and sorted the accordingly
    files = sorted(raw_dir.glob("shows__*.json"))

    if not files:
        raise FileNotFoundError(f"No raw JSON files found in {raw_dir}")

    records = []
    for file in files:

        logger.info("Reading raw file: %s", file.name)
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        #checks whether each files is list type or not
        if not isinstance(data, list):
            raise ValueError( f"Expected a list of show records in {file.name}")

        records.extend(data)

    logger.info(
        "Raw data loaded | Files: %d | Records: %d", len(files),len(records))
    return records

#normalizing the json files
def normalize_shows(records):
    """
    Flatting the nested JSON structures using pandas.json_normalize().
    """

    df = pd.json_normalize(records)
    logger.info(
        "JSON normalization completed | Rows: %d | Columns: %d",len(df),len(df.columns))

    return df



 #Selecting  AND Renaming Required Columns
def select_show_columns(df):
    """
    Select required TVMaze fields and rename them
    according to the target relational model.
    """

    column_mapping = {

        # Show
        "id": "show_id",
        "name": "show_name",
        "type": "show_type",
        "language": "language",
        "genres": "genres",
        "status": "status",

        # Runtime
        "runtime": "runtime_minutes",
        "averageRuntime": "average_runtime_minutes",

        # Dates
        "premiered": "premiered_date",
        "ended": "ended_date",

        # Website
        "officialSite": "official_site",

        # Schedule
        "schedule.time": "schedule_time",
        "schedule.days": "schedule_days",

        # Rating
        "rating.average": "rating",

        # Television network
        "network.id": "network_id",
        "network.name": "network_name",
        "network.country.name": "network_country",
        "network.country.code": "network_country_code",
        "network.country.timezone": "network_timezone",

        # Web channel
        "webChannel.id": "web_channel_id",
        "webChannel.name": "web_channel_name",
        "webChannel.officialSite": "web_channel_official_site",

        # Other
        "summary": "summary",
        "updated": "updated_at",
    }

    selected_columns = {}
    for source_column, target_column in column_mapping.items():

        if source_column in df.columns:
            selected_columns[target_column] = df[source_column]

        else:
            selected_columns[target_column] = pd.NA

    result = pd.DataFrame(selected_columns)

    logger.info(
        "Required columns selected | Rows: %d | Columns: %d",len(result),len(result.columns)
    )

    return result

# DATA CLEANING
def clean_shows(df):
    """
    Clean text, lists, HTML summary and invalid numeric values.
    """

    df = df.copy()

    logger.info("Cleaning transformation started")
    text_columns = [
        "show_name",
        "show_type",
        "language",
        "status",
        "network_name",
        "network_country",
        "network_country_code",
        "network_timezone",
        "web_channel_name",
        "web_channel_official_site",
        "official_site",
        "schedule_time",
    ]

    #converting text_columns into string (ensuring them to be string type)
    for column in text_columns:

        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
        )

 #normalizing the status column
    df["status"] = df["status"].str.title()


    df["genres"] = df["genres"].apply(
        lambda value: value if isinstance(value, list)else [])

    # Clean individual genre values
    df["genres"] = df["genres"].apply(
        lambda genres: [
            str(genre).strip()
            for genre in genres
            if str(genre).strip()
        ]
    )

    # Remove duplicate genres within a show
    df["genres"] = df["genres"].apply(
        lambda genres: list(dict.fromkeys(genres))
    )

    #handling schedule_day
    df["schedule_days"] = df["schedule_days"].apply(
        lambda value: value if isinstance(value, list)else []
    )

    df["schedule_days"] = df["schedule_days"].apply(
        lambda days: [str(day).strip().title()for day in days if str(day).strip()
        ]
    )

    # Remove duplicate days
    df["schedule_days"] = df["schedule_days"].apply(
        lambda days: list(dict.fromkeys(days))
    )

    # Summary
    df["summary"] = (
        df["summary"]
        .fillna("")
        .astype("string")
        .str.replace(r"<[^>]+>", "", regex=True)
        .str.strip()
    )

    # Invalid runtime values

    df.loc[
        df["runtime_minutes"] <= 0,
        "runtime_minutes"
    ] = pd.NA

    df.loc[
        df["average_runtime_minutes"] <= 0,
        "average_runtime_minutes"
    ] = pd.NA

    # Duplicate show IDs
    duplicate_count = df["show_id"].duplicated().sum()

    if duplicate_count > 0:

        logger.warning(
            "Duplicate show IDs found: %d",
            duplicate_count
        )

        df = (
            df
            .drop_duplicates(
                subset=["show_id"],
                keep="first"
            )
            .reset_index(drop=True)
        )

    logger.info(
        "Cleaning transformation completed | Rows: %d | Columns: %d",
        len(df),
        len(df.columns)
    )

    return df


# DATA TYPE CONVERSION
def convert_data_types(df):
    """
    Convert columns to appropriate pandas data types
    and apply basic data quality rules.
    """

    df = df.copy()

    logger.info("Data type conversion started")

    # Validate show IDs
    df["show_id"] = (
        pd.to_numeric(
            df["show_id"],
            errors="coerce"
        )
        .astype("Int64")
    )

    #checking null values in show_ids
    missing_show_ids = df["show_id"].isna().sum()

    if missing_show_ids > 0:

        logger.warning(
            "Rows with missing show_id removed: %d",
            missing_show_ids
        )

        df = (
            df[df["show_id"].notna()]
            .reset_index(drop=True)
        )


    # Dates

    df["premiered_date"] = pd.to_datetime(
        df["premiered_date"],
        errors="coerce"
    )

    df["ended_date"] = pd.to_datetime(
        df["ended_date"],
        errors="coerce"
    )

    # TVMaze updated field is Unix timestamp.
    # It measures the total number of seconds that have elapsed since January 1, 1970, at 00:00:00 UTC
    #converts unix timestamp into human readable datetime objects
    df["updated_at"] = pd.to_datetime(
        df["updated_at"],
        unit="s",
        errors="coerce",
        utc=True
    )


    # Foreign-key IDs

    id_columns = [
        "network_id",
        "web_channel_id",
    ]

    for column in id_columns:

        df[column] = (
            pd.to_numeric(
                df[column],
                errors="coerce"
            )
            .astype("Int64")
        )
    # Numeric fields
    numeric_columns = [
        "runtime_minutes",
        "average_runtime_minutes",
        "rating",
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # Rating validation
    invalid_ratings = (
        (df["rating"] < 0)
        | (df["rating"] > 10)
    )

    invalid_rating_count = invalid_ratings.sum()

    if invalid_rating_count > 0:

        logger.warning(
            "Invalid ratings found: %d",
            invalid_rating_count
        )

        df.loc[
            invalid_ratings,
            "rating"
        ] = pd.NA


    # Runtime validation
    invalid_runtime = (
        df["runtime_minutes"] <= 0
    )

    invalid_runtime_count = invalid_runtime.sum()

    if invalid_runtime_count > 0:

        logger.warning(
            "Invalid runtimes found: %d",
            invalid_runtime_count
        )

        df.loc[
            invalid_runtime,
            "runtime_minutes"
        ] = pd.NA


    # Average runtime validation
    invalid_average_runtime = (
        df["average_runtime_minutes"] <= 0
    )

    invalid_average_runtime_count = (
        invalid_average_runtime.sum()
    )

    if invalid_average_runtime_count > 0:

        logger.warning(
            "Invalid average runtimes found: %d",
            invalid_average_runtime_count
        )

        df.loc[
            invalid_average_runtime,
            "average_runtime_minutes"
        ] = pd.NA

    logger.info("Data type conversion completed")

    return df



# 6. ASSIGN STABLE SCHEDULE IDs

def assign_schedule_ids(df):
    """
    Assign a stable schedule_id to each show that has
    schedule information.

    schedule_id is derived from show_id.

    This design ensures that:
    - each show has at most one schedule_id
    - schedule_id remains stable across pipeline reruns
    - schedule IDs do not depend on API record ordering
    - schedule IDs do not change when new shows are added
    - Shows.schedule_id can safely remain UNIQUE
    - ShowScheduleDays.schedule_id can reference Shows.schedule_id

    Shows without schedule information receive NULL.
    """

    df = df.copy()

    schedule_ids = []

    for _, row in df.iterrows():

        show_id = row["show_id"]
        schedule_time = row["schedule_time"]
        schedule_days = row["schedule_days"]

        if not isinstance(schedule_days, list):
            schedule_days = []

        # Determine whether this show actually has
        # schedule information.
        has_schedule_time = (
            pd.notna(schedule_time)
            and str(schedule_time).strip() != ""
        )

        has_schedule_days = len(schedule_days) > 0

        if not has_schedule_time and not has_schedule_days:

            # No schedule information -> NULL
            schedule_ids.append(pd.NA)

        else:

            # Stable schedule ID.
            #
            # The schedule belongs to this show,
            # therefore the show_id provides a stable
            # identifier for the schedule.
            schedule_ids.append(show_id)

    df["schedule_id"] = (
        pd.Series(
            schedule_ids,
            index=df.index
        )
        .astype("Int64")
    )

    # Validation: every non-null schedule_id must be unique.
    duplicate_schedule_ids = (
        df["schedule_id"]
        .dropna()
        .duplicated()
        .sum()
    )

    if duplicate_schedule_ids > 0:

        raise ValueError(
            f"Duplicate schedule IDs found after assignment: "
            f"{duplicate_schedule_ids}"
        )

    unique_schedule_count = (
        df["schedule_id"]
        .dropna()
        .nunique()
    )

    logger.info(
        "Schedule IDs assigned | Unique schedules: %d",
        unique_schedule_count
    )

    return df

#  CREATE DERIVED FIELDS
def create_derived_fields(df):
    """
    Create business/analytical fields required by the project.
    """

    df = df.copy()

    logger.info("Derived field creation started")
   
    # Number of genres
    df["genre_count"] = df["genres"].apply(
        lambda value: (
            len(value)
            if isinstance(value, list)
            else 0
        )
    )
    # Rating availability
    df["has_rating"] = df["rating"].notna()
    # Show duration
    df["show_duration_days"] = (
        df["ended_date"]
        - df["premiered_date"]
    ).dt.days
    # Negative duration is invalid
    invalid_duration = (
        df["show_duration_days"] < 0
    )

    invalid_duration_count = invalid_duration.sum()

    if invalid_duration_count > 0:

        logger.warning(
            "Invalid show durations found: %d",
            invalid_duration_count
        )

        df.loc[
            invalid_duration,
            "show_duration_days"
        ] = pd.NA


    # Currently running
  
    df["is_currently_running"] = (
        df["status"] == "Running"
    )

    logger.info(
        "Derived fields created | Rows: %d | Columns: %d",
        len(df),
        len(df.columns)
    )

    return df

# CREATE GENRES + SHOW_GENRES

def create_genre_tables(df):
    """Create:
        Genres
        ShowGenres
    """

    genre_records = []
    show_genre_records = []

    genre_id_map = {}

    next_genre_id = 1

    for _, row in df.iterrows():

        show_id = row["show_id"]
        genres = row["genres"]

        if not isinstance(genres, list):
            continue

        for genre in genres:

            genre = str(genre).strip()

            if not genre:
                continue

            # ------------------------------------------------
            # Create genre entity
            # ------------------------------------------------

            if genre not in genre_id_map:

                genre_id_map[genre] = next_genre_id

                genre_records.append(
                    {
                        "genre_id": next_genre_id,
                        "genre_name": genre,
                    }
                )

                next_genre_id += 1

            # ------------------------------------------------
            # Create relationship
            # ------------------------------------------------

            show_genre_records.append(
                {
                    "show_id": show_id,
                    "genre_id": genre_id_map[genre],
                }
            )

    genres_df = pd.DataFrame(
        genre_records,
        columns=[
            "genre_id",
            "genre_name",
        ]
    )

    show_genres_df = pd.DataFrame(
        show_genre_records,
        columns=[
            "show_id",
            "genre_id",
        ]
    )

    show_genres_df = (
        show_genres_df
        .drop_duplicates()
        .reset_index(drop=True)
    )

    logger.info(
        "Genre datasets created | Genres: %d | Relationships: %d",
        len(genres_df),
        len(show_genres_df)
    )

    return genres_df, show_genres_df

# CREATE TELEVISION NETWORK
def create_network_table(df):
    """
    Create the Television_Network dataset.

    Shows without a network do not create a network record.
    """
    networks_df = df[
        [
            "network_id",
            "network_name",
            "network_country",
            "network_country_code",
            "network_timezone",
        ]
    ].copy()

    # Keep only valid network IDs
    networks_df = (
        networks_df[
            networks_df["network_id"].notna()
        ]
        .drop_duplicates(
            subset=["network_id"]
        )
        .reset_index(drop=True)
    )
    networks_df = networks_df.rename(
        columns={
            "network_name": "name",
            "network_country": "country",
            "network_country_code": "country_code",
            "network_timezone": "timezone",
        }
    )

    logger.info(
        "Television network dataset created | Networks: %d",
        len(networks_df)
    )

    return networks_df[
        [
            "network_id",
            "name",
            "country",
            "country_code",
            "timezone",
        ]
    ]


# CREATE WEB CHANNEL

def create_webchannel_table(df):
    """
    Create the WebChannel dataset.

    A missing TVMaze webChannel remains NULL in Shows.
    No artificial 'Unknown' web channel is created.
    """

    webchannels_df = df[
        [
            "web_channel_id",
            "web_channel_name",
            "web_channel_official_site",
        ]
    ].copy()

    webchannels_df = (
        webchannels_df[
            webchannels_df["web_channel_id"].notna()
        ]
        .drop_duplicates(
            subset=["web_channel_id"]
        )
        .reset_index(drop=True)
    )

    webchannels_df = webchannels_df.rename(
        columns={
            "web_channel_name": "name",
            "web_channel_official_site": "official_site",
        }
    )

    logger.info(
        "WebChannel dataset created | WebChannels: %d",
        len(webchannels_df)
    )

    return webchannels_df[
        [
            "web_channel_id",
            "name",
            "official_site",
        ]
    ]

# 11. CREATE SCHEDULE DAYS + MAPPING

def create_schedule_day_tables(df):
    """
    Create:

        ScheduleDays
        ShowScheduleDays

    schedule_id refers directly to Shows.schedule_id.
    """

    day_records = []
    show_schedule_day_records = []

    day_id_map = {}

    next_day_id = 1

    for _, row in df.iterrows():

        schedule_id = row["schedule_id"]
        schedule_days = row["schedule_days"]

        # No schedule -> no mapping
        if pd.isna(schedule_id):
            continue

        if not isinstance(schedule_days, list):
            continue

        for day in schedule_days:

            day = str(day).strip().title()

            if not day:
                continue

            # ------------------------------------------------
            # Create day entity
            # ------------------------------------------------

            if day not in day_id_map:

                day_id_map[day] = next_day_id

                day_records.append(
                    {
                        "day_id": next_day_id,
                        "day_name": day,
                    }
                )

                next_day_id += 1

            # ------------------------------------------------
            # Create schedule/day relationship
            # ------------------------------------------------

            show_schedule_day_records.append(
                {
                    "schedule_id": schedule_id,
                    "day_id": day_id_map[day],
                }
            )

    schedule_days_df = pd.DataFrame(
        day_records,
        columns=[
            "day_id",
            "day_name",
        ]
    )

    show_schedule_days_df = pd.DataFrame(
        show_schedule_day_records,
        columns=[
            "schedule_id",
            "day_id",
        ]
    )

    show_schedule_days_df = (
        show_schedule_days_df
        .drop_duplicates()
        .reset_index(drop=True)
    )

    logger.info(
        "Schedule day datasets created | Days: %d | Relationships: %d",
        len(schedule_days_df),
        len(show_schedule_days_df)
    )

    return (
        schedule_days_df,
        show_schedule_days_df,
    )
# 12. FINALIZE SHOWS DATASET

def finalize_shows(df):
    """
    Select the final Shows columns.

    schedule_time remains directly in Shows.
    schedule_days is removed because it has been normalized
    into ScheduleDays + ShowScheduleDays.
    genres is removed because it has been normalized
    into Genres + ShowGenres.
    """

    final_columns = [

        # Primary information
        "show_id",
        "show_name",
        "show_type",
        "language",
        "status",

        # Runtime
        "runtime_minutes",
        "average_runtime_minutes",

        # Dates
        "premiered_date",
        "ended_date",

        # Website
        "official_site",

        # Schedule
        "schedule_id",
        "schedule_time",

        # Rating
        "rating",

        # Relationships
        "network_id",
        "web_channel_id",

        # Other
        "summary",
        "updated_at",

        # Derived fields
        "genre_count",
        "has_rating",
        "show_duration_days",
        "is_currently_running",
    ]

    result = df[
        final_columns
    ].copy()

    logger.info(
        "Shows dataset finalized | Rows: %d | Columns: %d",
        len(result),
        len(result.columns)
    )

    return result
# SAVE PROCESSED DATASETS
def save_processed_datasets(
    shows_df,
    genres_df,
    show_genres_df,
    networks_df,
    webchannels_df,
    schedule_days_df,
    show_schedule_days_df,
    output_dir="data/processed",
):
    """
    Save all transformed datasets as CSV files.
    """

    output_dir = Path(output_dir)

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    datasets = {

        "shows.csv":
            shows_df,

        "genres.csv":
            genres_df,

        "show_genres.csv":
            show_genres_df,

        "television_network.csv":
            networks_df,

        "web_channel.csv":
            webchannels_df,

        "schedule_days.csv":
            schedule_days_df,

        "show_schedule_days.csv":
            show_schedule_days_df,
    }

    for filename, dataframe in datasets.items():

        output_file = (
            output_dir / filename
        )

        dataframe.to_csv(
            output_file,
            index=False
        )

        logger.info(
            "Processed dataset saved | "
            "File: %s | Rows: %d | Columns: %d",
            output_file,
            len(dataframe),
            len(dataframe.columns)
        )

    return output_dir
# MAIN TRANSFORMATION PIPELINE
def transform():
    """
    Execute the complete transformation process.
    """

    logger.info("TRANSFORMATION PIPELINE STARTED")
    # Load raw data

    records = load_raw_data()
    # Normalize JSON

    raw_df = normalize_shows(records)
    # Select required columns
    selected_df = select_show_columns(
        raw_df
    )
    # Clean data

    cleaned_df = clean_shows(
        selected_df
    )
    # Convert data types


    typed_df = convert_data_types(
        cleaned_df
    )
    # Assign unique schedule IDs

    scheduled_df = assign_schedule_ids(
        typed_df
    )
    # Create derived fields

    transformed_df = create_derived_fields(
        scheduled_df
    )
    # Create Genres + ShowGenres

    (
        genres_df,
        show_genres_df,
    ) = create_genre_tables(
        transformed_df
    )
    # Create Television Network

    networks_df = create_network_table(
        transformed_df
    )

    # Create WebChannel

    webchannels_df = create_webchannel_table(
        transformed_df
    )
    # Create ScheduleDays + ShowScheduleDays
 

    (
        schedule_days_df,
        show_schedule_days_df,
    ) = create_schedule_day_tables(
        transformed_df
    )

    # Finalize Shows

    shows_df = finalize_shows(
        transformed_df
    )
    # Save all datasets

    output_dir = save_processed_datasets(
        shows_df=shows_df,
        genres_df=genres_df,
        show_genres_df=show_genres_df,
        networks_df=networks_df,
        webchannels_df=webchannels_df,
        schedule_days_df=schedule_days_df,
        show_schedule_days_df=show_schedule_days_df,
    )
    # Dataset summary
    print("\nDATASET SUMMARY")

    print("Shows:",shows_df.shape)

    print("Genres:",genres_df.shape )

    print("ShowGenres:",show_genres_df.shape)

    print("Television Network:",networks_df.shape)

    print("WebChannel:",webchannels_df.shape)

    print("ScheduleDays:",schedule_days_df.shape)

    print("ShowScheduleDays:",show_schedule_days_df.shape)

    print("\nProcessed files saved to:", output_dir)

    logger.info(
        "TRANSFORMATION PIPELINE COMPLETED"
    )

    return {
        "shows": shows_df,
        "genres": genres_df,
        "show_genres": show_genres_df,
        "television_network": networks_df,
        "web_channel": webchannels_df,
        "schedule_days": schedule_days_df,
        "show_schedule_days": show_schedule_days_df,
    }
