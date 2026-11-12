import unittest
from src.matching import normalize_name, match_utility


class TestUtilityMatching(unittest.TestCase):

    def test_normalize_name(self):
        result = normalize_name("Brennan Twp. Municipal Auth.")
        self.assertEqual(result, "brennan township municipal authority")

    def test_successful_match(self):
        utilities = [{"utility_id": 1, "name": "Brennan Township Municipal Authority"}]

        result = match_utility("Brennan Twp. Municipal Auth.", utilities)

        self.assertEqual(result["status"], "matched")
        self.assertEqual(result["utility_id"], 1)

    def test_unmatched_name(self):
        utilities = [{"utility_id": 1, "name": "City of Ashbrook Water Department"}]

        result = match_utility("Tri-County Water Consortium", utilities)

        self.assertEqual(result["status"], "unmatched")


if __name__ == "__main__":
    unittest.main()
