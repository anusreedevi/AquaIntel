import pandas as pd
import hashlib
import json
import re
from pathlib import Path

from src.database import get_connection

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


# Convert empty CSV values into Python None
def clean_value(value):

    if pd.isna(value):
        return None

    if isinstance(value, str):
        value = value.strip()

        if value == "":
            return None

    return value


# Convert CSV dates into Python date objects
def clean_date(value):

    value = clean_value(value)

    if value is None:
        return None

    parsed_date = pd.to_datetime(value, errors="coerce")

    if pd.isna(parsed_date):
        return None

    return parsed_date.date()


# Convert currency values into numbers
def clean_amount(value):

    value = clean_value(value)

    if value is None:
        return None

    amount = re.sub(r"[^0-9.]", "", str(value))

    if not amount:
        return None

    return float(amount)


# Generate a stable key for each contact record
def generate_contact_key(row):

    record = [
        clean_value(row.get("utility_name")),
        clean_value(row.get("person_name")),
        clean_value(row.get("title")),
        clean_value(row.get("email")),
        clean_value(row.get("phone")),
        clean_value(row.get("source_url")),
        (
            str(clean_date(row.get("seen_date")))
            if clean_date(row.get("seen_date"))
            else None
        ),
    ]

    record_json = json.dumps(record, ensure_ascii=False)

    return hashlib.sha256(record_json.encode("utf-8")).hexdigest()


def import_utilities(connection):

    # Read the utilities CSV file
    file_path = DATA_DIR / "utilities_registry.csv"
    df = pd.read_csv(file_path, dtype={"registry_id": "string"})

    print("\nImporting utilities...")
    print("Original records:", len(df))

    # Remove records with missing registry ID or utility name
    df = df.dropna(subset=["registry_id", "name"])

    # Remove duplicate registry IDs
    df = df.drop_duplicates(subset=["registry_id"], keep="first")

    # Create cursor to execute SQL queries
    cursor = connection.cursor()

    # Insert each utility into PostgreSQL
    for _, row in df.iterrows():

        # Convert missing population to None (SQL NULL)
        if pd.isna(row["population_served"]):
            population = None
        else:
            population = int(row["population_served"])

        cursor.execute(
            """
            INSERT INTO utilities (
                registry_id,
                name,
                city,
                county,
                state,
                population_served,
                system_type
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (registry_id) DO NOTHING
        """,
            (
                row["registry_id"],
                row["name"],
                row["city"] if pd.notna(row["city"]) else None,
                row["county"] if pd.notna(row["county"]) else None,
                row["state"] if pd.notna(row["state"]) else None,
                population,
                row["system_type"] if pd.notna(row["system_type"]) else None,
            ),
        )

    cursor.close()

    print("Cleaned utility records:", len(df))
    print("Utilities imported successfully!")


# ==========================================
# IMPORT PROCUREMENT NOTICES
# ==========================================


def import_procurement_notices(connection):

    file_path = DATA_DIR / "procurement_notices.csv"

    df = pd.read_csv(file_path)

    print("Procurement CSV rows:", len(df))

    duplicate_count = df.duplicated(subset=["notice_url"]).sum()

    print("Duplicate notice URLs:", duplicate_count)

    # One procurement notice per unique URL.
    # Keep the first source record for now.
    df = df.drop_duplicates(subset=["notice_url"], keep="first")

    query = """
        INSERT INTO procurement_notices (
            notice_url,
            utility_name,
            title,
            category,
            posted_date,
            due_date,
            estimated_value,
            match_status
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending')

        ON CONFLICT (notice_url)
        DO UPDATE SET
            utility_name = EXCLUDED.utility_name,
            title = EXCLUDED.title,
            category = EXCLUDED.category,
            posted_date = EXCLUDED.posted_date,
            due_date = EXCLUDED.due_date,
            estimated_value = EXCLUDED.estimated_value,
            updated_at = CURRENT_TIMESTAMP;
    """

    with connection.cursor() as cursor:

        for _, row in df.iterrows():

            cursor.execute(
                query,
                (
                    clean_value(row["notice_url"]),
                    clean_value(row["utility_name"]),
                    clean_value(row["title"]),
                    clean_value(row["category"]),
                    clean_date(row["posted_date"]),
                    clean_date(row["due_date"]),
                    clean_amount(row["estimated_value"]),
                ),
            )

    print("Procurement notices processed:", len(df))


# ==========================================
# IMPORT CONTACTS
# ==========================================


def import_contacts(connection):

    file_path = DATA_DIR / "contacts.csv"

    df = pd.read_csv(file_path)

    print("Contacts CSV rows:", len(df))

    query = """
        INSERT INTO contacts (
            source_record_key,
            utility_name,
            person_name,
            title,
            email,
            phone,
            source_url,
            seen_date,
            match_status
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending')

        ON CONFLICT (source_record_key)
        DO NOTHING;
    """

    with connection.cursor() as cursor:

        for _, row in df.iterrows():

            cursor.execute(
                query,
                (
                    generate_contact_key(row),
                    clean_value(row["utility_name"]),
                    clean_value(row["person_name"]),
                    clean_value(row["title"]),
                    clean_value(row["email"]),
                    clean_value(row["phone"]),
                    clean_value(row["source_url"]),
                    clean_date(row["seen_date"]),
                ),
            )

    print("Contacts processed:", len(df))


# ==========================================
# MAIN FUNCTION
# ==========================================


def main():

    connection = get_connection()

    if connection is None:
        return

    try:
        import_utilities(connection)
        import_procurement_notices(connection)

        import_contacts(connection)

        connection.commit()

        print("\nAll CSV files imported successfully!")

    except Exception as error:

        connection.rollback()

        print("Import failed:", error)

    finally:

        connection.close()

        print("Database connection closed.")


if __name__ == "__main__":
    main()
