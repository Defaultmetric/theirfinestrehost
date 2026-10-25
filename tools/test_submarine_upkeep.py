"""Execute upkeep scripts across thresholds, fleet losses and country changes."""
from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import re
import unittest

from hoi4_script import Block, parse, walk

ROOT = Path(__file__).resolve().parents[1]
EFFECTS = parse((ROOT/'common/scripted_effects/tfr_submarine_upkeep.txt').read_text()).mapping()
TRIGGERS = parse((ROOT/'common/scripted_triggers/tfr_submarine_upkeep.txt').read_text()).mapping()
IDEAS = parse((ROOT/'common/ideas/tfr_submarine_upkeep.txt').read_text()).get('ideas').get('country').mapping()
UPKEEP = {f'tfr_submarine_upkeep_{i}' for i in range(1, 6)}


class Fleet:
    def __init__(self, tag='GER', count=0, focused=False):
        self.tag, self.count, self.focused = tag, count, focused
        self.ideas = {'unrelated_spirit'}
        self.changes = 0

    def check(self, block):
        def one(e):
            k, v = e.key, e.value
            if k == 'OR':
                return any(self.check(Block([child])) for child in v.entries())
            if k == 'NOT':
                return not self.check(v)
            if k == 'original_tag':
                return self.tag == v
            if k == 'has_completed_focus':
                assert v == 'HOL_rely_on_submarines'
                return self.focused
            if k == 'has_idea':
                return v in self.ideas
            if k == 'has_navy_size':
                assert v.get('archetype') == 'ship_hull_submarine'
                size = v.entries('size')[0]
                assert size.op == '>'
                return self.count > int(size.value)
            if k in TRIGGERS:
                return self.check(TRIGGERS[k]) == (v == 'yes')
            raise AssertionError(('unsupported trigger', k))
        return all(one(e) for e in block.entries())

    def effect(self, block):
        taken = False
        for e in block.entries():
            k, v = e.key, e.value
            if k in ('if', 'else_if', 'else'):
                if k == 'if':
                    taken = False
                matches = not taken and (k == 'else' or self.check(v.get('limit')))
                if matches:
                    self.effect(Block([child for child in v.items
                                       if not hasattr(child, 'key') or child.key != 'limit']))
                taken = taken or matches
            elif k == 'remove_ideas':
                self.ideas.difference_update(v.atoms())
                self.changes += 1
            elif k == 'add_ideas':
                assert v in IDEAS
                self.ideas.add(v)
                self.changes += 1
            elif k in EFFECTS:
                body = deepcopy(EFFECTS[k])
                parameters = v.mapping() if isinstance(v, Block) else {}
                for entry, _ in walk(body):
                    if isinstance(entry.value, str):
                        for name, value in parameters.items():
                            entry.value = entry.value.replace(f'${name}$', value)
                self.effect(body)
            else:
                raise AssertionError(('unsupported effect', k))

    def refresh(self):
        self.effect(EFFECTS['TFR_submarine_upkeep_refresh'])
        return self.ideas & UPKEEP


class SubmarineUpkeepTests(unittest.TestCase):
    def test_native_effects_use_literal_tiers_without_parameter_expansion(self):
        text=(ROOT/'common/scripted_effects/tfr_submarine_upkeep.txt').read_text()
        self.assertNotIn('$',text)
        for entry,_ in walk(parse(text)):
            if entry.key in EFFECTS and entry.key!='TFR_submarine_upkeep_refresh':
                # Top-level definitions contain blocks; invocations use '= yes'.
                if entry.key.startswith('TFR_submarine_upkeep_apply_tier_') and not isinstance(entry.value,Block):
                    self.assertEqual(entry.value,'yes')
        self.assertNotIn('TFR_submarine_upkeep_apply_tier',EFFECTS)
        self.assertTrue({f'TFR_submarine_upkeep_apply_tier_{i}' for i in range(1,6)}.issubset(EFFECTS))

    def test_major_boundaries_and_large_changes_in_both_directions(self):
        for tag in ('GER', 'ENG', 'ITA', 'JAP', 'USA'):
            fleet = Fleet(tag)
            for count in [*range(151), 500, 0, 100, 24, 75, 49, 50, 74, 25, 99, 0]:
                fleet.count = count
                tier = 1 + sum(count >= n for n in (25, 50, 75, 100))
                self.assertEqual(fleet.refresh(), {f'tfr_submarine_upkeep_{tier}'}, (tag, count))
                self.assertIn('unrelated_spirit', fleet.ideas)
                before = fleet.changes
                fleet.refresh()
                self.assertEqual(fleet.changes, before, 'Stable tier must not churn ideas')

    def test_dutch_focus_gate_thresholds_and_cleanup(self):
        fleet = Fleet('HOL', 100)
        self.assertEqual(fleet.refresh(), set())
        fleet.focused = True
        for count in [*range(51), 0, 34, 33, 25, 24, 17, 16, 9, 8]:
            fleet.count = count
            tier = 1 + sum(count >= n for n in (9, 17, 25, 34))
            self.assertEqual(fleet.refresh(), {f'tfr_submarine_upkeep_{tier}'}, count)
        fleet.focused = False
        self.assertEqual(fleet.refresh(), set())
        self.assertEqual(fleet.ideas, {'unrelated_spirit'})

    def test_unsupported_countries_and_inherited_spirit_cleanup(self):
        for tag in ('FRA', 'SOV', 'MAN', 'SPR', 'CAN', 'BRA'):
            for count in (0, 25, 100, 500):
                fleet = Fleet(tag, count)
                fleet.ideas.update(UPKEEP)
                self.assertEqual(fleet.refresh(), set())
                self.assertEqual(fleet.ideas, {'unrelated_spirit'})

    def test_exact_production_cost_modifiers_and_no_combat_modifiers(self):
        self.assertEqual(set(IDEAS), UPKEEP)
        for i, cost in enumerate(('-0.8', '-0.7', '-0.5', '-0.2', '3'), 1):
            body = IDEAS[f'tfr_submarine_upkeep_{i}']
            self.assertFalse(body.entries('modifier'))
            bonus = body.get('equipment_bonus')
            self.assertEqual(set(bonus.mapping()), {'submarine'})
            self.assertEqual(Decimal(bonus.get('submarine').get('build_cost_ic')), Decimal(cost))
            self.assertEqual(bonus.get('submarine').get('instant'), 'yes')

    def test_imported_base_costs_and_special_hull_aliases(self):
        hulls = parse((ROOT/'common/units/equipment/ship_hull_submarine.txt').read_text()).get('equipments').mapping()
        expected = {
            'ship_hull_submarine': 2000, 'ship_hull_submarine_2': 2100,
            'ship_hull_submarine_3': 2200, 'ship_hull_submarine_4': 2300,
            'ship_hull_cruiser_submarine': 2500, 'ship_hull_fleet_submarine': 2800,
            'ship_hull_midget_submarine': 600, 'ship_hull_nuclear_submarine': 3200,
            'submarine_1': 250, 'submarine_2': 250, 'submarine_3': 350, 'submarine_4': 400,
            'cruiser_submarine': 2500, 'fleet_submarine': 2800,
            'midget_submarine': 600, 'nuclear_submarine': 3200,
        }
        for name, value in expected.items():
            self.assertEqual(int(hulls[name].get('build_cost_ic')), value, name)
        policy = json.loads((ROOT/'docs/submarine-upkeep.json').read_text())
        for name, value in policy['unique_hull_costs_preserved'].items():
            self.assertEqual(hulls[name].get('build_cost_ic'), value)

    def test_initialization_daily_updates_and_localization(self):
        actions = parse((ROOT/'common/on_actions/tfr_submarine_upkeep.txt').read_text()).get('on_actions')
        self.assertEqual(actions.get('on_startup').get('effect').get('every_country').get('TFR_submarine_upkeep_refresh'), 'yes')
        self.assertEqual(actions.get('on_daily').get('effect').get('TFR_submarine_upkeep_refresh'), 'yes')
        raw = (ROOT/'localisation/english/tfr_submarine_upkeep_l_english.yml').read_bytes()
        self.assertTrue(raw.startswith(b'\xef\xbb\xbf'))
        loc = raw.decode('utf-8-sig')
        self.assertEqual(set(re.findall(r'^ (\w+):', loc, re.M)), UPKEEP | {i+'_desc' for i in UPKEEP})
        self.assertEqual(loc.count('Submarine Upkeep:'), 5)


if __name__ == '__main__':
    unittest.main()
