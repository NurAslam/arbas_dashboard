import unittest
from data_quality import run_checks


class TestDataQuality(unittest.TestCase):
    def test_run_checks_structure(self):
        rpt, issues = run_checks()
        self.assertIsInstance(rpt, dict)
        self.assertIn('rows', rpt)
        self.assertIsInstance(rpt['rows'], int)

    def test_no_duplicate_transaction_ids(self):
        rpt, _ = run_checks()
        # Expect no duplicate transaction ids in master
        self.assertEqual(rpt.get('duplicate_transaction_ids', 0), 0)


if __name__ == '__main__':
    unittest.main()
