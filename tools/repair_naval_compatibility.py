"""Preserve legacy ships while making historical naval variants valid."""
import json
import re
from collections import defaultdict

from hoi4_script import Block, parse, replace_spans
from naval_startup_audit import NavalData, ROOT, VANILLA

LEGACY = {'ship_hull_light_1', 'ship_hull_cruiser_1', 'ship_hull_heavy_1',
          'ship_hull_submarine_1', 'ship_hull_carrier_1'}


def source(path):
    raw = path.read_bytes()
    return raw.decode('utf-8-sig').replace('\r\n', '\n'), raw.startswith(b'\xef\xbb\xbf'), '\r\n' if b'\r\n' in raw else '\n'


def write(path, spans):
    text, bom, newline = source(path)
    updated = replace_spans(text, spans)
    parse(updated)
    target = ROOT / path.relative_to(ROOT if path.is_relative_to(ROOT) else VANILLA)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes((b'\xef\xbb\xbf' if bom else b'') + updated.replace('\n', newline).encode('utf-8'))


def main():
    data = NavalData()
    spans = defaultdict(list)
    categories = defaultdict(lambda: defaultdict(set))
    removed_limits = 0
    for tag, e, path, _ in data.history_variants:
        hull = e.value.get('type')
        if hull not in LEGACY:
            continue
        for kind, slot, mod in data.issues(hull, e.value):
            if kind == 'category':
                categories[hull][slot].add(data.modules[mod][0].get('category'))
    for hull in LEGACY:
        b, path = data.equipment[hull]
        for e in b.entries('module_count_limit'):
            if e.value.get('module'):
                spans[path].append((e.start, e.end, '# TFR: legacy historical hulls retain their original fitted modules.'))
                removed_limits += 1
        if hull in categories:
            slots = data.slot_map(hull)
            out = ['module_slots = {']
            for name, slot in slots.items():
                allowed = slot.get('allowed_module_categories', Block([])).atoms()
                allowed = allowed + sorted(categories[hull].get(name, set()) - set(allowed))
                out += [f'\t\t\t{name} = {{', f'\t\t\t\trequired = {slot.get("required", "no")}',
                    '\t\t\t\tallowed_module_categories = { ' + ' '.join(allowed) + ' }', '\t\t\t}']
            out.append('\t\t}')
            e = b.entries('module_slots')[0]
            spans[path].append((e.start, e.end, '\n'.join(out)))
    for path, edits in spans.items():
        write(path, edits)

    data = NavalData()
    spans = defaultdict(list)
    repairs = []
    for tag, e, path, _ in data.history_variants:
        hull = e.value.get('type')
        if not hull.startswith('ship_hull_'):
            continue
        modules = e.value.get('modules')
        if not isinstance(modules, Block):
            continue
        changes = {}
        # Mine modules were deliberately removed from the simplified navy.
        for slot in modules.entries():
            if slot.value.startswith('ship_mine_') and slot.value not in data.modules:
                changes[slot.key] = 'empty'
                slot.value = 'empty'
        for kind, slot, mod in data.issues(hull, e.value):
            if kind == 'category':
                current = modules.entries(slot)[0]
                allowed = data.slot_map(hull)[slot].get('allowed_module_categories').atoms()
                if 'ship_light_medium_battery' in allowed and data.modules[mod][0].get('category') in ('ship_light_battery', 'dp_light_battery'):
                    tier = re.search(r'_(\d+)$', mod).group(1)
                    replacement = f'ship_light_medium_battery_{tier}'
                    changes[slot] = replacement
                    current.value = replacement
        # Downgrade over-tier modules only on modern historical templates;
        # legacy hull loadouts above are preserved instead of being nerfed.
        for _ in range(8):
            problems = data.issues(hull, e.value)
            if not problems:
                break
            changed = False
            for kind, forbidden, rule in problems:
                if kind != 'count_limit' or forbidden not in data.modules:
                    continue
                category = data.modules[forbidden][0].get('category')
                match = re.search(r'_(\d+)$', forbidden)
                if not match:
                    continue
                tier = int(match.group(1))
                for slot in modules.entries():
                    if slot.value != forbidden:
                        continue
                    for lower in range(tier - 1, -1, -1):
                        candidate = forbidden[:match.start(1)] + str(lower)
                        if candidate in data.modules and data.modules[candidate][0].get('category') == category:
                            changes[slot.key] = candidate
                            slot.value = candidate
                            changed = True
                            break
            if not changed:
                raise ValueError(f'Cannot repair {tag} {e.value.get("name")}: {problems}')
        assert not data.issues(hull, e.value), (tag, e.value.get('name'), data.issues(hull, e.value))
        if changes:
            text, _, _ = source(path)
            for slot in modules.entries():
                if slot.key in changes:
                    spans[path].append((slot.start, slot.end, slot.key + ' = ' + slot.value))
            repairs.append(dict(country=tag, design=e.value.get('name'), hull=hull, changes=changes))
    for path, edits in spans.items():
        write(path, edits)
    (ROOT / 'docs/naval-compatibility-repairs.json').write_text(json.dumps(dict(legacy_module_limits_removed=removed_limits, historical_variant_repairs=repairs), indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'Removed {removed_limits} per-module restrictions from hidden legacy hulls; repaired {len(repairs)} historical variants in {len(spans)} country files.')


if __name__ == '__main__':
    main()
