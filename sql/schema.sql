

-- 1. MAIN UTILITIES TABLE
CREATE TABLE IF NOT EXISTS utilities (
    utility_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    registry_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    city VARCHAR(150),
    county VARCHAR(150),
    state VARCHAR(100),
    population_served INTEGER,
    system_type VARCHAR(150),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- 2. FACILITIES TABLE
CREATE TABLE IF NOT EXISTS facilities (
    facility_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    utility_id BIGINT NOT NULL,
    facility_name VARCHAR(255) NOT NULL,
    facility_type VARCHAR(100),
    city VARCHAR(150),
    state VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_facility_utility
        FOREIGN KEY (utility_id)
        REFERENCES utilities(utility_id)
        ON DELETE CASCADE
);


-- 3. PROCUREMENT NOTICES TABLE
CREATE TABLE IF NOT EXISTS procurement_notices (
    notice_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    utility_id BIGINT,
    notice_url TEXT UNIQUE NOT NULL,
    utility_name VARCHAR(255) NOT NULL,
    title TEXT,
    category VARCHAR(150),
    posted_date DATE,
    due_date DATE,
    estimated_value NUMERIC(15,2),

    match_status VARCHAR(20) DEFAULT 'pending',
    match_confidence NUMERIC(5,2),
    candidate_utility_id BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_notice_utility
        FOREIGN KEY (utility_id)
        REFERENCES utilities(utility_id)
        ON DELETE SET NULL,

    CONSTRAINT chk_notice_match_status
        CHECK (
            match_status IN (
                'pending',
                'matched',
                'review',
                'unmatched'
            )
        ),

    CONSTRAINT chk_notice_confidence
        CHECK (
            match_confidence IS NULL OR
            match_confidence BETWEEN 0 AND 100
        )
);


-- 4. CONTACTS TABLE
CREATE TABLE IF NOT EXISTS contacts (
    contact_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    utility_id BIGINT,
    source_record_key VARCHAR(64) UNIQUE NOT NULL,
    utility_name VARCHAR(255) NOT NULL,
    person_name VARCHAR(255),
    title VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    source_url TEXT,
    seen_date DATE,

    match_status VARCHAR(20) DEFAULT 'pending',
    match_confidence NUMERIC(5,2),
    candidate_utility_id BIGINT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_contact_utility
        FOREIGN KEY (utility_id)
        REFERENCES utilities(utility_id)
        ON DELETE SET NULL,

    CONSTRAINT chk_contact_match_status
        CHECK (
            match_status IN (
                'pending',
                'matched',
                'review',
                'unmatched'
            )
        ),

    CONSTRAINT chk_contact_confidence
        CHECK (
            match_confidence IS NULL OR
            match_confidence BETWEEN 0 AND 100
        )
);




CREATE INDEX IF NOT EXISTS idx_facilities_utility
ON facilities(utility_id);

CREATE INDEX IF NOT EXISTS idx_notices_utility
ON procurement_notices(utility_id);

CREATE INDEX IF NOT EXISTS idx_notices_due_date
ON procurement_notices(due_date);

CREATE INDEX IF NOT EXISTS idx_notices_posted_date
ON procurement_notices(posted_date);

CREATE INDEX IF NOT EXISTS idx_notices_match_status
ON procurement_notices(match_status);

CREATE INDEX IF NOT EXISTS idx_contacts_utility
ON contacts(utility_id);

CREATE INDEX IF NOT EXISTS idx_contacts_seen_date
ON contacts(seen_date);

CREATE INDEX IF NOT EXISTS idx_contacts_match_status
ON contacts(match_status);
