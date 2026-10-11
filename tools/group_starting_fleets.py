"""Group active 1936 MTG ships into one surface and one submarine task force.

Original ship entries remain semantically identical. Already grouped countries
and OOBs shared with 1939 are left intact. The audit stores original sources.
"""
from collections import Counter
import hashlib
import json

from hoi4_script import Block, TOKEN, overlay_files, parse, replace_spans, walk
from integrate_naval_tech_bonuses import write, sha
from naval_startup_audit import NavalData, ROOT, VANILLA

REPORT = ROOT / 'docs/naval-starting-fleet-grouping.json'


def freeze(block):
    return [[e.key, e.op, freeze(e.value) if isinstance(e.value, Block) else e.value]
            if hasattr(e, 'key') else freeze(e) if isinstance(e, Block) else e for e in block.items]


def ship_hashes(tree):
    return Counter(sha(json.dumps(freeze(e.value), ensure_ascii=True))
                   for e, _ in walk(tree) if e.key == 'ship')


def kind(ship):
    return 'submarine' if ship.get('definition') == 'submarine' else 'surface'


def fleets(tree):
    units = tree.entries('units')
    assert len(units) == 1
    return units[0], units[0].value.entries('fleet')


def grouped(tree):
    _, entries = fleets(tree)
    seen = set()
    for fleet in entries:
        forces = fleet.value.entries('task_force')
        if len(forces) != 1 or not forces[0].value.entries('ship'):
            return False
        kinds = {kind(e.value) for e in forces[0].value.entries('ship')}
        if len(kinds) != 1 or kinds & seen:
            return False
        seen.update(kinds)
    return bool(entries)


def reindent_ship(source):
    depth = 0
    lines = []
    for line in source.splitlines():
        text = line.strip()
        tokens = [m.group() for m in TOKEN.finditer(text) if not m.group().startswith('#')]
        indent = depth - int(bool(tokens) and tokens[0] == '}')
        lines.append('\t' * (3 + indent) + text)
        depth += tokens.count('{') - tokens.count('}')
    assert depth == 0
    return '\n'.join(lines)


def selected_oobs(data):
    paths = {p.name.lower(): p for p in overlay_files(ROOT, VANILLA, 'history/units')}
    for name, profiles in sorted(data.oob_profiles.items()):
        active = {(tag, mtg, year) for tag, mtg, year in profiles if mtg and year == 1936}
        if not active or name not in paths:
            continue
        path = paths[name]
        tree = parse(path.read_text(encoding='utf-8-sig'))
        if not any(e.key == 'ship' for e, _ in walk(tree)):
            continue
        yield path, profiles, active, tree


def main():
    assert not REPORT.exists(), 'Grouping already applied: run validate_grouped_fleets.py instead.'
    data = NavalData()
    rows = []
    plans = []
    for loaded, profiles, active, tree in selected_oobs(data):
        assert len(active) == 1, (loaded, active)
        tag = next(iter(active))[0]
        source = loaded.read_text(encoding='utf-8-sig')
        unit, old_fleets = fleets(tree)
        groups = {'surface': [], 'submarine': []}
        bases = {}
        for fleet in old_fleets:
            assert not [e.key for e in fleet.value.entries() if e.key not in ('name', 'naval_base', 'task_force')]
            for force in fleet.value.entries('task_force'):
                assert not [e.key for e in force.value.entries() if e.key not in ('name', 'location', 'ship')]
                for ship in force.value.entries('ship'):
                    group = kind(ship.value)
                    groups[group].append(ship)
                    bases.setdefault(group, fleet.value.get('naval_base') or force.value.get('location'))
        assert sum(map(len, groups.values())) == sum(ship_hashes(tree).values())
        row = dict(country=tag, source='history/units/' + loaded.name,
                   profiles=sorted(profiles), changed=not grouped(tree),
                   raw_before_sha256=hashlib.sha256(loaded.read_bytes()).hexdigest(),
                   before_sha256=sha(source), ships=sum(map(len, groups.values())),
                   surface_ships=len(groups['surface']), submarine_ships=len(groups['submarine']),
                   fleets_before=len(old_fleets), task_forces_before=sum(len(f.value.entries('task_force')) for f in old_fleets),
                   ship_fingerprints=dict(ship_hashes(tree)))
        after = source
        if row['changed']:
            assert not any(year == 1939 for _, _, year in profiles), 'Do not regroup an OOB also loaded in 1939'
            blocks = ['units = {', '\t# TFR: one surface fleet and one separate submarine fleet at the 1936 start.']
            # Preserve any unrelated units verbatim; currently these naval OOBs
            # contain only fleets, but never delete land/air data if present.
            blocks.extend(source[e.start:e.end] for e in unit.value.entries() if e.key != 'fleet')
            for group, ships in groups.items():
                if not ships:
                    continue
                base = bases[group]
                assert base and base.isdigit()
                fleet_name = 'Main Fleet' if group == 'surface' else 'Submarine Fleet'
                force_name = 'Main Task Force' if group == 'surface' else 'Submarine Task Force'
                blocks += ['\tfleet = {', f'\t\tname = "{fleet_name}"', f'\t\tnaval_base = {base}',
                           '\t\ttask_force = {', f'\t\t\tname = "{force_name}"', f'\t\t\tlocation = {base}']
                blocks.extend(reindent_ship(source[e.start:e.end]) for e in ships)
                blocks += ['\t\t}', '\t}']
            blocks += ['}']
            after = replace_spans(source, [(unit.start, unit.end, '\n'.join(blocks))])
            row['source_before'] = source
            row['source_before_bom'] = loaded.read_bytes().startswith(b'\xef\xbb\xbf')
            row['source_before_newline'] = '\r\n' if b'\r\n' in loaded.read_bytes() else '\n'
            row['bases_after'] = bases
        after_tree = parse(after)
        assert grouped(after_tree)
        assert ship_hashes(after_tree) == ship_hashes(tree), ('Ship data changed', loaded)
        after_unit, after_fleets = fleets(after_tree)
        assert source[:unit.start] + source[unit.end:] == after[:after_unit.start] + after[after_unit.end:], 'Non-naval effects changed'
        row.update(after_sha256=sha(after), fleets_after=len(after_fleets),
                   task_forces_after=sum(len(f.value.entries('task_force')) for f in after_fleets))
        rows.append(row)
        if row['changed']:
            plans.append((loaded, ROOT / row['source'], after, row))
    assert len(rows) == len({r['country'] for r in rows}), 'Country uses more than one starting naval OOB'
    # All plans have been checked before changing any game file.
    for loaded, target, after, row in plans:
        assert hashlib.sha256(loaded.read_bytes()).hexdigest() == row['raw_before_sha256']
        if not target.exists():
            target.write_bytes(loaded.read_bytes())
        write(target, after)
        row['raw_after_sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
    for row in rows:
        if not row['changed']:
            row['raw_after_sha256'] = row['raw_before_sha256']
    ledger_path = ROOT / 'docs/naval-starting-fleets.json'
    ledger = json.loads(ledger_path.read_text(encoding='utf-8'))
    for row in rows:
        if row['source'] in ledger['source_hashes']:
            hashes = ledger['source_hashes'][row['source']]
            assert hashes['after'] == row['before_sha256']
            hashes['after'] = row['after_sha256']
    ledger['fleet_grouping'] = 'docs/naval-starting-fleet-grouping.json; organization/locations only, ship data and IC unchanged'
    write(ledger_path, json.dumps(ledger, indent=2, ensure_ascii=False) + '\n')
    write(REPORT, json.dumps(dict(year=1936, mtg=True, countries=rows), indent=2, ensure_ascii=False) + '\n')
    print(f'Grouped {len(rows)} countries / {sum(r["ships"] for r in rows)} ships; {len(plans)} naval OOBs changed.')


if __name__ == '__main__':
    main()
