import re
from rapidfuzz import fuzz
from src.database import get_connection

# Convert utility names into a standard format


def normalize_name(name):
    if not name:
        return ""

    name = str(name).lower().strip()

    replacements = {
        "dept": "department",
        "auth": "authority",
        "dist": "district",
        "twp": "township",
        "boro": "borough",
        "muni": "municipal",
        "mun": "municipal",
        "wa": "water authority",
        "hts": "heights",
        "co": "company",
        "co-op": "cooperative",
        "w&s": "water and sewer",
    }

    # Replace punctuation with spaces
    name = re.sub(r"[^a-z0-9\s-]", " ", name)

    words = name.split()

    # Expand abbreviations
    words = [replacements.get(word, word) for word in words]

    return " ".join(words)


# Compare one source name with registry utility names


def match_utility(source_name, utilities, city=None, county=None):
    aliases = {"pcwa": "prescott county water authority"}

    source_name = normalize_name(source_name)
    source_name = aliases.get(source_name, source_name)

    results = []

    for utility in utilities:

        registry_name = normalize_name(utility["name"])

        # Compare utility names
        score = fuzz.token_set_ratio(source_name, registry_name)

        # Give a small bonus when city matches
        if city and utility["city"]:
            if city.lower().strip() == utility["city"].lower().strip():
                score = min(score + 5, 100)

        # Give a small bonus when county matches
        if county and utility["county"]:
            if county.lower().strip() == utility["county"].lower().strip():
                score = min(score + 5, 100)

        results.append(
            {
                "utility_id": utility["utility_id"],
                "name": utility["name"],
                "score": score,
            }
        )

    # Sort candidates from highest score to lowest
    results.sort(key=lambda item: item["score"], reverse=True)

    if not results:
        return {
            "utility_id": None,
            "candidate_utility_id": None,
            "confidence": 0,
            "status": "unmatched",
        }

    best = results[0]

    # Check second-best candidate
    second_score = results[1]["score"] if len(results) > 1 else 0

    # Decide matching status
    if best["score"] >= 90 and best["score"] - second_score >= 10:
        status = "matched"
        utility_id = best["utility_id"]

    elif best["score"] >= 75:
        status = "review"
        utility_id = None

    else:
        status = "unmatched"
        utility_id = None

    return {
        "utility_id": utility_id,
        "candidate_utility_id": best["utility_id"],
        "confidence": round(best["score"], 2),
        "status": status,
    }


if __name__ == "__main__":

    connection = get_connection()

    if connection:

        cursor = connection.cursor()

        try:
            # Get all utilities from PostgreSQL
            cursor.execute("""
                    SELECT utility_id, name, city, county, state
                    FROM utilities
                """)

            rows = cursor.fetchall()

            utilities = []

            for row in rows:
                utilities.append(
                    {
                        "utility_id": row[0],
                        "name": row[1],
                        "city": row[2],
                        "county": row[3],
                        "state": row[4],
                    }
                )
            print("\nTotal utilities:", len(utilities))

            # Get first 10 contact records
            cursor.execute("""
                SELECT utility_name
                FROM contacts
                WHERE utility_name IS NOT NULL
                
            """)

            contacts = cursor.fetchall()

            print("\nCONTACT MATCHING RESULTS")

            for row in contacts:
                source_name = row[0]

                result = match_utility(source_name, utilities)

                print("\nSource:", source_name)
                print("Candidate ID:", result["candidate_utility_id"])
                print("Confidence:", result["confidence"])
                print("Status:", result["status"])

                cursor.execute(
                    """
                    UPDATE contacts
                    SET
                        utility_id = %s,
                        candidate_utility_id = %s,
                        match_confidence = %s,
                        match_status = %s
                    WHERE utility_name = %s
                """,
                    (
                        result["utility_id"],
                        result["candidate_utility_id"],
                        result["confidence"],
                        result["status"],
                        source_name,
                    ),
                )

                connection.commit()
                print("\nContact matching results saved successfully!")
 
            # Match procurement notices

            print("\nPROCUREMENT NOTICE MATCHING")

            cursor.execute("""
                SELECT notice_url, utility_name
                FROM procurement_notices
                WHERE utility_name IS NOT NULL
            """)

            notices = cursor.fetchall()

            for row in notices:
                notice_url = row[0]
                source_name = row[1]

                result = match_utility(source_name, utilities)

                cursor.execute("""
                    UPDATE procurement_notices
                    SET
                        utility_id = %s,
                        candidate_utility_id = %s,
                        match_confidence = %s,
                        match_status = %s
                    WHERE notice_url = %s
                """, (
                    result["utility_id"],
                    result["candidate_utility_id"],
                    result["confidence"],
                    result["status"],
                    notice_url
                ))

                print(
                    source_name,
                    "|",
                    result["confidence"],
                    "|",
                    result["status"]
                )

            connection.commit()

            print("\nProcurement matching saved successfully!")

        finally:
            cursor.close()
            connection.close()
