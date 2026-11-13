"""Replace the visible engine copies with fixed, nonselectable variant bonuses.

The native create_equipment_variant effect supports upgrades alongside modules.
These upgrades have a single scripted level and cannot be selected by players.
Torpedo hit chance is an additive hull stat rather than a percentage upgrade.
"""
import json
from collections import defaultdict
from decimal import Decimal as D

from hoi4_script import Block, parse, replace_spans, walk
from integrate_naval_tech_bonuses import AUDIT, DESIGNS, FLEETS, sha, write
from naval_startup_audit import NavalData, ROOT, VANILLA


def main():
    audit = json.loads(AUDIT.read_text(encoding='utf-8'))
    assert 'hidden_variant_migration' not in audit, 'Already migrated'
    data = NavalData()
    rows = {r['name']: r for r in audit['designs'] if 'engine_after' in r}
    hull_upgrades, hit_hulls, upgrade_bodies = defaultdict(list), {}, []
    for row in rows.values():
        name = row['engine_after'].replace('tfr_integrated_', 'tfr_hidden_support_')
        row['hidden_upgrade'] = name
        hull_upgrades[row['hull']].append(name)
        values = {}
        for key, value in row['bonuses'].items():
            if key == 'naval_torpedo_hit_chance_factor':
                assert D(value) == D('0.1')
                hit_hulls[row['hull']] = D(value)
                continue
            # Upgrade and module percentage modifiers share the same base.
            clone = data.modules[row['engine_after']][0]
            base = data.modules[row['engine_before']][0]
            values[key] = D(clone.get('multiply_stats', Block([])).get(key, '0')) - D(base.get('multiply_stats', Block([])).get(key, '0'))
        row['upgrade_modifiers'] = {k: str(v) for k, v in values.items()}
        upgrade_bodies.append('\t' + name + ' = {\n\t\tmax_level = 1\n\t\tcost = naval\n'
                              '\t\tlevel_requirements = { 1 = { always = no } }\n' +
                              ''.join(f'\t\t{k} = {v}\n' for k, v in values.items()) + '\t}')
    write(ROOT / 'common/units/equipment/upgrades/tfr_hidden_naval_support.txt',
          '# Fixed variant statistics. No modules, slots or selectable upgrade levels.\nupgrades = {\n' + '\n\n'.join(upgrade_bodies) + '\n}\n')
    paths = defaultdict(list)
    for hull, names in hull_upgrades.items():
        body, path = data.equipment[hull]
        text = path.read_text(encoding='utf-8-sig')
        entry = next(e for e in parse(text).get('equipments').entries() if e.key == hull)
        old = data.hull(hull).get('upgrades', Block([])).atoms()
        upgrade_text = 'upgrades = { ' + ' '.join(old + names) + ' }'
        own = body.entries('upgrades')
        if own:
            assert len(own) == 1
            paths[path].append((own[0].start, own[0].end, upgrade_text))
        else:
            paths[path].append((entry.end - 1, entry.end - 1, '\n\t\t' + upgrade_text + '\n\t'))
        if hull in hit_hulls:
            value = D(data.hull(hull).get('naval_torpedo_hit_chance_factor', '0')) + hit_hulls[hull]
            own_hit = body.entries('naval_torpedo_hit_chance_factor')
            field = f'naval_torpedo_hit_chance_factor = {value}'
            if own_hit:
                assert len(own_hit) == 1
                paths[path].append((own_hit[0].start, own_hit[0].end, field))
            else:
                paths[path].append((entry.end - 1, entry.end - 1, '\n\t\t' + field + '\n\t'))
    for path, changes in paths.items():
        write(path, replace_spans(path.read_text(encoding='utf-8-sig'), changes))

    def migrate_variants(text):
        edits = []
        for entry, _ in walk(parse(text)):
            if entry.key != 'create_equipment_variant' or entry.value.get('name') not in rows:
                continue
            row = rows[entry.value.get('name')]
            slot = entry.value.get('modules').entries('fixed_ship_engine_slot')[0]
            assert slot.value == row['engine_after']
            assert not entry.value.entries('upgrades')
            edits.append((slot.start, slot.end, 'fixed_ship_engine_slot = ' + row['engine_before']))
            edits.append((entry.end - 1, entry.end - 1,
                          f'\n\t\t\tupgrades = {{ {row["hidden_upgrade"]} = 1 }}\n\t\t'))
        return replace_spans(text, edits)

    write(DESIGNS, migrate_variants(DESIGNS.read_text(encoding='utf-8-sig')))
    fleets = json.loads(FLEETS.read_text(encoding='utf-8'))
    history_updates = []
    for relative, hashes in fleets['source_hashes'].items():
        if not relative.startswith('history/countries/'):
            continue
        path = ROOT / relative
        before = path.read_text(encoding='utf-8-sig')
        assert sha(before) == hashes['after'], relative
        after = migrate_variants(before)
        write(path, after)
        history_updates.append({'source': relative, 'before': sha(before), 'after': sha(after)})
        hashes['after'] = sha(after)
    for model in fleets['models'].values():
        model['script'] = migrate_variants(model['script'])
    write(FLEETS, json.dumps(fleets, indent=2, ensure_ascii=False) + '\n')
    treaty_path = ROOT / 'docs/naval-treaty-removal.json'
    treaty = json.loads(treaty_path.read_text(encoding='utf-8'))
    migrated = {r['source']: r for r in history_updates}
    for row in treaty['files']:
        if row['source'] in migrated:
            assert row['after'] == migrated[row['source']]['before']
            row['after'] = migrated[row['source']]['after']
    treaty['hidden_support_migration'] = 'Engine copies removed; original treaty removals unchanged.'
    write(treaty_path, json.dumps(treaty, indent=2, ensure_ascii=False) + '\n')

    tech_path = ROOT / 'common/technologies/tfr_integrated_naval_bonuses.txt'
    text = tech_path.read_text(encoding='utf-8-sig')
    old = parse(text).get('technologies').entries('tfr_integrated_naval_modules')[0]
    write(tech_path, replace_spans(text, [(old.start, old.end, '')]))
    startup_path = ROOT / 'common/on_actions/tfr_navy_simplified_on_actions.txt'
    text = startup_path.read_text(encoding='utf-8-sig')
    write(startup_path, text.replace('\t\t\t\t\ttfr_integrated_naval_modules = 1\n', ''))
    loc_path = ROOT / 'localisation/english/tfr_integrated_naval_bonuses_l_english.yml'
    text = loc_path.read_text(encoding='utf-8-sig')
    text = '\n'.join(line for line in text.splitlines() if not line.startswith(' tfr_integrated_')) + '\n'
    write(loc_path, text)
    module_path = ROOT / 'common/units/equipment/modules/tfr_integrated_naval_modules.txt'
    assert module_path.resolve().is_relative_to(ROOT.resolve())
    module_path.unlink()
    audit['hidden_variant_migration'] = {'history_updates': history_updates,
        'policy': 'Original engines; locked native variant upgrades for percentage bonuses; additive homing chance on eligible 1942+ hulls. No new modules.'}
    write(AUDIT, json.dumps(audit, indent=2, ensure_ascii=False) + '\n')
    # Override the native alias: Vichy creation sets this flag before its tree.
    alias = (VANILLA / 'common/country_tag_aliases/tag_aliases.txt').read_text(encoding='utf-8-sig')
    vic = parse(alias).get('VIC').entries('has_focus_tree')[0]
    write(ROOT / 'common/country_tag_aliases/tag_aliases.txt',
          replace_spans(alias, [(vic.start, vic.end, 'has_country_flag = vichy_france')]))
    print(f'Migrated {len(rows)} designs to hidden fixed bonuses; restored original engines; fixed Vichy alias.')


if __name__ == '__main__':
    main()
