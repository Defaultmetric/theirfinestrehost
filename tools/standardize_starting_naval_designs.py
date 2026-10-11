"""Remove historical MTG start designs; bind every starting ship to a template.

Legacy DLC-off and 1939 designs are preserved. Counts, names, officers, ports
and grouping stay intact. Smaller fleets adopt standard stats without recompaction.
"""
from collections import Counter, defaultdict
import hashlib
import json
import re

from compact_starting_fleets import registry, resolve, role, formatted_template
from group_starting_fleets import selected_oobs, freeze, ship_hashes
from hoi4_script import Block, parse, replace_spans, walk
from integrate_naval_tech_bonuses import write, sha, DESIGNS
from naval_startup_audit import NavalData, ROOT, VANILLA, active_entries

REPORT = ROOT / 'docs/naval-standard-start-designs.json'
DATE = re.compile(r'^\d{4}\.\d+\.\d+')


def fingerprint(block):
    return json.dumps(freeze(block), sort_keys=True)


def templates():
    text = DESIGNS.read_text(encoding='utf-8-sig')
    return {e.value.get('name'): fingerprint(e.value) for e, _ in walk(parse(text))
            if e.key == 'create_equipment_variant'}


def main():
    assert not REPORT.exists(), 'Already standardized; use the validator.'
    data = NavalData()
    standard = templates()
    models = registry(data)
    country_sources = {tag: path.read_text(encoding='utf-8-sig') for tag, path in data.countries.items()}
    edits = defaultdict(list)
    prefixes = defaultdict(list)
    changed_files, removed, fleet_rows = {}, [], []
    file_plans = {}

    def save(relative, text, before_path):
        target = ROOT / relative
        before_raw = before_path.read_bytes()
        before = before_path.read_text(encoding='utf-8-sig')
        file_plans[relative] = (text, before_raw)
        newline = '\r\n' if b'\r\n' in before_raw else '\n'
        after_raw = (b'\xef\xbb\xbf' if before_raw.startswith(b'\xef\xbb\xbf') else b'') + text.replace('\n', newline).encode('utf-8')
        changed_files[relative] = dict(source_before=before, raw_before_sha256=hashlib.sha256(before_raw).hexdigest(),
            before_sha256=sha(before), after_sha256=sha(text), raw_after_sha256=hashlib.sha256(after_raw).hexdigest(),
            source_before_bom=before_raw.startswith(b'\xef\xbb\xbf'), source_before_newline='\r\n' if b'\r\n' in before_raw else '\n',
            original_source=str(before_path.relative_to(ROOT if before_path.is_relative_to(ROOT) else VANILLA)).replace('\\', '/'))

    for loaded, profiles, active, tree in selected_oobs(data):
        tag = next(iter(active))[0]
        before = loaded.read_text(encoding='utf-8-sig')
        changes, roles, bindings = [], set(), []
        old_ic = new_ic = 0
        for entry, _ in walk(tree):
            if entry.key != 'ship':
                continue
            ship = entry.value
            equipment = ship.get('equipment').entries()[0]
            owner = equipment.value.get('owner', tag)
            hull, variant = resolve(data, owner, equipment.key, equipment.value.get('version_name'))
            key = role(data, hull, variant, ship.get('definition'))
            model = models[key]
            roles.add(key)
            old_ic += data.cost(hull, variant)
            new_ic += float(model['unit_ic'])
            if equipment.key == model['hull'] and equipment.value.get('version_name') == model['name']:
                continue
            assert owner == tag, ('Foreign owned starting ship', tag, ship.get('name'))
            body = before[equipment.start:equipment.end]
            body = model['hull'] + body[len(equipment.key):]
            match = re.search(r'version_name\s*=\s*"[^"]*"', body)
            assert match
            body = body[:match.start()] + 'version_name = "' + model['name'] + '"' + body[match.end():]
            changes.append((equipment.start, equipment.end, body))
            bindings.append(dict(ship=ship.get('name'), role=key, owner=owner,
                hull_before=equipment.key, name_before=equipment.value.get('version_name'), hull_after=model['hull'], name_after=model['name']))
        relative = 'history/units/' + loaded.name
        if changes:
            if any(year == 1939 for _, _, year in profiles):
                # Finland uses one file for both scenarios; keep the 1939 copy.
                relative = 'history/units/' + loaded.stem + '_standard.txt'
                history = country_sources[tag]
                selectors = [(e, ancestors) for e, ancestors in walk(parse(history))
                             if e.key in ('oob', 'set_oob', 'set_naval_oob') and e.value.lower() == loaded.stem.lower()
                             and not any(DATE.match(a.key) for a in ancestors)]
                assert selectors
                for e, _ in selectors:
                    edits[tag].append((e.start, e.end, f'{e.key} = "{loaded.stem}_standard"'))
            after = replace_spans(before, changes)
            save(relative, after, loaded)
        else:
            after = before
        fleet_rows.append(dict(country=tag, source=relative, ships=sum(ship_hashes(tree).values()),
            updated=len(bindings), ic_before=old_ic, ic_after=new_ic, bindings=bindings))
        # All designs used by the OOB must exist before that OOB is read.
        existing = {e.value.get('name') for e in active_entries(parse(country_sources[tag]), True, 1936)
                    if e.key == 'create_equipment_variant' and data.naval(e.value.get('type', ''))
                    and fingerprint(e.value) == standard.get(e.value.get('name'))}
        missing = sorted(roles - {k for k, m in models.items() if m['name'] in existing})
        if missing:
            techs = {k: 'basic_ship_hull_' + kind for k, kind in
                     [('LD', 'light'), ('TD', 'light'), ('ASW', 'light'), ('LC', 'cruiser'), ('HC', 'cruiser'),
                      ('BB', 'heavy'), ('BC', 'heavy'), ('CV', 'carrier'), ('SS', 'submarine')]}
            lines = ['# TFR: only standard research designs at the MTG 1936 start.',
                     'if = {', '\tlimit = { has_dlc = "Man the Guns" }', '\tset_technology = { popup = no']
            lines += ['\t\t' + tech + ' = 1' for tech in sorted({techs[k] for k in missing})]
            lines.append('\t}')
            for key in missing:
                lines.extend('\t' + line for line in formatted_template(models[key]['script']))
                lines.append('\tset_country_flag = ' + models[key]['flag'])
            lines += ['}', '']
            prefixes[tag].append('\n'.join(lines))

    for tag, source in country_sources.items():
        tree = parse(source)
        historic = []
        for entry, ancestors in walk(tree):
            if entry.key != 'create_equipment_variant' or any(DATE.match(a.key) for a in ancestors):
                continue
            hull = entry.value.get('type', '')
            if not data.naval(hull) or fingerprint(entry.value) == standard.get(entry.value.get('name')):
                continue
            historic.append(entry)
            body = source[entry.start:entry.end]
            # Original conditional surroundings still govern legacy games.
            replacement = 'if = {\n\tlimit = { NOT = { has_dlc = "Man the Guns" } }\n' + body + '\n}'
            edits[tag].append((entry.start, entry.end, replacement))
        if historic:
            historic_starts = {e.start for e in historic}

            def extract(block):
                entries = block.entries()
                result = []
                index = 0
                while index < len(entries):
                    entry = entries[index]
                    if entry.key.lower() == 'if':
                        chain = [entry]
                        while index + 1 < len(entries) and entries[index + 1].key.lower() in ('else_if', 'else'):
                            index += 1
                            chain.append(entries[index])
                        children = [extract(e.value) for e in chain]
                        if any(children):
                            for branch, child in zip(chain, children):
                                limit = branch.value.entries('limit')
                                text = source[limit[0].start:limit[0].end] + '\n' if limit else ''
                                result.append(branch.key + ' = {\n' + text + child + '\n}')
                    elif entry.start in historic_starts:
                        result.append(source[entry.start:entry.end])
                    index += 1
                return '\n'.join(result)

            deferred = 'if = {\n\tlimit = { has_dlc = "Man the Guns" }\n' + extract(tree) + '\n}\n'
            dates = [e for e in tree.entries() if e.key == '1939.1.1']
            if dates:
                insertion = source.index('{', dates[0].start) + 1
                edits[tag].append((insertion, insertion, '\n# TFR: historical designs retained only for the 1939 scenario.\n' + deferred))
            else:
                edits[tag].append((len(source), len(source), '\n1939.1.1 = {\n' + deferred + '}\n'))
            active_starts = {e.start for e in active_entries(tree, True, 1936)}
            removed += [dict(country=tag, name=e.value.get('name'), hull=e.value.get('type'))
                        for e in historic if e.start in active_starts]
        if edits[tag] or prefixes[tag]:
            after = '\n'.join(prefixes[tag]) + replace_spans(source, edits[tag])
            parse(after)
            save('history/countries/' + data.countries[tag].name, after, data.countries[tag])

    # Finish planning and parsing before mutating any game file.
    for relative, (text, raw) in file_plans.items():
        target = ROOT / relative
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        write(target, text)
    # Keep prior audits immutable as baselines, and record explicit migrations.
    grouping_path = ROOT / 'docs/naval-starting-fleet-grouping.json'
    grouping = json.loads(grouping_path.read_text(encoding='utf-8'))
    for row in grouping['countries']:
        target = next(r for r in fleet_rows if r['country'] == row['country'])
        if not target['updated']:
            continue
        row['source_before_standardization'] = row['source']
        row['raw_after_before_standardization'] = row['raw_after_sha256']
        row['ship_fingerprints_before_standardization'] = row['ship_fingerprints']
        row['source'] = target['source']
        path = ROOT / row['source']
        row['after_sha256'] = sha(path.read_text(encoding='utf-8-sig'))
        row['raw_after_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        row['ship_fingerprints'] = dict(ship_hashes(parse(path.read_text(encoding='utf-8-sig'))))
    grouping['standard_design_migration'] = 'docs/naval-standard-start-designs.json; same ships and grouping, standard model bindings.'
    write(grouping_path, json.dumps(grouping, indent=2, ensure_ascii=False) + '\n')
    for relative, records_key in [('docs/naval-starting-fleets.json', 'source_hashes'), ('docs/naval-treaty-removal.json', 'files')]:
        path = ROOT / relative
        report = json.loads(path.read_text(encoding='utf-8'))
        records = report[records_key].items() if records_key == 'source_hashes' else ((r['source'], r) for r in report[records_key])
        for name, hashes in records:
            if name in changed_files:
                assert hashes['after'] == changed_files[name]['before_sha256'], name
                hashes['after'] = changed_files[name]['after_sha256']
        report['standard_design_migration'] = 'docs/naval-standard-start-designs.json; history template cleanup, original compaction budgets unchanged.'
        write(path, json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    result = dict(year=1936, mtg=True, removed=removed, countries=fleet_rows, files=changed_files,
                  policy='Only exact research templates at start. No ship-count changes; 11 smaller fleets adopt standard model statistics. Legacy and 1939 variants preserved.')
    write(REPORT, json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(f'Removed {len(removed)} historical MTG starting designs; rebound {sum(r["updated"] for r in fleet_rows)} ships in {sum(bool(r["updated"]) for r in fleet_rows)} countries.')


if __name__ == '__main__':
    main()
