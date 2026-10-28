"""Check the installed research tree, unlock progression, project gates and hooks."""
import json
from pathlib import Path

from hoi4_script import Block, overlay_files, parse, walk

ROOT = Path(__file__).resolve().parents[1]
VANILLA = Path('C:/Program Files (x86)/Steam/steamapps/common/Hearts of Iron IV')


def read(relative, root=ROOT):
    return parse((root / relative).read_text(encoding='utf-8-sig'))


def plain(b):
    if not isinstance(b, Block):
        return b
    return [(e.key, e.op, plain(e.value)) for e in b.entries()] + b.atoms()


def condition(block, held, bba, radar):
    values = []
    for e in block.entries():
        if e.key == 'OR':
            values.append(any(condition(Block([child]), held, bba, radar) for child in e.value.entries()))
        elif e.key == 'NOT':
            values.append(not condition(e.value, held, bba, radar))
        elif e.key == 'has_tech':
            values.append(e.value in held)
        elif e.key == 'has_dlc':
            assert e.value == 'By Blood Alone'
            values.append(bba)
        elif e.key == 'is_special_project_completed':
            assert e.value == 'sp:sp_air_radar'
            values.append(radar)
        else:
            raise AssertionError(f'Unimplemented condition: {e.key}')
    return all(values)


def execute(block, held, bba=True, radar=False):
    grants = []
    for e in block.entries():
        if e.key == 'if':
            if condition(e.value.get('limit'), held, bba, radar):
                grants += execute(e.value, held, bba, radar)
        elif e.key == 'set_technology':
            for tech in e.value.entries():
                if tech.key != 'popup':
                    assert tech.value == '1'
                    held.add(tech.key)
                    grants.append(tech.key)
        else:
            assert e.key == 'limit', e.key
    return grants


def main():
    airfile = 'common/technologies/bba_air_techs.txt'
    current = read(airfile).get('technologies')
    vanilla = read(airfile, VANILLA).get('technologies')
    assert set(current.mapping()) == set(vanilla.mapping()), 'Lost vanilla tech IDs'
    hidden = []
    hooks = 0
    for tech in current.entries():
        if not isinstance(tech.value, Block):
            continue
        original = vanilla.get(tech.key)
        assert plain(tech.value.get('enable_equipments')) == plain(original.get('enable_equipments'))
        assert plain(tech.value.get('enable_equipment_modules')) == plain(original.get('enable_equipment_modules'))
        year_changes = {f'{tier}_{family}_airframe': year
                        for tier, year in [('improved', '1939'), ('advanced', '1941'), ('modern', '1943')]
                        for family in ('small', 'medium', 'large')}
        year_changes.update({'bba_improved_transport_plane': '1939', 'bba_strategic_airlifter': '1942'})
        assert tech.value.get('start_year') == year_changes.get(tech.key, original.get('start_year')), tech.key
        assert tech.value.get('research_cost') == original.get('research_cost')
        if tech.value.get('enable_equipment_modules') and tech.key != 'suicide_charge':
            hidden.append(tech.key)
            assert not tech.value.entries('folder'), tech.key
            assert not tech.value.entries('path'), tech.key
            assert tech.value.get('allow').get('always') == 'no', tech.key
        else:
            assert plain(tech.value.get('allow')) == plain(original.get('allow')), tech.key
        if 'airframe' in tech.key:
            hook = tech.value.get('on_research_complete')
            assert hook.get('hidden_effect').get('TFR_air_unlock_modules') == 'yes', tech.key
            assert hook.get('custom_effect_tooltip') == 'TFR_AIR_MODULES_UNLOCK_TT'
            hooks += 1
    assert len(hidden) == 19, hidden
    assert hooks == 16

    technologies = {}
    for path in overlay_files(ROOT, VANILLA, 'common/technologies'):
        for tech in parse(path.read_text(encoding='utf-8-sig')).get('technologies').entries():
            if isinstance(tech.value, Block):
                assert tech.key not in technologies, f'Duplicate technology {tech.key}'
                technologies[tech.key] = tech.value
    effect = read('common/scripted_effects/tfr_air_modules.txt').get('TFR_air_unlock_modules')
    for entry, _ in walk(effect):
        if entry.key == 'has_tech':
            assert entry.value in technologies, entry.value
        if entry.key == 'set_technology':
            for tech in entry.value.entries():
                assert tech.key == 'popup' or tech.key in technologies, tech.key
    assert not any(e.key == 'create_equipment_variant' for e, _ in walk(effect))
    assert all(not e.key.startswith('tfr_air_') for e in current.entries())

    def modules(held):
        return {m for t in held for m in technologies[t].get('enable_equipment_modules', Block([])).atoms()}

    # Independent era expectations: first access follows the next researched
    # airframe generation at/after the module's vanilla date.
    eras = [('iw', 1926, 1), ('basic', 1936, 2), ('improved', 1940, 3),
            ('advanced', 1944, 4), ('modern', 1945, 4)]
    scenarios = 0
    for family in ('small', 'medium', 'large'):
        for tier, year, engine in eras:
            for radar in (False, True):
                for bba in (False, True):
                    initial = {f'{tier}_{family}_airframe'}
                    held = set(initial)
                    grants = execute(effect, held, bba, radar)
                    scenarios += 1
                    if not bba:
                        assert held == initial
                        continue
                    assert execute(effect, held, bba, radar) == [], 'Repeated grants'
                    unlocked = modules(held)
                    for number in range(1, 5):
                        assert (f'engine_{number}_1x' in unlocked) == (number <= engine)
                    for tech in hidden:
                        module_date = int(vanilla.get(tech).get('start_year'))
                        assert (tech in held) == (module_date <= year), (tier, tech)
                    assert ('tank_buster_1' in unlocked) == (year >= 1936)
                    assert ('rocket_rails' in unlocked) == (year >= 1940)
                    assert ('bomb_sights_2' in unlocked) == (year >= 1940)
                    assert ('air_air_radar_1' in unlocked) == (radar and year >= 1940)
                    assert ('air_ground_radar_2' in unlocked) == (radar and year >= 1944)
                    assert 'jet_engine_1x' not in unlocked, 'Jet project bypass'
                    assert 'fixed_explosive_charge' not in unlocked, 'Focus-only module granted'
                    assert not {'antitank1', 'antitank2', 'radio', 'centimetric_radar'} & set(grants)
                    assert not any('airframe' in t for t in grants), 'Free airframe granted'
    # Project arriving after airframe research; monthly/history/release catch-up.
    held = {'advanced_medium_airframe'}
    execute(effect, held)
    execute(effect, held, radar=True)
    assert 'air_ground_radar_2' in modules(held)
    held = set()
    execute(effect, held)
    assert not {'engines_2', 'aa_hmg', 'engines_4'} & held
    held.add('improved_small_airframe')
    execute(effect, held)
    assert {'engines_2', 'engines_3', 'aa_hmg'} <= held
    assert 'engines_4' not in held

    actions = read('common/on_actions/tfr_air_simplified_on_actions.txt').get('on_actions')
    assert actions.get('on_startup').get('effect').get('every_country').get('TFR_air_unlock_modules') == 'yes'
    assert actions.get('on_monthly').get('effect').get('TFR_air_unlock_modules') == 'yes'
    ui = read('interface/countrytechtreeview.gui')
    tab = next(e.value for e, _ in walk(ui) if isinstance(e.value, Block)
               and e.value.get('name') == 'bba_air_techs_folder')
    roots = {e.value.get('name') for e in tab.entries('gridboxtype')
             if not str(e.value.get('name')).startswith('tfr_project_card_')}
    assert roots == {'basic_small_airframe_tree', 'basic_medium_airframe_tree', 'basic_large_airframe_tree',
                     'bba_early_transport_plane_tree', 'sp_centrifugal_jet_tech_tree',
                     'reinforced_wings_mothership_tree'}
    for node in tab.entries('gridboxtype'):
        if node.value.get('name') in {'basic_small_airframe_tree', 'basic_medium_airframe_tree', 'basic_large_airframe_tree'}:
            assert node.value.get('position').get('y') == '32'
    for family in ('small', 'medium', 'large'):
        for tier, expected_y in [('basic', '2'), ('improved', '4'), ('advanced', '6'), ('modern', '10')]:
            folder = next(f.value for f in current.get(f'{tier}_{family}_airframe').entries('folder')
                          if f.value.get('name') == 'bba_air_techs_folder')
            assert folder.get('position').get('y') == expected_y
    wing = current.get('reinforced_wings_mothership')
    assert plain(wing.get('allow')) == plain(vanilla.get('reinforced_wings_mothership').get('allow'))
    assert not any(p.value.get('leads_to_tech') == 'reinforced_wings_mothership'
                   for p in current.get('improved_large_airframe').entries('path'))
    assert wing.entries('path')[0].value.get('leads_to_tech') == 'miniature_fighters'
    assert current.get('miniature_fighters').entries('path')[0].value.get('leads_to_tech') == 'aerial_hangars'
    for name, x in [('reinforced_wings_mothership', '0'), ('miniature_fighters', '3'), ('aerial_hangars', '6')]:
        folder = next(f.value for f in current.get(name).entries('folder') if f.value.get('name') == 'bba_air_techs_folder')
        assert folder.get('position').get('x') == '0' and folder.get('position').get('y') == x
    projects = {e.value.get('name'): e.value for e in tab.entries('gridboxtype')}
    assert projects['reinforced_wings_mothership_tree'].get('format') == 'LEFT'
    assert projects['sp_centrifugal_jet_tech_tree'].get('position').get('y') == '1380'
    for family in ('small', 'medium', 'large'):
        interwar = current.get(f'iw_{family}_airframe')
        assert not interwar.entries('folder')
        assert not any(p.value.get('leads_to_tech') == f'basic_{family}_airframe'
                       for p in interwar.entries('path'))
        assert current.get(f'basic_{family}_airframe').entries('folder')
        assert interwar.get('enable_equipments').atoms() == vanilla.get(f'iw_{family}_airframe').get('enable_equipments').atoms()
    support = next(e.value for e, _ in walk(ui) if isinstance(e.value, Block)
                   and e.value.get('name') == 'support_folder')
    assert not any(e.value.get('name') == 'sp_centrifugal_jet_tech_tree'
                   for e in support.entries('gridboxtype'))
    centrifugal = current.get('sp_centrifugal_jet_tech')
    assert [f.value.get('name') for f in centrifugal.entries('folder')] == ['bba_air_techs_folder', 'air_techs_folder']
    transport = next(e.value for e in tab.entries('gridboxtype') if e.value.get('name') == 'bba_early_transport_plane_tree')
    assert transport.get('format') == 'LEFT'
    assert int(transport.get('position').get('y')) > 1000
    for tech in ('bba_early_transport_plane', 'bba_improved_transport_plane', 'bba_strategic_airlifter'):
        pos = current.get(tech).entries('folder')[0].value.get('position')
        assert pos.get('x') == '0'
    equipment = read('common/units/equipment/plane_airframes.txt').get('equipments')
    for family in ('small', 'cv_small', 'medium', 'large'):
        for tier, year in [(2, '1939'), (3, '1941'), (4, '1943')]:
            assert equipment.get(f'{family}_plane_airframe_{tier}').get('year') == year
    transport_equipment = read('common/units/equipment/quad_engine_airframe.txt').get('equipments')
    assert transport_equipment.get('transport_plane_equipment_2').get('year') == '1939'
    assert transport_equipment.get('transport_plane_equipment_3').get('year') == '1942'
    # Existing designer and equipment files have not been altered.
    report = json.loads((ROOT / 'docs/air-research-simplified.json').read_text())
    backup = Path(report['backup'])
    before = read('interface/countrytechtreeview.gui', backup)
    def outside_air(tree):
        def normalized(block, skip_height=False):
            result = []
            name = block.get('name')
            for e in block.entries():
                if isinstance(e.value, Block):
                    child_name = e.value.get('name')
                    if child_name in {'bba_air_techs_folder', 'armor_tech_1_tree'} or str(child_name).startswith('tfr_experimental_projects_title') or str(child_name).startswith('tfr_project_card_'):
                        continue
                    # The experimental sections extend these existing backgrounds.
                    child_skip_height = e.key == 'size' and name in {'techtree_stripes', 'tiled_window_transparent_transparent', 'size_filler'}
                    value = normalized(e.value, child_skip_height)
                else:
                    if skip_height and e.key in {'height', 'width'}:
                        continue
                    value = e.value
                result.append((e.key, e.op, value))
            return result
        return normalized(tree)
    assert outside_air(ui) == outside_air(before), 'Unrelated UI changed'
    loc = ROOT / 'localisation/english/tfr_air_simplified_l_english.yml'
    assert loc.read_bytes().startswith(b'\xef\xbb\xbf')
    print(f'PASS: {len(hidden)} hidden module techs; {hooks} airframe hooks; {scenarios} DLC/era/family/project scenarios.')
    print('PASS: no future engines, free airframes, unrelated technology grants or template creation; project gates retained.')
    print('PASS: startup/monthly catch-up, idempotence, four main UI branches and unchanged surrounding UI.')


if __name__ == '__main__':
    main()
