"""Unit tests and verification for economy laws rebalance.

Applies and validates:
- All 13 economy laws receive -10% military factory construction speed (production_speed_arms_factory_factor -0.10)
- civilian_economy also receives -10% civilian factory construction speed (production_speed_industrial_complex_factor -0.4)
- Local Git repo and Workshop copies are kept 100% byte-identical.
"""

import os
import re
import unittest

REPO_FILE = r"C:\Users\mihai\Documents\GitHub\theirfinestrehost\common\ideas\_economic.txt"
WORKSHOP_FILE = r"C:\Program Files (x86)\Steam\steamapps\workshop\content\394360\3513811852\common\ideas\_economic.txt"

EXPECTED_VALUES = {
    "undisturbed_isolation": {
        "production_speed_arms_factory_factor": -0.6,
        "production_speed_industrial_complex_factor": -0.5,
    },
    "isolation": {
        "production_speed_arms_factory_factor": -0.5,
        "production_speed_industrial_complex_factor": -0.4,
    },
    "civilian_economy": {
        "production_speed_arms_factory_factor": -0.4,
        "production_speed_industrial_complex_factor": -0.4,
    },
    "low_economic_mobilisation": {
        "production_speed_arms_factory_factor": -0.2,
        "production_speed_industrial_complex_factor": -0.1,
    },
    "partial_economic_mobilisation": {
        "production_speed_arms_factory_factor": 0.0,
    },
    "war_economy": {
        "production_speed_arms_factory_factor": 0.1,
    },
    "tot_economic_mobilisation": {
        "production_speed_arms_factory_factor": 0.2,
    },
    "totaler_krieg_economy": {
        "production_speed_arms_factory_factor": 0.1,
    },
    "national_defense_state": {
        "production_speed_arms_factory_factor": 0.2,
    },
    "new_economic_policy": {
        "production_speed_arms_factory_factor": -0.1,
    },
    "new_economic_policy_2": {
        "production_speed_arms_factory_factor": -0.1,
    },
    "capital_investment_model": {
        "production_speed_arms_factory_factor": -0.25,
        "production_speed_industrial_complex_factor": 0.15,
    },
    "JAP_war_communism_idea": {
        "production_speed_arms_factory_factor": 0.1,
        "production_speed_industrial_complex_factor": -0.1,
    },
}


def parse_economy_block(content: str) -> dict:
    """Parse ideas within economy = { ... } and extract their modifiers."""
    econ_match = re.search(r"economy\s*=\s*\{(.*?)\n\t\}\s*\n\ttrade_laws", content, re.DOTALL)
    if not econ_match:
        raise ValueError("Could not find economy = { ... } block")
    econ_text = econ_match.group(1)

    # Find each idea definition inside economy
    # Ideas are top level within economy, e.g. \n\t\t<idea_name> = {
    idea_pattern = re.compile(r"\n\t\t([a-zA-Z0-9_]+)\s*=\s*\{", re.DOTALL)
    matches = list(idea_pattern.finditer(econ_text))

    results = {}
    for idx, match in enumerate(matches):
        idea_name = match.group(1)
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(econ_text)
        idea_body = econ_text[start:end]

        # Extract top-level modifier = { ... } block (not nested inside ai_will_do)
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


class TestEconomyLaws(unittest.TestCase):
    def test_repo_file_exists(self):
        self.assertTrue(os.path.exists(REPO_FILE), f"Repo file does not exist: {REPO_FILE}")

    def test_workshop_file_exists(self):
        self.assertTrue(os.path.exists(WORKSHOP_FILE), f"Workshop file does not exist: {WORKSHOP_FILE}")

    def test_files_are_identical(self):
        with open(REPO_FILE, "rb") as f1, open(WORKSHOP_FILE, "rb") as f2:
            self.assertEqual(f1.read(), f2.read(), "Repo and Workshop files must be 100% byte-identical")

    def test_all_13_laws_present(self):
        with open(REPO_FILE, "r", encoding="utf-8") as f:
            data = parse_economy_block(f.read())
        self.assertEqual(len(data), 13, f"Expected 13 economy laws, got {len(data)}: {list(data.keys())}")
        for expected_law in EXPECTED_VALUES:
            self.assertIn(expected_law, data, f"Missing economy law: {expected_law}")

    def test_arms_factory_construction_speed_values(self):
        with open(REPO_FILE, "r", encoding="utf-8") as f:
            data = parse_economy_block(f.read())
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
