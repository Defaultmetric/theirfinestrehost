"""Validate deployed models, the IC ledger, scope and load order after compaction."""
from collections import Counter
from decimal import Decimal, ROUND_FLOOR
import hashlib
import json
from pathlib import Path

from compact_starting_fleets import MODELS, SNAPSHOT, REPORT, dec, digest
from hoi4_script import Block, parse, walk
from naval_startup_audit import NavalData, ROOT, inventory


def main():
    data = NavalData()
    original = json.loads(SNAPSHOT.read_text(encoding='utf-8'))
    report = json.loads(REPORT.read_text(encoding='utf-8'))
    assert report['applied']
    assert set(report['countries']) == {'ENG', 'FRA', 'GER', 'ITA', 'JAP', 'SOV', 'SPR', 'USA'}
    production = json.loads((ROOT / 'docs/naval-starting-production.json').read_text(encoding='utf-8'))
    expected_production = {r['country']: dec(r['invested_ic']) for r in production['totals']
                           if r['year'] == 1936 and r['invested_ic'] >= 1000}
    totals = Counter()
    for tag, row in report['countries'].items():
        country = original['countries'][tag]
        assert dec(row['production_ic']) == expected_production[tag]
        assert dec(row['deployed_ic']) == sum(Decimal(s['ic']) for s in country['ships'])
        assert dec(row['budget_ic']) == dec(row['deployed_ic']) + dec(row['production_ic'])
        actual_counts = Counter()
        actual_names = []
        actual_ic = Decimal(0)
        for path in {s['source'] for s in country['ships']}:
            tree = parse((ROOT / path).read_text(encoding='utf-8-sig'))
            for e, _ in walk(tree):
                if e.key in ('fleet', 'task_force'):
                    assert e.value.entries('task_force' if e.key == 'fleet' else 'ship'), (tag, 'Empty naval group')
                if e.key != 'ship':
                    continue
                ship = e.value
                actual_names.append(ship.get('name'))
                assert len(ship.get('equipment').entries()) == 1
                eq = ship.get('equipment').entries()[0]
                assert eq.value.get('owner') == tag and eq.value.get('amount') == '1'
                matches = [k for k, (name, _) in MODELS.items() if name == eq.value.get('version_name')]
                assert len(matches) == 1, (tag, 'Nonstandard or legacy deployed model', eq.value.mapping())
                key = matches[0]
                model = report['models'][key]
                assert eq.key == model['hull'] and ship.get('definition') == model['definition']
                assert eq.value.get('version_name').endswith('1936')
                variant = data.variants[(tag, eq.key, model['name'], True, 1936)]
                assert not data.issues(eq.key, variant)
                actual_ic += dec(data.cost(eq.key, variant))
                actual_counts[key] += 1
        assert len(actual_names) == len(set(actual_names)), (tag, 'Duplicate ship names')
        assert actual_counts == Counter({k: r['final_count'] for k, r in row['roles'].items() if r['final_count']})
        assert actual_ic == dec(row['final_ic']) <= dec(row['budget_ic'])
        assert dec(row['budget_ic']) - actual_ic == dec(row['unspent_ic'])
        minimum_cost = min(dec(report['models'][k]['unit_ic']) for k in row['roles'])
        assert dec(row['unspent_ic']) < minimum_cost, (tag, 'Unused IC can still buy a qualifying ship')
        for key, r in row['roles'].items():
            floor = int((dec(r['budget_ic']) / dec(r['unit_ic'])).to_integral_value(rounding=ROUND_FLOOR))
            assert r['floor_count'] == floor <= r['final_count'], (tag, 'A separately budgeted class was sacrificed')
            if r['original_count']:
                assert r['final_count'] >= 1, (tag, 'Original class disappeared')
        expected_names = {s['name'] for s in row['retained'] + row['added']}
        assert set(actual_names) == expected_names
        for ship in country['ships']:
            if ship['pride']:
                assert ship['name'] in actual_names, (tag, 'Flagship was discarded')
        history_source = (ROOT / country['country_source']).read_text(encoding='utf-8-sig')
        history = parse(history_source)
        selected_names = {Path(s['source']).stem.lower() for s in country['ships']}
        oob_start = next(e.start for e, _ in walk(history)
                         if e.key == 'set_naval_oob' and e.value.lower() in selected_names)
        for key in actual_counts:
            model = report['models'][key]
            variants = [e for e, _ in walk(history) if e.key == 'create_equipment_variant' and e.value.get('name') == model['name']]
            assert len(variants) == 1 and variants[0].end < oob_start, (tag, 'Design not available before naval OOB')
            assert variants[0].value.get('allow_without_tech') == 'yes'
            flags = [e for e, _ in walk(history) if e.key == 'set_country_flag' and e.value == model['flag']]
            assert len(flags) == 1 and flags[0].end < oob_start, (tag, 'Duplicate startup design risk')
        totals['old_ships'] += row['original_ships']
        totals['new_ships'] += row['final_ships']
    for path, hashes in report['source_hashes'].items():
        assert digest((ROOT / path).read_text(encoding='utf-8-sig')) == hashes['after'], path
    grouping_path = ROOT / 'docs/naval-starting-fleet-grouping.json'
    regrouped = {r['source']: r for r in json.loads(grouping_path.read_text(encoding='utf-8'))['countries'] if r['changed']} if grouping_path.exists() else {}
    standard_path = ROOT / 'docs/naval-standard-start-designs.json'
    standard_files = json.loads(standard_path.read_text(encoding='utf-8'))['files'] if standard_path.exists() else {}
    unchanged, organization_only, standardized = 0, 0, 0
    for path, sha256 in original['untouched_history_hashes'].items():
        current = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        if current == sha256:
            unchanged += 1
            continue
        if path in standard_files:
            migration = standard_files[path]
            assert migration['raw_after_sha256'] == current
            if path in regrouped:
                row = regrouped[path]
                assert row['raw_before_sha256'] == sha256
                assert row['raw_after_before_standardization'] == migration['raw_before_sha256']
            else:
                assert migration['raw_before_sha256'] == sha256
            standardized += 1
            continue
        assert path in regrouped, ('Out-of-scope history changed', path)
        row = regrouped[path]
        assert row['raw_before_sha256'] == sha256 and row['raw_after_sha256'] == current
        from group_starting_fleets import ship_hashes
        assert dict(ship_hashes(parse((ROOT / path).read_text(encoding='utf-8-sig')))) == row['ship_fingerprints']
        assert ship_hashes(parse(row['source_before'])) == ship_hashes(parse((ROOT / path).read_text(encoding='utf-8-sig')))
        organization_only += 1
    assert not inventory(data)[0], 'Starting naval production was reintroduced'
    print(f'PASS: 8 countries, {totals["old_ships"]} -> {totals["new_ships"]} ships; only standard 1936 deployed models.')
    print('PASS: per-role compaction and pooled rounding IC; no class sacrifices; all budgets respected; no affordable remainder.')
    print('PASS: variants/flags precede OOB loading; names and flagships preserved; no empty fleets or duplicate ship names.')
    print(f'PASS: {unchanged} other history files unchanged; {organization_only} regrouped; {standardized} explicit standard-design migrations; 1939 OOBs unchanged; no starting production.')


if __name__ == '__main__':
    main()
