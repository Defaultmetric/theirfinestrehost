"""Check bonus accounting, IC preservation, research guards and idempotence."""
import itertools
import json
from decimal import Decimal as D

from hoi4_script import Block, parse, walk
from integrate_naval_tech_bonuses import AUDIT, DESIGNS, stat, ship_class
from naval_startup_audit import NavalData, ROOT, VANILLA


def condition(block, techs, project=False):
    tests = []
    for e in block.entries():
        if e.key == 'OR':
            tests.append(any(condition(Block([entry]), techs, project) for entry in e.value.entries()))
        elif e.key == 'NOT':
            tests.append(not condition(e.value, techs, project))
        elif e.key == 'has_tech':
            tests.append(e.value in techs)
        elif e.key == 'has_dlc':
            tests.append(True)
        elif e.key == 'is_special_project_completed':
            tests.append(project)
        else:
            raise AssertionError(('Unknown test condition', e.key))
    return all(tests)


def grant(effect, techs, project):
    result = set(techs)
    for branch in effect.entries('if'):
        if condition(branch.value.get('limit'), result, project):
            result.update(e.key for e in branch.value.get('set_technology').entries() if e.key != 'popup')
    return result


def main():
    data = NavalData()
    audit = json.loads(AUDIT.read_text(encoding='utf-8'))
    designs = {e.value.get('name'): e.value for e, _ in walk(parse(DESIGNS.read_text(encoding='utf-8-sig')))
               if e.key == 'create_equipment_variant'}
    vanilla = parse((VANILLA / 'common/technologies/MTG_naval_Support.txt').read_text(encoding='utf-8-sig')).get('technologies')
    upgrades_seen = set()
    assert 'hidden_variant_migration' in audit
    assert not (ROOT / 'common/units/equipment/modules/tfr_integrated_naval_modules.txt').exists()
    assert not any(name.startswith('tfr_integrated_') for name in data.modules)
    for row in audit['designs']:
        variant = designs[row['name']]
        assert row['ship_class'] == ship_class(row['name'])
        expected = {}
        for tech in row['vanilla_techs']:
            for e in vanilla.get(tech).get(row['ship_class'], Block([])).entries():
                expected[e.key] = expected.get(e.key, D(0)) + D(e.value)
        assert expected == {k: D(v) for k, v in row['bonuses'].items()}
        assert abs(data.cost(row['hull'], variant) - row['cost_before']) < 0.000001
        assert not data.issues(row['hull'], variant)
        if 'engine_after' not in row:
            assert not expected and row['year'] < 1936
            continue
        modules = data.module_map(row['hull'], variant)
        assert modules['fixed_ship_engine_slot'] == row['engine_before']
        upgrade_name = row['hidden_upgrade']
        assert upgrade_name not in upgrades_seen
        upgrades_seen.add(upgrade_name)
        upgrade = data.upgrades[upgrade_name][0]
        assert upgrade.get('max_level') == '1'
        assert upgrade.get('level_requirements').get('1').get('always') == 'no'
        assert variant.get('upgrades').mapping() == {upgrade_name: '1'}
        assert upgrade_name in data.hull(row['hull'])['upgrades'].atoms()
        for key, value in row['upgrade_modifiers'].items():
            assert D(upgrade.get(key)) == D(value)
        for key, value in row['expected_stats_after'].items():
            assert abs(stat(data, row['hull'], variant, key)[0] - D(value)) < D('0.000001'), (row['name'], key)
        # Engines and every other fitted module match the original template.
        before = parse(row['script_before']).get('create_equipment_variant')
        assert variant.get('modules').mapping() == before.get('modules').mapping()
        assert set(row['upgrade_modifiers']) <= set(expected)
        assert not (set(row['upgrade_modifiers']) & {'build_cost_ic', 'naval_speed', 'fuel_consumption', 'naval_range'})
        for _, e, _, _ in data.history_variants:
            if e.value.get('name') == row['name']:
                assert e.value.get('modules').get('fixed_ship_engine_slot') == row['engine_before']
                assert e.value.get('upgrades').mapping() == variant.get('upgrades').mapping()
    effect = parse((ROOT / 'common/scripted_effects/tfr_integrated_naval_bonuses.txt').read_text(encoding='utf-8-sig')).get('TFR_navy_apply_integrated_global_bonuses')
    hidden = parse((ROOT / 'common/technologies/tfr_integrated_naval_bonuses.txt').read_text(encoding='utf-8-sig')).get('technologies')
    for year in (1936, 1938, 1942):
        tech = hidden.get(f'tfr_naval_damage_control_{year}')
        assert tech.get('critical_receive_chance') == '-0.1'
        assert tech.get('naval_critical_effect_factor') == '-0.1'
    assert hidden.get('tfr_naval_torpedo_concealment_1942').get('naval_torpedo_reveal_chance_factor') == '-0.25'
    assert not hidden.entries('tfr_integrated_naval_modules')
    startup = (ROOT / 'common/on_actions/tfr_navy_simplified_on_actions.txt').read_text(encoding='utf-8-sig')
    assert 'tfr_integrated_naval_modules' not in startup
    starting = {f'basic_ship_hull_{kind}' for kind in ('light', 'cruiser', 'heavy', 'submarine', 'carrier')}
    assert grant(effect, starting, False) - starting == {'tfr_naval_damage_control_1936'}
    assert grant(effect, set(), False) == set()
    cases = 0
    for improved, advanced, project in itertools.product(range(6), range(6), (False, True)):
        kinds = ('light', 'cruiser', 'heavy', 'submarine', 'carrier')
        held = starting.copy()
        if improved:
            held.add('improved_ship_hull_' + kinds[improved - 1])
        if advanced:
            held.add('advanced_ship_hull_' + kinds[advanced - 1])
        result = grant(effect, held, project)
        assert grant(effect, result, project) == result, 'Research/monthly recheck duplicates bonus'
        assert ('tfr_naval_damage_control_1938' in result) == bool(improved)
        assert ('tfr_naval_damage_control_1942' in result) == bool(advanced)
        assert ('tfr_naval_torpedo_concealment_1942' in result) == (advanced in (1, 2, 4))
        assert ('tfr_naval_replenishment_1938' in result) == bool(improved and project)
        assert ('tfr_naval_replenishment_1942' in result) == bool(advanced and project)
        cases += 1
    assert parse(DESIGNS.read_text(encoding='utf-8-sig')).get('TFR_navy_create_designs').get('TFR_navy_apply_integrated_global_bonuses') == 'yes'
    print(f'PASS: {len(designs)} designs; {len(upgrades_seen)} hidden packages; original modules, vanilla bonuses, IC/speed/fuel and history templates match.')
    print(f'PASS: {cases} research/project combinations; no calendar grant, no duplicate grants, no future global bonuses at start.')


if __name__ == '__main__':
    main()
