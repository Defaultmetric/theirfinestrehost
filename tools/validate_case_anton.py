"""Exercise Case Anton's actual state-routing AST without running HOI4."""
from copy import deepcopy
from pathlib import Path
import re

from hoi4_script import Block, parse, walk

ROOT = Path(__file__).resolve().parents[1]
GER_STATES = {851, 21, 22, 32, 20, 26, 33, 25, 31}
ITA_STATES = {735, 1}
AFRICA_STATES = {665, 458, 513, 460, 459, 461, 462}
TARGETS = GER_STATES | ITA_STATES | AFRICA_STATES
OTHER_STATES = {448, 554, 670, 999}


def load(relative):
    return parse((ROOT / relative).read_text(encoding='utf-8-sig'))


def run(effect, states, vichy, flags=None, state_effect=None, fra_exists=True):
    """Small strict interpreter for only the triggers/effects used by this effect."""
    flags = set() if flags is None else flags

    def trigger(e, current, previous):
        if e.key == 'OR':
            return any(trigger(x, current, previous) for x in e.value.entries())
        if e.key == 'NOT':
            return not all(trigger(x, current, previous) for x in e.value.entries())
        if e.key == 'state':
            return current == int(e.value)
        if e.key == 'is_controlled_by':
            tag = previous if e.value == 'PREV' else 'GER' if e.value == 'ROOT' else e.value
            return states[current]['controller'] == tag
        if e.key == 'has_country_flag':
            return e.value in flags
        if e.key == 'country_exists':
            assert e.value == 'FRA'
            return fra_exists
        if e.key.isdigit() and isinstance(e.value, Block):
            return all(trigger(x, int(e.key), current) for x in e.value.entries())
        raise AssertionError(f'Unsupported trigger: {e.key}')

    def execute(block, current, previous):
        last_if = None
        for e in block.entries():
            if e.key == 'if':
                last_if = all(trigger(x, current, previous) for x in e.value.get('limit').entries())
                if last_if:
                    execute(Block([x for x in e.value.entries() if x.key != 'limit']), current, previous)
            elif e.key == 'else_if':
                assert last_if is not None
                matched = not last_if and all(trigger(x, current, previous) for x in e.value.get('limit').entries())
                if matched:
                    execute(Block([x for x in e.value.entries() if x.key != 'limit']), current, previous)
                last_if = last_if or matched
            elif e.key == 'else':
                assert last_if is not None
                if not last_if:
                    execute(e.value, current, previous)
            elif e.key == 'every_state':
                for state in states:
                    if all(trigger(x, state, current) for x in e.value.get('limit').entries()):
                        execute(Block([x for x in e.value.entries() if x.key != 'limit']), state, current)
            elif e.key == 'transfer_state_to':
                states[current] = {'controller': e.value, 'owner': e.value}
            elif e.key == 'set_country_flag':
                flags.add(e.value)
            elif e.key == 'TFR_case_anton_transfer_states':
                execute(state_effect if state_effect is not None else effect, current, previous)
            else:
                raise AssertionError(f'Unsupported effect: {e.key}')

    execute(effect, vichy, 'GER')


def check_routing(effect, states, vichy, recipient, fra_exists=True):
    before = deepcopy(states)
    run(effect, states, vichy, fra_exists=fra_exists)
    for state, original in before.items():
        expected = original
        if state in TARGETS and original['controller'] == vichy:
            destination = 'GER' if state in GER_STATES else 'ITA' if state in ITA_STATES else recipient
            expected = {'owner': destination, 'controller': destination}
        assert states[state] == expected, (vichy, state, original, states[state], expected)
    once = deepcopy(states)
    run(effect, states, vichy, fra_exists=fra_exists)
    assert states == once, 'Repeated effect changes already transferred states'


def main():
    effects = load('common/scripted_effects/tfr_case_anton_effects.txt')
    assert len(effects.entries('TFR_case_anton_transfer_states')) == 1
    effect = effects.get('TFR_case_anton_transfer_states')
    ger = load('common/decisions/GER.txt').get('GER_case_anton_category').get('GER_case_anton')
    selected = ger.get('complete_effect').get('hidden_effect').get('random_other_country')
    assert selected.get('TFR_case_anton_transfer_states') == 'yes'
    assert selected.get('activate_mission') == 'FRA_case_anton_mission'
    assert selected.get('set_country_flag') == 'TFR_case_anton_states_transferred'
    names = [e.key for e in selected.entries()]
    assert names.index('activate_mission') < names.index('TFR_case_anton_transfer_states')
    category = load('common/decisions/categories/GER_decision_categories.txt').get('GER_case_anton_category')
    candidates = [selected.get('limit'), category.get('visible').get('any_country')]
    candidates += [ger.get(key).get('any_country') for key in ('available', 'visible')]
    for candidate in candidates:
        identities = [entry.value.mapping() for entry in candidate.entries('OR')]
        assert {'tag': 'VIC', 'has_focus_tree': 'vichy_french_focus', 'has_country_flag': 'vichy_france'} in identities
        assert {'original_tag': 'FRA', 'tag': 'VIC'} in identities
        assert not any(e.key in ('country_exists', 'exists', 'original_tag_to_check') for e, _ in walk(candidate)), 'Free France still gates the Vichy selector'
    for block in (ger.get('available'), ger.get('visible'), category.get('visible')):
        assert not block.entries('any_country_with_original_tag')
        assert not any(e.key == 'FRA' or (e.key == 'country_exists' and e.value == 'FRA') for e, _ in walk(block))
    fra = load('common/decisions/FRA.txt').get('FRA_vichy_france').get('FRA_case_anton_mission')
    timeout = fra.get('timeout_effect')
    assert timeout.get('transfer_navy').get('target') == 'GER'
    assert fra.get('days_mission_timeout') == '7'
    assert any({e.value for e in branch.value.entries('original_tag')} == {'FRA', 'VIC'}
               for branch in fra.get('activation').entries('OR'))
    fra_category = load('common/decisions/categories/FRA_decision_categories.txt').get('FRA_vichy_france')
    assert {e.value for e in fra_category.get('allowed').get('OR').entries('original_tag')} == {'FRA', 'VIC'}
    for block in (ger.get('complete_effect'), timeout, effect):
        assert not any(e.key == 'annex_country' for e, _ in walk(block)), 'Blanket annexation remains'
    legacy = timeout.get('hidden_effect')
    flag = 'TFR_case_anton_states_transferred'
    for vichy in ('VIC', 'D01'):
        for controller_448 in ('ITA', 'FRA', 'GER', 'ENG', vichy):
            for fra_exists in (True, False):
                recipient = 'ITA' if controller_448 == 'ITA' else 'FRA' if fra_exists else 'ENG'
                for tested_state in TARGETS:
                    for controller in (vichy, 'GER', 'ITA', 'FRA', 'ENG', 'USA'):
                        states = {s: {'owner': 'VIC', 'controller': vichy} for s in TARGETS | OTHER_STATES}
                        states[448]['controller'] = controller_448
                        states[tested_state] = {'owner': 'FRA', 'controller': controller}
                        check_routing(effect, states, vichy, recipient, fra_exists)

                # Once clicked, the seven-day callback must not take newly captured states.
                occupied = {s: {'owner': vichy, 'controller': vichy} for s in TARGETS | OTHER_STATES}
                original = deepcopy(occupied)
                flags = {flag}
                run(legacy, occupied, vichy, flags, effect, fra_exists)
                assert occupied == original

                # Old saves with an already active mission still use per-state control checks.
                states = deepcopy(original)
                states[448]['controller'] = controller_448
                states[851]['controller'] = 'ENG'
                expected = deepcopy(states)
                run(effect, expected, vichy, fra_exists=fra_exists)
                flags = set()
                run(legacy, states, vichy, flags, effect, fra_exists)
                assert states == expected and flag in flags

    loc = ROOT / 'localisation/replace/tfr_case_anton_l_english.yml'
    assert loc.read_bytes().startswith(b'\xef\xbb\xbf')
    lines = loc.read_text(encoding='utf-8-sig').splitlines()[1:]
    assert all(re.fullmatch(r' [A-Za-z_0-9.]+:0 ".*"', line) for line in lines)
    keys = re.findall(r'^ ([A-Za-z_0-9.]+):0 ', loc.read_text(encoding='utf-8-sig'), re.M)
    assert len(keys) == len(set(keys)) == 6
    assert 'Free France is not required' in loc.read_text(encoding='utf-8-sig')
    assert 'United Kingdom (ENG)' in loc.read_text(encoding='utf-8-sig')
    print('PASS: all 18 states, 2,160 routing scenarios, fixed/dynamic Vichy tags,')
    print('FRA present/absent and ENG fallback; Italy control of 448 retains priority; occupied states unchanged,')
    print('unlisted states unchanged, repeat safety, legacy missions, seven-day fleet window, localisation.')


if __name__ == '__main__':
    main()
