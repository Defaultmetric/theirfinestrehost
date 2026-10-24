"""Validate design prerequisites, module legality, Vanilla module/hull/define parity, and Vanilla starting fleets."""
from collections import Counter
import re

from hoi4_script import Block, overlay_files, parse, walk
from naval_startup_audit import NavalData, ROOT, VANILLA, active_entries, inventory


def main():
    data = NavalData()
    path = ROOT / 'common/scripted_effects/tfr_navy_designs.txt'
    assert b'\xef\xbb\xbf' not in path.read_bytes(), 'BOM in scripted effects'
    tree = parse(path.read_text(encoding='utf-8'))
    assert len(tree.entries('TFR_navy_create_designs')) == 1
    effect = tree.get('TFR_navy_create_designs')
    dependencies, flags, design_count = set(), [], 0
    for branch in effect.entries('if'):
        b = branch.value
        variants = b.entries('create_equipment_variant')
        assert len(variants) == 1
        variant = variants[0].value
        assert variant.get('obsolete') != 'yes', f'Predefined design must not be obsolete: {variant.get("name")}'
        issues = data.issues(variant.get('type'), variant)
        assert not issues, (variant.get('name'), issues)
        flag = b.get('set_country_flag')
        assert flag and any(e.key == 'has_country_flag' and e.value == flag for e, a in walk(b.get('limit'))), 'Missing one-time design guard'
        assert b.entries().index(variants[0]) < b.entries().index(b.entries('set_country_flag')[0])
        flags.append(flag)
        design_count += 1
        dependencies.update(e.value for e, a in walk(b.get('limit')) if e.key == 'has_tech')
    assert len(flags) == len(set(flags)), 'Duplicate design flags'
    techs = {}
    for p in overlay_files(ROOT, VANILLA, 'common/technologies'):
        for group in parse(p.read_text(encoding='utf-8-sig')).entries('technologies'):
            techs.update(group.value.mapping())
    for tech in dependencies:
        assert tech in techs, f'Unknown design prerequisite {tech}'
        hook = techs[tech].get('on_research_complete', Block([]))
        assert any(e.key == 'TFR_navy_create_designs' for e, a in walk(hook)), f'Missing research hook: {tech}'
    startup = parse((ROOT / 'common/on_actions/tfr_navy_simplified_on_actions.txt').read_text(encoding='utf-8-sig'))
    country = startup.get('on_actions').get('on_startup').get('effect').get('every_country')
    assert country.entries().index(country.entries('set_technology')[0]) < country.entries().index(country.entries('TFR_navy_create_designs')[0])
    for tag, e, p, _ in data.history_variants:
        assert e.value.get('obsolete') == 'yes', f'Default/historical naval variant not obsolete: {tag} {e.value.get("name")}'
        if e.value.get('type', '').startswith('ship_hull_'):
            assert not data.issues(e.value.get('type'), e.value), (tag, e.value.get('name'))
    duplicate_limits = []
    for name, (b, p) in data.equipment.items():
        if data.naval(name):
            keys = [(e.value.get('module'), e.value.get('category')) for e in b.entries('module_count_limit')]
            duplicate_limits += [(name, k) for k, n in Counter(keys).items() if n > 1]
    assert not duplicate_limits, duplicate_limits

    # Verify 100% Vanilla 00_ship_modules.txt parity
    mod_file = ROOT / 'common/units/equipment/modules/00_ship_modules.txt'
    van_mod_file = VANILLA / 'common/units/equipment/modules/00_ship_modules.txt'
    assert mod_file.read_bytes() == van_mod_file.read_bytes(), '00_ship_modules.txt differs from Vanilla HOI4'

    # Verify Vanilla starting fleets and production lines resolve cleanly
    records, _ = inventory(data)
    assert len(records) > 200, f'Expected Vanilla starting naval production lines, found {len(records)}'
    unit_files = {p.name.lower(): p for p in overlay_files(ROOT, VANILLA, 'history/units')}
    total_ships = 0
    for oob_name, profiles in sorted(data.oob_profiles.items()):
        if oob_name not in unit_files:
            continue
        oob_tree = parse(unit_files[oob_name].read_text(encoding='utf-8-sig'))
        for tag, mtg, year in sorted(profiles):
            if not mtg or year != 1936:
                continue
            for e, _ in walk(oob_tree):
                if e.key != 'ship':
                    continue
                total_ships += 1
                eq = e.value.get('equipment').entries()[0]
                owner = eq.value.get('owner', tag)
                hull = eq.key
                vname = eq.value.get('version_name')
                variant = data.variants.get((owner, hull, vname, mtg, year))
                if variant is None:
                    candidates = [
                        v for (c, h, n, m, y), v in data.variants.items()
                        if (c, n, m, y) == (owner, vname, mtg, year)
                        and data.hull(h).get('archetype', h) == data.hull(hull).get('archetype', hull)
                    ]
                    assert len(candidates) == 1, f'Unresolved OOB ship variant: {oob_name} {owner} {hull} {vname!r} ({year})'

    # Verify TFR_defines.lua has only Mihai'sNavySimplified naval defines (mines = 0, positioning penalty = 0.5)
    defines_text = (ROOT / 'common/defines/TFR_defines.lua').read_text(encoding='utf-8-sig')
    assert 'NAVAL_STRIKE_DAMAGE_TO_STR' not in defines_text
    assert 'HIGHER_SHIP_RATIO_POSITIONING_PENALTY_FACTOR = 0.5' in defines_text
    assert 'NAVAL_MINES_PLANTING_SPEED_MULT = 0.0' in defines_text

    # Verify no OAK files remain
    oak_files = [p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*oak*') if p.is_file()]
    assert not oak_files, f'OAK files remain: {oak_files}'

    print(f'PASS: {design_count} fixed designs; {len(dependencies)} immediate research hooks; {len(data.history_variants)} historical naval variants valid.')
    print(f'PASS: 100% Vanilla 00_ship_modules.txt & naval defines parity; {total_ships} MTG OOB ship entries and {len(records)} Vanilla production lines verified; 0 OAK files remain.')


if __name__ == '__main__':
    main()
