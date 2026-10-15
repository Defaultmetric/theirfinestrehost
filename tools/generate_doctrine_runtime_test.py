"""Install/remove a temporary in-game regression decision. Use a disposable save.

python tools/generate_doctrine_runtime_test.py --install
Restart with -debug, click TFR_DOCTRINE_RUNTIME_TEST, inspect game.log, then
python tools/generate_doctrine_runtime_test.py --remove
"""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from generate_doctrine_switch import ROOT, read, get

CATEGORY = ROOT / 'common/decisions/categories/TFR_doctrine_runtime_test.txt'
DECISION = ROOT / 'common/decisions/TFR_doctrine_runtime_test.txt'


def main():
    if '--remove' in sys.argv:
        CATEGORY.unlink(missing_ok=True)
        DECISION.unlink(missing_ok=True)
        print('Removed temporary runtime test decision.')
        return
    assert '--install' in sys.argv
    subs = dict(item for path in sorted((ROOT / 'common/doctrines/subdoctrines').rglob('*.txt'))
                for item in read(path) if isinstance(get(item[1], 'track'), str))
    effects = ['log = "TFR_DOCTRINE_RUNTIME BEGIN"']
    for filename in ['land', 'sea', 'air']:
        grands = read(ROOT / 'common/doctrines/grand_doctrines' / (filename + '_grand_doctrines.txt'))
        folder = get(grands[0][1], 'folder')
        tracks = [v for _, v in get(grands[0][1], 'tracks')]
        selections = [next(name for name, data in subs.items() if get(data, 'track') == track)
                      for track in tracks]
        for sample, values in enumerate([['375', '123.45678', '74.99999', '0.00001'],
                                         ['74.00001', '150', '225', '300'],
                                         ['0', '0.00001', '0', '74.99999']]):
            effects.append('set_grand_doctrine = ' + grands[0][0])
            # Switching to another doctrine first ensures the fixture is reset.
            effects.append('set_grand_doctrine = ' + grands[1][0])
            effects.append('set_grand_doctrine = ' + grands[0][0])
            for slot, (track, sub, value) in enumerate(zip(tracks, selections, values)):
                effects.extend([
                    f'set_sub_doctrine = {{ sub_doctrine = {sub} folder = {folder} track = {slot} }}',
                    *([f'add_mastery = {{ folder = {folder} track = {track} amount = {value} }}'] if value != '0' else [])])
            for target, _ in grands[1:] + grands[:1]:
                effects.extend([f'tfr_save_{folder}_doctrines = yes',
                                f'set_grand_doctrine = {target}',
                                f'tfr_restore_{folder}_doctrines = yes'])
                from decimal import Decimal
                conditions = [f'has_doctrine = {target}']
                for track, sub, value in zip(tracks, selections, values):
                    conditions.extend([
                        f'has_doctrine = {sub}',
                        f'has_mastery = {{ track = {track} amount = {value} }}',
                        f'NOT = {{ has_mastery = {{ track = {track} amount = {Decimal(value) + Decimal("0.00001")} }} }}'])
                label = f'{folder} sample={sample} target={target}'
                effects.extend(['if = { limit = { ' + ' '.join(conditions) + ' }',
                                f'    log = "TFR_DOCTRINE_RUNTIME PASS {label}"',
                                '}', 'else = {',
                                f'    log = "TFR_DOCTRINE_RUNTIME FAIL {label}"', '}'])
    effects.append('log = "TFR_DOCTRINE_RUNTIME END"')
    CATEGORY.write_text('''tfr_doctrine_runtime_test = {
    icon = army_reform
    priority = 99999
    allowed = { always = yes }
    visible = { is_ai = no }
}
''', encoding='utf-8')
    DECISION.write_text('''tfr_doctrine_runtime_test = {
    TFR_DOCTRINE_RUNTIME_TEST = {
        icon = generic_military
        allowed = { always = yes }
        visible = { is_ai = no }
        cost = 0
        ai_will_do = { factor = 0 }
        complete_effect = {
            hidden_effect = {
''' + '\n'.join('                ' + line for line in effects) + '\n            }\n        }\n    }\n}\n', encoding='utf-8')
    print('Installed temporary decision. It changes doctrines; use a disposable save.')


if __name__ == '__main__':
    main()
