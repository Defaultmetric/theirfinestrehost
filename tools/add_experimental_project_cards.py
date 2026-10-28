"""Add informational technology cards for experimental-project completions.

Projects retain their own rewards; the cards do not award equipment or modifiers.
"""
from collections import defaultdict
from datetime import datetime
import json
import shutil
from pathlib import Path

from hoi4_script import Block, overlay_files, parse, replace_spans, walk

ROOT = Path(__file__).resolve().parents[1]
VANILLA = Path('C:/Program Files (x86)/Steam/steamapps/common/Hearts of Iron IV')

# These project rewards already have their own completion cards in the naval
# tree, or a project-gated radar technology in Electronics.
EXISTING = {
    'sp_naval_cruiser_submarine', 'sp_naval_fleet_submarine',
    'sp_naval_nuclear_submarine', 'sp_naval_midget_submarine',
    'sp_naval_submarine_carrier', 'sp_naval_torpedo_cruiser',
    'sp_naval_super_heavy_battleship', 'sp_naval_modern_battleship',
    'sp_naval_modern_carrier', 'sp_naval_ice_carrier',
    'sp_naval_support_ships', 'sp_naval_escort_carrier', 'sp_air_radar',
}
FOLDERS = {
    'specialization_land': ['infantry_folder'],
    'specialization_air': ['bba_air_techs_folder', 'air_techs_folder'],
    'specialization_naval': ['mtgnavalfolder', 'naval_folder'],
    'specialization_nuclear': ['electronics_folder'],
}
# Left-to-right cards, in distinct sections below existing trees.
LAYOUT = {
    'infantry_folder': (180, 1420, 5, 240),
    'bba_air_techs_folder': (180, 1690, 6, 240),
    'air_techs_folder': (180, 1470, 6, 240),
    'mtgnavalfolder': (180, 2320, 6, 240),
    'naval_folder': (180, 1420, 6, 240),
    'electronics_folder': (180, 1200, 6, 240),
}
HEIGHTS = {'infantry_folder': 1850, 'bba_air_techs_folder': 2350,
           'air_techs_folder': 2100, 'mtgnavalfolder': 2750,
           'naval_folder': 1800, 'electronics_folder': 1650}


def read(path):
    return path.read_text(encoding='utf-8-sig')


def write(path, value, bom=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding='utf-8-sig' if bom else 'utf-8', newline='\r\n')


def main():
    cards_path = ROOT / 'common/technologies/tfr_experimental_project_cards.txt'
    if cards_path.exists():
        raise SystemExit('Cards already exist; edit existing files instead of rerunning.')
    project_files = overlay_files(ROOT, VANILLA, 'common/special_projects/projects')
    project_defs = []
    for path in project_files:
        source = read(path)
        for entry in parse(source).entries():
            if not isinstance(entry.value, Block):
                continue
            specialization = entry.value.get('specialization')
            if specialization in FOLDERS:
                project_defs.append((entry, path, source))
    assert len({e.key for e, _, _ in project_defs}) == len(project_defs)
    assert EXISTING <= {e.key for e, _, _ in project_defs}
    added = [(e, p, s) for e, p, s in project_defs if e.key not in EXISTING]
    assert len(added) > 20

    sprite_file = VANILLA / 'interface/special_projects/project.gfx'
    sprites = {e.value.get('name'): e.value.get('texturefile', e.value.get('textureFile'))
               for e, _ in walk(parse(read(sprite_file)))
               if e.key.lower() == 'spritetype' and isinstance(e.value, Block)}

    gui_path = ROOT / 'interface/countrytechtreeview.gui'
    gui = read(gui_path)
    gui_tree = parse(gui)
    ui_folders = {}
    for folder in LAYOUT:
        matches = [e for e, _ in walk(gui_tree)
                   if isinstance(e.value, Block) and e.value.get('name') == folder]
        assert len(matches) == 1, folder
        ui_folders[folder] = matches[0]

    backup = Path.home() / '.codex/backups' / ('tfr-project-cards-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
    backup.mkdir(parents=True)
    changed_existing = {gui_path}
    changed_existing.update(ROOT / p.relative_to(VANILLA) if p.is_relative_to(VANILLA) else p
                            for _, p, _ in added)
    for path in changed_existing:
        if path.exists():
            dst = backup / path.relative_to(ROOT)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dst)

    file_edits = defaultdict(list)
    folder_cards = defaultdict(list)
    techs = ['# Informational cards; project output is applied by the project itself.', 'technologies = {']
    gfx = ['spriteTypes = {']
    loc = ['l_english:', ' TFR_EXPERIMENTAL_CARDS: "§WExperimental Projects§!"',
           ' TFR_EXPERIMENTAL_NUCLEAR_CARDS: "§WNuclear Projects§!"']
    effect = ['# Existing games and projects completed through alternate paths are synchronized monthly.',
              'TFR_sync_experimental_project_cards = {']
    manifest = []

    for entry, path, source in added:
        project = entry.key
        spec = entry.value.get('specialization')
        card = 'tfr_project_card_' + project.removeprefix('sp_')
        icon = entry.value.get('icon', 'GFX_' + project)
        texture = sprites.get(icon)
        assert texture and (ROOT / texture).exists() or texture and (VANILLA / texture).exists(), (project, icon, texture)
        allowed = entry.value.entries('allowed')
        allowed_body = source[allowed[0].start:allowed[0].end].replace('allowed =', 'allow_branch =', 1) if allowed else ''
        output = entry.value.get('project_output')
        assert isinstance(output, Block), project
        country = output.entries('country_effects')
        assert country, project
        # This block always runs in the completing country. Put a hidden,
        # idempotent marker beside existing effects, without changing rewards.
        at = country[-1].end - 1
        insertion = f'\n\t\t\thidden_effect = {{ set_technology = {{ {card} = 1 popup = no }} }} # TFR: project card\n\t\t'
        file_edits[path].append((at, at, insertion))
        techs += [f'\t{card} = {{',
                  '\t\tis_special_project_tech = yes',
                  f'\t\tallow = {{ ROOT = {{ is_special_project_completed = sp:{project} }} }}',
                  f'\t\t{allowed_body}' if allowed_body else '',
                  '\t\tresearch_cost = 1', '\t\tstart_year = 1936',
                  '\t\tai_will_do = { factor = 0 }']
        for folder in FOLDERS[spec]:
            techs.append(f'\t\tfolder = {{ name = {folder} position = {{ x = 0 y = 0 }} }}')
            folder_cards[folder].append(card)
        techs += ['\t}', '']
        gfx += [f'\tSpriteType = {{ name = "GFX_{card}_medium" texturefile = "{texture}" }}']
        loc += [f' {card}: "${project}$"',
                f' {card}_desc: "${project}_desc$\\n\\nComplete the §Y${project}$§! special project in an experimental facility to unlock its rewards."']
        effect += ['\tif = {',
                   f'\t\tlimit = {{ is_special_project_completed = sp:{project} NOT = {{ has_tech = {card} }} }}',
                   f'\t\tset_technology = {{ {card} = 1 popup = no }}', '\t}']
        manifest.append({'project': project, 'card': card, 'specialization': spec,
                         'folders': FOLDERS[spec], 'project_file': str(path.relative_to(ROOT if path.is_relative_to(ROOT) else VANILLA)).replace('\\', '/'),
                         'icon': icon, 'texture': texture})
    techs.append('}')
    gfx.append('}')
    effect.append('}')

    gui_changes = []
    for folder, cards in folder_cards.items():
        node = ui_folders[folder]
        x0, y0, columns, dx = LAYOUT[folder]
        title = 'TFR_EXPERIMENTAL_NUCLEAR_CARDS' if folder == 'electronics_folder' else 'TFR_EXPERIMENTAL_CARDS'
        addition = f'''\n\t\t\tinstantTextBoxType = {{
                name = "tfr_experimental_projects_title"
                position = {{ x = {x0} y = {y0 - 80} }}
                font = "hoi_33"
                text = "{title}"
                maxWidth = 600
                maxHeight = 62
                format = left
            }}\n'''
        for i, card in enumerate(cards):
            x, y = x0 + (i % columns) * dx, y0 + (i // columns) * 170
            addition += f'''\t\t\tgridboxtype = {{
                name = "{card}_tree"
                position = {{ x = {x} y = {y} }}
                size = {{ width = 100 height = 140 }}
                slotsize = {{ width = 10 height = 10 }}
                format = "UP"
            }}\n'''
        gui_changes.append((node.end - 1, node.end - 1, addition + '\t\t'))
        bg = next((e for e in node.value.entries('containerWindowType')
                   if e.value.get('name') in ('techtree_stripes', 'tiled_window_transparent_transparent', 'size_filler')), None)
        assert bg is not None, folder
        size = bg.value.get('size')
        height = size.entries('height')[0]
        gui_changes.append((height.start, height.end, f'height = {HEIGHTS[folder]}'))

    # Generate only after validating all inputs and setting up a full backup.
    write(cards_path, '\n'.join(techs) + '\n')
    write(ROOT / 'interface/tfr_experimental_project_cards.gfx', '\n'.join(gfx) + '\n')
    write(ROOT / 'localisation/english/tfr_experimental_project_cards_l_english.yml', '\n'.join(loc) + '\n', bom=True)
    write(ROOT / 'common/scripted_effects/tfr_experimental_project_cards.txt', '\n'.join(effect) + '\n')
    write(ROOT / 'common/on_actions/tfr_experimental_project_cards.txt', '''on_actions = {
    on_startup = { effect = { every_country = { TFR_sync_experimental_project_cards = yes } } }
    on_monthly = { effect = { TFR_sync_experimental_project_cards = yes } }
}
''')
    write(gui_path, replace_spans(gui, gui_changes))
    for path, edits in file_edits.items():
        target = ROOT / path.relative_to(VANILLA) if path.is_relative_to(VANILLA) else path
        after = replace_spans(read(path), edits)
        parse(after)
        write(target, after)
    report = {'backup': str(backup), 'project_count': len(project_defs),
              'existing_cards': sorted(EXISTING), 'added_cards': manifest,
              'folder_counts': {k: len(v) for k, v in folder_cards.items()}}
    write(ROOT / 'docs/experimental-project-cards.json', json.dumps(report, indent=2) + '\n')
    print(json.dumps({'backup': str(backup), 'project_count': len(project_defs),
                      'new_cards': len(added), 'folder_counts': report['folder_counts']}, indent=2))


if __name__ == '__main__':
    main()
