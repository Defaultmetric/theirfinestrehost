"""Remove legacy volunteer capacity rewards without removing unrelated mechanics.

Dry run by default. --apply writes overrides into the mod, never into the game.
Original bytes and a manifest are backed up outside the mod before any writes.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT.parents[3] / 'common' / 'Hearts of Iron IV'
FOLDERS = ('common/ideas', 'common/dynamic_modifiers', 'common/country_leader',
           'common/unit_leader', 'common/modifiers', 'common/national_focus',
           'common/decisions', 'common/scripted_effects', 'events', 'common/on_actions',
           'common/characters', 'common/doctrines')
CAPACITY = {'send_volunteer_size', 'send_volunteer_factor', 'air_volunteer_cap'}
THRESHOLDS = {'send_volunteer_divisions_required', 'send_volunteers_tension'}
PERMISSIONS = {'can_send_volunteers', 'can_send_volunteer'}
PROTECTED = {'common/ideas/tfr_scw_volunteers.txt',
             'common/dynamic_modifiers/tfr_scw_volunteers.txt',
             'common/scripted_effects/tfr_scw_volunteers.txt',
             'common/on_actions/tfr_scw_volunteers.txt'}
LEX = re.compile(r'#[^\n]*|"(?:\\.|[^"\\])*"|>=|<=|!=|[{}=<>]|[^\s{}=<>]+')
OPS = {'=', '<', '>', '<=', '>=', '!='}


@dataclass
class Entry:
    key: str
    start: int
    end: int
    value: str = ''
    value_start: int = 0
    value_end: int = 0
    children: list[Entry] | None = None
    deleted: bool = False
    replacement: str | None = None
    lost_reward: bool = False
    closed: bool = True
    verbatim: str | None = None

    def active(self):
        return [e for e in (self.children or []) if not e.deleted]

    def get(self, key):
        return next((e for e in self.active() if e.key == key), None)


def parse(text):
    tokens = [m for m in LEX.finditer(text) if not m.group().startswith('#')]
    pos = 0

    def block():
        nonlocal pos
        entries = []
        while pos < len(tokens) and tokens[pos].group() != '}':
            first = tokens[pos]
            if pos + 1 >= len(tokens) or tokens[pos + 1].group() not in OPS:
                entries.append(Entry('_', first.start(), first.end(), first.group().strip('"'), first.start(), first.end()))
                pos += 1
                continue
            key = first.group()
            pos += 2
            value = tokens[pos]
            if value.group() == '{':
                pos += 1
                children = block()
                closed = pos < len(tokens)
                assert not closed or tokens[pos].group() == '}', key
                end = tokens[pos].end() if closed else len(text)
                if closed:
                    pos += 1
                # Some shipped files use implicit EOF closure. Preserve their existing structure.
                entries.append(Entry(key, first.start(), end, children=children, closed=closed))
            else:
                entries.append(Entry(key, first.start(), value.end(), value.group().strip('"'), value.start(), value.end()))
                pos += 1
        return entries

    result = block()
    while pos < len(tokens):
        # Preserve pre-existing stray top-level closing braces without inventing new ones.
        token = tokens[pos]
        assert token.group() == '}'
        result.append(Entry('_', token.start(), token.end(), '}', token.start(), token.end()))
        pos += 1
        result.extend(block())
    return result


def walk(entries):
    for entry in entries:
        yield entry
        if entry.children is not None:
            yield from walk(entry.children)


def bonus(entry):
    if entry.children is not None:
        return False
    if entry.key in PERMISSIONS:
        # Legacy negative overrides can also block an approved allocation.
        return entry.value in ('yes', 'no')
    if entry.key not in CAPACITY | THRESHOLDS:
        return False
    try:
        number = float(entry.value)
    except ValueError:
        return True  # A variable-backed modifier can grant capacity later.
    return number > 0 if entry.key in CAPACITY else number < 0


def orphaned_relation_rule(entry):
    # An override needs at least one actual rule, in addition to its target or
    # trigger. Removing can_send_volunteers can otherwise leave a native error.
    return (entry.key in {'add_relation_rule_override', 'remove_relation_rule_override'}
            and entry.children is not None
            and all(e.key in {'target', 'trigger', 'usage_desc'} for e in entry.active()))


def strip_bonuses(entries):
    for entry in entries:
        if bonus(entry):
            entry.deleted = entry.lost_reward = True
        elif entry.children is not None:
            strip_bonuses(entry.children)
            entry.lost_reward = any(e.lost_reward for e in entry.children)
            if entry.lost_reward and entry.key in {'modifier', 'rule', 'set_rule', 'clear_rule'} and not entry.active():
                entry.deleted = True
            if entry.lost_reward and entry.key in {'add_rule', 'remove_rule'}:
                if all(e.key in {'target', 'trigger', 'usage_desc'} for e in entry.active()):
                    entry.deleted = True
            if orphaned_relation_rule(entry):
                entry.deleted = True


def render(text, entries):
    edits = []
    def collect(items):
        for e in items:
            if e.deleted:
                start, end = e.start, e.end
                line_start = text.rfind('\n', 0, start) + 1
                line_end = text.find('\n', end)
                line_end = len(text) if line_end < 0 else line_end + 1
                if not text[line_start:start].strip() and not text[end:line_end].split('#', 1)[0].strip():
                    start, end = line_start, line_end
                edits.append((start, end, ''))
            elif e.verbatim is not None:
                edits.append((e.start, e.end, e.verbatim))
            elif e.replacement is not None:
                edits.append((e.value_start, e.value_end, e.replacement))
            elif e.children is not None:
                collect(e.children)
    collect(entries)
    # Adjacent one-line deletions can share whitespace, but must not erase live tokens.
    edits.sort()
    merged = []
    for start, end, replacement in edits:
        if merged and start < merged[-1][1]:
            assert not replacement and not merged[-1][2], 'Overlapping replacements'
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]), '')
        else:
            merged.append((start, end, replacement))
    for start, end, replacement in reversed(merged):
        text = text[:start] + replacement + text[end:]
    return text


def canonical(entries):
    """Compare the planned AST with the rendered result, independently of whitespace."""
    result = []
    for entry in entries:
        if entry.deleted:
            continue
        if entry.verbatim is not None:
            result.extend(canonical(parse(entry.verbatim)))
        elif entry.children is not None:
            result.append((entry.key, canonical(entry.children)))
        else:
            value = entry.replacement.strip('"') if entry.replacement is not None else entry.value
            result.append((entry.key, value))
    return result


def sources(folder, game=GAME, root=ROOT):
    paths = {p.relative_to(game).as_posix().lower(): p for p in (game / folder).rglob('*.txt')}
    paths.update({p.relative_to(root).as_posix().lower(): p for p in (root / folder).rglob('*.txt')})
    return paths


def prepare(root=ROOT, game=GAME):
    loaded = {}
    for folder in FOLDERS:
        for rel, path in sources(folder, game, root).items():
            if rel in PROTECTED:
                continue
            raw = path.read_bytes()
            text = raw.decode('utf-8-sig', errors='surrogateescape')
            if not any(key in text for key in CAPACITY | THRESHOLDS | PERMISSIONS | {'relation_rule_override'}):
                continue
            try:
                entries = parse(text)
            except (AssertionError, IndexError) as error:
                raise ValueError(f'Cannot parse {path}: {error}') from error
            if not any(bonus(e) or orphaned_relation_rule(e) for e in walk(entries)):
                continue
            strip_bonuses(entries)
            loaded[rel] = (path, raw, text, entries)

    # A spirit that retains any non-volunteer effect, callback or rule is preserved.
    metadata = {'name', 'picture', 'allowed', 'allowed_civil_war', 'removal_cost', 'available', 'cancel', 'ledger', 'visible'}
    empty_ideas = set()
    for rel, (_, _, _, entries) in loaded.items():
        if not rel.startswith('common/ideas/'):
            continue
        for top in entries:
            for category in top.active():
                for idea in category.active():
                    if idea.lost_reward and all(e.key in metadata for e in idea.active()):
                        empty_ideas.add(idea.key)

    # Empty spirits can still be used as flags by unrelated mechanics. Keep such assignments.
    gated_ideas = set()
    for folder in ('common', 'events', 'history'):
        for _, path in sources(folder, game, root).items():
            text = path.read_text(encoding='utf-8-sig', errors='surrogateescape')
            gated_ideas.update(re.findall(r'\bhas_idea\s*=\s*([A-Za-z0-9_]+)', re.sub(r'#[^\n]*', '', text)))
    removable_ideas = empty_ideas - gated_ideas

    # Inspect all focus files, including those whose reward only adds a spirit.
    focus_files = sources('common/national_focus', game, root)
    for rel, path in focus_files.items():
        if rel not in loaded:
            raw = path.read_bytes()
            text = raw.decode('utf-8-sig', errors='surrogateescape')
            loaded[rel] = (path, raw, text, parse(text))
    focuses = {}
    removed = {}
    for rel, (_, _, _, entries) in loaded.items():
        if not rel.startswith('common/national_focus/'):
            continue
        for focus in walk(entries):
            if focus.key not in {'focus', 'shared_focus', 'joint_focus'} or not focus.get('id'):
                continue
            ident = focus.get('id').value
            focuses[ident] = focus
            reward = focus.get('completion_reward')
            if not reward:
                continue
            for e in walk(reward.children):
                if e.key in {'add_ideas', 'show_ideas_tooltip'}:
                    if e.children is None and e.value in removable_ideas:
                        e.deleted = e.lost_reward = True
                    elif e.children is not None:
                        for item in e.children:
                            if item.key == '_' and item.value in removable_ideas:
                                item.deleted = item.lost_reward = True
                        if not e.active() and any(item.deleted for item in e.children):
                            e.deleted = e.lost_reward = True
                elif e.key == 'add_timed_idea' and e.get('idea') and e.get('idea').value in removable_ideas:
                    e.deleted = e.lost_reward = True
            # Only remove ordinary focuses reduced to no reward and with one clear prerequisite group.
            prerequisites = [e for e in focus.active() if e.key == 'prerequisite']
            if focus.key == 'focus' and any(e.lost_reward for e in walk(reward.children)) and not reward.active():
                if len(prerequisites) == 1 and prerequisites[0].active() and all(e.key == 'focus' for e in prerequisites[0].active()):
                    parents = [e.value for e in prerequisites[0].active()]
                    removed[ident] = {'parents': parents, 'file': rel}

    def parents(ident, seen=frozenset()):
        if ident not in removed:
            return [ident]
        assert ident not in seen, 'Cyclic removed focus ancestry'
        return list(dict.fromkeys(p for value in removed[ident]['parents'] for p in parents(value, seen | {ident})))

    # Preserve absolute positions when a removed focus served as a layout anchor.
    for ident, focus in focuses.items():
        if ident in removed:
            focus.deleted = True
            continue
        anchor = focus.get('relative_position_id')
        if anchor and anchor.value in removed:
            target = anchor.value
            dx = dy = 0
            while target in removed:
                old = focuses[target]
                dx += float(old.get('x').value) if old.get('x') else 0
                dy += float(old.get('y').value) if old.get('y') else 0
                old_anchor = old.get('relative_position_id')
                target = old_anchor.value if old_anchor else None
            if target:
                anchor.replacement = target
            else:
                anchor.deleted = True
            for key, delta in [('x', dx), ('y', dy)]:
                coordinate = focus.get(key)
                assert coordinate is not None or delta == 0, (ident, key)
                if coordinate and delta:
                    coordinate.replacement = f'{float(coordinate.value) + delta:g}'
        for mutex in [e for e in focus.active() if e.key == 'mutually_exclusive']:
            for e in mutex.children:
                if e.key == 'focus' and e.value in removed:
                    e.deleted = True
            if not mutex.active():
                mutex.deleted = True

    # Update mechanical references and AI focus queues, without renaming idea IDs.
    for folder in ('common', 'events', 'history'):
        for rel, path in sources(folder, game, root).items():
            if rel in PROTECTED:
                continue
            if rel not in loaded:
                raw = path.read_bytes()
                text = raw.decode('utf-8-sig', errors='surrogateescape')
                if not any(re.search(r'\b' + re.escape(fid) + r'\b', text) for fid in removed):
                    continue
                loaded[rel] = (path, raw, text, parse(text))
            for e in walk(loaded[rel][3]):
                if e.key in {'focus', 'has_completed_focus', 'complete_national_focus', 'unlock_national_focus'} and e.children is None and e.value in removed and not e.deleted:
                    targets = parents(e.value)
                    if len(targets) == 1:
                        e.replacement = targets[0]
                    elif e.key == 'focus':
                        e.verbatim = ' '.join(f'focus = {target}' for target in targets)
                    elif e.key == 'has_completed_focus':
                        e.verbatim = 'OR = { ' + ' '.join(f'has_completed_focus = {target}' for target in targets) + ' }'
                    else:
                        raise ValueError(f'Cannot safely retarget {e.key} = {e.value} in {rel}')
                elif e.key == '_' and e.value in removed and rel.startswith('common/ai_strategy_plans/'):
                    e.deleted = True
                elif e.key in removed and rel.startswith('common/ai_strategy_plans/'):
                    e.deleted = True

    # The French policy now controls domestic support, independently of allocated troops.
    french_rel = 'common/decisions/fra.txt'
    if french_rel not in loaded:
        path = sources('common/decisions', game, root)[french_rel]
        raw = path.read_bytes()
        text = raw.decode('utf-8-sig', errors='surrogateescape')
        loaded[french_rel] = (path, raw, text, parse(text))
    french_decisions = loaded[french_rel][3]
    for e in walk(french_decisions):
        if e.key == 'FRA_ban_covert_intervention' and e.get('available'):
            available = e.get('available')
            assert any(item.key == 'has_volunteers_amount_from' for item in walk(available.children))
            available.deleted = True

    changes = {}
    for rel, (path, raw, text, entries) in loaded.items():
        updated = render(text, entries)
        if updated == text:
            continue
        reparsed = parse(updated)
        assert canonical(reparsed) == canonical(entries), f'Rendered script differs from planned edits: {rel}'
        assert sum(not e.closed for e in walk(reparsed)) == sum(not e.closed for e in walk(entries) if not e.deleted), rel
        assert sum(e.key == '_' and e.value == '}' for e in walk(reparsed)) == sum(e.key == '_' and e.value == '}' for e in walk(entries) if not e.deleted), rel
        # Retain the original virtual path and byte encoding, including BOM and line endings.
        virtual_path = path.relative_to(root) if path.is_relative_to(root) else path.relative_to(game)
        data = (b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b'') + updated.encode('utf-8', errors='surrogateescape')
        changes[virtual_path.as_posix()] = (path, data)

    rel = 'localisation/replace/France_TFR_l_english.yml'
    path = root / rel
    raw = path.read_bytes()
    text = raw.decode('utf-8-sig')
    newline = '\r\n' if '\r\n' in text else '\n'
    french_text = {
        'FRA_intervention_in_spain_tt': 'Gain access to decisions that boost §YWar Support§! at the cost of §YStability§!.',
        'FRA_allow_covert_intervention': 'Mobilize Public Support for Spain',
        'FRA_allow_covert_intervention_desc': 'Build public support for Spain. This increases War Support while reducing Stability for as long as the policy remains active.',
        'FRA_ban_covert_intervention': 'End Public Mobilization for Spain',
        'FRA_ban_covert_intervention_desc': 'End the public mobilization campaign and remove its War Support and Stability modifiers.',
    }
    updated = text
    for key, value in french_text.items():
        line = f' {key}:0 "{value}"'
        pattern = r'(?m)^[ \t]*' + re.escape(key) + r':[^\r\n]*'
        if re.search(pattern, updated):
            updated = re.sub(pattern, lambda _: line, updated)
        else:
            updated = updated.rstrip('\r\n') + newline + line + newline
    if updated != text:
        changes[rel] = (path, (b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b'') + updated.encode('utf-8'))
    return changes, removed, empty_ideas, gated_ideas & empty_ideas


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    assert (GAME / 'common/ideas').is_dir(), GAME
    changes, removed, empty, gated = prepare()
    summary = {'files': len(changes), 'removed_focuses': removed, 'empty_spirits': sorted(empty), 'retained_gate_spirits': sorted(gated)}
    if args.apply:
        backup = Path.home() / '.codex/backups/tfr-volunteer-capacity' / datetime.now().strftime('%Y%m%dT%H%M%S')
        for rel, (source, _) in changes.items():
            destination = ROOT / rel
            saved = backup / ('mod' if destination.exists() else 'inherited') / rel
            saved.parent.mkdir(parents=True, exist_ok=True)
            saved.write_bytes(source.read_bytes())
        for rel, (_, data) in changes.items():
            destination = ROOT / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        backup.mkdir(parents=True, exist_ok=True)
        (backup / 'manifest.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
        summary['backup'] = str(backup)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
