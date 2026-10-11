"""Check exact standard templates, ship bindings and preserved legacy/1939 data."""
import hashlib
import json
from collections import Counter

from group_starting_fleets import grouped, selected_oobs
from hoi4_script import parse, replace_spans, walk
from naval_startup_audit import NavalData, ROOT, active_entries
from standardize_starting_naval_designs import REPORT, fingerprint, templates


def variant_map(source, data, mtg, year):
    return {(e.value.get('type'), e.value.get('name')): fingerprint(e.value)
            for e in active_entries(parse(source), mtg, year)
            if e.key == 'create_equipment_variant' and data.naval(e.value.get('type', ''))}


def main():
    data = NavalData()
    report = json.loads(REPORT.read_text(encoding='utf-8'))
    standard = templates()
    count = 0
    for tag, path in data.countries.items():
        for e in active_entries(parse(path.read_text(encoding='utf-8-sig')), True, 1936):
            if e.key == 'create_equipment_variant' and data.naval(e.value.get('type', '')):
                assert fingerprint(e.value) == standard.get(e.value.get('name')), (tag, e.value.get('name'))
                count += 1
    for relative, row in report['files'].items():
        path = ROOT / relative
        after = path.read_text(encoding='utf-8-sig')
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row['raw_after_sha256'], relative
        assert hashlib.sha256(after.encode('utf-8')).hexdigest() == row['after_sha256'], relative
        raw_before = (b'\xef\xbb\xbf' if row['source_before_bom'] else b'') + row['source_before'].replace('\n', row['source_before_newline']).encode('utf-8')
        assert hashlib.sha256(raw_before).hexdigest() == row['raw_before_sha256']
        if relative.startswith('history/countries/'):
            for mtg, year in ((False, 1936), (False, 1939), (True, 1939)):
                before_variants = variant_map(row['source_before'], data, mtg, year)
                after_variants = variant_map(after, data, mtg, year)
                assert all(after_variants.get(k) == v for k, v in before_variants.items()), (relative, mtg, year, 'Historical variant changed')
    total = updated = 0
    oobs = {next(iter(active))[0]: (path, tree) for path, _, active, tree in selected_oobs(data)}
    for row in report['countries']:
        tag = row['country']
        path, tree = oobs[tag]
        assert path.name == (ROOT / row['source']).name
        assert grouped(tree)
        ships = [e for e, _ in walk(tree) if e.key == 'ship']
        assert len(ships) == row['ships']
        total += len(ships)
        used = set()
        for entry in ships:
            ship = entry.value
            equipment = ship.get('equipment').entries()[0]
            key = (equipment.value.get('owner'), equipment.key, equipment.value.get('version_name'), True, 1936)
            assert key in data.variants, (tag, ship.get('name'), 'Missing design before OOB')
            variant = data.variants[key]
            assert fingerprint(variant) == standard.get(variant.get('name'))
            assert not data.issues(equipment.key, variant)
            used.add(variant.get('name'))
        history = parse(data.countries[tag].read_text(encoding='utf-8-sig'))
        selector = next(e for e in active_entries(history, True, 1936)
                        if e.key in ('oob', 'set_oob', 'set_naval_oob') and e.value.lower() == path.stem.lower())
        for name in used:
            variant = next(e for e in active_entries(history, True, 1936)
                           if e.key == 'create_equipment_variant' and e.value.get('name') == name)
            assert variant.end < selector.start, (tag, name, 'Design created after OOB')
        if not row['updated']:
            continue
        before = report['files'][row['source']]['source_before']
        edits = []
        bindings = {r['ship']: r for r in row['bindings']}
        assert len(bindings) == row['updated']
        for e, _ in walk(parse(before)):
            if e.key != 'ship' or e.value.get('name') not in bindings:
                continue
            binding = bindings[e.value.get('name')]
            eq = e.value.get('equipment').entries()[0]
            assert eq.key == binding['hull_before'] and eq.value.get('version_name') == binding['name_before']
            text = before[eq.start:eq.end]
            text = binding['hull_after'] + text[len(eq.key):]
            import re
            text = re.sub(r'version_name\s*=\s*"[^"]*"', 'version_name = "' + binding['name_after'] + '"', text)
            edits.append((eq.start, eq.end, text))
        assert replace_spans(before, edits) == path.read_text(encoding='utf-8-sig'), (tag, 'A ship property other than its model changed')
        updated += len(edits)
    assert len(oobs) == len(report['countries']) == 19
    assert total == 976 and updated == 83
    print(f'PASS: {len(report["removed"])} historical start designs removed; {count} precreated variants match research templates exactly.')
    print(f'PASS: {total} ships in 19 countries; {updated} model bindings standardized; counts, names, experience, officers, flags and ports preserved.')
    print('PASS: templates precede OOB loading; legacy and 1939 variants preserved; only standard researched designs at the MTG 1936 start.')


if __name__ == '__main__':
    main()
