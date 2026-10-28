"""Unit tests for the faction-wide refinery scaling system."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from hoi4_script import Block, parse

IDEAS_PARSED = parse((ROOT / 'common/ideas/tfr_refinery_scaling.txt').read_text(encoding='utf-8')).get('ideas').get('country').mapping()
TRIGGERS_PARSED = parse((ROOT / 'common/scripted_triggers/tfr_refinery_scaling.txt').read_text(encoding='utf-8')).mapping()
EFFECTS_PARSED = parse((ROOT / 'common/scripted_effects/tfr_refinery_scaling.txt').read_text(encoding='utf-8')).mapping()
ON_ACTIONS_PARSED = parse((ROOT / 'common/on_actions/tfr_refinery_scaling.txt').read_text(encoding='utf-8'))


class CountrySim:
    def __init__(self, tag, original_tag=None, faction=None, at_war_with=None, refineries=0):
        self.tag = tag
        self.original_tag = original_tag or tag
        self.faction = faction
        self.at_war_with = set(at_war_with or [])
        self.refineries = refineries
        self.ideas = set()

    def is_in_faction_with(self, target):
        return self.faction is not None and self.faction == target

    def has_war_with(self, target):
        return target in self.at_war_with


class WorldSim:
    def __init__(self):
        self.countries = {}
        self.globals = {
            'global.tfr_axis_refineries': 0,
            'global.tfr_geacps_refineries': 0,
            'global.tfr_allies_refineries': 0,
        }

    def add_country(self, tag, **kwargs):
        c = CountrySim(tag, **kwargs)
        self.countries[tag] = c
        return c

    def check_trigger(self, trigger_name, country):
        block = TRIGGERS_PARSED[trigger_name]
        return self.eval_trigger_block(block, country)

    def eval_trigger_block(self, block, country):
        def one(e):
            k, v = e.key, e.value
            if k == 'OR':
                return any(self.eval_trigger_block(Block([child]), country) for child in v.entries())
            if k == 'NOT':
                return not self.eval_trigger_block(v, country)
            if k == 'original_tag':
                return country.original_tag == v
            if k == 'tag':
                return country.tag == v
            if k == 'is_in_faction_with':
                return country.is_in_faction_with(v)
            if k == 'has_war_with':
                return country.has_war_with(v)
            raise AssertionError(f'Unsupported trigger key: {k}')
        return all(one(e) for e in block.entries())

    def recalculate_pools(self):
        self.globals['global.tfr_axis_refineries'] = 0
        self.globals['global.tfr_geacps_refineries'] = 0
        self.globals['global.tfr_allies_refineries'] = 0

        for c in self.countries.values():
            if self.check_trigger('TFR_is_axis_refinery_pool_member', c):
                self.globals['global.tfr_axis_refineries'] += c.refineries
            elif self.check_trigger('TFR_is_geacps_refinery_pool_member', c):
                self.globals['global.tfr_geacps_refineries'] += c.refineries
            elif self.check_trigger('TFR_is_allies_refinery_pool_member', c):
                self.globals['global.tfr_allies_refineries'] += c.refineries

    def get_tier_for_count(self, count):
        if count > 40:
            return 8
        elif count > 32:
            return 7
        elif count > 24:
            return 6
        elif count > 18:
            return 5
        elif count > 12:
            return 4
        elif count > 9:
            return 3
        elif count > 6:
            return 2
        else:
            return 1

    def refresh_countries(self):
        self.recalculate_pools()
        for c in self.countries.values():
            # remove existing refinery scaling ideas
            c.ideas = {i for i in c.ideas if not i.startswith('tfr_refinery_scaling_')}
            if self.check_trigger('TFR_is_axis_refinery_pool_member', c):
                tier = self.get_tier_for_count(self.globals['global.tfr_axis_refineries'])
                c.ideas.add(f'tfr_refinery_scaling_{tier}')
            elif self.check_trigger('TFR_is_geacps_refinery_pool_member', c):
                tier = self.get_tier_for_count(self.globals['global.tfr_geacps_refineries'])
                c.ideas.add(f'tfr_refinery_scaling_{tier}')
            elif self.check_trigger('TFR_is_allies_refinery_pool_member', c):
                count = self.globals['global.tfr_allies_refineries']
                if count > 12:
                    tier = self.get_tier_for_count(count)
                    c.ideas.add(f'tfr_refinery_scaling_{tier}')


class TestRefineryScaling(unittest.TestCase):
    def test_ideas_and_modifiers(self):
        expected_modifiers = {
            'tfr_refinery_scaling_1': 0.80,
            'tfr_refinery_scaling_2': 0.45,
            'tfr_refinery_scaling_3': 0.10,
            'tfr_refinery_scaling_4': -0.15,
            'tfr_refinery_scaling_5': -0.25,
            'tfr_refinery_scaling_6': -0.35,
            'tfr_refinery_scaling_7': -0.55,
            'tfr_refinery_scaling_8': -0.70,
        }
        for idea_id, expected_mod in expected_modifiers.items():
            self.assertIn(idea_id, IDEAS_PARSED)
            idea_block = IDEAS_PARSED[idea_id]
            mod_val = float(idea_block.get('modifier').get('production_speed_synthetic_refinery_factor'))
            self.assertAlmostEqual(mod_val, expected_mod, places=2)

    def test_pool_membership(self):
        w = WorldSim()
        # Axis core & historical
        ger = w.add_country('GER')
        ita = w.add_country('ITA')
        hun = w.add_country('HUN')
        rom = w.add_country('ROM')
        bul = w.add_country('BUL')
        spr = w.add_country('SPR')
        spa = w.add_country('SPA', original_tag='SPR')
        fin = w.add_country('FIN')
        # GEACPS
        jap = w.add_country('JAP')
        sia = w.add_country('SIA')
        # Allies
        eng = w.add_country('ENG')
        fra = w.add_country('FRA')
        usa = w.add_country('USA')
        sov = w.add_country('SOV')
        can = w.add_country('CAN')
        ast = w.add_country('AST')
        raj = w.add_country('RAJ')
        saf = w.add_country('SAF')
        mex = w.add_country('MEX')
        bra = w.add_country('BRA')
        # Neutral minor
        swe = w.add_country('SWE')

        for c in [ger, ita, hun, rom, bul, spr, spa, fin]:
            self.assertTrue(w.check_trigger('TFR_is_axis_refinery_pool_member', c), f'{c.tag} should be Axis')
            self.assertFalse(w.check_trigger('TFR_is_geacps_refinery_pool_member', c))
            self.assertFalse(w.check_trigger('TFR_is_allies_refinery_pool_member', c))

        for c in [jap, sia]:
            self.assertTrue(w.check_trigger('TFR_is_geacps_refinery_pool_member', c), f'{c.tag} should be GEACPS')
            self.assertFalse(w.check_trigger('TFR_is_axis_refinery_pool_member', c))
            self.assertFalse(w.check_trigger('TFR_is_allies_refinery_pool_member', c))

        for c in [eng, fra, usa, sov, can, ast, raj, saf, mex, bra]:
            self.assertTrue(w.check_trigger('TFR_is_allies_refinery_pool_member', c), f'{c.tag} should be Allies')
            self.assertFalse(w.check_trigger('TFR_is_axis_refinery_pool_member', c))
            self.assertFalse(w.check_trigger('TFR_is_geacps_refinery_pool_member', c))

        self.assertFalse(w.check_trigger('TFR_is_axis_refinery_pool_member', swe))
        self.assertFalse(w.check_trigger('TFR_is_geacps_refinery_pool_member', swe))
        self.assertFalse(w.check_trigger('TFR_is_allies_refinery_pool_member', swe))


    def test_allies_no_bonuses_only_penalties(self):
        w = WorldSim()
        eng = w.add_country('ENG', refineries=4)
        usa = w.add_country('USA', refineries=6)

        # 10 refineries total -> <= 12, so NO bonus for Allies
        w.refresh_countries()
        self.assertEqual(w.globals['global.tfr_allies_refineries'], 10)
        self.assertEqual(len([i for i in eng.ideas if 'tfr_refinery' in i]), 0)
        self.assertEqual(len([i for i in usa.ideas if 'tfr_refinery' in i]), 0)

        # Build up to 15 -> > 12, receives Tier 4 penalty (-15%)
        usa.refineries = 11
        w.refresh_countries()
        self.assertEqual(w.globals['global.tfr_allies_refineries'], 15)
        self.assertIn('tfr_refinery_scaling_4', eng.ideas)
        self.assertIn('tfr_refinery_scaling_4', usa.ideas)

        # Build up to 35 -> > 32, receives Tier 7 penalty (-55%)
        usa.refineries = 31
        w.refresh_countries()
        self.assertEqual(w.globals['global.tfr_allies_refineries'], 35)
        self.assertIn('tfr_refinery_scaling_7', eng.ideas)
        self.assertIn('tfr_refinery_scaling_7', usa.ideas)

        # Build up to 45 -> > 40, receives Tier 8 penalty (-70%)
        usa.refineries = 41
        w.refresh_countries()
        self.assertEqual(w.globals['global.tfr_allies_refineries'], 45)
        self.assertIn('tfr_refinery_scaling_8', eng.ideas)

    def test_tier_transitions_and_synchronization(self):
        w = WorldSim()
        ger = w.add_country('GER', refineries=4)
        ita = w.add_country('ITA', refineries=2)
        hun = w.add_country('HUN', refineries=0)
        swe = w.add_country('SWE', refineries=5)

        # 4 + 2 = 6 refineries -> Tier 1 (+80%)
        w.refresh_countries()
        self.assertEqual(w.globals['global.tfr_axis_refineries'], 6)
        self.assertIn('tfr_refinery_scaling_1', ger.ideas)
        self.assertIn('tfr_refinery_scaling_1', ita.ideas)
        self.assertIn('tfr_refinery_scaling_1', hun.ideas)
        self.assertEqual(len([i for i in swe.ideas if 'tfr_refinery' in i]), 0)

        # Build 2 more in Hungary -> 8 total -> Tier 2 (+40%)
        hun.refineries = 2
        w.refresh_countries()
        self.assertEqual(w.globals['global.tfr_axis_refineries'], 8)
        self.assertIn('tfr_refinery_scaling_2', ger.ideas)
        self.assertIn('tfr_refinery_scaling_2', ita.ideas)
        self.assertIn('tfr_refinery_scaling_2', hun.ideas)

        # Build 3 more in Germany -> 11 total -> Tier 3 (Vanilla 0%)
        ger.refineries = 7
        w.refresh_countries()
        self.assertEqual(w.globals['global.tfr_axis_refineries'], 11)
        self.assertIn('tfr_refinery_scaling_3', ger.ideas)
        self.assertIn('tfr_refinery_scaling_3', ita.ideas)
        self.assertIn('tfr_refinery_scaling_3', hun.ideas)

        # 15 total -> Tier 4 (-20%)
        ger.refineries = 11
        w.refresh_countries()
        self.assertEqual(w.globals['global.tfr_axis_refineries'], 15)
        self.assertIn('tfr_refinery_scaling_4', ger.ideas)

        # 22 total -> Tier 5 (-30%) - approx 150 mils
        ger.refineries = 18
        w.refresh_countries()
        self.assertEqual(w.globals['global.tfr_axis_refineries'], 22)
        self.assertIn('tfr_refinery_scaling_5', ger.ideas)
        self.assertIn('tfr_refinery_scaling_5', ita.ideas)

        # 30 total -> Tier 6 (-45%) - approx 200 mils
        ger.refineries = 26
        w.refresh_countries()
        self.assertEqual(w.globals['global.tfr_axis_refineries'], 30)
        self.assertIn('tfr_refinery_scaling_6', ger.ideas)

        # 36 total -> Tier 7 (-60%) - approx 300 mils
        ger.refineries = 32
        w.refresh_countries()
        self.assertEqual(w.globals['global.tfr_axis_refineries'], 36)
        self.assertIn('tfr_refinery_scaling_7', ger.ideas)

        # 45 total -> Tier 8 (-75%) - 300+ mils INSANE
        ger.refineries = 41
        w.refresh_countries()
        self.assertEqual(w.globals['global.tfr_axis_refineries'], 45)
        self.assertIn('tfr_refinery_scaling_8', ger.ideas)
        self.assertIn('tfr_refinery_scaling_8', hun.ideas)

        # If refineries are lost/destroyed: drops back down
        ger.refineries = 0
        ita.refineries = 0
        hun.refineries = 5
        w.refresh_countries()
        self.assertEqual(w.globals['global.tfr_axis_refineries'], 5)
        self.assertIn('tfr_refinery_scaling_1', ger.ideas)
        self.assertIn('tfr_refinery_scaling_1', ita.ideas)


if __name__ == '__main__':
    unittest.main()
