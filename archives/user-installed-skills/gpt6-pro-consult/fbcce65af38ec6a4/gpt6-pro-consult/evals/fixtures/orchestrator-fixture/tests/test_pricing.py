from decimal import Decimal
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pricing import apply_discount


class PricingTests(unittest.TestCase):
    def test_normal_discount(self) -> None:
        self.assertEqual(apply_discount(Decimal("100"), Decimal("20")), Decimal("80"))

    def test_discount_above_one_hundred_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            apply_discount(Decimal("100"), Decimal("125"))

    def test_negative_discount_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            apply_discount(Decimal("100"), Decimal("-1"))


if __name__ == "__main__":
    unittest.main()
