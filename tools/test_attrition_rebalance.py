import unittest
import os
import re

class TestAttritionRebalance(unittest.TestCase):
    def setUp(self):
        self.repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.terrain_path = os.path.join(self.repo_root, 'common', 'terrain', '00_terrain.txt')
        self.modifiers_path = os.path.join(self.repo_root, 'common', 'modifiers', '00_static_modifiers.txt')
        self.defines_path = os.path.join(self.repo_root, 'common', 'defines', 'TFR_defines.lua')

    def test_terrain_attrition_moderated(self):
        with open(self.terrain_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check mountain attrition reduced to 0.2 and truck to 0.7
        self.assertIn('mountain = {', content)
        self.assertIn('attrition = 0.2', content)
        self.assertIn('truck_attrition_factor = 0.7', content)

        # Check jungle attrition reduced to 0.12 and truck to 2.0
        self.assertIn('jungle = {', content)
        self.assertIn('attrition = 0.12', content)
        self.assertIn('truck_attrition_factor = 2.0', content)

        # Check marsh attrition reduced to 0.25 and truck to 2.5
        self.assertIn('marsh = {', content)
        self.assertIn('attrition = 0.25', content)
        self.assertIn('truck_attrition_factor = 2.5', content)

        # Check desert attrition reduced to 0.03 and truck to 0.3
        self.assertIn('desert = {', content)
        self.assertIn('attrition = 0.03', content)
        self.assertIn('truck_attrition_factor = 0.3', content)

        # Check forest & hills truck attrition reduced to 0.1
        self.assertIn('truck_attrition_factor = 0.1', content)

    def test_static_modifiers_winter_increased(self):
        with open(self.modifiers_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Winter conditions increased
        self.assertIn('weather_extreme_cold = {', content)
        self.assertIn('winter_attrition = 0.55', content)
        self.assertIn('truck_attrition_factor = 1.3', content)

        self.assertIn('weather_very_cold = {', content)
        self.assertIn('winter_attrition = 0.35', content)
        self.assertIn('truck_attrition_factor = 0.3', content)

        self.assertIn('weather_blizzard = {', content)
        self.assertIn('truck_attrition_factor = 1.4', content)

        self.assertIn('weather_snow = {', content)
        self.assertIn('truck_attrition_factor = 0.45', content)

        self.assertIn('weather_ground_snow_high = {', content)
        self.assertIn('truck_attrition_factor = 1.4', content)

        self.assertIn('weather_ground_snow_medium = {', content)
        self.assertIn('truck_attrition_factor = 0.7', content)

    def test_static_modifiers_non_winter_decreased(self):
        with open(self.modifiers_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Non-winter conditions decreased
        self.assertIn('weather_mud = {', content)
        self.assertIn('attrition = 0.5', content)
        self.assertIn('truck_attrition_factor = 3.5', content)

        self.assertIn('weather_sandstorm = {', content)
        self.assertIn('truck_attrition_factor = 2.0', content)

        self.assertIn('flooded = {', content)
        self.assertIn('truck_attrition_factor = 2.0', content)

        self.assertIn('weather_very_hot = {', content)
        self.assertIn('heat_attrition = 0.07', content)

        self.assertIn('weather_extreme_hot = {', content)
        self.assertIn('heat_attrition = 0.15', content)
        self.assertIn('truck_attrition_factor = 0.05', content)

    def test_combat_damage_defines(self):
        with open(self.defines_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn('NDefines.NMilitary.LAND_COMBAT_STR_DAMAGE_MODIFIER = 0.046', content)
        self.assertIn('NDefines.NMilitary.LAND_COMBAT_ORG_DAMAGE_MODIFIER = 0.045', content)

if __name__ == '__main__':
    unittest.main()
