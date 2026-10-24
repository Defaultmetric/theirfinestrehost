"""Static 1936 industrial audit. Assumes all DLC; does not simulate a campaign."""
from pathlib import Path
from collections import defaultdict, Counter
from bisect import bisect_right
import json
import re
from hoi4_script import TOKEN, Block, Entry, unquote, walk

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT.parents[3] / 'common/Hearts of Iron IV'
STATS = set('industrial_capacity_factory industrial_capacity_dockyard production_speed_buildings_factor production_speed_industrial_complex_factor production_speed_arms_factory_factor production_speed_dockyard_factor production_factory_max_efficiency_factor production_factory_efficiency_gain_factor production_factory_start_efficiency_factor line_change_production_efficiency_factor consumer_goods_factor consumer_goods_expected_value local_resources_factor resources_factor global_building_slots_factor research_speed_factor min_export factory_energy_consumption'.split())
FACTORIES = ('industrial_complex', 'arms_factory', 'dockyard')
RESOURCES = ('steel', 'aluminium', 'tungsten', 'chromium', 'rubber', 'oil', 'coal')


def parse(source):
    tokens = [t for t in TOKEN.finditer(source) if not t.group().startswith('#')]
    lines = [m.start() for m in re.finditer('\n', source)]
    pos = 0
    def block():
        nonlocal pos
        items = []
        while pos < len(tokens):
            t = tokens[pos]; pos += 1
            if t.group() == '}':
                return Block(items), t.end()
            if t.group() == '{':
                value, end = block(); items.append(value); continue
            key = unquote(t.group())
            if pos >= len(tokens) or tokens[pos].group() not in ('=', '<', '>', '<=', '>=', '!=', '?='):
                items.append(key); continue
            op = tokens[pos].group(); pos += 1
            v = tokens[pos]; pos += 1
            value, end = block() if v.group() == '{' else (unquote(v.group()), v.end())
            items.append(Entry(key, op, value, t.start(), end, bisect_right(lines, t.start())+1))
        return Block(items), len(source)
    return block()[0]


def overlay(folder):
    result = {p.name: p for p in (BASE / folder).glob('*.txt')}
    result.update({p.name: p for p in (ROOT / folder).glob('*.txt')})
    return sorted(result.values())


def read(p):
    return parse(p.read_text(encoding='utf-8-sig'))


def number(v, variables=None):
    try: return float(v)
    except (ValueError, TypeError): return (variables or {}).get(str(v).removeprefix('var:'), 0)


def condition(b, tag, flags, variables):
    tests = []
    for e in b.entries():
        if e.key in ('OR', 'AND', 'NOT'):
            val = condition(e.value, tag, flags, variables)
            if e.key == 'OR':
                val = any(condition(Block([x]), tag, flags, variables) for x in e.value.entries())
            if e.key == 'NOT': val = not val
        elif e.key == 'has_dlc': val = True
        elif e.key == 'always': val = e.value == 'yes'
        elif e.key in ('tag', 'original_tag'): val = tag == e.value
        elif e.key == 'has_country_flag': val = e.value in flags
        elif e.key in ('has_completed_focus', 'has_war', 'is_in_faction'): val = False
        elif e.key == 'date': val = ('1936.1.1' < e.value) if e.op == '<' else ('1936.1.1' > e.value)
        else: val = False
        tests.append(val)
    return all(tests)


def main():
    assert BASE.exists(), BASE
    effects = {}
    for p in overlay('common/scripted_effects'):
        for e in read(p).entries():
            if isinstance(e.value, Block): effects[e.key] = e.value
    ideas, dynamics, techs, defaults = {}, {}, {}, {}
    for p in overlay('common/ideas'):
        for e, parents in walk(read(p)):
            if len(parents) == 2 and parents[0].key == 'ideas' and isinstance(e.value, Block):
                ideas[e.key] = (parents[-1].key, e.value.get('modifier', Block([])))
                allowed = e.value.get('allowed', Block([]))
                if e.value.get('default') == 'yes' and parents[-1].key != 'country' and allowed.get('always') != 'no': defaults[parents[-1].key] = e.key
    for p in overlay('common/dynamic_modifiers'):
        for e in read(p).entries(): dynamics[e.key] = e.value
    for p in overlay('common/technologies'):
        for e, parents in walk(read(p)):
            if len(parents) == 1 and parents[0].key == 'technologies': techs[e.key] = e.value
    countries = {}
    for p in overlay('history/countries'):
        tag = p.name[:3]
        row = dict(tag=tag, name=p.stem[6:], factories=Counter(), resources=Counter(),
                   vanilla_factories=Counter(), vanilla_resources=Counter(), states=0,
                   ideas=list(defaults.values()), dynamics=[], variables={}, technology=[], flags=set(), unresolved=[])
        def execute(b, depth=0):
            if not isinstance(b, Block) or depth > 12: return
            chain = False
            for e in b.entries():
                key, v = e.key.lower(), e.value
                if re.fullmatch(r'\d{4}\.\d+\.\d+', key):
                    if key <= '1936.1.1': execute(v, depth+1)
                elif key in ('if', 'else_if', 'else'):
                    ok = (key == 'else' or condition(v.get('limit', Block([])), tag, row['flags'], row['variables']))
                    if key == 'if': chain = False
                    if not chain and ok:
                        execute(Block([x for x in v.items if not isinstance(x,Entry) or x.key.lower() != 'else']), depth+1); chain = True
                    # Older history scripts place else inside the if block.
                    elif key == 'if' and isinstance(v.get('else'), Block): execute(v.get('else'), depth+1)
                elif key == 'set_country_flag': row['flags'].add(v.get('flag') if isinstance(v,Block) else v)
                elif key in ('set_stability', 'set_war_support', 'set_research_slots'): row[key] = number(v)
                elif key in ('add_ideas', 'remove_ideas'):
                    for idea in v.atoms() if isinstance(v, Block) else [v]:
                        if key == 'add_ideas':
                            group = ideas.get(idea, ('country',))[0]
                            if group != 'country':
                                row['ideas'] = [i for i in row['ideas'] if ideas.get(i, ('country',))[0] != group]
                            if idea not in row['ideas']: row['ideas'].append(idea)
                        elif idea in row['ideas']: row['ideas'].remove(idea)
                elif key == 'add_timed_idea': row['ideas'].append(v.get('idea'))
                elif key == 'add_dynamic_modifier':
                    if v.get('modifier') not in row['dynamics']: row['dynamics'].append(v.get('modifier'))
                elif key in ('set_variable', 'add_to_variable', 'subtract_from_variable'):
                    var = v.get('var')
                    values = [(var, v.get('value'))] if var else [(x.key,x.value) for x in v.entries() if x.key != 'tooltip']
                    for var, value in values:
                        n = number(value, row['variables'])
                        row['variables'][var] = n if key == 'set_variable' else row['variables'].get(var,0) + n * (-1 if key == 'subtract_from_variable' else 1)
                elif key == 'set_technology': row['technology'].extend(x.key for x in v.entries() if x.value == '1')
                elif e.key in effects: execute(effects[e.key], depth+1)
                elif key == 'add_offsite_building': row['factories'][v.get('type')] += number(v.get('level'))
        execute(read(p))
        row['flags'] = sorted(row['flags'])
        stats = Counter(); contributions = []
        for kind, names, library in [('idea',row['ideas'],ideas), ('dynamic',row['dynamics'],dynamics), ('tech',row['technology'],techs)]:
            for name in names:
                b = library.get(name)
                if b is None:
                    if kind != 'tech': row['unresolved'].append(name)
                    continue
                if kind == 'idea': b = b[1]
                if not isinstance(b, Block): continue
                delta = {e.key:number(e.value,row['variables']) for e in b.entries() if e.key in STATS and not isinstance(e.value,Block)}
                if delta:
                    stats.update(delta); contributions.append(dict(kind=kind,id=name,modifiers=delta))
        row['modifiers'] = dict(stats); row['contributions'] = contributions
        countries[tag] = row
    state_owners = {}
    def states(paths, vanilla=False):
        for p in paths:
            b = read(p).get('state')
            if not b: continue
            h = b.get('history',Block([])); owner = state_owners.get(b.get('id')) if vanilla else h.get('owner')
            if not vanilla: state_owners[b.get('id')] = owner
            if owner not in countries: continue
            row = countries[owner]
            if not vanilla: row['states'] += 1
            builds = h.get('buildings',Block([]))
            prefix = 'vanilla_' if vanilla else ''
            for k in FACTORIES: row[prefix+'factories'][k] += number(builds.get(k,0))
            resources = b.get('resources',Block([]))
            for k in RESOURCES: row[prefix+'resources'][k] += number(resources.get(k,0))
    states(overlay('history/states'))
    states(sorted((BASE/'history/states').glob('*.txt')), True)
    rows = sorted((r for r in countries.values() if r['states']), key=lambda r:sum(r['factories'].values()),reverse=True)
    result = dict(date='1936.1.1', assumptions='All DLC. State resources are raw deposits; ownership only. Static country history, ideas, dynamic variables and techs. Excludes live events, leader traits, state modifiers, trade, infrastructure extraction, occupation, faction transfers, focus completion and conditional modifier blocks.', countries=rows)
    (ROOT/'docs/industrial-balance-audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    header = '| Tag | Civ | Mil | Dock | Δ factories on same states vs base | Steel | Al | W | Cr | Rubber | Oil | Coal | Output | Build | Cap | CG factor | CG expected |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n'
    out = ['# Industrial balance: static 1936 audit\n\n'+result['assumptions']+'\n\n'+header]
    for r in rows:
        f,s,m = r['factories'],r['resources'],r['modifiers']
        values = [r['tag'],*[f.get(k,0) for k in FACTORIES],sum(f.values())-sum(r['vanilla_factories'].values()),*[s.get(k,0) for k in RESOURCES],*[f'{m.get(k,0):+.1%}' for k in ('industrial_capacity_factory','production_speed_buildings_factor','production_factory_max_efficiency_factor','consumer_goods_factor','consumer_goods_expected_value')]]
        out.append('| '+' | '.join(str(int(v)) if isinstance(v,float) and v.is_integer() else str(v) for v in values)+' |\n')
    (ROOT/'docs/industrial-balance-audit.md').write_text(''.join(out),encoding='utf-8')
    print('Audited',len(rows),'countries. Top 30:')
    for r in rows[:30]: print(r['tag'],dict(r['factories']),r['modifiers'])


if __name__ == '__main__': main()
