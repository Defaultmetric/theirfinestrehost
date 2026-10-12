"""Repair the concrete HOI4 1.19 compatibility errors reported by error.log.

Vanilla files are overridden in the mod; the Steam game installation is untouched.
--check verifies the repaired effective overlay without changing any files.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT.parents[3] / 'common' / 'Hearts of Iron IV'
LOG = Path.home() / 'Documents/Paradox Interactive/Hearts of Iron IV/logs/error.log'
MANIFEST = ROOT / 'docs/log-compatibility-repairs.json'
TOKENS = re.compile(r'#[^\n]*|"(?:\\.|[^"\\])*"|[{}]|[^\s{}]+')
STATES = {
    '870-North West Australia.txt': '870-Pilbara-Kimberley.txt',
    '871-South West Australia.txt': '871-Esperence-Goldfields.txt',
    '873-South West Queensland.txt': '873-Channel Country.txt',
    '1074 - Central West Australia.txt': '1074 - Gibson Desert.txt',
}
MINE_FILES = ['common/decisions/POR.txt', 'common/national_focus/indonesia_joint.txt', 'common/national_focus/siam.txt']
HULL_TECH = {
    'ship_hull_light_1': 'early_ship_hull_light',
    'ship_hull_submarine_1': 'early_ship_hull_submarine',
    'ship_hull_cruiser_1': 'early_ship_hull_cruiser',
    'ship_hull_heavy_1': 'early_ship_hull_heavy',
    # TFR's first standard carrier uses hull_1, unlocked by the 1936 carrier tech.
    'ship_hull_carrier_1': 'basic_ship_hull_carrier',
    'ship_hull_light_2': 'basic_ship_hull_light',
    'ship_hull_submarine_2': 'basic_ship_hull_submarine',
    'ship_hull_cruiser_2': 'basic_ship_hull_cruiser',
    'ship_hull_heavy_2': 'basic_ship_hull_heavy',
    'ship_hull_carrier_2': 'basic_ship_hull_carrier',
    'ship_hull_cruiser_panzerschiff': 'panzerschiffe',
    'ship_hull_pre_dreadnought': 'pre_dreadnoughts',
    'ship_hull_cruiser_coastal_defense_ship': 'coastal_defense_ships',
    'ship_hull_cruiser_submarine': 'cruiser_submarines',
}


def active(text):
    return re.sub(r'#[^\n]*', '', text)


def effective_files(directory):
    return {**{p.relative_to(GAME).as_posix(): p for p in (GAME/directory).rglob('*.txt')},
            **{p.relative_to(ROOT).as_posix(): p for p in (ROOT/directory).rglob('*.txt')}}


def source(rel):
    return ROOT/rel if (ROOT/rel).exists() else GAME/rel


def blocks(text, key):
    """Return source offsets of named blocks, ignoring comments and quoted braces."""
    pattern = re.compile(r'\b' + re.escape(key) + r'\s*=\s*\{')
    ignored = [(m.start(), m.end()) for m in re.finditer(r'#[^\n]*|"(?:\\.|[^"\\])*"', text)]
    for m in pattern.finditer(text):
        if any(a <= m.start() < b for a, b in ignored):
            continue
        depth = 1
        for token in TOKENS.finditer(text, m.end()):
            if token.group() == '{': depth += 1
            elif token.group() == '}': depth -= 1
            if depth == 0:
                yield m.start(), token.end()
                break
        else:
            raise AssertionError(f'Unclosed {key} block')


def balanced(text):
    depth = 0
    for token in TOKENS.finditer(text):
        if token.group() == '{': depth += 1
        elif token.group() == '}': depth -= 1
        assert depth >= 0, 'Unexpected closing brace'
    assert depth == 0, 'Unclosed braces'


def apply():
    log = LOG.read_text(encoding='utf-8-sig')
    backup = Path.home()/'.codex/backups/tfr-log-compatibility'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup.mkdir(parents=True)
    (backup/'error-before-repairs.log').write_text(log, encoding='utf-8')
    changes = {}
    report = {'backup': str(backup), 'focus_checks': [], 'idea_checks': [], 'mine_modules': [], 'state_renames': [], 'naval_initialization': [], 'tooltips': []}

    def read(rel):
        if rel not in changes:
            changes[rel] = source(rel).read_text(encoding='utf-8-sig')
        return changes[rel]

    focus_ids = set()
    for p in effective_files('common/national_focus').values():
        focus_ids.update(re.findall(r'\bid\s*=\s*(\w+)', active(p.read_text(encoding='utf-8-sig'))))
    missing = set(re.findall(r'Invalid focus scripted in trigger\. has_completed_focus = (\w+) \(([^():]+):\d+:', log))
    for focus, rel in sorted(missing):
        assert focus not in focus_ids, f'{focus} is present; needs a different diagnosis'
        text = read(rel)
        pattern = re.compile(r'\bhas_completed_focus\s*=\s*' + re.escape(focus) + r'\b')
        matches = [m for m in pattern.finditer(text) if not text[text.rfind('\n',0,m.start())+1:m.start()].lstrip().startswith('#')]
        for m in reversed(matches):
            text = text[:m.start()] + f'always = no # TFR: {focus} is absent from the mod focus tree' + text[m.end():]
        changes[rel] = text
        report['focus_checks'].append({'file': rel, 'focus': focus, 'count': len(matches)})

    # The newer vanilla advisors still refer to a political branch removed by TFR.
    rel = 'common/characters/AST.txt'
    text, count = re.subn(r'has_idea\s*=\s*AST_monarchist_intervention_spirit\b',
                        'always = no # TFR: removed monarchist intervention branch', read(rel))
    changes[rel] = text
    report['idea_checks'].append({'file': rel, 'idea': 'AST_monarchist_intervention_spirit', 'count': count})

    # Mines are intentionally disabled in the mod. Keep the existing ship and other slots.
    for rel in MINE_FILES:
        text, count = re.subn(r'(\b\w+_slot\s*=\s*)ship_mine_(?:layer|sweeper)_1\b',
                             r'\1empty', read(rel))
        changes[rel] = text
        report['mine_modules'].append({'file': rel, 'count': count})

    # The mod's formable-decision file removed this decision. Remove only its UI tooltip.
    rel = 'common/national_focus/siam.txt'
    text = read(rel)
    for a, b in reversed(list(blocks(text, 'unlock_decision_tooltip'))):
        if re.search(r'\bdecision\s*=\s*form_pan_tai_empire\b', active(text[a:b])):
            text = text[:a] + '# TFR: Pan-Tai formable decision is disabled in this mod.' + text[b:]
            report['tooltips'].append({'file': rel, 'decision': 'form_pan_tai_empire'})
    changes[rel] = text

    # Standard starting designs were placed before country naval technology initialization.
    # HOI4 already force-unlocked these hulls implicitly with a warning. Initialize explicitly
    # before creation, keeping that effective starting technology and all fleet/design data.
    for p in sorted((ROOT/'history/countries').glob('*.txt')):
        rel = p.relative_to(ROOT).as_posix()
        text = read(rel)
        marker = '# TFR: standard 1936 designs must exist before the starting naval OOB loads.'
        if marker not in text or '# TFR: initialize standard fleet hulls before creating designs.' in text:
            if rel not in [x['file'] for x in report['focus_checks']]: changes.pop(rel, None)
            continue
        start = text.index(marker)
        # Only the leading standard-design block, before its corresponding naval OOB.
        end = text.index('set_naval_oob', start)
        hulls = set(re.findall(r'\btype\s*=\s*(ship_hull_\w+)', active(text[start:end])))
        assert hulls <= HULL_TECH.keys(), (rel, hulls-HULL_TECH.keys())
        techs = sorted({HULL_TECH[h] for h in hulls})
        line_start = text.rfind('\n', 0, start)+1
        indent = text[line_start:start]
        insert = '# TFR: initialize standard fleet hulls before creating designs.\n' + indent
        insert += 'set_technology = {\n' + ''.join(indent+'\t'+tech+' = 1\n' for tech in techs) + indent+'}\n'+indent
        changes[rel] = text[:start] + insert + text[start:]
        report['naval_initialization'].append({'file': rel, 'techs': techs, 'hulls': sorted(hulls)})

    for old, new in STATES.items():
        src, dest = ROOT/'history/states'/old, ROOT/'history/states'/new
        assert src.resolve().is_relative_to(ROOT.resolve()) and dest.resolve().is_relative_to(ROOT.resolve())
        if not src.exists(): continue
        assert not dest.exists(), f'Unexpected second mod file: {dest}'
        saved = backup/'history/states'/old
        saved.parent.mkdir(parents=True, exist_ok=True)
        saved.write_bytes(src.read_bytes())
        digest = hashlib.sha256(src.read_bytes()).hexdigest()
        src.rename(dest)
        report['state_renames'].append({'old': old, 'new': new, 'sha256': digest})

    for rel, text in changes.items():
        balanced(text)
        dest = ROOT/rel
        old_path = source(rel)
        old_data = old_path.read_bytes()
        data = text.encode('utf-8')
        if data == old_data: continue
        saved = backup/rel
        saved.parent.mkdir(parents=True, exist_ok=True)
        saved.write_bytes(old_data)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    report['files'] = sorted(changes)
    MANIFEST.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(f'Repaired {len(changes)} files; backup: {backup}')
    print(json.dumps({k: len(v) for k,v in report.items() if isinstance(v,list)}))


def check():
    report = json.loads(MANIFEST.read_text(encoding='utf-8'))
    for rel in report['files']:
        balanced((ROOT/rel).read_text(encoding='utf-8-sig'))
    for item in report['focus_checks']:
        assert not re.search(r'\bhas_completed_focus\s*=\s*'+item['focus']+r'\b', active((ROOT/item['file']).read_text(encoding='utf-8-sig'))), item
    for item in report['idea_checks']:
        assert not re.search(r'\bhas_idea\s*=\s*'+item['idea']+r'\b', active((ROOT/item['file']).read_text(encoding='utf-8-sig'))), item
    for item in report['mine_modules']:
        assert not re.search(r'\b\w+_slot\s*=\s*ship_mine_(?:layer|sweeper)_1\b', active((ROOT/item['file']).read_text(encoding='utf-8-sig'))), item
    # The entire effective state overlay must have unique IDs and province ownership.
    ids, provinces = {}, {}
    for rel,p in effective_files('history/states').items():
        text = active(p.read_text(encoding='utf-8-sig'))
        state_id = int(re.search(r'\bid\s*=\s*(\d+)',text).group(1))
        assert state_id not in ids, (state_id,rel,ids.get(state_id))
        ids[state_id] = rel
        province_block = re.search(r'\bprovinces\s*=\s*\{([^}]+)\}',text)
        for number in re.findall(r'\d+',province_block.group(1)):
            assert number not in provinces, (number,rel,provinces.get(number))
            provinces[number] = rel
    for item in report['state_renames']:
        assert not (ROOT/'history/states'/item['old']).exists()
        assert hashlib.sha256((ROOT/'history/states'/item['new']).read_bytes()).hexdigest()==item['sha256']
    for item in report['naval_initialization']:
        text = active((ROOT/item['file']).read_text(encoding='utf-8-sig'))
        marker = (ROOT/item['file']).read_text(encoding='utf-8-sig').index('# TFR: initialize standard fleet hulls')
        raw = (ROOT/item['file']).read_text(encoding='utf-8-sig')
        a,b = next((a,b) for a,b in blocks(raw,'set_technology') if a>marker)
        tech_end = b
        c,d = next((x,y) for x,y in blocks(raw,'create_equipment_variant') if x>tech_end)
        assert all(re.search(r'\b'+t+r'\s*=\s*1',active(raw[a:b])) for t in item['techs'])
        assert b<c
        original = (Path(report['backup'])/item['file']).read_text(encoding='utf-8-sig')
        before = [active(original[x:y]) for x,y in blocks(original,'create_equipment_variant')]
        after = [active(raw[x:y]) for x,y in blocks(raw,'create_equipment_variant')]
        assert before == after, f'Equipment definitions changed: {item["file"]}'
    print(f'PASS: {len(report["files"])} balanced scripts; unique IDs for {len(ids)} states and {len(provinces)} provinces; recorded invalid references removed; hulls initialized before designs.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    assert GAME.exists(), GAME
    if args.apply: apply()
    if args.check: check()
