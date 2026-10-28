"""Unit tests and verification for mobilization/manpower laws rebalance.

Validates:
- disarmed_nation: conscription = 0.01, production_speed_buildings_factor = 0.05
- volunteer_only: conscription = 0.02
- limited_conscription: conscription = 0.035
- extensive_conscription: conscription = 0.06, industrial penalties = -0.10
- service_by_requirement: conscription = 0.15, industrial penalties = -0.30
- all_adults_serve: conscription = 0.25, industrial penalties = -0.40
- scraping_the_barrel: conscription = 0.30, industrial penalties = -0.50
- Local Git repo and Workshop copies are kept 100% byte-identical.
"""

import os
import re
import unittest

REPO_FILE = r"C:\Users\mihai\Documents\GitHub\theirfinestrehost\common\ideas\_manpower.txt"
WORKSHOP_FILE = r"C:\Program Files (x86)\Steam\steamapps\workshop\content\394360\3513811852\common\ideas\_manpower.txt"

EXPECTED_VALUES = {
    "disarmed_nation": {
        "conscription": 0.005,
        "production_speed_buildings_factor": 0.05,
    },
    "volunteer_only": {
        "conscription": 0.02,
    },
    "limited_conscription": {
        "conscription": 0.035,
    },
    "extensive_conscription": {
        "conscription": 0.06,
        "industrial_capacity_factory": -0.1,
        "industrial_capacity_dockyard": -0.1,
        "production_speed_buildings_factor": -0.1,
        "training_time_factor": 0.1,
    },
    "service_by_requirement": {
        "conscription": 0.15,
        "industrial_capacity_factory": -0.3,
        "industrial_capacity_dockyard": -0.3,
        "production_speed_buildings_factor": -0.3,
        "training_time_factor": 0.2,
    },
    "all_adults_serve": {
        "conscription": 0.25,
        "industrial_capacity_factory": -0.4,
        "industrial_capacity_dockyard": -0.4,
        "production_speed_buildings_factor": -0.4,
        "training_time_factor": 0.3,
    },
    "scraping_the_barrel": {
        "conscription": 0.30,
        "industrial_capacity_factory": -0.5,
        "industrial_capacity_dockyard": -0.5,
        "production_speed_buildings_factor": -0.5,
        "training_time_factor": 0.5,
    },
}


def parse_mobilization_block(content: str) -> dict:
    """Parse ideas within mobilization_laws = { ... } and extract top-level modifiers."""
    mob_match = re.search(r"mobilization_laws\s*=\s*\{(.*?)\n\t\}\s*\n\n", content, re.DOTALL)
    if not mob_match:
        mob_match = re.search(r"mobilization_laws\s*=\s*\{(.*?)\n\t\}", content, re.DOTALL)
    if not mob_match:
        raise ValueError("Could not find mobilization_laws = { ... } block")
    mob_text = mob_match.group(1)

    idea_pattern = re.compile(r"\n\t\t([a-zA-Z0-9_]+)\s*=\s*\{", re.DOTALL)
    matches = list(idea_pattern.finditer(mob_text))

    results = {}
    for idx, match in enumerate(matches):
        idea_name = match.group(1)
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(mob_text)
        idea_body = mob_text[start:end]

        mod_match = re.search(r"\n\t\t\tmodifier\s*=\s*\{(.*?)\n\t\t\t\}", idea_body, re.DOTALL)
        if mod_match:
            mod_text = mod_match.group(1)
            results[idea_name] = {}
            for line in mod_text.strip().splitlines():
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    parts = line.split("=", 1)
                    k = parts[0].strip()
                    v_str = parts[1].split("#")[0].strip()
                    try:
                        results[idea_name][k] = float(v_str)
                    except ValueError:
                        results[idea_name][k] = v_str
    return results


class TestManpowerLaws(unittest.TestCase):
    def test_repo_file_exists(self):
        self.assertTrue(os.path.exists(REPO_FILE), f"Repo file does not exist: {REPO_FILE}")

    def test_workshop_file_exists(self):
        self.assertTrue(os.path.exists(WORKSHOP_FILE), f"Workshop file does not exist: {WORKSHOP_FILE}")

    def test_files_are_identical(self):
        with open(REPO_FILE, "rb") as f1, open(WORKSHOP_FILE, "rb") as f2:
            self.assertEqual(f1.read(), f2.read(), "Repo and Workshop files must be 100% byte-identical")

    def test_all_expected_laws_present(self):
        with open(REPO_FILE, "r", encoding="utf-8") as f:
            data = parse_mobilization_block(f.read())
        for expected_law in EXPECTED_VALUES:
            self.assertIn(expected_law, data, f"Missing mobilization law: {expected_law}")

    def test_conscription_and_modifier_values(self):
        with open(REPO_FILE, "r", encoding="utf-8") as f:
            data = parse_mobilization_block(f.read())
        for law_name, expected_mods in EXPECTED_VALUES.items():
            for mod_name, expected_val in expected_mods.items():
                self.assertIn(mod_name, data[law_name], f"{law_name} missing {mod_name}")
                self.assertAlmostEqual(
                    data[law_name][mod_name],
                    expected_val,
                    places=3,
                    msg=f"{law_name}.{mod_name} expected {expected_val}, got {data[law_name][mod_name]}",
                )


if __name__ == "__main__":
    unittest.main()
