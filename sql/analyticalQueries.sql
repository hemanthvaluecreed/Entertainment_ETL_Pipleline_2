
---Analytical sql queries : these helps to find the patterns,understand insights from the data


--  Business Question:
--  How many shows are available in each genre?
-- 1. Number of Shows by Genre

SELECT
    g.genre_name,
    COUNT(sg.show_id) AS show_count
FROM Genres g
LEFT JOIN ShowGenres sg
    ON g.genre_id = sg.genre_id
GROUP BY
    g.genre_id,
    g.genre_name
ORDER BY
    show_count DESC;



-- Business Question:
-- What is the average rating of shows in each genre?
-- 2. Average Rating by Genre


SELECT
    g.genre_name,
    ROUND(AVG(s.rating), 2) AS average_rating,
    COUNT(s.show_id) AS rated_show_count
FROM Genres g
JOIN ShowGenres sg
    ON g.genre_id = sg.genre_id
JOIN Shows s
    ON sg.show_id = s.show_id
WHERE s.rating IS NOT NULL
GROUP BY
    g.genre_id,
    g.genre_name
ORDER BY
    average_rating DESC;



-- Business Question:
-- How many shows are associated with each television network?
-- 3. Number of Shows by Television Network


SELECT
    tn.name AS network_name,
    COUNT(s.show_id) AS show_count
FROM Television_Network tn
LEFT JOIN Shows s
    ON tn.network_id = s.network_id
GROUP BY
    tn.network_id,
    tn.name
ORDER BY
    show_count DESC;

-- Business Question:
-- Which shows are currently running?
-- 4. Currently Running Shows


SELECT
    show_id,
    show_name,
    status,
    premiered_date,
    rating,
    network_id,
    web_channel_id
FROM Shows
WHERE is_currently_running = TRUE
ORDER BY
    show_name;



-- Business Question:
-- On which days are shows most commonly scheduled?
-- 5. Number of Shows Scheduled by Day


SELECT
    sd.day_name,
    COUNT(ssd.schedule_id) AS scheduled_show_count
FROM ScheduleDays sd
LEFT JOIN ShowScheduleDays ssd
    ON sd.day_id = ssd.day_id
GROUP BY
    sd.day_id,
    sd.day_name
ORDER BY
    scheduled_show_count DESC;


-- Business Question:
-- How many shows do not have an associated web channel?
-- 6. Shows Without a Web Channel


SELECT
    COUNT(*) AS shows_without_web_channel
FROM Shows
WHERE web_channel_id IS NULL;



-- Business Question:
-- How has the number of shows changed over time?
-- 7. Number of Shows by Premiere Year

SELECT
    EXTRACT(YEAR FROM premiered_date) AS premiere_year,
    COUNT(*) AS show_count
FROM Shows
WHERE premiered_date IS NOT NULL
GROUP BY
    EXTRACT(YEAR FROM premiered_date)
ORDER BY
    premiere_year;
