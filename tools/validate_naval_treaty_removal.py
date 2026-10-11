"""Ensure the loaded overlay cannot restore treaties or their ship-cost limits."""
import json

from hoi4_script import Block, overlay_files, parse, walk
from integrate_naval_tech_bonuses import sha
from naval_startup_audit import ROOT, VANILLA
from remove_naval_treaty import IDEAS, FOCUSES, FLAGS, REPORT

REMOVED_DECISIONS = {'MTG_abandon_treaty_democratic', 'MTG_abandon_treaty_fascist',
    'MTG_abandon_treaty_japanese', 'MTG_cheat_on_treaty', 'MTG_invite_FROM_to_treaty',
    'MTG_send_treaty_warning_to_FROM_previous_signatory', 'MTG_send_treaty_warning_to_FROM',
    'MTG_treaty_reduction_mission', 'MTG_treaty_reduction_signatory_mission',
    'MTG_treaty_renew_mission', 'MTG_escalator_clause_invocation_mission',
    'ENG_britain_demands_treaty_compliance', 'ENG_demand_treaty_compliance',
    'JAP_break_the_london_naval_treaty'}
REMOVED_EVENTS = {'mtg_britain.106', 'mtg_britain.107', 'mtg_britain.108',
                  'mtg_news.17', 'mtg_news.60', 'mtg_news.61'}


def main():
    report = json.loads(REPORT.read_text(encoding='utf-8'))
    for change in report['files']:
        assert sha((ROOT / change['source']).read_text(encoding='utf-8-sig')) == change['after'], change['source']
        parse((ROOT / change['source']).read_text(encoding='utf-8-sig'))
    forbidden = IDEAS | FOCUSES | FLAGS | REMOVED_DECISIONS | REMOVED_EVENTS | {'MTG_naval_treaties'}
    checked = 0
    for folder in ('common/ideas', 'common/decisions', 'common/decisions/categories',
                   'common/national_focus', 'common/ai_strategy', 'common/ai_strategy_plans',
                   'common/on_actions', 'common/scripted_effects', 'common/factions/goals',
                   'history/countries', 'events'):
        for path in overlay_files(ROOT, VANILLA, folder):
            source = path.read_text(encoding='utf-8-sig')
            checked += 1
            if not any(value in source for value in forbidden) and 'production_cost_max_ship_hull_' not in source and 'MTG_naval_treaty.' not in source:
                continue
            for e, _ in walk(parse(source)):
                assert e.key not in forbidden, (path, e.key)
                assert not e.key.startswith('production_cost_max_ship_hull_'), (path, 'Treaty hull cap remains')
                if isinstance(e.value, str):
                    assert e.value not in forbidden, (path, e.line, e.key, e.value)
                    assert not e.value.startswith('MTG_naval_treaty.'), (path, 'Treaty event survives')
                else:
                    assert not (set(e.value.atoms()) & forbidden), (path, 'Deleted treaty focus remains in AI plan')
    for relative in ('common/decisions/MTG_naval_treaty.txt', 'events/MTG_naval_treaty_events.txt'):
        assert (ROOT / relative).exists(), 'Missing vanilla fallback override'
        assert not parse((ROOT / relative).read_text(encoding='utf-8-sig')).entries()
    trigger = parse((ROOT / 'common/scripted_triggers/00_scripted_triggers.txt').read_text(encoding='utf-8-sig'))
    assert trigger.get('has_naval_treaty_trigger').mapping() == {'always': 'no'}
    effects = parse((ROOT / 'common/scripted_effects/00_scripted_effects.txt').read_text(encoding='utf-8-sig'))
    assert not effects.get('remove_naval_treaty_effect').entries()
    japan = parse((ROOT / 'common/national_focus/japan.txt').read_text(encoding='utf-8-sig'))
    focuses = {e.value.get('id'): e.value for e, _ in walk(japan)
               if e.key == 'focus' and isinstance(e.value, Block)}
    downstream = focuses['JAP_non_aggression_pact_with_china']
    parent = 'JAP_prepare_for_war_with_the_soviet_union'
    assert parent in focuses
    assert downstream.get('relative_position_id') == parent
    assert downstream.get('prerequisite').get('focus') == parent
    # Keep the unrelated South American arms-race penalties, invasion bonuses,
    # and British monarchy/independence events intact.
    shared = parse((ROOT / 'common/ideas/TOA_shared_ideas.txt').read_text(encoding='utf-8-sig'))
    idea = next(e.value for e, _ in walk(shared) if e.key == 'SMB_MTG_naval_arms_race_legacy')
    assert idea.get('modifier').get('production_speed_dockyard_factor') == '-0.4'
    assert idea.get('modifier').get('industrial_capacity_dockyard') == '-0.15'
    events = parse((ROOT / 'events/MTG_Britain.txt').read_text(encoding='utf-8-sig'))
    ids = {e.value.get('id') for e in events.entries('country_event')}
    assert {'mtg_britain.105', 'mtg_britain.109'} <= ids
    print(f'PASS: {checked} loaded script files inspected; no treaty ideas, decisions, categories, event calls, focus references or hull cost caps remain.')
    print(f'PASS: {len(report["files"])} edited files parse; vanilla fallbacks blocked; Japan branch preserved; compatibility helpers inert.')


if __name__ == '__main__':
    main()
