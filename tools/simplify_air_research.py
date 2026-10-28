"""Integrate ordinary aircraft module research into BBA airframe generations."""
import json
import shutil
from datetime import datetime
from pathlib import Path

from hoi4_script import Block, parse, replace_spans, walk

ROOT = Path(__file__).resolve().parents[1]
VANILLA = Path('C:/Program Files (x86)/Steam/steamapps/common/Hearts of Iron IV')
TIERS = {
    'iw': ['early_bombs', 'photo_reconnaisance', 'aa_lmg', 'engines_1'],
    'basic': ['armor_piercing_bombs', 'air_torpedoe_1', 'engines_2',
              'range_improvements', 'aircraft_construction'],
    'improved': ['heavy_bombs', 'air_torpedoe_2', 'survivability_studies',
                 'aa_hmg', 'aa_cannon_1', 'engines_3'],
    'advanced': ['air_torpedoe_3', 'aa_cannon_2', 'engines_4'],
    'modern': ['aa_cannon_3'],
}
SUPPORT = {
    'basic': ['tank_buster_1', 'radio_navigation_1', 'bomb_sights_1'],
    'improved': ['tank_buster_2', 'rocket_rails', 'radio_navigation_2', 'bomb_sights_2'],
}
RADAR = {
    'improved': ['air_air_radar_1', 'air_ground_radar_1'],
    'advanced': ['air_air_radar_2', 'air_ground_radar_2'],
}
FAMILIES = ('small', 'medium', 'large')
EFFECT = 'TFR_air_unlock_modules'


def save(relative, text, bom=False):
    p = ROOT / relative
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding='utf-8-sig' if bom else 'utf-8', newline='\r\n')


def generation_condition(tier):
    tiers = list(TIERS)
    return 'OR = { ' + ' '.join(
        f'has_tech = {t}_{family}_airframe'
        for t in tiers[tiers.index(tier):] for family in FAMILIES
    ) + ' has_tech = supersonic_small_airframe }'


def grant(techs, condition=None):
    missing = 'OR = { ' + ' '.join(f'NOT = {{ has_tech = {t} }}' for t in techs) + ' }'
    return ('\tif = {\n\t\tlimit = {\n' +
            (f'\t\t\t{condition}\n' if condition else '') +
            f'\t\t\t{missing}\n\t\t}}\n\t\tset_technology = {{\n\t\t\tpopup = no\n' +
            ''.join(f'\t\t\t{t} = 1\n' for t in techs) + '\t\t}\n\t}\n')


def main():
    relative_files = [
        'common/technologies/bba_air_techs.txt',
        'common/technologies/tfr_integrated_air_modules.txt',
        'common/scripted_effects/tfr_air_modules.txt',
        'common/on_actions/tfr_air_simplified_on_actions.txt',
        'interface/countrytechtreeview.gui',
        'localisation/english/tfr_air_simplified_l_english.yml',
    ]
    if (ROOT / relative_files[0]).exists():
        raise SystemExit('Air override already exists; edit the installed implementation in place.')
    backup = Path.home() / '.codex/backups' / ('tfr-air-simplified-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
    backup.mkdir(parents=True)
    for relative in relative_files:
        p = ROOT / relative
        if p.exists():
            dest = backup / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest)
    shutil.copy2(VANILLA / relative_files[0], backup / 'vanilla_bba_air_techs.txt')
    (backup / 'manifest.json').write_text(json.dumps({
        'root': str(ROOT), 'files': relative_files,
        'originally_present': [r for r in relative_files if (ROOT / r).exists()],
    }, indent=2), encoding='utf-8')

    source = (VANILLA / relative_files[0]).read_text(encoding='utf-8-sig')
    techs = parse(source).get('technologies')
    hidden = {t for group in TIERS.values() for t in group}
    replacements = []
    for tech in techs.entries():
        if not isinstance(tech.value, Block):
            continue
        b = tech.value
        years = {f'{tier}_{family}_airframe': year
                 for tier, year in [('improved', 1939), ('advanced', 1941), ('modern', 1943)]
                 for family in FAMILIES}
        years.update({'bba_improved_transport_plane': 1939, 'bba_strategic_airlifter': 1942})
        if tech.key in years:
            y = b.entries('start_year')[0]
            replacements.append((y.start, y.end, f'start_year = {years[tech.key]}'))
        if tech.key in {f'iw_{family}_airframe' for family in FAMILIES}:
            for item in b.entries('folder') + b.entries('path'):
                replacements.append((item.start, item.end,
                                     '# TFR: interwar airframe remains in country history, hidden from the tree.'))
        if tech.key == 'improved_large_airframe':
            item = next(e for e in b.entries('path') if e.value.get('leads_to_tech') == 'reinforced_wings_mothership')
            replacements.append((item.start, item.end, '# TFR: mothership research is independent of improved large airframes.'))
        project_positions = {'reinforced_wings_mothership': 0, 'miniature_fighters': 3,
                             'aerial_hangars': 6, 'sp_centrifugal_jet_tech': 0}
        if tech.key in project_positions:
            folder = next(f for f in b.entries('folder') if f.value.get('name') == 'bba_air_techs_folder')
            pos = folder.value.entries('position')[0]
            replacements.append((pos.start, pos.end, f'position = {{ x = 0 y = {project_positions[tech.key]} }}'))
        if tech.key in hidden:
            for key in ('folder', 'path', 'ai_will_do', 'allow'):
                for item in b.entries(key):
                    replacements.append((item.start, item.end, ''))
            replacements.append((tech.end - 1, tech.end - 1,
                                 '\n\t\t# TFR: granted automatically by airframe generation.\n'
                                 '\t\tallow = { always = no }\n\t\tai_will_do = { factor = 0 }\n\t'))
        if 'airframe' in tech.key:
            unlock = (f'hidden_effect = {{ {EFFECT} = yes }} '
                      'custom_effect_tooltip = TFR_AIR_MODULES_UNLOCK_TT')
            hooks = b.entries('on_research_complete')
            if hooks:
                replacements.append((hooks[0].end - 1, hooks[0].end - 1,
                                     f'\n\t\t\t{unlock}\n\t\t'))
            else:
                replacements.append((tech.end - 1, tech.end - 1,
                                     f'\n\t\ton_research_complete = {{ {unlock} }}\n\t'))
        if '_medium_airframe' in tech.key or tech.key.startswith('bba_'):
            for folder in b.entries('folder'):
                pos = folder.value.get('position').entries('x')[0]
                replacements.append((pos.start, pos.end, 'x = 0'))
        if tech.key in {f'{tier}_{family}_airframe' for tier in ('basic', 'improved', 'advanced', 'modern') for family in FAMILIES}:
            folder = next(f for f in b.entries('folder') if f.value.get('name') == 'bba_air_techs_folder')
            y = folder.value.get('position').entries('y')[0]
            offset = 2
            replacements.append((y.start, y.end, f'y = {int(y.value) - offset}'))
    save(relative_files[0], '# TFR: four aircraft families; ordinary modules follow airframe research.\n' +
         replace_spans(source, replacements))

    extra_techs = 'technologies = {\n'
    for prefix, groups in [('support', SUPPORT), ('radar', RADAR)]:
        for tier, modules in groups.items():
            extra_techs += (f'\ttfr_air_{prefix}_{tier} = {{\n'
                            '\t\tallow = { always = no }\n\t\tai_will_do = { factor = 0 }\n'
                            '\t\tresearch_cost = 1\n\t\tenable_equipment_modules = {\n' +
                            ''.join(f'\t\t\t{m}\n' for m in modules) + '\t\t}\n\t}\n')
    save(relative_files[1], '# Aircraft-only unlocks: no artillery/electronics country bonuses.\n' + extra_techs + '}\n')

    effect = '# Shared aircraft modules follow the best researched airframe family, never the calendar.\n'
    effect += f'{EFFECT} = {{\n\tif = {{\n\t\tlimit = {{ has_dlc = "By Blood Alone" }}\n'
    body = ''
    for tier, tech_ids in TIERS.items():
        body += grant(tech_ids, generation_condition(tier) if tier != 'iw' else None)
    for tier in SUPPORT:
        body += grant([f'tfr_air_support_{tier}'], generation_condition(tier))
    for tier in RADAR:
        body += grant([f'tfr_air_radar_{tier}'], generation_condition(tier) +
                      '\n\t\t\tis_special_project_completed = sp:sp_air_radar')
    effect += ''.join('\t\t' + line + '\n' for line in body.splitlines()) + '\t}\n}\n'
    save(relative_files[2], effect)
    save(relative_files[3], '''# Startup covers history; monthly covers focuses, released countries and project rewards.
on_actions = {
    on_startup = {
        effect = { every_country = { TFR_air_unlock_modules = yes } }
    }
    on_monthly = {
        effect = { TFR_air_unlock_modules = yes }
    }
}
''')

    gui = (ROOT / relative_files[4]).read_text(encoding='utf-8-sig')
    gui_tree = parse(gui)
    tree = next(e for e, _ in walk(gui_tree)
                if isinstance(e.value, Block) and e.value.get('name') == 'bba_air_techs_folder')
    changes = []
    obsolete = {'early_bombs_tree', 'aa_lmg_tree', 'photo_reconnaisance_tree',
                'air_torpedoe_1_tree', 'experimental_rockets_tree'}
    positions = {'iw_small_airframe_tree': 565, 'iw_medium_airframe_tree': 905,
                 'iw_large_airframe_tree': 1245, 'bba_early_transport_plane_tree': 180,
                 'engines_1_tree': 1430}
    for item in tree.value.entries():
        if not isinstance(item.value, Block):
            continue
        name = item.value.get('name')
        if name in obsolete:
            changes.append((item.start, item.end, ''))
        elif name in positions:
            pos = item.value.entries('position')[0]
            y = 1160 if name == 'bba_early_transport_plane_tree' else (1380 if name == 'engines_1_tree' else 32)
            changes.append((pos.start, pos.end, f'position = {{ x = {positions[name]} y = {y} }}'))
            size = item.value.entries('size')[0]
            dimensions = ('1200 height = 150' if name == 'bba_early_transport_plane_tree' else
                          '200 height = 150' if name == 'engines_1_tree' else '400 height = 1100')
            changes.append((size.start, size.end, f'size = {{ width = {dimensions} }}'))
            if name in {'bba_early_transport_plane_tree', 'engines_1_tree'}:
                fmt = item.value.entries('format')[0]
                changes.append((fmt.start, fmt.end, 'format = "LEFT"'))
            if name == 'engines_1_tree':
                label = item.value.entries('name')[0]
                changes.append((label.start, label.end, 'name = "sp_centrifugal_jet_tech_tree"'))
            if name.startswith('iw_') and name.endswith('_airframe_tree'):
                label = item.value.entries('name')[0]
                changes.append((label.start, label.end, f'name = "{name.replace("iw_", "basic_", 1)}"'))
        elif name in {'airtech_subtitle_airframe', 'airtech_subtitle_transport', 'airtech_subtitle_weapons', 'airtech_subtitle_engines'}:
            changes.append((item.start, item.end, ''))
        elif name == 'airtech_year_right':
            pos = item.value.entries('position')[0]
            changes.append((pos.start, pos.end, 'position = { x = 1950 y = 25 }'))
        elif name == 'techtree_stripes':
            size = item.value.get('size').entries('width')[0]
            changes.append((size.start, size.end, 'width = 2200'))
            height = item.value.get('size').entries('height')[0]
            changes.append((height.start, height.end, 'height = 1600'))
        if name in {'airtech_year_left', 'airtech_year_right'}:
            for label in item.value.entries('instantTextBoxType'):
                if label.value.get('text') == '1933':
                    changes.append((label.start, label.end, ''))
                elif label.value.get('text') == '1950':
                    changes.append((label.start, label.end, ''))
                else:
                    pos = label.value.entries('position')[0]
                    old_date = label.value.get('text')
                    if old_date in {'1940', '1944', '1945'}:
                        date = label.value.entries('text')[0]
                        new_date = {'1940': '1939', '1944': '1941', '1945': '1943'}[old_date]
                        changes.append((date.start, date.end, f'text = "{new_date}"'))
                    shift = 140
                    changes.append((pos.start, pos.end,
                                    f'position = {{ x = {pos.value.get("x")} y = {int(pos.value.get("y")) - shift} }}'))
    headers = ''
    for name, label, xpos in [('small', 'TFR_AIR_SMALL', 632), ('medium', 'TFR_AIR_MEDIUM', 972),
                              ('large', 'TFR_AIR_LARGE', 1312), ('transport', 'TFR_AIR_TRANSPORT', 180),
                              ('projects', 'TFR_AIR_PROJECTS', 180)]:
        y = 1080 if name == 'transport' else (1300 if name == 'projects' else 110)
        alignment = 'left' if name in {'transport', 'projects'} else 'centre'
        headers += f'''
            instantTextBoxType = {{
                name = "tfr_air_title_{name}"
                position = {{ x = {xpos} y = {y} }}
                font = "hoi_33"
                text = "{label}"
                maxWidth = 260
                maxHeight = 62
                format = {alignment}
            }}
'''
    headers += '''
            gridboxtype = {
                name = "reinforced_wings_mothership_tree"
                position = { x = 180 y = 1380 }
                size = { width = 1000 height = 150 }
                slotsize = { width = 70 height = 70 }
                format = "LEFT"
            }
'''
    changes.append((tree.end - 1, tree.end - 1, headers + '\t\t'))
    save(relative_files[4], replace_spans(gui, changes))
    save(relative_files[5], '''l_english:
 TFR_AIR_SMALL: "§WSmall Airframes§!"
 TFR_AIR_MEDIUM: "§WMedium Airframes§!"
 TFR_AIR_LARGE: "§WLarge Airframes§!"
 TFR_AIR_TRANSPORT: "§WTransport Planes§!"
 TFR_AIR_PROJECTS: "§WSpecial Projects§!"
 TFR_AIR_MODULES_UNLOCK_TT: "Unlocks standard aircraft modules up to the best researched airframe generation. Special-project equipment retains its project requirements."
''', bom=True)
    report = {'backup': str(backup), 'tiers': TIERS, 'support_modules': SUPPORT,
              'radar_modules': RADAR, 'changed_files': relative_files}
    save('docs/air-research-simplified.json', json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
