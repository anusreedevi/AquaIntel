
-- 1. Open procurement notices with utility details

SELECT
    p.notice_id,
    p.utility_name,
    p.title,
    p.due_date,
    u.county,
    u.population_served
FROM procurement_notices p
JOIN utilities u ON p.utility_id = u.utility_id
WHERE p.due_date > CURRENT_DATE
ORDER BY p.due_date;


-- 2. Current operations or engineering contacts for each utility

SELECT DISTINCT ON (u.utility_id)
    u.name AS utility_name,
    c.person_name,
    c.title,
    c.email,
    c.phone,
    c.seen_date
FROM utilities u
JOIN contacts c ON u.utility_id = c.utility_id
WHERE
    c.title ILIKE '%operat%'
    OR c.title ILIKE '%engineer%'
ORDER BY u.utility_id, c.seen_date DESC NULLS LAST;


-- 3. Utilities serving more than 50,000 people
-- without notices in the last 12 months

SELECT
    u.utility_id,
    u.name,
    u.county,
    u.population_served
FROM utilities u
WHERE u.population_served > 50000
AND NOT EXISTS (
    SELECT 1
    FROM procurement_notices p
    WHERE p.utility_id = u.utility_id
      AND p.posted_date >= CURRENT_DATE - INTERVAL '12 months'
)
ORDER BY u.population_served DESC;
