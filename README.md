# AquaIntel – Utility Data Management System

## About the Project

AquaIntel is a Python project that I developed to manage utility information collected from different CSV files. The main objective was to bring utility registry details, procurement notices, and contact information into one PostgreSQL database and connect the records that belong to the same utility.

One challenge I came across was that utility names were not always written in the same way across the CSV files. For example, one file might contain "Brennan Twp. Municipal Auth." while another contains "Brennan Township Municipal Authority". Since both can refer to the same utility, comparing names directly would not be reliable.

To handle this, I implemented a name-cleaning and fuzzy-matching process using Python and RapidFuzz. The system automatically links clear matches and keeps uncertain records for manual review.

## Technologies Used

I used Python for data processing and database operations, PostgreSQL for storing the information, and Pandas for reading and cleaning the CSV files. Psycopg2 is used to connect Python with PostgreSQL, while RapidFuzz handles utility name comparisons.

I also used Supabase to host a PostgreSQL database so the project could be demonstrated without requiring someone to set up a local database first.

## How I Designed the Database

I created four tables in PostgreSQL: `utilities`, `facilities`, `procurement_notices`, and `contacts`.

The `utilities` table acts as the main registry. It stores each utility's registry ID, name, location, county, state, and population served. I used the registry ID as a unique identifier to avoid storing the same utility more than once.

The `procurement_notices` and `contacts` tables store information from the other two CSV files. Both tables contain a `utility_id` to connect a record to the main utility registry. I also added `match_status` and `match_confidence` fields to keep track of the matching results. When a record is not confidently matched, its suggested utility ID is stored separately in `candidate_utility_id`.

The `facilities` table stores facility details linked to utilities. The supplied CSV files did not include a separate facilities dataset, so I added three sample facility records for demonstration. These are synthetic records, not actual verified facility information.

## Importing the CSV Files

I implemented the data import process in `src/ingestion.py`.

First, I used Pandas to read the three CSV files. Before inserting the utility records, I checked for missing registry IDs and utility names and removed duplicate registry IDs. The original utility registry contained 27 records, but after cleaning, 25 unique utilities remained.

For procurement notices, I noticed that some notice URLs appeared more than once. Since the notice URL identifies a notice, I used it as a unique field and removed duplicate URLs before inserting the records.

For contacts, I generated a SHA-256 key from the source record details. This gives each source contact record a consistent identifier and helps prevent duplicate insertions when the script is executed again.

I also used PostgreSQL's `ON CONFLICT DO NOTHING` to avoid inserting records that already exist. This makes the ingestion process safe to run multiple times without creating duplicate records.

The database operations are handled using transactions. If everything succeeds, the changes are committed. If an error occurs, the transaction is rolled back, and the connection is closed.

## Matching Utility Names

I implemented the matching logic separately in `src/matching.py` so that the ingestion process and matching process remain easy to understand and maintain.

Before comparing utility names, I created a `normalize_name()` function. It converts names to lowercase, removes punctuation, and expands common abbreviations such as:

- `Twp.` into `Township`
- `Auth.` into `Authority`
- `Dept.` into `Department`
- `Dist.` into `District`
- `Boro.` into `Borough`

After cleaning the names, I used RapidFuzz's `token_set_ratio()` function to compare the source utility name with the names in the main registry. It returns a similarity score between 0 and 100.

I used the following rules to decide the matching status:

- A score of 90 or above is considered a match only when the best candidate is at least 10 points ahead of the second-best candidate.
- A score of 75 or above that does not satisfy the matching condition is marked for review.
- Scores below 75 are marked as unmatched.

I added the second-candidate check because some utilities have similar names. Automatically selecting one of them based only on a high score could connect a record to the wrong utility.

For records marked as review, I save the suggested utility ID in `candidate_utility_id` and leave the actual `utility_id` empty. This allows someone to verify the record before making the final connection.

After matching, the results are saved back into the contacts and procurement tables.

## Matching Results

After running the matching process with the supplied data, I obtained the following results.

**Contacts – 51 records**

- Matched: 47
- Review: 4
- Unmatched: 0

**Procurement Notices – 48 records**

- Matched: 41
- Review: 6
- Unmatched: 1

The records marked for review are not automatically linked to a utility. They can be checked manually to avoid incorrect associations.

## SQL Queries

I created three queries in `sql/queries.sql` to retrieve information from the database.

The first query retrieves open procurement notices by checking whether the due date is later than the current date. It also displays the corresponding utility's county and population served.

The second query finds contacts whose job titles contain operations-related or engineering-related terms. I used `DISTINCT ON` with the contact's `seen_date` to retrieve the most recently seen matching contact for each utility.

The third query identifies utilities serving more than 50,000 people that have not received a matched procurement notice during the last 12 months. I used `NOT EXISTS` to check whether a qualifying notice is available for each utility.

## Testing

I added basic unit tests in `test/test_ingestion.py` using Python's built-in `unittest` module.

The tests check whether utility names are normalized correctly, whether an exact utility match is identified, and whether an unrelated utility name is handled as unmatched.

To run the tests:


py -m unittest discover -s test


All three implemented tests passed successfully.

## Running the Project

### 1. Clone the repository


git clone https://github.com/anusreedevi/AquaIntel.git
cd AquaIntel


### 2. Create and activate a virtual environment


py -m venv venv
venv\Scripts\Activate


### 3. Install the required packages


pip install -r requirements.txt


### 4. Configure the database

Create a `.env` file in the project root with the PostgreSQL connection details.

For a local PostgreSQL database:


DB_HOST=localhost
DB_PORT=5432
DB_NAME=aquaintel
DB_USER=postgres
DB_PASSWORD=your_password


For the hosted Supabase database, use the Session Pooler connection details from the Supabase project instead.

### 5. Create the database tables

Execute `sql/schema.sql` in pgAdmin or the Supabase SQL Editor.

### 6. Import the CSV data

Run the following command from the project root:


py -m src.ingestion


### 7. Run utility matching


py -m src.matching


### 8. Add the sample facilities

Execute `sql/schema.sql` again after ingestion. The sample facility records depend on the utilities already being present in the database.

### 9. Run the SQL queries

Open `sql/queries.sql` in pgAdmin or the Supabase SQL Editor and execute the queries individually.

### 10. Run the tests


py -m unittest discover -s test


## Hosted Database

I also configured the project to connect to a hosted PostgreSQL database using Supabase. This makes it possible to keep the demonstration data available online rather than requiring a separate local database setup.

The current hosted database contains:

- 25 utility records
- 48 procurement notices
- 51 contact records
- 3 sample facility records

The database connection is configured through environment variables, and SSL is enabled for the hosted connection. Database credentials are kept in the local `.env` file and are not included in the GitHub repository.

The Supabase project is private, so anyone who needs to inspect the live database must be given appropriate access separately.

## What I Would Improve Next

The current version covers CSV ingestion, duplicate handling, utility matching, manual review identification, and SQL-based data retrieval.

If I extend this project further, I would like to add a simple manual review process where uncertain matches can be approved or rejected. I would also improve matching by considering additional location details such as city and county, add more tests, and automate the ingestion process for regular updates.

For larger datasets, I would consider PostgreSQL bulk loading, batch processing, and incremental updates so that only new or changed records need to be processed.

## Repository

GitHub: https://github.com/anusreedevi/AquaIntel