"""Place experimental cards with related research and reuse native tech art."""
import json
import shutil
from datetime import datetime
from pathlib import Path

from hoi4_script import Block, parse, replace_spans, walk

ROOT = Path(__file__).resolve().parents[1]
VANILLA = Path('C:/Program Files (x86)/Steam/steamapps/common/Hearts of Iron IV')

ICONS = {
    'sp_air_bouncing_bomb': 'sp_rockets_glide_bombs',
    'sp_air_earthshaker_bomb': 'heavy_bombs',
    'sp_air_intercontinental_bomber': 'strat_bomber_intercontinental_equipment',
    'sp_air_mothership_aircraft': 'mothership_equipment',
    'sp_air_jet_engine': 'sp_centrifugal_jet_tech',
    'sp_air_axial_jet_engine': 'jet_engines',
    'sp_air_supersonic_jet': 'supersonic_fighter1',
    'sp_air_helicopter': 'helicopter_equipment',
    'sp_land_flamethrower_tank': 'light_flame_tank',
    'sp_land_military_engineering_vehicles': 'armored_support_vehicle',
    'sp_land_land_cruiser': 'land_cruiser_chassis',
    'sp_land_super_heavy_howitzer': 'super_heavy_artillery_equipment',
    'sp_land_self_propelled_super_heavy_howitzer': 'self_propelled_super_heavy_artillery_equipment',
    'sp_land_super_heavy_railway_gun': 'super_heavy_railway_gun_equipment',
    'sp_land_multi_charge_large_caliber_gun': 'railway_gun',
    'sp_land_stronghold_network': 'basic_fortification_tech',
    'sp_naval_rocket_launching_submarine': 'rocket_submarine',
    'sp_naval_nuclear_missile_submarine': 'nuclear_missile_submarine',
    'sp_naval_nuclear_torpedo': 'sp_variable_time_fuze_shells',
    'sp_naval_aip_engine': 'sp_submarine_aip_diesel_combination_engines',
    'sp_naval_anechoic_tiles': 'sp_surface_shock_hardening_techniques',
    'sp_naval_underway_replenishment': 'sp_surface_standard_tensioned_replenishment_alongside_method',
    'sp_naval_proximity_fuze': 'sp_surface_variable_time_fuze_shells',
    'sp_nuclear_reactor': 'nuclear_reactor',
    'sp_commercial_nuclear_reactor': 'atomic_research',
    'sp_nuclear_engines': 'sp_centrifugal_jet_tech',
    'sp_nuclear_bomb': 'heavy_bombs',
    'sp_thermo_nuclear_bomb': 'sp_nuclear_isotope_separation',
    'sp_nuclear_warheads': 'sp_rockets_improved_guidance',
    'sp_rockets_flying_bomb': 'sp_rockets_glide_bombs',
    'sp_rockets_ballistic_missile': 'sp_rockets_improved_guidance',
    'sp_rockets_medium_range_ballistic_missile': 'sp_rockets_dual_chamber_rocket_engine_1',
    'sp_rockets_long_range_ballistic_missile': 'sp_rockets_dual_chamber_rocket_engine_2',
    'sp_rockets_ground_to_air_missile': 'sp_rockets_rocket_bomber',
    'sp_rocket_interceptor': 'rocket_interceptor_equipment_1',
}

LAND = {
    'sp_land_flamethrower_tank': ['armour_folder', 'nsb_armour_folder'],
    'sp_land_land_cruiser': ['armour_folder', 'nsb_armour_folder'],
    'sp_land_military_engineering_vehicles': ['support_folder'],
    'sp_land_super_heavy_howitzer': ['artillery_folder'],
    'sp_land_self_propelled_super_heavy_howitzer': ['artillery_folder'],
    'sp_land_super_heavy_railway_gun': ['support_folder'],
    'sp_land_multi_charge_large_caliber_gun': ['artillery_folder'],
    'sp_land_stronghold_network': ['electronics_folder'],
}


def groups(row):
    project = row['project']
    if project in LAND:
        return LAND[project]
    if project.startswith('sp_rockets_'):
        return ['electronics_folder']
    return row['folders']


def section(row):
    if row['project'].startswith('sp_nuclear_') or row['project'] == 'sp_commercial_nuclear_reactor':
        return 'nuclear'
    if row['project'].startswith('sp_rockets_'):
        return 'rockets'
    return 'general'


# Each section is placed after the folder's existing content, rather than
# overlaying the last visible research row. The paired armor folders serve
# games with and without No Step Back.
SECTIONS = {
    ('armour_folder', 'general'): (180, 1350, 5, 240, 1650),
    ('nsb_armour_folder', 'general'): (180, 1350, 5, 240, 1650),
    ('support_folder', 'general'): (180, 1660, 5, 240, 2000),
    ('artillery_folder', 'general'): (180, 1650, 5, 240, 2000),
    ('bba_air_techs_folder', 'general'): (180, 1690, 6, 240, 2250),
    ('air_techs_folder', 'general'): (180, 1470, 6, 240, 2050),
    ('mtgnavalfolder', 'general'): (180, 2320, 6, 240, 2750),
    ('naval_folder', 'general'): (180, 1420, 6, 240, 1850),
    ('electronics_folder', 'nuclear'): (180, 1530, 6, 240, 2350),
    ('electronics_folder', 'rockets'): (180, 1800, 6, 240, 2350),
    ('electronics_folder', 'general'): (180, 2070, 6, 240, 2350),
}


def read(path):
    return path.read_text(encoding='utf-8-sig')


def write(path, s, bom=False):
    path.write_text(s, encoding='utf-8-sig' if bom else 'utf-8', newline='\r\n')


def main():
    report_path = ROOT / 'docs/experimental-project-cards.json'
    report = json.loads(read(report_path))
    cards = report['added_cards']
    assert set(ICONS) == {row['project'] for row in cards}
    tech_path = ROOT / 'common/technologies/tfr_experimental_project_cards.txt'
    gui_path = ROOT / 'interface/countrytechtreeview.gui'
    gfx_path = ROOT / 'interface/tfr_experimental_project_cards.gfx'
    loc_path = ROOT / 'localisation/english/tfr_experimental_project_cards_l_english.yml'
    backup = Path.home() / '.codex/backups' / ('tfr-project-card-layout-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
    for p in (report_path, tech_path, gui_path, gfx_path, loc_path):
        target = backup / p.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, target)

    s = read(tech_path)
    techs = parse(s).get('technologies')
    changes = []
    for row in cards:
        row['folders'] = groups(row)
        b = techs.get(row['card'])
        folders = b.entries('folder')
        replacement = '\n'.join(f'folder = {{ name = {folder} position = {{ x = 0 y = 0 }} }}'
                                for folder in row['folders'])
        changes.append((folders[0].start, folders[0].end, replacement))
        changes.extend((f.start, f.end, '') for f in folders[1:])
    changed = replace_spans(s, changes)
    parse(changed)
    write(tech_path, changed)

    # These are the game's own research icons, not the larger monochrome
    # project blueprints intended for the facility window.
    gfx = parse(read(ROOT / 'interface/Technologies.gfx'))
    native = {e.value.get('name'): e.value.get('texturefile', e.value.get('textureFile'))
              for e, _ in walk(gfx) if e.key.lower() == 'spritetype' and isinstance(e.value, Block)}
    out = ['spriteTypes = {']
    for row in cards:
        source = 'GFX_' + ICONS[row['project']] + '_medium'
        texture = native[source]
        assert texture and ((ROOT / texture).is_file() or (VANILLA / texture).is_file()), source
        row['source_technology_icon'] = source
        row['texture'] = texture
        out.append(f'\tSpriteType = {{ name = "GFX_{row["card"]}_medium" texturefile = "{texture}" }}')
    out.append('}')
    write(gfx_path, '\n'.join(out) + '\n')

    gui = read(gui_path)
    tree = parse(gui)
    folder_names = set(k[0] for k in SECTIONS) | {'infantry_folder'}
    folders = {name: next(e for e, _ in walk(tree) if isinstance(e.value, Block) and e.value.get('name') == name)
               for name in folder_names}
    edits = []
    for name, folder in folders.items():
        for e in folder.value.entries():
            if isinstance(e.value, Block):
                item = str(e.value.get('name'))
                if item.startswith('tfr_project_card_') or item.startswith('tfr_experimental_projects_title'):
                    edits.append((e.start, e.end, ''))
        bg = next(e for e in folder.value.entries('containerWindowType') if e.value.get('name') in
                  ('techtree_stripes', 'size_filler', 'tiled_window_transparent_transparent'))
        desired = max([cfg[4] for (f, _), cfg in SECTIONS.items() if f == name] or [1275])
        h = bg.value.get('size').entries('height')[0]
        edits.append((h.start, h.end, f'height = {desired}'))
        if name == 'electronics_folder':
            width = bg.value.get('size').entries('width')[0]
            edits.append((width.start, width.end, 'width = 1700'))
    grouped = {}
    for row in cards:
        for folder in row['folders']:
            grouped.setdefault((folder, section(row)), []).append(row['card'])
    for key, members in grouped.items():
        x0, y0, columns, dx, height = SECTIONS[key]
        assert y0 + ((len(members) - 1) // columns) * 170 + 140 <= height
        folder, category = key
        title = {'nuclear': 'TFR_EXPERIMENTAL_NUCLEAR_CARDS',
                 'rockets': 'TFR_EXPERIMENTAL_ROCKET_CARDS'}.get(category, 'TFR_EXPERIMENTAL_CARDS')
        addition = f'''\n            instantTextBoxType = {{
                name = "tfr_experimental_projects_title_{category}"
                position = {{ x = {x0} y = {y0 - 80} }}
                font = "hoi_33"
                text = "{title}"
                maxWidth = 600
                maxHeight = 62
                format = left
            }}\n'''
        for i, card in enumerate(members):
            x, y = x0 + (i % columns) * dx, y0 + (i // columns) * 170
            addition += f'''            gridboxtype = {{
                name = "{card}_tree"
                position = {{ x = {x} y = {y} }}
                size = {{ width = 100 height = 140 }}
                slotsize = {{ width = 10 height = 10 }}
                format = "UP"
            }}\n'''
        edits.append((folders[folder].end - 1, folders[folder].end - 1, addition + '\t\t'))
    changed = replace_spans(gui, edits)
    parse(changed)
    write(gui_path, changed)

    loc = read(loc_path)
    if 'TFR_EXPERIMENTAL_ROCKET_CARDS:' not in loc:
        loc += ' TFR_EXPERIMENTAL_ROCKET_CARDS: "§WRocket Projects§!"\n'
    write(loc_path, loc, bom=True)
    report['folder_counts'] = {name: sum(name in row['folders'] for row in cards) for name in sorted(folder_names)}
    report['layout_backup'] = str(backup)
    write(report_path, json.dumps(report, indent=2) + '\n')
    print(json.dumps({'backup': str(backup), 'folder_counts': report['folder_counts']}, indent=2))


if __name__ == '__main__':
    main()
