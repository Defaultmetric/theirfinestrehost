"""Move the five Land Cruiser follow-up technologies into unit baselines."""
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import json
import shutil

from hoi4_script import Block, parse, replace_spans, walk

ROOT = Path(__file__).resolve().parents[1]
VANILLA = Path('C:/Program Files (x86)/Steam/steamapps/common/Hearts of Iron IV')
TECHS = [
    'sp_armored_lc_naval_engine_conversion_tech',
    'sp_armored_lc_transmission_improvements_tech',
    'sp_armored_lc_specialized_field_manuals_tech',
    'sp_armored_lc_weapon_fire_control_tech',
    'sp_armored_lc_high_impact_obliterator_cannon_tech',
]


def read(path):
    return path.read_text(encoding='utf-8-sig')


def save(path, text):
    parse(text)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8', newline='\r\n')


def value(n):
    return format(Decimal(n).normalize(), 'f')


def main():
    marker = ROOT / 'common/scripted_effects/tfr_lc_integrated_tech.txt'
    if marker.exists():
        raise SystemExit('Integration already exists; edit the installed implementation instead.')
    relatives = ['common/technologies/NSB_armor.txt', 'common/technologies/armor.txt',
                 'common/units/super_heavy_armor.txt', 'common/units/land_cruiser.txt',
                 'common/special_projects/projects/land_projects.txt']
    backup = Path.home() / '.codex/backups' / ('tfr-land-cruiser-integration-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
    for rel in relatives:
        src = ROOT / rel if (ROOT / rel).exists() else VANILLA / rel
        dst = backup / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    # Read the values from the actual installed technologies, preserving their
    # separate scopes for the two unit types rather than applying every bonus
    # to both. The same numeric unit and terrain fields are added to each unit.
    tech_path = ROOT / relatives[0]
    tech_text = read(tech_path)
    tech_tree = parse(tech_text).get('technologies')
    bonuses = {'land_cruiser': {}, 'super_heavy_armor': {}}
    for name in TECHS:
        tech = tech_tree.get(name)
        for unit in bonuses:
            b = tech.get(unit)
            if not isinstance(b, Block):
                continue
            for item in b.entries():
                if isinstance(item.value, Block):
                    for modifier in item.value.entries():
                        key = (item.key, modifier.key)
                        bonuses[unit][key] = bonuses[unit].get(key, Decimal('0')) + Decimal(modifier.value)
                else:
                    key = (item.key,)
                    bonuses[unit][key] = bonuses[unit].get(key, Decimal('0')) + Decimal(item.value)

    def integrate_unit(unit, rel):
        original = backup / rel
        text = read(original)
        tree = parse(text).get('sub_units')
        definition = tree.get(unit)
        edits = []
        additions = []
        for key, bonus in bonuses[unit].items():
            if len(key) == 1:
                existing = definition.entries(key[0])
                if existing:
                    assert len(existing) == 1
                    e = existing[0]
                    edits.append((e.start, e.end, f'{e.key} = {value(Decimal(e.value) + bonus)}'))
                else:
                    additions.append(f'\t\t{key[0]} = {value(bonus)}')
            else:
                terrain = definition.get(key[0])
                assert isinstance(terrain, Block), (unit, key)
                e = terrain.entries(key[1])[0]
                edits.append((e.start, e.end, f'{e.key} = {value(Decimal(e.value) + bonus)}'))
        if additions:
            unit_entry = tree.entries(unit)[0]
            edits.append((unit_entry.end - 1, unit_entry.end - 1,
                          '\n\t\t# Integrated Land Cruiser project follow-up bonuses.\n' + '\n'.join(additions) + '\n\t'))
        save(ROOT / rel, replace_spans(text, edits))

    integrate_unit('land_cruiser', relatives[3])
    integrate_unit('super_heavy_armor', relatives[2])

    # Hidden technology IDs are kept for focuses and existing saves. Their
    # stat blocks are removed because the unit definitions now contain them;
    # the cannon technology keeps its actual module unlock.
    edits = []
    for tech in tech_tree.entries():
        if tech.key in TECHS:
            for field in ('folder', 'path', 'allow', 'allow_branch', 'land_cruiser', 'super_heavy_armor'):
                for e in tech.value.entries(field):
                    edits.append((e.start, e.end, '# TFR: integrated into the unit baseline.'))
            edits.append((tech.end - 1, tech.end - 1,
                          '\n\t\tallow = { always = no } # TFR: granted automatically.\n\t'))
        else:
            for e in tech.value.entries('path') if isinstance(tech.value, Block) else []:
                if e.value.get('leads_to_tech') in TECHS:
                    edits.append((e.start, e.end, '# TFR: follow-up technology integrated.'))
    save(tech_path, replace_spans(tech_text, edits))

    # The non-designer tree also points to these hidden follow-ups.
    other = ROOT / relatives[1]
    text = read(other)
    edits = [(e.start, e.end, '# TFR: follow-up technology integrated.')
             for e, _ in walk(parse(text)) if e.key == 'path' and isinstance(e.value, Block)
             and e.value.get('leads_to_tech') in TECHS]
    save(other, replace_spans(text, edits))

    # Do not advertise a research step that no longer exists when the project
    # completes; retain all other effects, including the project card marker.
    path = ROOT / relatives[4]
    text = read(path)
    tree = parse(text)
    project = tree.get('sp_land_land_cruiser')
    edits = []
    for e, parents in walk(project):
        if e.key != 'custom_effect_tooltip' or not isinstance(e.value, Block) or e.value.get('TECH') not in TECHS:
            continue
        parent = parents[-1] if parents else None
        target = parent if parent and parent.key == 'if' and len(parent.value.entries()) == 2 and parent.value.get('limit') else e
        edits.append((target.start, target.end, '# TFR: follow-up technology integrated into unit stats.'))
    assert len(edits) == 5
    save(path, replace_spans(text, edits))

    techlines = ' '.join(f'{tech} = 1' for tech in TECHS)
    missing = '\n'.join(f'                NOT = {{ has_tech = {tech} }}' for tech in TECHS)
    save(marker, f'''# Grant the retained IDs and the cannon once; stats are in the unit definitions.
TFR_grant_lc_integrated_tech = {{
    if = {{
        limit = {{
            has_dlc = "Gotterdammerung"
            OR = {{
{missing}
            }}
        }}
        set_technology = {{ {techlines} popup = no }}
    }}
}}
''')
    save(ROOT / 'common/on_actions/tfr_lc_integrated_tech.txt', '''on_actions = {
    on_startup = { effect = { every_country = { TFR_grant_lc_integrated_tech = yes } } }
    on_monthly = { effect = { TFR_grant_lc_integrated_tech = yes } }
}
''')
    report = {'backup': str(backup), 'techs': TECHS,
              'unit_bonuses': {unit: {'/'.join(k): str(v) for k, v in rows.items()}
                               for unit, rows in bonuses.items()}}
    (ROOT / 'docs/land-cruiser-integrated-tech.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
