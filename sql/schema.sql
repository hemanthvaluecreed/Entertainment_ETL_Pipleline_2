
-- Entertainment ETL Pipeline
-- PostgreSQL Database Schema

-- 1. GENRES
CREATE TABLE IF NOT EXISTS Genres (
    genre_id INTEGER PRIMARY KEY,
    genre_name VARCHAR(100) NOT NULL UNIQUE
);


-- 2. TELEVISION NETWORK

CREATE TABLE IF NOT EXISTS Television_Network (
    network_id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    country VARCHAR(100),
    country_code VARCHAR(10),
    timezone VARCHAR(100)
);

-- 3. WEB CHANNEL

CREATE TABLE IF NOT EXISTS WebChannel (
    web_channel_id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    official_site TEXT
);

-- 4. SCHEDULE DAYS

CREATE TABLE IF NOT EXISTS ScheduleDays (
    day_id INTEGER PRIMARY KEY,
    day_name VARCHAR(20) NOT NULL UNIQUE
);

-- 5. SHOWS

CREATE TABLE IF NOT EXISTS Shows (
    show_id INTEGER PRIMARY KEY,

    show_name VARCHAR(500) NOT NULL,
    show_type VARCHAR(100),
    language VARCHAR(100),
    status VARCHAR(50),

    runtime_minutes INTEGER,
    average_runtime_minutes INTEGER,

    premiered_date DATE,
    ended_date DATE,

    official_site TEXT,

    -- Schedule
    schedule_id INTEGER UNIQUE,
    schedule_time TIME,

    -- Rating
    rating NUMERIC(3,1),

    -- Relationships
    network_id INTEGER,
    web_channel_id INTEGER,

    -- Other
    summary TEXT,
    updated_at TIMESTAMPTZ,

    -- Derived fields
    genre_count INTEGER,
    has_rating BOOLEAN NOT NULL DEFAULT FALSE,
    show_duration_days INTEGER,
    is_currently_running BOOLEAN NOT NULL DEFAULT FALSE,

    -- Constraints
    CONSTRAINT chk_show_runtime
        CHECK (
            runtime_minutes IS NULL
            OR runtime_minutes > 0
        ),

    CONSTRAINT chk_average_runtime
        CHECK (
            average_runtime_minutes IS NULL
            OR average_runtime_minutes > 0
        ),

    CONSTRAINT chk_rating
        CHECK (
            rating IS NULL
            OR rating BETWEEN 0 AND 10
        ),

    CONSTRAINT chk_genre_count
        CHECK (
            genre_count IS NULL
            OR genre_count >= 0
        ),

    CONSTRAINT chk_duration
        CHECK (
            show_duration_days IS NULL
            OR show_duration_days >= 0
        ),

    -- Foreign keys
    CONSTRAINT fk_shows_network
        FOREIGN KEY (network_id)
        REFERENCES Television_Network(network_id),

    CONSTRAINT fk_shows_web_channel
        FOREIGN KEY (web_channel_id)
        REFERENCES WebChannel(web_channel_id)
);

-- 6. SHOW ↔ GENRE

CREATE TABLE IF NOT EXISTS ShowGenres (
    show_id INTEGER NOT NULL,
    genre_id INTEGER NOT NULL,

    PRIMARY KEY (show_id, genre_id),

    CONSTRAINT fk_showgenres_show
        FOREIGN KEY (show_id)
        REFERENCES Shows(show_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_showgenres_genre
        FOREIGN KEY (genre_id)
        REFERENCES Genres(genre_id)
        ON DELETE CASCADE
);



-- 7. SHOW ↔ SCHEDULE DAY

CREATE TABLE IF NOT EXISTS ShowScheduleDays (
    schedule_id INTEGER NOT NULL,
    day_id INTEGER NOT NULL,

    PRIMARY KEY (schedule_id, day_id),

    CONSTRAINT fk_showscheduledays_schedule
        FOREIGN KEY (schedule_id)
        REFERENCES Shows(schedule_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_showscheduledays_day
        FOREIGN KEY (day_id)
        REFERENCES ScheduleDays(day_id)
        ON DELETE CASCADE
);