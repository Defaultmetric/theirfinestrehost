"""Bake removed vanilla support bonuses into fixed designs, without changing IC.

The migration at the end restores the original engines and stores the package
as locked native variant statistics. No extra modules remain in the mod.
Run once to apply; an existing audit is deliberately not silently overwritten.
"""
import hashlib
import json
import re
from decimal import Decimal as D
from pathlib import Path

from hoi4_script import Block, parse, replace_spans, walk
from naval_startup_audit import NavalData, ROOT, VANILLA

AUDIT = ROOT / 'docs/naval-integrated-tech-bonuses.json'
DESIGNS = ROOT / 'common/scripted_effects/tfr_navy_designs.txt'
FLEETS = ROOT / 'docs/naval-starting-fleets.json'
SHIP_CLASSES = ('destroyer', 'light_cruiser', 'heavy_cruiser', 'battleship', 'battle_cruiser', 'carrier')
TIERS = [(1936, 'basic'), (1938, 'improved'), (1942, 'advanced')]


def write(path, source):
    old = path.read_bytes() if path.exists() else b''
    bom = b'\xef\xbb\xbf' if old.startswith(b'\xef\xbb\xbf') else b''
    newline = '\r\n' if b'\r\n' in old else '\n'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bom + source.replace('\r\n', '\n').replace('\n', newline).encode('utf-8'))


def sha(source):
    return hashlib.sha256(source.encode('utf-8')).hexdigest()


def ship_class(name):
    # The carrier submarine is based on the submarine equipment archetype.
    if name == 'Submarine Carrier 1936':
        return 'submarine'
    if 'Carrier' in name:
        return 'carrier'
    if 'Submarine' in name:
        return 'submarine'
    if 'Destroyer' in name:
        return 'destroyer'
    if 'Battlecruiser' in name:
        return 'battle_cruiser'
    if 'Battleship' in name or name == 'Pre-Dreadnought':
        return 'battleship'
    if 'Heavy Cruiser' in name or name in ('Panzerschiff', 'Coastal Defense Ship'):
        return 'heavy_cruiser'
    return 'light_cruiser'


def stat(data, hull, variant, key):
    base = D(str(data.hull(hull).get(key, '0')))
    multiplier = D(0)
    average = []
    for name in data.module_map(hull, variant).values():
        module = data.modules[name][0]
        base += D(module.get('add_stats', Block([])).get(key, '0'))
        multiplier += D(module.get('multiply_stats', Block([])).get(key, '0'))
        value = module.get('add_average_stats', Block([])).get(key)
        if value is not None:
            average.append(D(value))
    if average:
        base += sum(average) / len(average)
    for upgrade in variant.get('upgrades', Block([])).entries():
        multiplier += D(data.upgrades[upgrade.key][0].get(key, '0')) * D(upgrade.value)
    return base * (1 + multiplier), multiplier


def hull_condition(prefix, kinds=('light', 'cruiser', 'heavy', 'submarine', 'carrier')):
    return 'OR = { ' + ' '.join(f'has_tech = {prefix}_ship_hull_{kind}' for kind in kinds) + ' }'


def main():
    assert not AUDIT.exists(), 'Already integrated: validate the existing audit instead of applying twice.'
    data = NavalData()
    source = DESIGNS.read_text(encoding='utf-8-sig')
    vanilla_path = VANILLA / 'common/technologies/MTG_naval_Support.txt'
    vanilla = parse(vanilla_path.read_text(encoding='utf-8-sig')).get('technologies')
    rows, modules, edits, replacements = [], [], [], {}
    for branch in parse(source).get('TFR_navy_create_designs').entries('if'):
        entry = branch.value.entries('create_equipment_variant')[0]
        variant = entry.value
        name, hull = variant.get('name'), variant.get('type')
        named_year = re.search(r'\b(1936|1938|1942)\b', name)
        year = int(named_year[1]) if named_year else int(data.hull(hull)['year'])
        category = ship_class(name)
        techs = []
        if year >= 1936:
            techs += ['basic_light_shell', 'basic_heavy_shell', 'magnetic_detonator', 'fire_control_methods_1']
        if year >= 1938:
            techs += ['degaussing', 'fire_control_methods_2']
        if year >= 1942:
            techs += ['improved_light_shell', 'improved_heavy_shell', 'homing_torpedo', 'fire_control_methods_3']
        bonuses = {}
        for tech in techs:
            for effect in vanilla.get(tech).get(category, Block([])).entries():
                bonuses[effect.key] = bonuses.get(effect.key, D(0)) + D(effect.value)
        row = dict(name=name, hull=hull, year=year, ship_class=category,
                   vanilla_techs=techs, bonuses={k: str(v) for k, v in bonuses.items()},
                   cost_before=data.cost(hull, variant), script_before=source[entry.start:entry.end])
        if not bonuses:
            rows.append(row)
            continue
        engine = variant.get('modules').entries('fixed_ship_engine_slot')[0]
        base_name = engine.value
        base_module, base_path = data.modules[base_name]
        engine_source = base_path.read_text(encoding='utf-8-sig')
        base_entry = next(e for e, _ in walk(parse(engine_source)) if e.key == base_name)
        clone_name = 'tfr_integrated_' + branch.value.get('set_country_flag').removeprefix('tfr_dsg_')
        body = engine_source[base_entry.start:base_entry.end]
        clone_edits = [(0, len(base_name), clone_name)]
        local = parse(body).entries()[0].value
        for key in ('parent', 'abbreviation'):
            for e in local.entries(key):
                clone_edits.append((e.start, e.end, ''))
        clone_edits.append((body.index('{') + 1, body.index('{') + 1,
                            f'\n\t\tparent = {base_name}\n\t\tabbreviation = "tfn{len(rows):02d}"'))
        changes = {'add_stats': {}, 'multiply_stats': {}}
        row['stats_before'], row['expected_stats_after'] = {}, {}
        for key, bonus in bonuses.items():
            old, existing_multiplier = stat(data, hull, variant, key)
            # Hit chance factors are additive percentage-point modifiers, as in
            # vanilla torpedo modules. Ordinary ship stats are percent upgrades.
            if key == 'naval_torpedo_hit_chance_factor':
                changes['add_stats'][key] = bonus
                expected = old + bonus * (1 + existing_multiplier)
            else:
                changes['multiply_stats'][key] = bonus * (1 + existing_multiplier)
                expected = old * (1 + bonus)
            row['stats_before'][key], row['expected_stats_after'][key] = str(old), str(expected)
        for group, values in changes.items():
            if not values:
                continue
            group_entries = local.entries(group)
            old_values = group_entries[0].value.mapping() if group_entries else {}
            for key, change in values.items():
                old_values[key] = str(D(old_values.get(key, '0')) + change)
            text = group + ' = {\n' + ''.join(f'\t\t\t{k} = {v}\n' for k, v in old_values.items()) + '\t\t}'
            if group_entries:
                assert len(group_entries) == 1
                e = group_entries[0]
                clone_edits.append((e.start, e.end, text))
            else:
                clone_edits.append((len(body) - 1, len(body) - 1, '\n\t\t' + text + '\n\t'))
        modules.append('\t' + replace_spans(body, clone_edits))
        edits.append((engine.start, engine.end, f'fixed_ship_engine_slot = {clone_name}'))
        row.update(engine_before=base_name, engine_after=clone_name)
        replacements[name] = clone_name
        rows.append(row)
    write(ROOT / 'common/units/equipment/modules/tfr_integrated_naval_modules.txt',
          '# Generated by tools/integrate_naval_tech_bonuses.py. One support package per fixed ship.\nequipment_modules = {\n' + '\n\n'.join(modules) + '\n}\n')
    source_after = replace_spans(source, edits)
    source_after = source_after.replace('TFR_navy_create_designs = {', 'TFR_navy_create_designs = {\n\tTFR_navy_apply_integrated_global_bonuses = yes', 1)
    write(DESIGNS, source_after)
    # Keep precreated day-one standard variants identical to the research templates.
    fleet_report = json.loads(FLEETS.read_text(encoding='utf-8'))
    history_updates = []
    for relative, hashes in fleet_report['source_hashes'].items():
        if not relative.startswith('history/countries/'):
            continue
        path = ROOT / relative
        before = path.read_text(encoding='utf-8-sig')
        assert sha(before) == hashes['after'], f'Unexpected edit before migration: {relative}'
        changes = []
        for e, _ in walk(parse(before)):
            if e.key == 'create_equipment_variant' and e.value.get('name') in replacements:
                slot = e.value.get('modules').entries('fixed_ship_engine_slot')[0]
                changes.append((slot.start, slot.end, 'fixed_ship_engine_slot = ' + replacements[e.value.get('name')]))
        after = replace_spans(before, changes)
        write(path, after)
        history_updates.append(dict(source=relative, before=hashes['after'], after=sha(after)))
        hashes['after'] = sha(after)
    for model in fleet_report['models'].values():
        if model['name'] in replacements:
            model['script'] = re.sub(r'fixed_ship_engine_slot = \w+',
                                    'fixed_ship_engine_slot = ' + replacements[model['name']], model['script'])
    fleet_report['support_bonus_migration'] = 'docs/naval-integrated-tech-bonuses.json; stats only, original IC ledger unchanged'
    write(FLEETS, json.dumps(fleet_report, indent=2, ensure_ascii=False) + '\n')
    hidden, effects = [], []
    for year, prefix in TIERS:
        tech = f'tfr_naval_damage_control_{year}'
        hidden.append(f'\t{tech} = {{\n\t\tallow = {{ always = no }}\n\t\tresearch_cost = 1\n\t\tstart_year = {year}\n\t\tcritical_receive_chance = -0.1\n\t\tnaval_critical_effect_factor = -0.1\n\t}}')
        effects.append(f'\tif = {{\n\t\tlimit = {{ {hull_condition(prefix)} NOT = {{ has_tech = {tech} }} }}\n\t\tset_technology = {{ popup = no {tech} = 1 }}\n\t}}')
    tech = 'tfr_naval_torpedo_concealment_1942'
    hidden.append(f'\t{tech} = {{ allow = {{ always = no }} research_cost = 1 start_year = 1942 naval_torpedo_reveal_chance_factor = -0.25 }}')
    effects.append(f'\tif = {{\n\t\tlimit = {{ {hull_condition("advanced", ("light", "cruiser", "submarine"))} NOT = {{ has_tech = {tech} }} }}\n\t\tset_technology = {{ popup = no {tech} = 1 }}\n\t}}')
    module_names = [r['engine_after'] for r in rows if 'engine_after' in r]
    hidden.append('\ttfr_integrated_naval_modules = { allow = { always = no } research_cost = 1 start_year = 1922\n\t\tenable_equipment_modules = { ' + ' '.join(module_names) + ' }\n\t}')
    # Removed replenishment improvements stay gated by their actual project,
    # as well as the corresponding hull generation; they are never free at start.
    for year, prefix, original in [(1938, 'improved', 'sp_multi_product_supply_ships'), (1942, 'advanced', 'sp_standard_tenshioned_replenishment_alongside_method')]:
        tech = f'tfr_naval_replenishment_{year}'
        hidden.append(f'\t{tech} = {{ allow = {{ always = no }} research_cost = 1 start_year = {year} underway_replenishment_range = 0.25 underway_replenishment_convoy_cost = -0.2 }}')
        effects.append(f'\tif = {{\n\t\tlimit = {{ has_dlc = "Gotterdammerung" is_special_project_completed = sp:sp_naval_underway_replenishment {hull_condition(prefix)} NOT = {{ has_tech = {tech} }} }}\n\t\tset_technology = {{ popup = no {tech} = 1 }}\n\t}}')
    write(ROOT / 'common/technologies/tfr_integrated_naval_bonuses.txt', 'technologies = {\n' + '\n\n'.join(hidden) + '\n}\n')
    write(ROOT / 'common/scripted_effects/tfr_integrated_naval_bonuses.txt', '# Country scope; research/startup hooks call this through TFR_navy_create_designs.\nTFR_navy_apply_integrated_global_bonuses = {\n' + '\n'.join(effects) + '\n}\n')
    startup = ROOT / 'common/on_actions/tfr_navy_simplified_on_actions.txt'
    text = startup.read_text(encoding='utf-8-sig')
    text = text.replace('popup = no', 'popup = no\n\t\t\t\t\ttfr_integrated_naval_modules = 1', 1)
    write(startup, text)
    loc = ['l_english:', ' tfr_integrated_naval_modules:0 "Integrated naval support technologies"']
    for row in rows:
        if 'engine_after' in row:
            loc += [f' {row["engine_after"]}:0 "Integrated systems ({row["name"]})"',
                    f' {row["engine_after"]}_desc:0 "Includes the support technologies appropriate to this fixed ship design. No additional IC cost."']
    for year, _ in TIERS:
        loc.append(f' tfr_naval_damage_control_{year}:0 "Integrated damage control ({year})"')
    loc += [' tfr_naval_torpedo_concealment_1942:0 "Integrated torpedo concealment (1942)"',
            ' tfr_naval_replenishment_1938:0 "Integrated replenishment (1938)"',
            ' tfr_naval_replenishment_1942:0 "Integrated replenishment (1942)"']
    loc_path = ROOT / 'localisation/english/tfr_integrated_naval_bonuses_l_english.yml'
    loc_path.write_bytes(b'\xef\xbb\xbf' + ('\n'.join(loc) + '\n').encode('utf-8'))
    audit = dict(vanilla_source=str(vanilla_path), vanilla_sha256=hashlib.sha256(vanilla_path.read_bytes()).hexdigest(),
                 fire_control_mapping='Undated vanilla levels 1/2/3 assigned to mod hull generations 1936/1938/1942.',
                 global_policy='Research driven, not calendar driven. Ordinary hull generations grant one global tier each; torpedo concealment requires advanced light/cruiser/submarine. Replenishment also requires completed special project.',
                 designs=rows, history_updates=history_updates)
    write(AUDIT, json.dumps(audit, indent=2, ensure_ascii=False) + '\n')
    from hide_integrated_naval_bonuses import main as hide_packages
    hide_packages()


if __name__ == '__main__':
    main()
