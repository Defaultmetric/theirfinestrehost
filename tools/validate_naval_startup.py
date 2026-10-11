"""Validate design prerequisites, module legality and removed production records."""
from collections import Counter, defaultdict
from decimal import Decimal
import json

from hoi4_script import Block, overlay_files, parse, walk
from naval_startup_audit import NavalData, ROOT, VANILLA, inventory


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
        issues = data.issues(variant.get('type'), variant)
        assert not issues, (variant.get('name'), issues)
        flag = b.get('set_country_flag')
        assert flag and any(e.key == 'has_country_flag' and e.value == flag for e,a in walk(b.get('limit'))), 'Missing one-time design guard'
        assert b.entries().index(variants[0]) < b.entries().index(b.entries('set_country_flag')[0])
        flags.append(flag)
        design_count += 1
        dependencies.update(e.value for e,a in walk(b.get('limit')) if e.key == 'has_tech')
    assert len(flags) == len(set(flags)), 'Duplicate design flags'
    techs = {}
    for p in overlay_files(ROOT, VANILLA, 'common/technologies'):
        for group in parse(p.read_text(encoding='utf-8-sig')).entries('technologies'):
            techs.update(group.value.mapping())
    for tech in dependencies:
        assert tech in techs, f'Unknown design prerequisite {tech}'
        hook = techs[tech].get('on_research_complete', Block([]))
        assert any(e.key == 'TFR_navy_create_designs' for e,a in walk(hook)), f'Missing research hook: {tech}'
    startup = parse((ROOT/'common/on_actions/tfr_navy_simplified_on_actions.txt').read_text(encoding='utf-8-sig'))
    country = startup.get('on_actions').get('on_startup').get('effect').get('every_country')
    assert country.entries().index(country.entries('set_technology')[0]) < country.entries().index(country.entries('TFR_navy_create_designs')[0])
    for tag, e, p, _ in data.history_variants:
        if e.value.get('type', '').startswith('ship_hull_'):
            assert not data.issues(e.value.get('type'), e.value), (tag, e.value.get('name'))
    duplicate_limits = []
    for name,(b,p) in data.equipment.items():
        if data.naval(name):
            keys = [(e.value.get('module'),e.value.get('category')) for e in b.entries('module_count_limit')]
            duplicate_limits += [(name,k) for k,n in Counter(keys).items() if n>1]
    assert not duplicate_limits, duplicate_limits
    assert not inventory(data)[0], 'Starting naval production still exists'
    report = json.loads((ROOT/'docs/naval-starting-production.json').read_text(encoding='utf-8'))
    actual = defaultdict(lambda: [0, Decimal(0)])
    sources = defaultdict(set)
    for r in report['lines']:
        key = (r['year'],r['mtg'],r['country'])
        actual[key][0] += 1
        actual[key][1] += Decimal(str(r['invested_ic']))
        assert abs(Decimal(str(r['design_cost_ic'])) * Decimal(str(r['progress'])) - Decimal(str(r['invested_ic']))) < Decimal('0.000002')
        sources[r['source']].add(r['line'])
    for row in report['totals']:
        key = (row['year'],row['mtg'],row['country'])
        n, ic = actual.pop(key)
        assert row['production_lines'] == n
        assert abs(Decimal(str(row['invested_ic'])) - ic) < Decimal('0.000002')
    assert not actual
    for source, lines in sources.items():
        text = (ROOT/source).read_text(encoding='utf-8-sig')
        assert text.count('# TFR: starting naval production removed; invested IC recorded') == len(lines), source
    print(f'PASS: {design_count} fixed designs; {len(dependencies)} immediate research hooks; historical naval designs valid; no duplicate hull limits.')
    print(f'PASS: no starting naval production remains; {len(report["lines"])} country/scenario records, {sum(map(len,sources.values()))} removed source blocks, {len(sources)} OOB files; archived IC reconciles.')


if __name__ == '__main__':
    main()
