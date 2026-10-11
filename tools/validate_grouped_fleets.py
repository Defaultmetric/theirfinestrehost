"""Verify exact ship preservation, nationwide grouping and original port use."""
import hashlib
import json

from group_starting_fleets import REPORT, fleets, grouped, kind, selected_oobs, ship_hashes
from hoi4_script import parse
from integrate_naval_tech_bonuses import sha
from naval_startup_audit import NavalData


def main():
    report = json.loads(REPORT.read_text(encoding='utf-8'))
    assert report['year'] == 1936 and report['mtg']
    rows = {r['country']: r for r in report['countries']}
    data = NavalData()
    seen = set()
    ships = fleet_count = 0
    changed = 0
    for path, profiles, active, tree in selected_oobs(data):
        tag = next(iter(active))[0]
        row = rows[tag]
        seen.add(tag)
        source = path.read_text(encoding='utf-8-sig')
        assert sha(source) == row['after_sha256']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row['raw_after_sha256']
        assert grouped(tree), (tag, 'Ships are split across fleets/task forces or mixed with submarines')
        assert dict(ship_hashes(tree)) == row['ship_fingerprints'], (tag, 'Lost, added or edited ship')
        unit, groups = fleets(tree)
        counts = {'surface': 0, 'submarine': 0}
        for group in groups:
            force = group.value.entries('task_force')[0].value
            for ship in force.entries('ship'):
                counts[kind(ship.value)] += 1
            if row['changed']:
                group_kind = kind(force.entries('ship')[0].value)
                assert group.value.get('naval_base') == force.get('location') == row['bases_after'][group_kind]
        assert counts == {'surface': row['surface_ships'], 'submarine': row['submarine_ships']}
        assert len(groups) == row['fleets_after'] == row['task_forces_after']
        ships += row['ships']
        fleet_count += len(groups)
        if row['changed']:
            changed += 1
            before = row['source_before']
            original = parse(before)
            assert ship_hashes(original) == ship_hashes(tree)
            before_unit, before_groups = fleets(original)
            assert before[:before_unit.start] + before[before_unit.end:] == source[:unit.start] + source[unit.end:]
            raw = (b'\xef\xbb\xbf' if row['source_before_bom'] else b'') + before.replace('\n', row['source_before_newline']).encode('utf-8')
            assert hashlib.sha256(raw).hexdigest() == row['raw_before_sha256'], 'Original source snapshot is inconsistent'
            assert not any(year == 1939 for _, _, year in profiles)
            old_ports = {f.value.get('naval_base') for f in before_groups}
            assert set(row['bases_after'].values()) <= old_ports
    assert seen == set(rows), 'Starting naval country was omitted'
    print(f'PASS: {len(seen)} countries, {ships} identical ships, {fleet_count} fleets; one task force per fleet; surface/submarines separated.')
    print(f'PASS: {changed} OOBs regrouped; ship models/names/experience/officers/flagships and non-naval effects preserved; original ports retained; 1939 unchanged.')


if __name__ == '__main__':
    main()
