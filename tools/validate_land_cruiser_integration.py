"""Check integrated unit stats against all five original technologies."""
from decimal import Decimal
import json
from pathlib import Path

from hoi4_script import Block, parse, walk
from integrate_land_cruiser_bonuses import ROOT, TECHS


def read(path):
    return parse(path.read_text(encoding='utf-8-sig'))


def main():
    report = json.loads((ROOT / 'docs/land-cruiser-integrated-tech.json').read_text(encoding='utf-8'))
    backup = Path(report['backup'])
    before_techs = read(backup / 'common/technologies/NSB_armor.txt').get('technologies')
    current_techs = read(ROOT / 'common/technologies/NSB_armor.txt').get('technologies')
    original_bonuses = {'land_cruiser': {}, 'super_heavy_armor': {}}
    for name in TECHS:
        original = before_techs.get(name)
        current = current_techs.get(name)
        assert current.get('allow').get('always') == 'no'
        assert not current.entries('folder') and not current.entries('path')
        assert not current.entries('land_cruiser') and not current.entries('super_heavy_armor')
        assert current.get('enable_equipment_modules', Block([])).atoms() == original.get('enable_equipment_modules', Block([])).atoms()
        for unit in original_bonuses:
            modifiers = original.get(unit)
            if not isinstance(modifiers, Block):
                continue
            for stat in modifiers.entries():
                children = stat.value.entries() if isinstance(stat.value, Block) else [stat]
                for child in children:
                    key = (stat.key, child.key) if isinstance(stat.value, Block) else (stat.key,)
                    original_bonuses[unit][key] = original_bonuses[unit].get(key, Decimal(0)) + Decimal(child.value)
    for unit, filename in [('land_cruiser', 'land_cruiser.txt'), ('super_heavy_armor', 'super_heavy_armor.txt')]:
        original = read(backup / 'common/units' / filename).get('sub_units').get(unit)
        current = read(ROOT / 'common/units' / filename).get('sub_units').get(unit)
        for key, expected in original_bonuses[unit].items():
            a, b = original, current
            for part in key[:-1]:
                a, b = a.get(part), b.get(part)
            delta = Decimal(b.get(key[-1], '0')) - Decimal(a.get(key[-1], '0'))
            assert delta == expected, (unit, key, delta, expected)
        # Core requirements and cost-related unit attributes are preserved.
        for key in ('manpower', 'weight', 'training_time', 'combat_width'):
            assert original.get(key) == current.get(key), (unit, key)
        assert original.get('need').mapping() == current.get('need').mapping()
    cannon = current_techs.get(TECHS[-1]).get('enable_equipment_modules').atoms()
    assert cannon == ['lc_high_impact_obliterator_cannon']
    effect = read(ROOT / 'common/scripted_effects/tfr_lc_integrated_tech.txt').get('TFR_grant_lc_integrated_tech').get('if')
    assert {e.key for e in effect.get('set_technology').entries()} == set(TECHS) | {'popup'}
    assert effect.get('limit').get('has_dlc') == 'Gotterdammerung'
    actions = read(ROOT / 'common/on_actions/tfr_lc_integrated_tech.txt').get('on_actions')
    assert actions.get('on_startup').get('effect').get('every_country').get('TFR_grant_lc_integrated_tech') == 'yes'
    assert actions.get('on_monthly').get('effect').get('TFR_grant_lc_integrated_tech') == 'yes'
    for file in ('NSB_armor.txt', 'armor.txt'):
        techs = read(ROOT / 'common/technologies' / file)
        assert not [e for e, _ in walk(techs) if e.key == 'leads_to_tech' and e.value in TECHS]
    print('PASS: all original Land Cruiser and Super Heavy unit/terrain values integrated once, with scopes preserved.')
    print('PASS: cannon retained, technologies hidden and granted automatically; unit needs/costs preserved.')


if __name__ == '__main__':
    main()
