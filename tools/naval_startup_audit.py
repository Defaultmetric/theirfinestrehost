"""Audit naval designs and record/remove historical naval production.

Costs use the mod's hull/module definitions, before compatibility repairs.
Progress belongs to the current hull on each line, not its queued amount.
"""
import argparse
import json
import re
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from hoi4_script import Block, overlay_files, parse, replace_spans, walk

ROOT = Path(__file__).resolve().parents[1]
VANILLA = Path('C:/Program Files (x86)/Steam/steamapps/common/Hearts of Iron IV')


def number(value, default=0):
    return float(value) if value is not None else default


def definitions(relative, container):
    result = {}
    for path in overlay_files(ROOT, VANILLA, relative):
        tree = parse(path.read_text(encoding='utf-8-sig'))
        for e, _ in walk(tree):
            if e.key == container and isinstance(e.value, Block):
                for child in e.value.entries():
                    if isinstance(child.value, Block):
                        result[child.key] = (child.value, path)
    return result


def condition(b, mtg=True):
    values = []
    for e in b.entries():
        k, v = e.key.upper(), e.value
        if k == 'HAS_DLC':
            values.append(mtg if v == 'Man the Guns' else True)
        elif k == 'NOT':
            values.append(not condition(v, mtg))
        elif k == 'OR':
            values.append(any(condition(Block([x]), mtg) for x in v.entries()))
        elif k == 'AND':
            values.append(condition(v, mtg))
        elif k == 'ALWAYS':
            values.append(v == 'yes')
        elif k == 'IS_TUTORIAL':
            values.append(v == 'no')
        else:
            # Static country-history choices unrelated to DLC do not gate
            # naval templates in the current production inventory.
            values.append(True)
    return all(values)


def active_entries(tree, mtg=True, year=1936):
    previous = None
    for e in tree.entries():
        if re.fullmatch(r'\d{4}\.\d+\.\d+(?:\.\d+)?', e.key):
            if int(e.key[:4]) <= year:
                yield from active_entries(e.value, mtg, year)
        elif e.key.lower() in ('if', 'else_if', 'else'):
            eligible = e.key.lower() == 'if' or previous is False
            matched = eligible and condition(e.value.get('limit', Block([])), mtg)
            if matched:
                yield from active_entries(e.value, mtg, year)
            previous = matched if e.key.lower() == 'if' else (previous or matched)
        else:
            yield e
            if isinstance(e.value, Block) and e.key != 'limit':
                yield from active_entries(e.value, mtg, year)


class NavalData:
    def __init__(self):
        self.equipment = definitions('common/units/equipment', 'equipments')
        self.modules = definitions('common/units/equipment/modules', 'equipment_modules')
        self.upgrades = definitions('common/units/equipment/upgrades', 'upgrades')
        self.countries = {p.name[:3]: p for p in overlay_files(ROOT, VANILLA, 'history/countries')}
        self.variants = {}
        self.history_variants = []
        self.oob_profiles = defaultdict(set)
        for tag, path in self.countries.items():
            tree = parse(path.read_text(encoding='utf-8-sig'))
            for e, ancestors in walk(tree):
                if e.key == 'create_equipment_variant' and isinstance(e.value, Block):
                    hull = e.value.get('type', '')
                    if self.naval(hull):
                        self.history_variants.append((tag, e, path, ancestors))
            for mtg in (False, True):
                for year in (1936, 1939):
                    selected_oobs = {}
                    for e in active_entries(tree, mtg, year):
                        if e.key == 'create_equipment_variant':
                            self.variants[(tag, e.value.get('type'), e.value.get('name'), mtg, year)] = e.value
                        if e.key in ('oob', 'set_oob', 'set_naval_oob', 'set_air_oob'):
                            selected_oobs['oob' if e.key == 'set_oob' else e.key] = e.value
                    for name in selected_oobs.values():
                        self.oob_profiles[(str(name) + '.txt').lower()].add((tag, mtg, year))

    def hull(self, name):
        b = self.equipment[name][0]
        result = {}
        archetype = b.get('archetype')
        if archetype:
            result.update(self.hull(archetype))
        for e in b.entries():
            if e.key == 'module_slots' and e.value == 'inherit':
                continue
            if e.key == 'module_slots' and isinstance(e.value, Block):
                inherited = result.get(e.key, Block([])).mapping()
                result[e.key] = Block([type(e)(s.key, '=', inherited[s.key] if s.value == 'inherit' else s.value, 0, 0, 0) for s in e.value.entries()])
                continue
            if e.key == 'default_modules' and isinstance(e.value, Block):
                inherited = result.get(e.key, Block([])).mapping()
                inherited.update(e.value.mapping())
                result[e.key] = Block([type(e)(k, '=', v, 0, 0, 0) for k, v in inherited.items()])
            else:
                result[e.key] = e.value
        return result

    def naval(self, name):
        if name not in self.equipment:
            return False
        b = self.equipment[name][0]
        return (str(b.get('type', '')).endswith('_ship') or
                name.startswith(('ship_hull_', 'convoy_', 'destroyer_', 'submarine_',
                                 'light_cruiser_', 'heavy_cruiser_', 'battle_cruiser_', 'battleship_', 'carrier_')) or
                (bool(b.get('archetype')) and self.naval(b.get('archetype'))))

    def module_map(self, name, variant):
        h = self.hull(name)
        defaults = h.get('default_modules', Block([])).mapping()
        slots = self.slot_map(name)
        defaults = {k: v for k, v in defaults.items() if k in slots}
        if variant and isinstance(variant.get('modules'), Block):
            defaults.update(variant.get('modules').mapping())
        return {slot: mod for slot, mod in defaults.items() if mod != 'empty'}

    def cost(self, name, variant=None):
        h = self.hull(name)
        add, multiply, average = 0, 0, []
        for mod in self.module_map(name, variant).values():
            if mod not in self.modules:
                raise ValueError(f'Unknown module {mod} on {name}')
            b = self.modules[mod][0]
            add += number(b.get('add_stats', Block([])).get('build_cost_ic'))
            multiply += number(b.get('multiply_stats', Block([])).get('build_cost_ic'))
            val = b.get('add_average_stats', Block([])).get('build_cost_ic')
            if val is not None:
                average.append(number(val))
        result = (number(h.get('build_cost_ic')) + add + (sum(average) / len(average) if average else 0)) * (1 + multiply)
        return result

    def slot_map(self, name):
        slots = self.hull(name).get('module_slots', Block([])).mapping()
        def resolve(key, seen=()):
            val = slots[key]
            if isinstance(val, str):
                if key in seen:
                    raise ValueError('Cyclic slot inheritance')
                return resolve(val, seen + (key,))
            return val
        return {k: resolve(k) for k in slots}

    def issues(self, name, variant):
        slots = self.slot_map(name)
        mods = self.module_map(name, variant)
        issues = []
        for slot, mod in mods.items():
            if mod not in self.modules:
                issues.append(('unknown_module', slot, mod))
            elif slot not in slots:
                issues.append(('unknown_slot', slot, mod))
            elif self.modules[mod][0].get('category') not in slots[slot].get('allowed_module_categories', Block([])).atoms():
                issues.append(('category', slot, mod))
        for slot, b in slots.items():
            if b.get('required') == 'yes' and slot not in mods:
                issues.append(('required', slot, 'empty'))
        # Hull-specific restrictions; archetype limits are validated too.
        limits = self.equipment[name][0].entries('module_count_limit')
        archetype = self.equipment[name][0].get('archetype')
        if archetype:
            limits += self.equipment[archetype][0].entries('module_count_limit')
        for e in limits:
            b = e.value
            module, category = b.get('module'), b.get('category')
            count = sum(m == module if module else self.modules.get(m, (Block([]),))[0].get('category') == category for m in mods.values())
            rule = b.entries('count')[0]
            maximum = number(rule.value)
            valid = {'<': count < maximum, '<=': count <= maximum, '=': count == maximum, '>': count > maximum, '>=': count >= maximum}[rule.op]
            if not valid:
                issues.append(('count_limit', module or category, f'{count} {rule.op} {rule.value}'))
        return issues


def inventory(data):
    records, removals = [], defaultdict(list)
    for relative in ('history/units', 'history/countries'):
        for path in overlay_files(ROOT, VANILLA, relative):
            profiles = data.oob_profiles.get(path.name.lower(), set()) if relative == 'history/units' else {(path.name[:3], True, 1936)}
            profiles = {(tag, mtg, year) for tag, mtg, year in profiles if mtg}
            if not profiles:
                continue
            text = path.read_text(encoding='utf-8-sig')
            tree = parse(text)
            for e, ancestors in walk(tree):
                if e.key != 'add_equipment_production':
                    continue
                b = e.value
                eq = b.get('equipment', Block([]))
                hull = eq.get('type')
                if not data.naval(hull):
                    continue
                for tag, mtg, year in sorted(profiles):
                    if not mtg:
                        continue
                    if e not in list(active_entries(tree, mtg, year)):
                        continue
                    creator = eq.get('creator', tag)
                    version = eq.get('version_name')
                    variant = data.variants.get((creator, hull, version, mtg, year)) if version else None
                    design_hull = hull
                    if version and variant is None:
                        candidates = [v for (c,h,n,m,y),v in data.variants.items()
                            if (c,n,m,y) == (creator,version,mtg,year) and
                            data.hull(h).get('archetype', h) == data.hull(hull).get('archetype', hull)]
                        if len(candidates) == 1:
                            variant = candidates[0]
                            design_hull = variant.get('type')
                    if version and variant is None:
                        raise ValueError(f'Missing {creator} {hull} {version!r} for {path.name}:{e.line}')
                    cost = data.cost(design_hull, variant)
                    progress = number(b.get('progress'))
                    if not 0 <= progress <= 1:
                        raise ValueError(f'Invalid progress {progress}: {path}:{e.line}')
                    records.append(dict(country=tag, creator=creator, year=year, mtg=mtg,
                        source=str(Path(relative) / path.name).replace('\\', '/'), line=e.line,
                        name=b.get('name', version or hull), equipment=hull, variant=version,
                        design_equipment_type=design_hull,
                        progress=progress, queued_amount=b.get('amount'), design_cost_ic=round(cost, 6),
                        invested_ic=round(cost * progress, 6), manufacturer=b.get('industrial_manufacturer'),
                        original_script=text[e.start:e.end]))
                removals[path].append((e.start, e.end, '# TFR: starting naval production removed; invested IC recorded in docs/naval-starting-production.json'))
    return records, removals


def write_report(records, countries):
    totals = defaultdict(lambda: [0, Decimal(0)])
    for r in records:
        key = (r['year'], r['mtg'], r['country'])
        totals[key][0] += 1
        totals[key][1] += Decimal(str(r['invested_ic']))
    def fmt(value):
        return f"{Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,.2f}"
    payload = dict(method='design_cost_ic * progress; queued_amount does not multiply progress',
        cost_basis='Mod hull + modules after compatibility fixes; excludes MIO/national/technology cost modifiers.',
        totals=[dict(year=y, mtg=m, country=t, production_lines=n, invested_ic=float(round(ic, 6))) for (y,m,t),(n,ic) in sorted(totals.items())],
        countries_with_zero_invested_ic={str(y): sorted(set(countries) - {r['country'] for r in records if r['year']==y and r['invested_ic']>0}) for y in (1936,1939)},
        lines=records)
    (ROOT / 'docs/naval-starting-production.json').write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    lines = ['# IC investit în producția navală inițială', '',
        'Calcul: costul complet al design-ului × progresul navei curente. Cantitatea din coadă nu multiplică IC-ul deja investit.', '',
        'Costurile provin din hull-urile și modulele modului, după corecțiile de compatibilitate. Nu includ reduceri de cost de la MIO, idei sau tehnologii. Navele și convoaiele cu progres zero au 0 IC investit.', '',
        'Datele originale ale liniilor eliminate sunt păstrate în `naval-starting-production.json`.', '']
    lines += ['Țările care nu apar în tabelul unui scenariu au 0 IC investit în producția navală inițială. Lista completă este inclusă în JSON.', '']
    for year in sorted({r['year'] for r in records}):
        for mtg in (True, False):
            group = [r for r in records if r['year'] == year and r['mtg'] == mtg]
            if not group:
                continue
            lines += [f'## {year} — {"Man the Guns" if mtg else "Legacy (fără Man the Guns)"}', '',
                '| Țară | Linii navale eliminate | IC investit |', '|---|---:|---:|']
            for (y,m,t),(n,ic) in sorted(totals.items()):
                if y == year and m == mtg:
                    lines.append(f'| {t} | {n} | {fmt(ic)} |')
            lines += ['', '| Țară | Navă / design | Cost IC | Progres | IC investit |', '|---|---|---:|---:|---:|']
            for r in sorted(group, key=lambda r: (r['country'], r['source'], r['line'])):
                name = str(r['name']).replace('|', '/')
                lines.append(f'| {r["country"]} | {name} | {fmt(r["design_cost_ic"])} | {r["progress"]*100:g}% | {fmt(r["invested_ic"])} |')
            lines += ['']
    (ROOT / 'docs/naval-starting-production.md').write_text('\n'.join(lines), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--remove-production', action='store_true')
    parser.add_argument('--designs-only', action='store_true')
    args = parser.parse_args()
    data = NavalData()
    design_tree = parse((ROOT / 'common/scripted_effects/tfr_navy_designs.txt').read_text(encoding='utf-8-sig'))
    fixed = []
    for e, _ in walk(design_tree):
        if e.key == 'create_equipment_variant':
            issues = data.issues(e.value.get('type'), e.value)
            if issues:
                fixed.append(dict(name=e.value.get('name'), type=e.value.get('type'), issues=issues))
    historical = []
    for tag, e, path, ancestors in data.history_variants:
        if e.value.get('type', '').startswith('ship_hull_'):
            issues = data.issues(e.value.get('type'), e.value)
            if issues:
                historical.append(dict(country=tag, source=path.name, line=e.line,
                    name=e.value.get('name'), type=e.value.get('type'), issues=issues))
    (ROOT / 'docs/naval-design-audit.json').write_text(json.dumps(dict(fixed=fixed, historical=historical), indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'Fixed designs invalid: {len(fixed)}; historical designs invalid: {len(historical)}')
    print('Fixed design issues:', json.dumps(fixed, ensure_ascii=False))
    print('Historical issue categories:', Counter(i[0] for r in historical for i in r['issues']))
    if args.designs_only:
        return
    records, removals = inventory(data)
    if not records and (ROOT / 'docs/naval-starting-production.json').exists():
        print('No starting naval production remains. Preserved the original IC report.')
        return
    write_report(records, data.countries)
    print(f'Naval starting production: {len(records)} lines in {len(removals)} files')
    print('1936 MTG totals:', {t: round(sum(r['invested_ic'] for r in records if r['country']==t and r['year']==1936 and r['mtg']), 2) for t in sorted({r['country'] for r in records if r['year']==1936 and r['mtg']})})
    if args.remove_production:
        for path, spans in removals.items():
            raw = path.read_bytes()
            bom = raw.startswith(b'\xef\xbb\xbf')
            text = raw.decode('utf-8-sig')
            # Source character positions were calculated with universal newlines.
            newline = '\r\n' if '\r\n' in text else '\n'
            text = text.replace('\r\n', '\n')
            updated = replace_spans(text, spans)
            parse(updated)
            destination = ROOT / path.relative_to(ROOT if path.is_relative_to(ROOT) else VANILLA)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((b'\xef\xbb\xbf' if bom else b'') + updated.replace('\n', newline).encode('utf-8'))
        assert not inventory(NavalData())[0], 'Naval starting production remains'
        print('Removed all historical naval production; verification passed.')


if __name__ == '__main__':
    main()
