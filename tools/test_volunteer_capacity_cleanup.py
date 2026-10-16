"""Acceptance checks for volunteer capacity cleanup and retained game mechanics."""
import unittest

from cleanup_volunteer_capacity import ROOT, FOLDERS, PROTECTED, bonus, parse, sources, walk, orphaned_relation_rule, strip_bonuses, render


def script(rel):
    return parse((ROOT / rel).read_text(encoding='utf-8-sig', errors='surrogateescape'))


def named(entries, key):
    return next(e for e in walk(entries) if e.key == key)


def scalar(entries, key):
    return next(e.value for e in entries if e.key == key)


REMOVED = {
    'ARG_socialist_volunteers', 'ah_volunteer_corps', 'ah_foreign_expeditions',
    'BRA_international_brigades', 'ETH_peacekeeping_forces',
    'FRA_league_of_french_bolshevist_volunteers', 'HOA_the_adjective_volunteer_force',
    'wuw_HUN_officialize_the_rakosi_battalion', 'JAP_communist_volunteers',
    'JAP_anti_communist_volunteers', 'POL_dabrowszczacy', 'POL_volunteer_corps',
    'SWI_volunteer_force', 'AST_citizen_military_forces', 'PRC_peoples_volunteer_army',
    'PRC_sea_peoples_volunteer_army', 'NZL_2nzef', 'ROM_romanian_volunteer_brigades',
    'ROM_legion_condor', 'MON_legion_condor', 'SOV_transpolar_flights', 'AST_volunteers',
}


class CapacityCleanupTests(unittest.TestCase):
    def test_no_rule_overrides_without_actual_rules_remain(self):
        remaining=[]
        for folder in FOLDERS:
            for rel,path in sources(folder).items():
                text=path.read_text(encoding='utf-8-sig',errors='surrogateescape')
                if 'relation_rule_override' not in text:continue
                remaining.extend((rel,e.key) for e in walk(parse(text)) if orphaned_relation_rule(e))
        self.assertEqual(remaining,[])

    def test_empty_relation_overrides_are_removed_but_other_rules_survive(self):
        text='''add_relation_rule_override = { target = SPA can_send_volunteers = yes }
        remove_relation_rule_override = { target = CHL }
        add_relation_rule_override = { trigger = my_trigger usage_desc = my_tt can_send_volunteers = yes can_not_declare_war = yes }
        add_political_power = 50'''
        entries=parse(text);strip_bonuses(entries);new=render(text,entries)
        self.assertNotIn('target = SPA',new);self.assertNotIn('target = CHL',new)
        self.assertIn('can_not_declare_war = yes',new);self.assertIn('add_political_power = 50',new)
        self.assertNotIn('can_send_volunteers',new)

    def test_no_legacy_capacity_rewards_or_permissions_in_loaded_scripts(self):
        remaining = []
        for folder in FOLDERS:
            for rel, path in sources(folder).items():
                if rel in PROTECTED:
                    continue
                text = path.read_text(encoding='utf-8-sig', errors='surrogateescape')
                if not any(key in text for key in ('send_volunteer', 'air_volunteer_cap')):
                    continue
                for e in walk(parse(text)):
                    if bonus(e):
                        remaining.append((rel, e.key, e.value))
        self.assertEqual(remaining, [])

    def test_france_keeps_decisions_and_their_domestic_benefits(self):
        decisions = script('common/decisions/FRA.txt')
        expected = {
            'FRA_allow_arms_purchases': ('-0.1', '0.05'),
            'FRA_allow_sending_weapons': ('-0.15', '0.075'),
            'FRA_allow_volunteer_work': ('-0.2', '0.1'),
            'FRA_allow_covert_intervention': ('-0.25', '0.125'),
        }
        for key, (stability, war_support) in expected.items():
            with self.subTest(decision=key):
                modifier = named(decisions, key).get('modifier')
                self.assertEqual(scalar(modifier.children, 'stability_factor'), stability)
                self.assertEqual(scalar(modifier.children, 'war_support_factor'), war_support)
        self.assertIsNone(named(decisions, 'FRA_ban_covert_intervention').get('available'))
        # Civilian assistance still provides Spain with manpower through its original event.
        assistance = named(decisions, 'FRA_allow_volunteer_work')
        self.assertTrue(any(e.key == 'country_event' and e.value == 'lar_france_volunteers.1' for e in walk(assistance.children)))
        category = named(script('common/decisions/categories/FRA_decision_categories.txt'), 'FRA_spanish_intervention_category')
        self.assertTrue(any(e.key == 'has_completed_focus' and e.value == 'FRA_intervention_in_spain' for e in walk(category.children)))
        focuses = script('common/national_focus/france.txt')
        self.assertTrue(any(e.key == 'id' and e.value == 'FRA_intervention_in_spain' for e in walk(focuses)))
        localization = (ROOT / 'localisation/replace/France_TFR_l_english.yml').read_text(encoding='utf-8-sig')
        self.assertIn('Gain access to decisions that boost §YWar Support§! at the cost of §YStability§!.', localization)

    def test_removed_focuses_have_no_tree_or_ai_references(self):
        remaining = []
        for folder in ('common', 'events', 'history'):
            for rel, path in sources(folder).items():
                text = path.read_text(encoding='utf-8-sig', errors='surrogateescape')
                if not any(fid in text for fid in REMOVED):
                    continue
                for e in walk(parse(text)):
                    if e.children is None and e.value in REMOVED:
                        if e.key in {'focus', 'shared_focus', 'relative_position_id', 'has_completed_focus', 'complete_national_focus', 'unlock_national_focus'} or (e.key == 'id' and rel.startswith('common/national_focus/')) or (e.key == '_' and rel.startswith(('common/ai_strategy_plans/', 'common/focus_inlay_windows/'))):
                            remaining.append((rel, e.key, e.value))
        self.assertEqual(remaining, [])

    def test_children_still_unlock_from_surviving_parents(self):
        france = script('common/national_focus/france.txt')
        host = next(e for e in walk(france) if e.key == 'focus' and e.get('id') and e.get('id').value == 'FRA_host_the_german_exiles')
        self.assertEqual(scalar(host.get('prerequisite').children, 'focus'), 'FRA_loyalty_to_moscow')
        japan = script('common/national_focus/japan.txt')
        seen = {e.value for e in walk(japan) if e.key == 'focus' and e.children is None}
        self.assertIn('JAP_red_brigades', seen)
        self.assertIn('JAP_anti_communist_bulwark', seen)

    def test_mixed_spirits_keep_combat_and_recruitment_benefits(self):
        legion = named(script('common/ideas/GER.txt'), 'GER_legion_condor_ns').get('modifier')
        self.assertEqual(scalar(legion.children, 'experience_gain_army_factor'), '0.15')
        self.assertEqual(scalar(legion.children, 'experience_gain_air_factor'), '0.15')
        brigades = named(script('common/ideas/czechoslovakia.txt'), 'CZE_revolutionary_brigades_idea').get('modifier')
        self.assertEqual(scalar(brigades.children, 'conscription'), '0.015')
        self.assertEqual(scalar(brigades.children, 'army_core_defence_factor'), '0.15')
        recruitment = named(script('common/ideas/czechoslovakia.txt'), 'CZE_state_sponsored_recruitment_idea').get('modifier')
        self.assertEqual(scalar(recruitment.children, 'army_experience_from_volunteers'), '0.20')
        finnish = named(script('common/ideas/finland.txt'), 'FIN_international_volunteers').get('modifier')
        self.assertEqual(scalar(finnish.children, 'weekly_manpower'), '600')

    def test_bulgarian_manpower_and_indian_economic_reward_survive(self):
        bulgaria = script('common/national_focus/bulgaria.txt')
        for fid in ('BUL_the_spanish_struggle', 'BUL_support_the_spanish_coup'):
            focus = next(e for e in walk(bulgaria) if e.key == 'focus' and e.get('id') and e.get('id').value == fid)
            self.assertTrue(any(e.key == 'add_manpower' and e.value == '-3000' for e in walk(focus.get('completion_reward').children)))
        india = (ROOT / 'common/national_focus/india_goe.txt').read_text(encoding='utf-8-sig')
        self.assertIn('RAJ_a_private_military_tt_1', india)
        # The event hook paying for deployments is separate from permission/capacity rewards.
        hook = named(script('common/on_actions/13_goe_on_actions.txt'), 'on_send_volunteers')
        self.assertTrue(any(e.key == 'has_completed_focus' and e.value == 'RAJ_a_private_military' for e in walk(hook.children)))
        building = named(hook.children, 'add_offsite_building')
        self.assertEqual(scalar(building.children, 'type'), 'industrial_complex')
        self.assertEqual(scalar(building.children, 'level'), '1')

    def test_allocation_system_still_controls_capacity_and_authority(self):
        authority = named(script('common/ideas/tfr_scw_volunteers.txt'), 'TFR_scw_volunteer_authority')
        self.assertEqual(scalar(authority.get('rule').children, 'can_send_volunteers'), 'yes')
        modifier = named(script('common/dynamic_modifiers/tfr_scw_volunteers.txt'), 'TFR_scw_volunteer_limits')
        self.assertEqual(scalar(modifier.children, 'send_volunteer_size'), 'var:TFR_scw_land_adjustment')
        self.assertEqual(scalar(modifier.children, 'send_volunteer_factor'), '-1000')
        self.assertEqual(scalar(modifier.children, 'send_volunteer_divisions_required'), '-1')


if __name__ == '__main__':
    unittest.main(verbosity=2)
