# Entertainment ETL Pipeline

## 1. Project Overview

This project is an ETL pipeline built using Python, Pandas and PostgreSQL. It extracts TV show data from the TVMaze API, cleans and transforms the data, and loads the processed data into a PostgreSQL database.

The pipeline follows:

```text
Extract -> Transform -> Load -> Validate
```

Raw API responses are also stored as JSON files so the source data can be checked or processed again when required.

## 2. Dataset Selection

The data is collected from the TVMaze API:

```text
https://api.tvmaze.com/shows?page={page}
```

The API provides show information such as name, type, language, genres, status, runtime, dates, rating, network, web channel and schedule.

The API is paginated. The pipeline continues requesting pages until there are no more pages available. The extraction produced **90,233 show records from 379 successful pages**.

Each API page is stored separately under:

```text
data/raw/
```

Keeping the raw JSON files makes the extraction reproducible and preserves the source data used for transformation.

## 3. Database Design

PostgreSQL is used as the target database. The data is divided into seven tables:

- `Shows`
- `Genres`
- `ShowGenres`
- `Television_Network`
- `WebChannel`
- `ScheduleDays`
- `ShowScheduleDays`

`Shows` contains the main show information. Repeated information such as genres, networks and schedule days is stored separately.

The schedule time is kept directly in `Shows`. Schedule days are stored separately because a show can have more than one schedule day.

## 4. Primary Keys

Primary keys uniquely identify records.

| Table | Primary Key |
|---|---|
| Shows | `show_id` |
| Genres | `genre_id` |
| Television_Network | `network_id` |
| WebChannel | `web_channel_id` |
| ScheduleDays | `day_id` |
| ShowGenres | `show_id, genre_id` |
| ShowScheduleDays | `schedule_id, day_id` |

The relationship tables use composite primary keys to prevent the same relationship from being inserted more than once.

## 5. Foreign Keys

Foreign keys maintain valid relationships between tables.

- `Shows.network_id` -> `Television_Network.network_id`
- `Shows.web_channel_id` -> `WebChannel.web_channel_id`
- `ShowGenres.show_id` -> `Shows.show_id`
- `ShowGenres.genre_id` -> `Genres.genre_id`
- `ShowScheduleDays.schedule_id` -> `Shows.schedule_id`
- `ShowScheduleDays.day_id` -> `ScheduleDays.day_id`

`web_channel_id` can be NULL because the API does not provide a web channel for every show.

## 6. Relationships

A network can have many shows, while a show belongs to one network when network information is available.

A show can have multiple genres, and a genre can belong to many shows. This many-to-many relationship is handled through `ShowGenres`.

A show can also have multiple schedule days. `ShowScheduleDays` connects shows with their schedule days.

```text
Television_Network ---< Shows >--- WebChannel
                         |
                         +--- ShowGenres >--- Genres
                         |
                         +--- ShowScheduleDays >--- ScheduleDays
```

## 7. Transformations

The raw JSON data is processed using Pandas.

The main transformations include:

- Cleaning column names and values.
- Handling missing values.
- Converting numeric fields to appropriate types.
- Converting date fields.
- Extracting genres, networks and web channels.
- Extracting schedule days.
- Creating unique schedule IDs.
- Removing duplicate records.
- Creating separate relationship datasets.
- Preparing the final datasets for PostgreSQL.

Processed files are saved under:

```text
data/processed/
```

The main files are:

```text
shows.csv
genres.csv
show_genres.csv
television_network.csv
web_channel.csv
schedule_days.csv
show_schedule_days.csv
```

## 8. Business Rules

The following rules are applied during transformation and validation:

- `show_id` must be unique.
- Show names cannot be empty.
- Ratings must be between 0 and 10 when available.
- Runtime values must be positive when available.
- Average runtime values must be positive when available.
- Genre count cannot be negative.
- Schedule IDs must be unique when schedule information exists.
- Relationship records must reference existing records.
- A show can have multiple genres and schedule days.
- A show does not have to have a web channel.

## 9. Derived Fields

Some fields are calculated from the source data.

### `genre_count`
Number of genres associated with a show.

### `has_rating`
Indicates whether a rating is available.

### `show_duration_days`
Calculates the duration between the premiere and ending dates when both are available.

### `is_currently_running`
Indicates whether a show is currently running based on its status and date information.

These fields make the data easier to use for analysis.

## 10. Batch Loading

The processed CSV files are loaded into PostgreSQL in batches of **500 records**.

Batch loading avoids sending the complete dataset in one database operation and makes the loading process easier to manage.

Tables are loaded in dependency order so that foreign-key constraints are satisfied.

## 11. Transactions

The database loading process is handled as a transaction.

```text
Start transaction
       |
       v
Load datasets
       |
   +---+---+
   |       |
Success   Failure
   |       |
Commit   Rollback
```

This prevents the database from being left in a partially loaded state if an error occurs.

## 12. Commit and Rollback

When all datasets are loaded successfully, the transaction is committed and the changes are saved.

If an error occurs, the transaction is rolled back.

A rollback test was performed by intentionally attempting to insert the same primary key twice. PostgreSQL rejected the duplicate record, the transaction was rolled back, and the temporary record was confirmed to be absent afterward.

## 13. Idempotency

The pipeline is designed to be safely run more than once.

Primary keys, unique constraints and conflict handling are used to prevent unintended duplicates.

- Parent tables use UPSERT operations where updates are required.
- Relationship tables use `ON CONFLICT DO NOTHING`.
- Primary and composite keys prevent duplicate records.

The complete pipeline was run twice. The row counts remained unchanged after the second run, confirming that repeated execution did not create unintended duplicates.

## 14. Failure Scenario

A controlled failure was tested during database loading.

The test attempted to insert the same `show_id` twice. The second insert caused a PostgreSQL unique-constraint error.

The error was detected, the transaction was rolled back, and the database was checked afterward. The temporary test record was not present.

This confirmed that a failed transaction does not leave the test data in the database.

## 15. Assumptions

- TVMaze is treated as the source of truth for the extracted show information.
- API pagination continues until the API indicates that there are no more pages.
- Missing web channel information is stored as NULL rather than creating a fake web channel.
- A show can have multiple genres.
- A show can have multiple schedule days.
- Raw JSON files are retained for reproducibility.
- PostgreSQL is the final storage layer.
- The pipeline should be safe to run repeatedly without creating unintended duplicates.

## 16. Running the Pipeline

Install the required packages:

```bash
pip install -r requirements.txt
```

Configure the database connection in `.env`, then run:

```bash
python -m main
```

The pipeline executes:

```text
Extraction
    |
Transformation
    |
Database Loading
    |
Validation
```

Logs are generated during execution to track progress and record errors.
