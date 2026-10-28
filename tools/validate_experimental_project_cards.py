"""Validate project coverage, unchanged rewards, card layout and synchronization."""
import json
import re
from collections import Counter
from pathlib import Path

from hoi4_script import Block, overlay_files, parse, replace_spans, walk
from add_experimental_project_cards import EXISTING, FOLDERS, ROOT, VANILLA
from arrange_experimental_cards import ICONS, LAND, SECTIONS, section
from integrate_land_cruiser_bonuses import TECHS as LC_TECHS


def read(path):
    return path.read_text(encoding='utf-8-sig')


def main():
    report = json.loads(read(ROOT / 'docs/experimental-project-cards.json'))
    cards = report['added_cards']
    by_project = {row['project']: row for row in cards}
    assert len(by_project) == len(cards) == 35
    techs = parse(read(ROOT / 'common/technologies/tfr_experimental_project_cards.txt')).get('technologies')
    assert set(techs.mapping()) == {r['card'] for r in cards}
    gfx = parse(read(ROOT / 'interface/tfr_experimental_project_cards.gfx'))
    sprites = {e.value.get('name'): e.value.get('texturefile') for e, _ in walk(gfx)
               if e.key.lower() == 'spritetype' and isinstance(e.value, Block)}
    assert len(sprites) == len(cards)
    loc_path = ROOT / 'localisation/english/tfr_experimental_project_cards_l_english.yml'
    assert loc_path.read_bytes().startswith(b'\xef\xbb\xbf')
    loc = read(loc_path)
    sync = parse(read(ROOT / 'common/scripted_effects/tfr_experimental_project_cards.txt')).get('TFR_sync_experimental_project_cards')
    branches = sync.entries('if')
    assert len(branches) == len(cards)
    backup = Path(report['backup'])
    all_projects = {}
    modified_files = set()
    for path in overlay_files(ROOT, VANILLA, 'common/special_projects/projects'):
        source = read(path)
        for e in parse(source).entries():
            if isinstance(e.value, Block) and e.value.get('specialization') in FOLDERS:
                assert e.key not in all_projects
                all_projects[e.key] = (e, path)
                if e.key not in by_project:
                    continue
                row = by_project[e.key]
                card = row['card']
                countries = e.value.get('project_output').entries('country_effects')
                markers = [m for country in countries for m, _ in walk(country.value)
                           if m.key == 'set_technology' and isinstance(m.value, Block) and m.value.get(card) == '1']
                assert len(markers) == 1, e.key
                assert markers[0].value.get('popup') == 'no'
                modified_files.add(path)
        # Removing only inserted markers must reconstruct every project's input
        # exactly, including optional rewards and all country/project effects.
        rel = path.relative_to(ROOT if path.is_relative_to(ROOT) else VANILLA)
        original = backup / rel
        if not original.exists():
            original = VANILLA / rel
        pattern = r'\n\t\t\thidden_effect = \{ set_technology = \{ tfr_project_card_[a-z0-9_]+ = 1 popup = no \} \} # TFR: project card\n\t\t'
        restored = re.sub(pattern, '', source)
        expected_source = read(original)
        if rel.as_posix() == 'common/special_projects/projects/land_projects.txt':
            project = parse(expected_source).get('sp_land_land_cruiser')
            replacements = []
            for e, parents in walk(project):
                if e.key != 'custom_effect_tooltip' or not isinstance(e.value, Block) or e.value.get('TECH') not in LC_TECHS:
                    continue
                parent = parents[-1] if parents else None
                target = parent if parent and parent.key == 'if' and len(parent.value.entries()) == 2 and parent.value.get('limit') else e
                replacements.append((target.start, target.end, '# TFR: follow-up technology integrated into unit stats.'))
            assert len(replacements) == 5
            expected_source = replace_spans(expected_source, replacements)
            project = parse(expected_source).get('sp_land_multi_charge_large_caliber_gun')
            parent = project.entries('special_project_parent')[0]
            original_parent = expected_source[parent.start:parent.end]
            new_parent = original_parent.replace('sp_land_super_heavy_howitzer', 'sp_land_self_propelled_super_heavy_howitzer')
            expected_source = expected_source[:parent.start] + new_parent + expected_source[parent.end:]
        assert restored == expected_source, f'Unexpected changes to project rewards in {rel}'
    assert len(all_projects) == report['project_count'] == 48
    assert set(all_projects) == set(by_project) | EXISTING
    assert not set(by_project) & EXISTING
    naval_cards = parse(read(ROOT / 'common/technologies/tfr_naval_project_ships.txt')).get('technologies')
    for name in ('tfr_card_naval_torpedo_cruiser', 'tfr_card_naval_fleet_submarine', 'tfr_card_naval_midget_submarine'):
        assert not naval_cards.get(name).entries('allow_branch')
    for name in ('tfr_card_naval_escort_carrier', 'tfr_card_naval_submarine_carrier'):
        assert naval_cards.get(name).get('allow_branch').get('has_dlc') == 'No Compromise, No Surrender'
    for row in cards:
        project, card = row['project'], row['card']
        b = techs.get(card)
        assert b.get('is_special_project_tech') == 'yes'
        assert b.get('allow').get('ROOT').get('is_special_project_completed') == 'sp:' + project
        assert b.get('ai_will_do').get('factor') == '0'
        visual_markers = {'tfr_project_card_land_flamethrower_tank': 'tfr_visual_marker_flame_tank',
                          'tfr_project_card_land_land_cruiser': 'tfr_visual_marker_land_cruiser',
                          'tfr_project_card_land_military_engineering_vehicles': 'tfr_visual_marker_military_engineering_vehicles',
                          'tfr_project_card_land_super_heavy_railway_gun': 'tfr_visual_marker_super_heavy_railway_gun',
                          'tfr_project_card_land_super_heavy_howitzer': 'tfr_visual_marker_super_heavy_howitzer',
                          'tfr_project_card_land_self_propelled_super_heavy_howitzer': 'tfr_visual_marker_self_propelled_super_heavy_howitzer',
                          'tfr_project_card_land_multi_charge_large_caliber_gun': 'tfr_visual_marker_multi_charge_large_caliber_gun',
                          }
        unlocks = [e for e in b.entries() if e.key.startswith('enable_')]
        if card in visual_markers:
            assert len(unlocks) == 1 and unlocks[0].key == 'enable_equipments'
            assert unlocks[0].value.atoms() == [visual_markers[card]]
        else:
            assert not unlocks, card
        assert {f.value.get('name') for f in b.entries('folder')} == set(row['folders'])
        assert sprites['GFX_' + card + '_medium'] == row['texture']
        assert (ROOT / row['texture']).is_file() or (VANILLA / row['texture']).is_file()
        assert f'{card}: "${project}$"' in loc
        matching = [b.value for b in branches if b.value.get('set_technology').get(card) == '1']
        assert len(matching) == 1
        limit = matching[0].get('limit')
        assert limit.get('is_special_project_completed') == 'sp:' + project
        assert limit.get('NOT').get('has_tech') == card
    actions = parse(read(ROOT / 'common/on_actions/tfr_experimental_project_cards.txt')).get('on_actions')
    assert actions.get('on_startup').get('effect').get('every_country').get('TFR_sync_experimental_project_cards') == 'yes'
    assert actions.get('on_monthly').get('effect').get('TFR_sync_experimental_project_cards') == 'yes'
    markers = read(ROOT / 'common/units/equipment/tfr_project_card_visual_markers.txt')
    marker_defs = parse(markers).get('equipments')
    assert set(marker_defs.mapping()) == set(visual_markers.values()) | {'tfr_visual_marker_amphibious_engine'}
    for name in visual_markers.values():
        marker = marker_defs.get(name)
        assert marker.get('is_buildable') == 'no' and marker.get('is_archetype') == 'yes'
        for p in (ROOT / 'common/units').glob('*.txt'):
            assert name not in read(p), (name, p)
    ui = parse(read(ROOT / 'interface/countrytechtreeview.gui'))
    for folder in {key[0] for key in SECTIONS} | {'infantry_folder'}:
        container = next(e.value for e, _ in walk(ui) if isinstance(e.value, Block) and e.value.get('name') == folder)
        expected = [row['card'] for row in cards if folder in row['folders']]
        grids = [e.value for e in container.entries('gridboxtype') if str(e.value.get('name')).startswith('tfr_project_card_')]
        integrated = {'tfr_project_card_land_land_cruiser'} if folder in {'armour_folder', 'nsb_armour_folder'} else ({'tfr_project_card_land_super_heavy_railway_gun'} if folder == 'support_folder' else ({'tfr_project_card_land_super_heavy_howitzer', 'tfr_project_card_land_self_propelled_super_heavy_howitzer', 'tfr_project_card_land_multi_charge_large_caliber_gun'} if folder == 'artillery_folder' else set()))
        assert {g.get('name') for g in grids} == {c + '_tree' for c in expected if c not in integrated}
        pos = [(int(g.get('position').get('x')), int(g.get('position').get('y'))) for g in grids]
        assert len(pos) == len(set(pos))
        section_names = {section(row) for row in cards if folder in row['folders']}
        for category in section_names:
            x0, y0, cols, dx, height = SECTIONS[(folder, category)]
            members = {row['card'] for row in cards if folder in row['folders'] and section(row) == category}
            for g in grids:
                card_name = g.get('name').removesuffix('_tree')
                if card_name not in members or (folder == 'nsb_armour_folder' and card_name == 'tfr_project_card_land_flamethrower_tank') or (folder == 'support_folder' and card_name == 'tfr_project_card_land_military_engineering_vehicles'):
                    continue
                x, y = int(g.get('position').get('x')), int(g.get('position').get('y'))
                assert x >= x0 and (x - x0) % dx == 0 and (x - x0) // dx < cols
                assert y >= y0 and (y - y0) % 170 == 0 and y + 140 <= height
            title = 'tfr_experimental_projects_title_' + category
            assert len([e for e in container.entries('instantTextBoxType') if e.value.get('name') == title]) == (0 if category == 'general' else 1)
    for row in cards:
        if row['project'] in LAND:
            assert row['folders'] == LAND[row['project']]
        assert row['source_technology_icon'] == 'GFX_' + ICONS[row['project']] + '_medium'
        assert '/special_project/project_icons/' not in row['texture']
    print(f'PASS: {len(all_projects)} projects accounted for: {len(EXISTING)} existing cards/techs and {len(cards)} new cards.')
    print('PASS: project effects and rewards preserved, immediate completion markers and guarded startup/monthly catch-up.')
    print('PASS: all cards have unique positions, project gating, native tech art and subject-appropriate folders.')


if __name__ == '__main__':
    main()
