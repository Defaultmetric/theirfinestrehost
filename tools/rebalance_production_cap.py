"""Scale country production efficiency cap sources to the 7/10 machine-tool balance.

Run once with --apply; subsequent runs verify the saved manifest without reapplying.
Signed offsets scale together so removing a penalty still cancels it exactly.
Technology, base game constants, gain/retention and host balancing tools are excluded.
"""
from pathlib import Path
from decimal import Decimal
import hashlib
import json
import re
import sys

from hoi4_script import Block, parse, walk, replace_spans

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'docs/production_cap_rebalance.json'
KEY = 'production_factory_max_efficiency_factor'
NUMBER = re.compile(r'-?(?:\d+(?:\.\d*)?|\.\d+)\Z')
OPERATIONS = {'set_variable', 'add_to_variable', 'subtract_from_variable',
              'set_temp_variable', 'add_to_temp_variable', 'subtract_from_temp_variable',
              'clamp_variable', 'clamp_temp_variable', 'check_variable', 'check_temp_variable'}


def canonical(value):
    return value.removeprefix('var:').split('.')[-1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    if MANIFEST.exists():
        report = json.loads(MANIFEST.read_text(encoding='utf-8'))
        for item in report['files']:
            assert digest((ROOT / item['path']).read_bytes()) == item['after_sha256'], item['path']
        print(f"Verified {report['changes']} edits in {len(report['files'])} files; no second scaling applied.")
        return
    files = [p for folder in ('common', 'events', 'history') for p in (ROOT / folder).rglob('*.txt')]
    sources = {p: p.read_bytes().decode('utf-8') for p in files}
    variables = set()
    # Resolve the actual variables used by dynamic modifiers, including short custom names.
    for p, source in sources.items():
        if p.parent.name != 'dynamic_modifiers':
            continue
        for match in re.finditer(r'(?m)^\s*' + KEY + r'\s*=\s*([^\s#{}]+)', source):
            if not NUMBER.fullmatch(match[1]):
                variables.add(canonical(match[1]))
    variables = {v for v in variables if not v.startswith('Horst_tool_')}
    report = {'ratio': '0.7', 'changes': 0, 'variables': sorted(variables), 'files': []}
    pending = []
    for p, source in sources.items():
        relative = p.relative_to(ROOT).as_posix()
        if relative.startswith(('common/technologies/', 'common/defines/', 'common/modifiers/')) or 'hosttool' in p.name.lower() or p.name == 'Horst_tool_modifiers.txt':
            continue
        if KEY not in source and not any(v in source for v in variables):
            continue
        # Some shipped files already lack trailing braces. Parse with virtual
        # closing braces while preserving their existing structure byte for byte.
        suffix = ''
        for attempt in range(10):
            try:
                tree = parse(source + suffix)
                break
            except ValueError as error:
                if str(error) != 'Unclosed block':
                    raise ValueError(f'{relative}: {error}') from error
                suffix += '\n}'
        else:
            raise ValueError(f'{relative}: cannot parse existing source')
        edits = {}
        details = []
        for entry, ancestors in walk(tree):
            if isinstance(entry.value, Block) or not NUMBER.fullmatch(entry.value):
                continue
            parent = ancestors[-1] if ancestors else None
            operation = next((a for a in reversed(ancestors) if a.key in OPERATIONS), None)
            direct = entry.key == KEY
            variable = canonical(entry.key) in variables and operation is not None
            explicit = (parent is not None and parent.key in OPERATIONS
                        and entry.key in {'value', 'min', 'max'}
                        and canonical(str(parent.value.get('var', ''))) in variables)
            # Multipliers are dimensionless; only offsets/limits scale.
            if not (direct or variable or explicit):
                continue
            if any(a.key in {'multiply_variable', 'divide_variable', 'multiply_temp_variable', 'divide_temp_variable'} for a in ancestors):
                continue
            old = Decimal(entry.value)
            if old == 0:
                continue
            new = format(old * Decimal('0.7'), 'f').rstrip('0').rstrip('.')
            start = entry.end - len(entry.value)
            assert source[start:entry.end] == entry.value
            edits[start] = (start, entry.end, new)
            details.append({'line': entry.line, 'key': entry.key, 'before': entry.value, 'after': new})
        if not edits:
            continue
        updated = replace_spans(source, edits.values())
        parse(updated + suffix)
        before, after = source.encode('utf-8'), updated.encode('utf-8')
        report['files'].append({'path': relative, 'before_sha256': digest(before),
                                'after_sha256': digest(after), 'edits': details})
        report['changes'] += len(edits)
        pending.append((p, after))
    if '--apply' in sys.argv:
        for p, data in pending:
            p.write_bytes(data)
        MANIFEST.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f"{'Applied' if '--apply' in sys.argv else 'Planned'} {report['changes']} edits in {len(pending)} files.")


if __name__ == '__main__':
    main()
