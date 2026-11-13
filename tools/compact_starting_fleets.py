"""Compact the 1936 MTG fleets by role and IC, using the fixed 1936 designs.

The immutable source snapshot makes recalculation repeatable without counting
already modernized ships as the original fleet. --apply checks source hashes.
"""
import argparse
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
import re

from hoi4_script import Block, overlay_files, parse, replace_spans, walk
from naval_startup_audit import NavalData, ROOT, VANILLA

SNAPSHOT = ROOT / 'docs/naval-starting-fleets-original.json'
REPORT = ROOT / 'docs/naval-starting-fleets.json'
MODELS = {
    'LD': ('Light Destroyer 1936', 'destroyer'),
    'TD': ('Torpedo Destroyer 1936', 'destroyer'),
    'ASW': ('ASW Destroyer 1936', 'destroyer'),
    'LC': ('Light Cruiser 1936', 'light_cruiser'),
    'HC': ('Heavy Cruiser 1936', 'heavy_cruiser'),
    'BB': ('Battleship 1936', 'battleship'),
    'BC': ('Battlecruiser 1936', 'battle_cruiser'),
    'CV': ('Carrier 1936', 'carrier'),
    'SS': ('Submarine 1936', 'submarine'),
    'CS': ('Cruiser Submarine 1936', 'submarine'),
}
DEFINITIONS = {'light_cruiser': 'LC', 'heavy_cruiser': 'HC',
               'battleship': 'BB', 'battle_cruiser': 'BC', 'carrier': 'CV'}


def dec(value):
    return Decimal(str(value)).quantize(Decimal('0.000001'))


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def money(value):
    return f'{Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP):,.2f}'


def formatted_template(script):
    lines = []
    depth = 0
    for line in script.splitlines():
        stripped = line.strip()
        level = depth - int(stripped.startswith('}'))
        lines.append('\t' * level + stripped)
        depth += stripped.count('{') - stripped.count('}')
    assert depth == 0
    return lines


def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def resolve(data, owner, hull, name, year=1936):
    variant = data.variants.get((owner, hull, name, True, year))
    if variant is not None:
        return variant.get('type'), variant
    candidates = [v for (c, h, n, mtg, y), v in data.variants.items()
                  if (c, n, mtg, y) == (owner, name, True, year)
                  and data.hull(h).get('archetype', h) == data.hull(hull).get('archetype', hull)]
    assert len(candidates) == 1, (owner, hull, name, year)
    return candidates[0].get('type'), candidates[0]


def role(data, hull, variant, definition=None):
    name = variant.get('name', '')
    for key, (standard, _) in MODELS.items():
        if name == standard or name == standard.replace('1936', '1922'):
            return key
    mods = list(data.module_map(hull, variant).values())
    if hull.startswith('convoy_'):
        return 'CONVOY'
    if 'carrier' in hull:
        return 'CV'
    if 'submarine' in hull:
        return 'CS' if hull == 'ship_hull_cruiser_submarine' else 'SS'
    if definition == 'destroyer' or hull.startswith('ship_hull_light_'):
        icon = variant.get('role_icon_index')
        if icon in ('2', '8', '3'):
            return {'2': 'LD', '8': 'TD', '3': 'ASW'}[icon]
        # Historical general-purpose DDs lack explicit LD/TD/ASW labels.
        # Two depth-charge modules identify ASW; two torpedo modules identify TD.
        # Single mixed weapon packages remain LD instead of converting every DD to TD.
        if sum(m.startswith('ship_depth_charge') for m in mods) >= 2:
            return 'ASW'
        return 'TD' if sum(m.startswith('ship_torpedo') for m in mods) >= 2 else 'LD'
    if definition in DEFINITIONS:
        return DEFINITIONS[definition]
    if hull == 'ship_hull_cruiser_panzerschiff':
        return 'HC'
    if hull == 'ship_hull_cruiser_coastal_defense_ship':
        return 'LC'
    if 'cruiser' in hull:
        return 'HC' if any(m.startswith('ship_medium_battery') for m in mods) else 'LC'
    if 'heavy' in hull or 'dreadnought' in hull:
        return 'BC' if any(m.startswith('ship_armor_bc') for m in mods) else 'BB'
    raise AssertionError(('Unknown ship role', hull, name, definition))


def registry(data):
    path = ROOT / 'common/scripted_effects/tfr_navy_designs.txt'
    source = path.read_text(encoding='utf-8-sig')
    result = {}
    for branch in parse(source).get('TFR_navy_create_designs').entries('if'):
        entry = branch.value.entries('create_equipment_variant')[0]
        variant = entry.value
        for key, (name, definition) in MODELS.items():
            if variant.get('name') == name:
                assert not data.issues(variant.get('type'), variant)
                result[key] = dict(name=name, hull=variant.get('type'), definition=definition,
                    unit_ic=str(dec(data.cost(variant.get('type'), variant))),
                    flag=branch.value.get('set_country_flag'),
                    script=source[entry.start:entry.end])
    assert set(result) == set(MODELS)
    return result


def reserve_names(data, tags):
    """Use historical 1939 names for extra ships instead of technical labels."""
    files = {p.name.lower(): p for p in overlay_files(ROOT, VANILLA, 'history/units')}
    result = {tag: defaultdict(list) for tag in tags}
    for name, profiles in sorted(data.oob_profiles.items()):
        matching = {tag for tag, mtg, year in profiles if tag in tags and mtg and year == 1939}
        if not matching:
            continue
        for e, _ in walk(parse(files[name].read_text(encoding='utf-8-sig'))):
            if e.key != 'ship':
                continue
            for tag in matching:
                eq = e.value.get('equipment').entries()[0]
                hull, variant = resolve(data, eq.value.get('owner', tag), eq.key, eq.value.get('version_name'), 1939)
                key = role(data, hull, variant, e.value.get('definition'))
                ship_name = e.value.get('name')
                if ship_name not in result[tag][key]:
                    result[tag][key].append(ship_name)
    return result


def snapshot(data):
    production = json.loads((ROOT / 'docs/naval-starting-production.json').read_text(encoding='utf-8'))
    eligible = {r['country']: r for r in production['totals']
                if r['year'] == 1936 and r['mtg'] and r['invested_ic'] >= 1000}
    files = {p.name.lower(): p for p in overlay_files(ROOT, VANILLA, 'history/units')}
    # Use actual historical ship definitions for production models where available.
    historical_definitions = defaultdict(set)
    for name, profiles in data.oob_profiles.items():
        if not any(tag in eligible and mtg for tag, mtg, year in profiles):
            continue
        for e, _ in walk(parse(files[name].read_text(encoding='utf-8-sig'))):
            if e.key == 'ship':
                for eq in e.value.get('equipment').entries():
                    historical_definitions[(eq.value.get('owner'), eq.key, eq.value.get('version_name'))].add(e.value.get('definition'))
    result = dict(schema=1, year=1936, mtg=True, minimum_production_ic=1000,
                  cost_basis=production['cost_basis'], sources={}, countries={})

    def archive(path):
        relative = path.relative_to(ROOT).as_posix()
        raw = path.read_bytes()
        text = path.read_text(encoding='utf-8-sig')
        result['sources'][relative] = dict(text=text, sha256=digest(text),
            bom=raw.startswith(b'\xef\xbb\xbf'), newline='\r\n' if b'\r\n' in raw else '\n')
        return relative, text

    for tag in sorted(eligible):
        country_path, _ = archive(data.countries[tag])
        country = dict(country_source=country_path, ships=[], production=[])
        for name, profiles in sorted(data.oob_profiles.items()):
            if (tag, True, 1936) not in profiles:
                continue
            path = files[name]
            source = path.read_text(encoding='utf-8-sig')
            ships = [(e, a) for e, a in walk(parse(source)) if e.key == 'ship']
            if not ships:
                continue
            assert profiles == {(tag, True, 1936)}, (name, profiles)
            assert path.is_relative_to(ROOT), 'Copy the country OOB into the mod first'
            relative, source = archive(path)
            for e, ancestors in ships:
                ship = e.value
                eq = ship.get('equipment').entries()[0]
                assert eq.value.get('amount') == '1'
                hull, variant = resolve(data, eq.value.get('owner', tag), eq.key, eq.value.get('version_name'))
                tf = next(a for a in reversed(ancestors) if a.key == 'task_force')
                country['ships'].append(dict(source=relative, start=e.start, end=e.end,
                    name=ship.get('name'), role=role(data, hull, variant, ship.get('definition')),
                    hull=hull, variant=variant.get('name'), ic=str(dec(data.cost(hull, variant))),
                    task_force=tf.value.get('name'), task_force_start=tf.start,
                    pride=ship.get('pride_of_the_fleet') == 'yes', officer=bool(ship.get('officer')),
                    experience=float(ship.get('start_experience_factor', 0))))
        assert country['ships'], tag
        for line in production['lines']:
            if (line['country'], line['year'], line['mtg']) != (tag, 1936, True):
                continue
            if line['equipment'].startswith('convoy_'):
                key = 'CONVOY'
            else:
                hull, variant = resolve(data, line['creator'], line['equipment'], line['variant'])
                definitions = historical_definitions[(line['creator'], hull, line['variant'])]
                definition = next(iter(definitions)) if len(definitions) == 1 else None
                key = role(data, hull, variant, definition)
                assert abs(dec(data.cost(hull, variant)) - dec(line['design_cost_ic'])) < Decimal('.00001')
            country['production'].append(dict(role=key, name=line['name'], variant=line['variant'],
                ic=str(dec(line['invested_ic'])), original_source=line['source'], original_line=line['line']))
        result['countries'][tag] = country
    result['reserve_names'] = reserve_names(data, result['countries'])
    save_json(SNAPSHOT, result)
    return result


def plan(original, models):
    countries = {}
    for tag, country in original['countries'].items():
        budgets = defaultdict(Decimal)
        deployed = Counter()
        deployed_ic = defaultdict(Decimal)
        production_ic = defaultdict(Decimal)
        for ship in country['ships']:
            deployed[ship['role']] += 1
            deployed_ic[ship['role']] += Decimal(ship['ic'])
        for line in country['production']:
            production_ic[line['role']] += Decimal(line['ic'])
        assert production_ic['CONVOY'] == 0, 'Convoy IC must not silently become warships'
        for key in MODELS:
            budgets[key] = deployed_ic[key] + production_ic[key]
        costs = {k: Decimal(v['unit_ic']) for k, v in models.items()}
        counts = {k: int((budgets[k] / costs[k]).to_integral_value(rounding=ROUND_FLOOR)) for k in MODELS}
        floor_counts = counts.copy()
        remaining = sum(budgets.values()) - sum(costs[k] * n for k, n in counts.items())
        topups = []
        # Preserve an existing rare class (e.g. France's sole carrier) using
        # unspent rounding IC; no already-budgeted ships are removed.
        for key in sorted(MODELS, key=lambda k: costs[k], reverse=True):
            if deployed[key] and counts[key] == 0:
                assert remaining >= costs[key], (tag, key, 'Cannot preserve class without cuts')
                counts[key] += 1
                remaining -= costs[key]
                topups.append(dict(role=key, reason='preserve_existing_class'))
        # Spend the common remainder on the role furthest below its fractional
        # IC-equivalent count. Only roles already present in ships/production qualify.
        while True:
            candidates = [k for k in MODELS if budgets[k] > 0 and costs[k] <= remaining]
            if not candidates:
                break
            key = max(candidates, key=lambda k: (budgets[k] / costs[k] - counts[k], budgets[k]))
            counts[key] += 1
            remaining -= costs[key]
            topups.append(dict(role=key, reason='pooled_rounding_ic'))
        spent = sum(costs[k] * n for k, n in counts.items())
        assert spent <= sum(budgets.values())
        countries[tag] = dict(deployed_ic=str(sum(deployed_ic.values())),
            production_ic=str(sum(production_ic.values())), budget_ic=str(sum(budgets.values())),
            final_ic=str(spent), unspent_ic=str(remaining),
            original_ships=sum(deployed.values()), final_ships=sum(counts.values()),
            roles={k: dict(original_count=deployed[k], deployed_ic=str(deployed_ic[k]),
                production_ic=str(production_ic[k]), budget_ic=str(budgets[k]),
                unit_ic=str(costs[k]), floor_count=floor_counts[k], final_count=counts[k],
                final_ic=str(costs[k] * counts[k])) for k in MODELS if budgets[k] > 0},
            topups=topups)
    return dict(year=1936, minimum_production_ic=1000, pooled_rounding_ic=True,
                cost_basis=original['cost_basis'], models=models, countries=countries)


def apportion(total, weights):
    quotas = {k: total * n // sum(weights.values()) for k, n in weights.items()}
    ordered = sorted(weights, key=lambda k: (-(total * weights[k] % sum(weights.values())), k))
    for key in ordered[:total - sum(quotas.values())]:
        quotas[key] += 1
    return quotas


def equipment(tag, model):
    return 'equipment = { ' + model['hull'] + ' = { amount = 1 owner = ' + tag + ' version_name = ' + json.dumps(model['name']) + ' } }'


def render(original, report):
    edits = defaultdict(list)
    outputs = {}
    for tag, country in original['countries'].items():
        row = report['countries'][tag]
        role_ships = defaultdict(list)
        for ship in country['ships']:
            role_ships[ship['role']].append(ship)
        tf_entries = {}
        for relative in {s['source'] for s in country['ships']}:
            for e, _ in walk(parse(original['sources'][relative]['text'])):
                if e.key == 'task_force':
                    tf_entries[(relative, e.start)] = e
        preferred = next((s['source'], s['task_force_start']) for s in country['ships']
                         if s['role'] not in ('SS', 'CS'))
        retained = []
        removed = []
        added = []
        used_names = {s['name'] for s in country['ships']}
        for key, role_row in row['roles'].items():
            model = report['models'][key]
            members = role_ships[key]
            groups = defaultdict(list)
            for ship in members:
                groups[(ship['source'], ship['task_force_start'])].append(ship)
            target = role_row['final_count']
            quotas = apportion(target, {k: len(v) for k, v in groups.items()}) if groups else {preferred: target}
            # Keep the historical flagship even if proportional rounding gives its TF zero.
            for group, ships in groups.items():
                if any(s['pride'] for s in ships) and quotas[group] == 0 and target:
                    donor = max(quotas, key=lambda k: quotas[k])
                    quotas[donor] -= 1
                    quotas[group] = 1
            for group, quota in quotas.items():
                ships = sorted(groups.get(group, []), key=lambda s:
                    (-s['pride'], -s['officer'], -s['experience'], -Decimal(s['ic']), s['start']))
                keep = ships[:quota]
                for ship in keep:
                    source = original['sources'][ship['source']]['text']
                    body = source[ship['start']:ship['end']]
                    old = parse(body).get('ship').entries('equipment')[0]
                    body = replace_spans(body, [(old.start, old.end, equipment(tag, model))])
                    edits[ship['source']].append((ship['start'], ship['end'], body))
                    retained.append(dict(name=ship['name'], role=key, task_force=ship['task_force'], original_hull=ship['hull'], original_variant=ship['variant']))
                for ship in ships[quota:]:
                    edits[ship['source']].append((ship['start'], ship['end'], ''))
                    removed.append(dict(name=ship['name'], role=key, task_force=ship['task_force']))
                for index in range(max(0, quota - len(keep))):
                    names = [p['name'] for p in country['production'] if p['role'] == key
                             and p['name'] not in used_names and p['name']
                             and p['name'] != p['variant'] and not p['name'].endswith('Class')]
                    names += [n for n in original['reserve_names'][tag].get(key, []) if n not in used_names]
                    # France had only one historical cruiser submarine; use a
                    # ship name derived from that class for a pooled-IC addition.
                    fallback = members[0]['name'] + ' II' if members else model['name']
                    name = names[0] if names else fallback
                    while name in used_names:
                        name += ' II'
                    used_names.add(name)
                    tf = tf_entries[group]
                    body = '\n\t\t\tship = { name = ' + json.dumps(name, ensure_ascii=False) + ' definition = ' + model['definition'] + ' ' + equipment(tag, model) + ' }\n\t\t'
                    edits[group[0]].append((tf.end - 1, tf.end - 1, body))
                    added.append(dict(name=name, role=key, task_force=tf.value.get('name')))
        row.update(retained=retained, removed=removed, added=added)
        path = country['country_source']
        source = original['sources'][path]['text']
        selected_names = {Path(s['source']).stem.lower() for s in country['ships']}
        first_oob = next(e for e, _ in walk(parse(source))
                         if e.key == 'set_naval_oob' and e.value.lower() in selected_names)
        indent = source[source.rfind('\n', 0, first_oob.start) + 1:first_oob.start]
        lines = ['# TFR: standard 1936 designs must exist before the starting naval OOB loads.']
        for key, role_row in row['roles'].items():
            if not role_row['final_count']:
                continue
            model = report['models'][key]
            lines.extend(formatted_template(model['script']))
            lines.append('set_country_flag = ' + model['flag'])
        insertion = ('\n' + indent).join(lines) + '\n' + indent
        edits[path].append((first_oob.start, first_oob.start, insertion))
    for path, changes in edits.items():
        source = replace_spans(original['sources'][path]['text'], changes)
        # Remove empty naval groups produced by compaction.
        for kind, child in (('task_force', 'ship'), ('fleet', 'task_force')):
            empty = [(e.start, e.end, '') for e, _ in walk(parse(source))
                     if e.key == kind and not e.value.entries(child)]
            source = replace_spans(source, empty)
        source = re.sub(r'\s*\([^\n)]*(?:CP|SCREENING)[^\n)]*\)(?=\s*###)', '', source)
        parse(source)
        outputs[path] = source
    report['source_hashes'] = {p: dict(before=original['sources'][p]['sha256'], after=digest(t)) for p, t in outputs.items()}
    return outputs


def markdown(report):
    lines = ['# Flote inițiale compactate — 1936, Man the Guns', '',
        'Țări cu minimum 1.000 IC în producția navală eliminată. Fiecare tip este compactat separat:',
        '`număr inițial compactat = floor((IC deployed + IC investit în producție) / cost design standard 1936)`.', '',
        'Resturile de IC sunt reunite pentru completări, fără eliminarea navelor deja bugetate.',
        'Se păstrează minimum o navă din fiecare tip deja deployed. Costurile exclud reducerile de MIO/idei/tehnologii.', '',
        '| Țară | Nave înainte | Nave după | IC deployed | IC producție | Buget total | IC flotă nouă | Rest IC |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for tag, row in report['countries'].items():
        values = [money(row[k]) for k in ('deployed_ic', 'production_ic', 'budget_ic', 'final_ic', 'unspent_ic')]
        lines.append(f'| {tag} | {row["original_ships"]} | {row["final_ships"]} | ' + ' | '.join(values) + ' |')
    lines += ['', '## Identificarea subtipurilor', '',
        'Denumirile standard explicite și role_icon_index (LD=2, TD=8, ASW=3) au prioritate pentru destroyers.',
        'Design-urile istorice fără aceste indicii sunt ASW dacă au cel puțin două module depth charge,',
        'TD dacă au cel puțin două module torpedo, altfel LD. O singură torpilă/depth charge nu schimbă un DD mixt în TD/ASW.',
        'LC/HC/BB/BC păstrează definition-ul istoric; submarinele crucișător rămân CS.',
        'Producția folosește definition-ul aceluiași design în OOB-urile istorice, unde există.', '',
        'Navele vechi și cele deja din 1936 sunt incluse împreună și înlocuite cu variantele standard.',
        'Numele, experiența, flagship-ul, ofițerii și distribuția între task forces sunt păstrate unde numărul compactat permite.',
        'Flotele 1939, țările sub prag și liniile de producție eliminate rămân neschimbate.', '',
        'Snapshot-ul surselor originale și inventarul pe navă sunt în `naval-starting-fleets-original.json`.',
        'Calculul pe tip, completările din resturi și navele păstrate/eliminate/adăugate sunt în `naval-starting-fleets.json`.']
    for tag, row in report['countries'].items():
        lines += ['', f'## {tag}', '', '| Tip | Înainte | Floor pe tip | După resturi comune | IC deployed | IC producție | Cost/navă 1936 | IC final |',
                  '|---|---:|---:|---:|---:|---:|---:|---:|']
        for key, r in row['roles'].items():
            vals = [money(r[k]) for k in ('deployed_ic', 'production_ic', 'unit_ic', 'final_ic')]
            lines.append(f'| {key} | {r["original_count"]} | {r["floor_count"]} | {r["final_count"]} | ' + ' | '.join(vals) + ' |')
    (ROOT / 'docs/naval-starting-fleets.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    data = NavalData()
    previous = json.loads(REPORT.read_text(encoding='utf-8')) if REPORT.exists() else {}
    original = json.loads(SNAPSHOT.read_text(encoding='utf-8')) if SNAPSHOT.exists() else snapshot(data)
    if 'reserve_names' not in original:
        original['reserve_names'] = reserve_names(data, original['countries'])
        save_json(SNAPSHOT, original)
    if 'untouched_history_hashes' not in original:
        original['untouched_history_hashes'] = {
            p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for directory in ('history/units', 'history/countries')
            for p in (ROOT / directory).glob('*.txt')
            if p.relative_to(ROOT).as_posix() not in original['sources']}
        save_json(SNAPSHOT, original)
    report = plan(original, registry(data))
    outputs = render(original, report)
    if args.apply:
        # Check every source before making any mutation; reject unrelated edits.
        for path, source in outputs.items():
            current = (ROOT / path).read_text(encoding='utf-8-sig')
            prior = previous.get('source_hashes', {}).get(path, {})
            accepted = {original['sources'][path]['sha256'], digest(source)}
            if previous.get('applied') and prior.get('before') == original['sources'][path]['sha256']:
                accepted.add(prior['after'])
            assert digest(current) in accepted, ('Source changed', path)
        for path, source in outputs.items():
            old = original['sources'][path]
            (ROOT / path).write_bytes((b'\xef\xbb\xbf' if old['bom'] else b'') + source.replace('\n', old['newline']).encode('utf-8'))
    report['applied'] = args.apply
    save_json(REPORT, report)
    markdown(report)
    for tag, row in report['countries'].items():
        counts = ', '.join(f'{k}:{r["original_count"]}->{r["final_count"]}' for k, r in row['roles'].items())
        print(tag, counts, 'IC', row['final_ic'], '/', row['budget_ic'], 'rest', row['unspent_ic'])
    print('APPLIED' if args.apply else 'PREVIEW: no game history files changed')


if __name__ == '__main__':
    main()
