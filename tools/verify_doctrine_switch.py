"""Exercise the generated scripts against a small doctrine-state model.

This checks script behavior and references; it does not replace an in-game test.
"""
from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
import random
import re
import sys
sys.dont_write_bytecode = True
from generate_doctrine_switch import ROOT, get, parse, read

D = Decimal
UNIT = D('0.00001')
EFFECTS = {}
for filename in ['TFR_doctrine_switch.txt', 'TFR_doctrine_switch_generated.txt']:
    EFFECTS.update(read(ROOT / 'common/scripted_effects' / filename))
DECISIONS = get(read(ROOT / 'common/decisions/TFR_doctrine_switch.txt'),
                'tfr_doctrine_reorganization')
GRANDS = {}
SUBS = {}
for filename in ['land_grand_doctrines.txt', 'sea_grand_doctrines.txt',
                 'air_grand_doctrines.txt']:
    GRANDS.update(read(ROOT / 'common/doctrines/grand_doctrines' / filename))
for path in (ROOT / 'common/doctrines/subdoctrines').rglob('*.txt'):
    SUBS.update(read(path))


def substitute(tree, replacements):
    if isinstance(tree, list):
        return [(substitute(k, replacements), substitute(v, replacements))
                for k, v in tree]
    if isinstance(tree, str):
        for old, new in replacements.items():
            tree = tree.replace(old, str(new))
    return tree


class Model:
    def __init__(self, folder, doctrine, tracks, selections, mastery):
        self.folder = folder
        self.doctrine = doctrine
        self.tracks = tracks
        self.selections = dict(zip(tracks, selections))
        self.mastery = dict(zip(tracks, map(D, mastery)))
        self.vars = {}
        self.xp = {'army': D(500), 'navy': D(500), 'air': D(500)}
        self.other_branch = {'unchanged': ("selected", D('123.45678'))}
        self.probes = 0
        self.flags = set()

    def value(self, expression):
        try:
            return D(expression)
        except Exception:
            return self.vars.get(expression, D(0))

    def condition(self, tree):
        results = []
        for key, value in tree:
            if key == 'OR':
                results.append(any(self.condition([entry]) for entry in value))
            elif key == 'NOT':
                results.append(not self.condition(value))
            elif key == 'has_any_grand_doctrine':
                results.append(value == self.folder and bool(self.doctrine))
            elif key.startswith('has_') and key.endswith('_experience >'):
                results.append(self.xp[key[4:].removesuffix('_experience >')] > self.value(value))
            elif key == 'has_mastery':
                self.probes += 1
                results.append(self.mastery[get(value, 'track')] >= self.value(get(value, 'amount')))
            elif key == 'check_variable':
                left, right = value[0]
                parts = left.split()
                if parts[-1] in ('>', '<'):
                    left, operator = parts
                    right = right.lstrip('=')
                else:
                    left, operator = left, '='
                results.append({'=': self.value(left) == self.value(right),
                                '>': self.value(left) > self.value(right),
                                '<': self.value(left) < self.value(right)}[operator])
            elif key == 'has_doctrine':
                results.append(value == self.doctrine or value in self.selections.values())
            elif key == 'has_variable':
                results.append(value in self.vars)
            else:
                raise AssertionError(f'Unmodeled trigger: {key}')
        return all(results)

    def run(self, tree):
        matched = False
        for key, body in tree:
            if key in ('if', 'else_if', 'else'):
                execute = key == 'if' or not matched
                if key == 'if':
                    matched = False
                if execute and (key == 'else' or self.condition(get(body, 'limit'))):
                    self.run([(k, v) for k, v in body if k != 'limit'])
                    matched = True
            elif key == 'while_loop_effect':
                iterations = 0
                while self.condition(get(body, 'limit')):
                    self.run([(k, v) for k, v in body if k != 'limit'])
                    iterations += 1
                    assert iterations < 100, 'Search did not converge'
            elif key in EFFECTS:
                replacements = {} if body == 'yes' else {
                    '$' + k + '$': v for k, v in body}
                self.run(substitute(EFFECTS[key], replacements))
            elif key == 'meta_effect':
                replacements = {}
                for name, value in body:
                    if name == 'text':
                        continue
                    replacements['[' + name + ']'] = re.sub(
                        r'\[\?([^|]+)\|\.(\d+)\]',
                        lambda match: format(self.value(match[1]), '.' + match[2] + 'f'),
                        value.strip('"'))
                self.run(substitute(get(body, 'text'), replacements))
            elif key in ('set_variable', 'add_to_variable', 'subtract_from_variable',
                         'multiply_variable', 'divide_variable'):
                name, value = body[0]
                old, value = self.value(name), self.value(value)
                result = {'set_variable': value, 'add_to_variable': old + value,
                          'subtract_from_variable': old - value,
                          'multiply_variable': old * value,
                          'divide_variable': old / value if value else D(0)}[key]
                # Integer-only measurement must work with 3-place variables.
                self.vars[name] = result.quantize(D('0.001'))
                assert abs(result) < 2000000, 'Unsafe scaled script variable'
            elif key == 'round_variable':
                self.vars[body] = self.value(body).quantize(D(1), rounding=ROUND_HALF_UP)
            elif key == 'clear_variable':
                self.vars.pop(body, None)
            elif key == 'hidden_effect':
                self.run(body)
            elif key == 'set_grand_doctrine':
                assert get(GRANDS[body], 'folder') == self.folder
                if self.doctrine == body:
                    continue
                self.doctrine = body
                self.selections = dict.fromkeys(self.tracks)
                self.mastery = dict.fromkeys(self.tracks, D(0))
            elif key == 'set_sub_doctrine':
                slot = int(get(body, 'track'))
                assert get(body, 'folder') == self.folder
                name = get(body, 'sub_doctrine')
                assert get(SUBS[name], 'track') == self.tracks[slot]
                self.selections[self.tracks[slot]] = name
            elif key == 'add_mastery':
                assert get(body, 'folder') == self.folder
                track = get(body, 'track')
                assert self.value(get(body, 'amount')) > 0, 'Engine rejects add_mastery = 0'
                self.mastery[track] += self.value(get(body, 'amount'))
                selected = self.selections[track]
                if selected is not None:
                    # Model the milestone counter side effect on completed tracks.
                    threshold = sum(self.value(next((v for k, v in fields if k == 'mastery'), '75'))
                                    for _, fields in get(SUBS[selected], 'rewards'))
                    if self.mastery[track] >= threshold:
                        generated = EFFECTS['tfr_restore_' + self.folder + '_doctrines']
                        counters = [v for k, v in generated if k == 'else']
                        counter = next(v for k, v in counters[self.tracks.index(track)] if k == 'clear_variable')
                        self.vars[counter] = self.value(counter) + 1
            elif key.endswith('_experience'):
                self.xp[key.removesuffix('_experience')] += self.value(body)
            elif key in ('custom_effect_tooltip', 'log'):
                pass
            elif key == 'clr_country_flag':
                self.flags.discard(body)
            else:
                raise AssertionError(f'Unmodeled effect: {key}')


def main():
    rng = random.Random(394360)
    count = 0
    for decision, fields in DECISIONS:
        target = decision.removeprefix('tfr_switch_')
        grand = GRANDS[target]
        folder = get(grand, 'folder')
        tracks = [v for _, v in get(grand, 'tracks')]
        initial = next(name for name, data in GRANDS.items()
                       if get(data, 'folder') == folder and name != target)
        choices = [next(name for name, data in SUBS.items()
                        if get(data, 'track') == track) for track in tracks]
        for samples in [('0', '0.00001', '74.99999', '375'),
                        ('123.45678', '300', '374.99999', '2048.12345')]:
            for empty_slot in [None, 1]:
                selected = choices.copy()
                progress = list(samples)
                if empty_slot is not None:
                    selected[empty_slot] = None
                    progress[empty_slot] = '0'
                model = Model(folder, initial, tracks, selected, progress)
                # Preserve both absent counters and existing achievement history.
                model.vars['infantry_milestone_var'] = D(3)
                original_vars = deepcopy(model.vars)
                for step in range(3):
                    old_mastery = deepcopy(model.mastery)
                    selected_decision = fields if step != 1 else next(
                        data for name, data in DECISIONS if name == 'tfr_switch_' + initial)
                    model.run(get(selected_decision, 'complete_effect'))
                    assert model.mastery == old_mastery, (decision, model.mastery, old_mastery)
                    assert model.selections == dict(zip(tracks, selected))
                    assert model.vars == original_vars, model.vars
                    assert model.other_branch == {'unchanged': ('selected', D('123.45678'))}
                xp = get(grand, 'xp_type')
                assert model.xp[xp] == 200
                assert all(value == 500 for key, value in model.xp.items() if key != xp)
                assert model.probes < 500
                count += 1
    # Independent coverage of all twelve tracks with randomized fractional inputs.
    for track in {v for data in GRANDS.values() for _, v in get(data, 'tracks')}:
        folder = next(get(data, 'folder') for data in GRANDS.values()
                      if track in [v for _, v in get(data, 'tracks')])
        for value in [D(rng.randrange(0, 1000000000)) * UNIT for _ in range(20)]:
            model = Model(folder, '', [track], [None], [value])
            model.run(EFFECTS['tfr_save_' + track + '_mastery'])
            prefix = 'tfr_saved_mastery_' + track
            saved = str(int(model.value(prefix + '_whole'))) + '.' + ''.join(
                str(int(model.value(prefix + '_d' + str(digit)))) for digit in range(1, 6))
            assert D(saved) == value, (track, saved, value)
    assert len(DECISIONS) == 10
    for track in {v for data in GRANDS.values() for _, v in get(data, 'tracks')}:
        folder = next(get(data, 'folder') for data in GRANDS.values()
                      if track in [v for _, v in get(data, 'tracks')])
        for sub, data in SUBS.items():
            if get(data, 'track') != track:
                continue
            tracks = next([v for _, v in get(data, 'tracks')] for data in GRANDS.values()
                          if get(data, 'folder') == folder)
            selected = dict.fromkeys(tracks)
            selected[track] = sub
            model = Model(folder, '', tracks, list(selected.values()), ['0'] * 4)
            model.run(EFFECTS['tfr_save_' + folder + '_doctrines'])
            model.selections = dict.fromkeys(tracks)
            model.run(EFFECTS['tfr_restore_' + folder + '_doctrines'])
            assert model.selections == selected, sub
            assert not model.vars
    assert (ROOT / 'localisation/english/TFR_doctrine_switch_l_english.yml').read_bytes().startswith(b'\xef\xbb\xbf')
    # The previous model passed while the actual game rejected these constructs.
    # Check the emitted script, including call sites and the limited allowed block.
    for name, body in EFFECTS.items():
        assert '$' not in str(body), f'Unexpanded scripted effect parameter: {name}'
        def check_calls(tree):
            for key, value in tree:
                assert key != 'while', 'HOI4 requires while_loop_effect'
                if key in EFFECTS:
                    assert value == 'yes', (name, key, value)
                elif isinstance(value, list):
                    check_calls(value)
        check_calls(body)
    category = get(read(ROOT / 'common/decisions/categories/TFR_doctrine_switch.txt'),
                   'tfr_doctrine_reorganization')
    for fields in [category] + [fields for _, fields in DECISIONS]:
        assert get(fields, 'allowed') == [('always', 'yes')]
        assert ('is_ai', 'no') in get(fields, 'visible')
    gui = get(read(ROOT / 'common/scripted_guis/TFR_doctrine_switch.txt'), 'scripted_gui')
    selector = get(gui, 'tfr_doctrine_selector')
    assert get(selector, 'parent_window_name') == '"country_doctrine_view"'
    triggers = dict(get(selector, 'triggers'))
    clicks = dict(get(selector, 'effects'))
    layout = get(read(ROOT / 'interface/TFR_doctrine_switch.gui'), 'guiTypes')
    panel = next(body for _, body in layout
                 if get(body, 'name') == '"tfr_doctrine_selector_window"')
    buttons = {get(body, 'name').strip('"') for key, body in panel if key == 'buttonType'}
    for decision, fields in DECISIONS:
        target = decision.removeprefix('tfr_switch_')
        grand = GRANDS[target]
        folder = get(grand, 'folder')
        tracks = [value for _, value in get(grand, 'tracks')]
        xp = get(grand, 'xp_type')
        initial = next(name for name, data in GRANDS.items()
                       if get(data, 'folder') == folder and name != target)
        selected = [next(name for name, data in SUBS.items()
                         if get(data, 'track') == track) for track in tracks]
        button = 'switch_' + target
        assert button in buttons
        callback = clicks[button + '_click']
        guarded = get(get(callback, 'hidden_effect'), 'if')
        requirements = get(guarded, 'limit')
        assert requirements == triggers[button + '_click_enabled']
        actions = [(key, value) for key, value in guarded if key != 'limit']
        assert actions[-1] == ('clr_country_flag', 'tfr_doctrine_selector_open')
        assert actions[:-1] == get(get(fields, 'complete_effect'), 'hidden_effect')
        # Exercise the actual callback at exactly 100 XP, and each rejected case.
        for old_grand, balance, allowed in [(initial, '100', True),
                                            (initial, '99.99999', False),
                                            (target, '100', False),
                                            ('', '100', False)]:
            model = Model(folder, old_grand, tracks, selected,
                          ['375', '123.45678', '0', '0.00001'])
            model.xp[xp] = D(balance)
            model.flags.add('tfr_doctrine_selector_open')
            assert model.condition(requirements) == allowed
            before = deepcopy((model.mastery, model.selections, model.vars))
            model.run(callback)
            assert (model.mastery, model.selections, model.vars) == before
            assert model.doctrine == (target if allowed else old_grand)
            assert model.xp[xp] == D(balance) - (100 if allowed else 0)
            assert ('tfr_doctrine_selector_open' in model.flags) == (not allowed)
    print(f'PASS: {count} switch scenarios, 120 repeated switches, 240 exact mastery snapshots; 10 decisions.')
    print('PASS: 10 GUI callbacks preserve mastery; exact XP boundary, current-doctrine and missing-doctrine guards.')
    print('Verification uses a script model. In-game UI, parsing and runtime still require a game test.')


if __name__ == '__main__':
    main()
