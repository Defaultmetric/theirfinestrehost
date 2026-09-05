"""Deterministic design/budget sensitivity analysis, NOT a HOI4 battle simulator."""
import argparse
import json
import math
import re
from pathlib import Path


def parse(text):
    tokens = re.findall(r'"[^"\n]*"|[{}=]|[^\s{}=]+', re.sub(r'#[^\n]*', '', text))
    pos = 0

    def block():
        nonlocal pos
        out = {}
        while pos < len(tokens) and tokens[pos] != '}':
            key = tokens[pos]
            pos += 1
            if pos >= len(tokens) or tokens[pos] != '=':
                continue
            pos += 1
            value = tokens[pos]
            pos += 1
            if value == '{':
                value = block()
            else:
                try:
                    value = float(value)
                except ValueError:
                    value = value.strip('"')
            out[key] = value
        if pos < len(tokens):
            pos += 1
        return out
    return block()


def run(root, output):
    def read(p):
        return parse((root / p).read_text(encoding='utf-8-sig'))
    modules = read('common/units/equipment/modules/00_ship_modules.txt')['equipment_modules']
    hulls = {}
    for kind in ('light', 'cruiser', 'heavy'):
        hulls.update(read(f'common/units/equipment/ship_hull_{kind}.txt')['equipments'])
    cap_text = (root / 'common/on_actions/naval_cap_on_actions.txt').read_text()
    caps = {k: float(v) for k, v in re.findall(r'global\.(\w+)\s*=\s*([\d.]+)', cap_text)}
    stats = ('build_cost_ic', 'max_strength', 'naval_speed', 'surface_visibility',
             'lg_attack', 'hg_attack', 'torpedo_attack', 'armor_value')
    designs = []
    for tier in range(1, 5):
        for label in ('DD_torp3', 'DD_torp1', 'CL_gun2', 'CL_gun4', 'CA_gun4', 'BB_gun3'):
            kind = 'light' if label.startswith('DD') else 'heavy' if label.startswith('BB') else 'cruiser'
            base = hulls[f'ship_hull_{kind}']
            hull = {**base, **hulls[f'ship_hull_{kind}_{tier}']}
            mods = [f'{"light" if kind == "light" else "heavy" if kind == "heavy" else "cruiser"}_ship_engine_{tier}']
            if kind == 'light':
                mods += [f'ship_light_battery_{tier}']
                mods += [f'ship_torpedo_{tier}'] * (3 if label.endswith('3') else 1)
            else:
                mods += ['ship_fire_control_system_0']
                if kind == 'heavy':
                    mods += [f'ship_heavy_battery_{tier}'] * 3
                    mods += [f'ship_armor_bb_{min(tier, 3)}', f'ship_anti_air_{tier}']
                else:
                    battery = 'medium' if label.startswith('CA') else 'light_medium'
                    mods += [f'ship_{battery}_battery_{tier}'] * int(label[-1])
                    mods += [f'ship_armor_cruiser_{tier}']
            values = {}
            for stat in stats:
                add = sum(modules[m].get('add_stats', {}).get(stat, 0) for m in mods)
                averaged = [modules[m]['add_average_stats'][stat] for m in mods
                            if stat in modules[m].get('add_average_stats', {})]
                avg = sum(averaged) / len(averaged) if averaged else 0
                mult = sum(modules[m].get('multiply_stats', {}).get(stat, 0) for m in mods)
                values[stat] = (hull.get(stat, 0) + add + avg) * (1 + mult)
            assert values['build_cost_ic'] > 0 and values['naval_speed'] > 0
            cap = caps['DDCAP' if kind == 'light' else 'BBCAP' if kind == 'heavy' else 'HCCAP' if label.startswith('CA') else 'LCCAP']
            designs.append(dict(tier=tier, design=label, modules=mods, cap=cap, **values))

    # Compare fleets with the same IC ceiling AND the same admiral cap ceiling.
    # CA/BB fleets include three cheap DDs per capital; CL fleets need no capital screens.
    scenarios = []
    for tier in range(1, 5):
        lookup = {d['design']: d for d in designs if d['tier'] == tier}
        attacker, escort = lookup['DD_torp3'], lookup['DD_torp1']
        for budget in (50000, 100000, 150000):
            ndd = min(math.floor(budget / attacker['build_cost_ic']), math.floor(caps['CAP'] / attacker['cap']))
            for name in ('CL_gun2', 'CL_gun4', 'CA_gun4', 'BB_gun3'):
                target = lookup[name]
                screens = 3 if name.startswith(('CA', 'BB')) else 0
                unit_cost = target['build_cost_ic'] + screens * escort['build_cost_ic']
                unit_cap = target['cap'] + screens * escort['cap']
                n = min(math.floor(budget / unit_cost), math.floor(caps['CAP'] / unit_cap))
                scenarios.append(dict(tier=tier, budget=budget, defender=name,
                    attacker_dd=ndd, defender_ships=n, defender_escort_dd=n*screens,
                    attacker_ic=ndd*attacker['build_cost_ic'], defender_ic=n*unit_cost,
                    attacker_cap=ndd*attacker['cap'], defender_cap=n*unit_cap,
                    defender_screen_ratio=3 if screens else None,
                    attacker_torpedo_attack=ndd*attacker['torpedo_attack'],
                    defender_light_attack=n*(target['lg_attack']+screens*escort['lg_attack']),
                    defender_heavy_attack=n*target['hg_attack'],
                    dd_losses_equal_one_target_ic=target['build_cost_ic']/attacker['build_cost_ic']))
    output.mkdir(parents=True, exist_ok=True)
    (output/'naval-balance-estimates.json').write_text(json.dumps(dict(designs=designs, scenarios=scenarios), indent=2)+'\n')
    lines = ['# TFR naval budget and loss sensitivity', '',
        'Static estimates from local hull/module files. NOT simulated battles or predicted losses.', '',
        '## Assumptions and limits', '',
        '- Hull and weapons use matching tiers I-IV; these are explicit illustrative designs, not the unknown feedback designs.',
        '- DD: one light battery, one or three launchers, engine. CL: two/four light-medium batteries, armor, engine, fire control 0. CA: four medium batteries, armor, engine, fire control 0. BB: three heavy batteries, armor (III for tier IV), engine, AA, fire control 0.',
        '- Base hull plus module add_stats and mean of contributing add_average_stats, multiplied by 1 + summed module multiply_stats. No MIO, national, doctrine, tech, admiral, experience or production discounts. Designer values still need in-game confirmation.',
        '- Same IC ceiling and 50-cap ceiling, not guaranteed equal spent IC. Unspent industry is visible; this is not a full-war production/refit model.',
        '- CA/BB fleets have three DD screens per capital at initial full positioning. Screening deteriorates with losses and positioning; this model does not simulate that.',
        '- No target selection, gun cadence, penetration, critical hits, retreat, repairs, weather, carrier aircraft or combat reinforcement model. Raw torpedo/light/heavy attack totals cannot be compared as equivalent damage.',
        '- No fake victory probabilities or surviving-ship counts are generated. Armor/speed/HP are listed as design stats, not converted into an unverified combat formula.', '',
        '## Designs', '', '|Tier|Design|IC estimate|HP estimate|Speed estimate|Light|Heavy|Torpedo|Armor|', '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for d in designs:
        lines.append('|'+ '|'.join([str(d['tier']),d['design']]+[f"{d[s]:.2f}" for s in ('build_cost_ic','max_strength','naval_speed','lg_attack','hg_attack','torpedo_attack','armor_value')])+'|')
    lines += ['', '## Fleet configurations', '', '|Tier|IC ceiling|DD torp3 count / IC / cap|Opponent|Main + escort count|Opponent IC / cap|DD losses equal one main enemy ship IC|', '|---|---:|---|---|---|---|---:|']
    for s in scenarios:
        lines.append(f"|{s['tier']}|{s['budget']}|{s['attacker_dd']} / {s['attacker_ic']:.0f} / {s['attacker_cap']:.1f}|{s['defender']}|{s['defender_ships']} + {s['defender_escort_dd']}|{s['defender_ic']:.0f} / {s['defender_cap']:.1f}|{s['dd_losses_equal_one_target_ic']:.2f}|")
    lines += ['', '## Feedback sensitivity: 63 CL sunk against 157 DD', '',
        'Assume 80 starting CL and 17 survivors exactly for this calculation. Carriers/capitals survive and their aircraft/repair losses are unknown. This is an IC break-even calculation only.', '',
        '|DD tier|CL tier|CL design|IC of 63 CL lost|Equivalent DD losses|Interpretation if all 157 DD sink|', '|---|---|---|---:|---:|---|']
    dd = next(d for d in designs if d['tier']==2 and d['design']=='DD_torp3')
    for cl in (d for d in designs if d['design'].startswith('CL')):
        losses=63*cl['build_cost_ic']
        threshold=losses/dd['build_cost_ic']
        lines.append(f"|II|{cl['tier']}|{cl['design']}|{losses:.0f}|{threshold:.1f}|{'DD side loses less IC' if threshold>157 else 'CL side loses less IC'}|")
    lines += ['', '## Uniform nerf applied', '',
        '|Launcher tier|Previous attack|Current attack|Change|', '|---|---:|---:|---:|']
    for tier, old in enumerate((8, 14, 32, 42), 1):
        current = modules[f'ship_torpedo_{tier}']['add_stats']['torpedo_attack']
        lines.append(f'|{tier}|{old}|{current:g}|{(current/old-1)*100:.1f}%|')
    lines += ['', 'Only surface launcher attack changed. Costs, accuracy, speed penalties, hulls, cap and submarine launchers are unchanged.',
        '', '## Uniform nerf sensitivity', '',
        'At unchanged targets, hit chances and firing opportunities, -10% launcher attack gives -10% launcher attack-weighted damage. It does NOT guarantee -10% ships sunk. Damage thresholds, screening collapse and retreat make losses nonlinear.',
        'With costs unchanged, all IC break-even thresholds above remain unchanged. To neutralize an economic exchange, compare the observed DD-loss count to the threshold rather than comparing victory alone.', '',
        'For a real validation: use identical country bonuses, full strength/organization, same region/weather/start hour and engagement rules; test each listed pair with several repetitions and side swaps. Record sunk IC, repair IC/time, survivors, retreat and aircraft losses. Repeat with mixed legacy hull / modern weapon refits and equal refit budgets before tuning the UK/Italy matchup.', '']
    (output/'naval-balance-estimates.md').write_text('\n'.join(lines), encoding='utf-8')
    print(f'{len(designs)} designs; {len(scenarios)} fleet configurations; report: {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    run(args.root, args.output or args.root/'docs')
