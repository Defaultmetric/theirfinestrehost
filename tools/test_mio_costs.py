"""Unit tests to verify no positive production cost penalties exist in non-tank MIOs."""

import os
import re
import unittest
from pathlib import Path

REPO_DIR = Path(r"C:\Users\mihai\Documents\GitHub\theirfinestrehost")
WORKSHOP_DIR = Path(r"C:\Program Files (x86)\Steam\steamapps\workshop\content\394360\3513811852")

MODIFIED_FILES = [
    r"common\military_industrial_organization\organizations\00_generic_organization.txt",
    r"common\military_industrial_organization\organizations\AUS_organization.txt",
    r"common\military_industrial_organization\organizations\CZE_organization.txt",
    r"common\military_industrial_organization\organizations\GER_organization.txt",
    r"common\military_industrial_organization\organizations\RAJ_GOE_organization .txt",
    r"common\military_industrial_organization\organizations\SWE_organization.txt",
    r"common\military_industrial_organization\policies\_air_policies.txt",
]


class TestMioCosts(unittest.TestCase):
    def test_repo_and_workshop_files_are_identical(self):
        for rel in MODIFIED_FILES:
            f1 = REPO_DIR / rel
            f2 = WORKSHOP_DIR / rel
            self.assertTrue(f1.exists(), f"Missing repo file: {f1}")
            self.assertTrue(f2.exists(), f"Missing workshop file: {f2}")
            self.assertEqual(f1.read_bytes(), f2.read_bytes(), f"Mismatch in {rel}")

    def test_no_positive_cost_penalties_in_non_tank_mios(self):
        mio_dir = REPO_DIR / "common" / "military_industrial_organization"
        for p in mio_dir.rglob("*.txt"):
            if p.name in ["AlliesTankMios.txt", "AxisTankMios.txt"]:
                continue
            content = p.read_text(encoding="utf-8", errors="ignore")
            for m in re.finditer(r"(build_cost_ic|production_cost_factor|production_cost)\s*=\s*([0-9\.\-\+]+)", content):
                val = float(m.group(2))
                if val > 0:
                    line_no = content[:m.start()].count("\n") + 1
                    # Only the 2 tank traits in 00_generic_organization.txt are allowed
                    if p.name == "00_generic_organization.txt":
                        self.assertIn(
                            line_no,
                            [1220, 2016],
                            f"Unexpected positive cost penalty in {p.name}:{line_no} ({m.group(1)} = {val})",
                        )
                    else:
                        self.fail(f"Found positive cost penalty in {p.name}:{line_no} ({m.group(1)} = {val})")


if __name__ == "__main__":
    unittest.main()
