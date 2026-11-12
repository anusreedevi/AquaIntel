# AquaIntel – Utility Data Management System

## 1. Project Overview

AquaIntel is a Python project that imports utility, procurement notice, and contact information from CSV files into a PostgreSQL database.

It also matches utility names from the contact and procurement files with the main utility registry. Since names may be written differently in different files, the project uses name cleaning and fuzzy matching to find possible matches.

If a match is not clear, it is marked for manual review instead of linking it to the wrong utility.

## 2. Technologies Used

- Python
- PostgreSQL
- Pandas
- Psycopg2
- RapidFuzz
- Python-dotenv
- SQL

## 3. Project Folder Structure


AquaIntel/
│
├── data/
│   ├── utilities_registry.csv
│   ├── procurement_notices.csv
│   └── contacts.csv
│
├── sql/
│   └── schema.sql
|   └── queries.sql
│
├── src/
│   ├── __init__.py
│   ├── database.py
│   ├── ingestion.py
│   └── matching.py
│
│   
│
├── test/
│   └── test_ingestion.py
│
├── .env
├── .gitignore
├── requirements.txt
└── README.md


## 4. Database Tables

I created four tables in PostgreSQL:

- **utilities:** Stores utility details such as name, registry ID, city, county, state, and population served.
- **facilities:** Stores facility details linked to the corresponding utility.
- **procurement_notices:** Stores procurement notice information, including title, dates, category, and estimated value.
- **contacts:** Stores contact information such as person name, job title, email, and phone number.

The contacts and procurement notices tables also store matching status and confidence scores.

## 5. How to Set Up the Project

### Step 1: Create a virtual environment


py -m venv venv


Activate it using:


venv\Scripts\activate


### Step 2: Install the required packages


pip install -r requirements.txt


### Step 3: Create the database

Open PostgreSQL or pgAdmin and create a database named: aquaintel


### Step 4: Configure the database connection

Create a `.env` file in the main project folder and add your PostgreSQL details:


DB_HOST=localhost
DB_PORT=5432
DB_NAME=aquaintel
DB_USER=postgres
DB_PASSWORD=your_password


Replace `your_password` with your PostgreSQL password.

### Step 5: Create the tables

Open `sql/schema.sql` in pgAdmin and execute the SQL statements to create the tables.

## 6. How to Run the Project

Run the following commands from the main AquaIntel project folder.

### First: Import the CSV data


py -m src.ingestion


This script reads the three CSV files and inserts their data into PostgreSQL.

It also handles duplicate records so that running the script again does not create duplicate utilities, procurement notices, or contacts.

### Second: Match utilities with contacts and notices


py -m src.matching


This script compares utility names from the contacts and procurement files with the names in the utility registry.

The matching results are saved in the database.

### Third: Run the SQL queries

Open `sql/queries.sql` in pgAdmin and execute the queries.

The file contains three queries:

1. Finds open procurement notices and displays the related utility's county and population.
2. Finds the latest operations or engineering-related contact for each matched utility.
3. Finds utilities serving more than 50,000 people that have not posted a procurement notice in the last 12 months.

## 7. How Utility Matching Works

Utility names may appear differently in different CSV files. For example, a name may contain abbreviations such as `Twp.` or `Auth.`.

To handle this, I used Python to clean the names before comparing them.

The project uses the RapidFuzz library to calculate how closely two utility names match.

Based on the matching score, records are classified into three categories:

| Matching condition | Status |
|---|---|
| Score is 90 or above and is at least 10 points higher than the second candidate | Matched |
| Score is 75 or above but does not meet the matched condition | Review |
| Score is below 75 | Unmatched |

- **Matched:** A suitable utility is identified and linked.
- **Review:** A possible utility is identified, but the match needs to be checked.
- **Unmatched:** No suitable utility is found.

For review and unmatched records, the candidate utility ID is saved when available. This helps with checking the records later.

## 8. Data Handling and Limitations

- Duplicate registry IDs are removed before importing utility records.
- Duplicate procurement notice URLs are skipped.
- Contact records use a generated unique key to avoid importing the same record again.
- Missing values such as email, phone number, population, and estimated value are allowed to remain empty.
- Some utility names are similar, so not every record can be matched automatically.
- Contact matching mainly uses utility names because city and county details are not available in the contacts CSV.
- Records marked for review may need manual verification.
- The facilities table is created, but the provided CSV files do not contain facility data.

## 9. Running the Tests

To run the unit tests, execute:

py -m unittest discover -s test


The test check:

- Utility name normalization.
- Successful utility matching.
- Handling of unmatched utility names.

## 10. Handling Larger Data and Daily Updates

If the project needs to handle around 50,000 utilities, a few improvements can help:

- Use PostgreSQL bulk loading to import large amounts of data faster.
- Add indexes to frequently searched database columns.
- Process records in batches instead of one at a time.
- Save normalized utility names so they do not need to be cleaned repeatedly.
- Import only new or updated records during regular updates.
- Schedule the scripts to run automatically every night using Windows Task Scheduler or Linux cron.
- Keep logs of errors and records that need manual review.

These improvements can help the project handle larger datasets and regular updates more efficiently.