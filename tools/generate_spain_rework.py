"""Generate the nationalist post-civil-war tree and its runtime from the reviewed plan.

Run with --check to compare generated files without changing anything. The generated
postwar block is merged into the country tree, after its original anchor focuses.
"""
from pathlib import Path
import argparse
import collections
import json
import cleanup_volunteer_capacity as script
from hoi4_script import parse as native_parse, replace_spans

ROOT = Path(__file__).resolve().parents[1]
PLAN = json.loads((ROOT / 'tools/spain_focus_plan.json').read_text(encoding='utf-8'))
FOCUSES = PLAN['focuses']
BY_CODE = {f['code']: f for f in FOCUSES}
BRANCH_MODIFIERS = {'air': 'A01', 'navy': 'N01'}
BALANCE_REVISION = json.loads((ROOT/'tools/spain_balance_revision.json').read_text())
TYPES = {'civ': 'industrial_complex', 'mil': 'arms_factory', 'dock': 'dockyard', 'refinery': 'synthetic_refinery'}
BUILDING_DESTINATIONS = sorted({(a['state'],a['kind']) for f in FOCUSES for a in f.get('buildingStates',[])})
LEGACY_IDEAS = {}
RECOVERY_PENALTIES = {}
_ideas = script.parse((ROOT/'common/ideas/spain_nationalist.txt').read_text(encoding='utf-8-sig'))
_names = {'SPA_fascist_economic_aid','SPA_italian_shipbuilding_expertise','SPA_the_duty_to_work','SPA_expand_the_axis_gold_trade'} | {f'SPA_national_recovery_{i}' for i in range(1,8)}
for _entry in script.walk(_ideas):
    if _entry.key in _names and _entry.get('modifier'):
        LEGACY_IDEAS[_entry.key] = {'economy.'+e.key:float(e.value) for e in _entry.get('modifier').active() if e.children is None}
    if _entry.key in {'SPA_recovering_from_civil_war','SPA_recovering_from_civil_war_2','SPA_recovering_from_civil_war_3'} and _entry.get('modifier'):
        _stage = {'SPA_recovering_from_civil_war':1,'SPA_recovering_from_civil_war_2':2,'SPA_recovering_from_civil_war_3':3}[_entry.key]
        RECOVERY_PENALTIES[_stage] = {'economy.'+e.key:float(e.value) for e in _entry.get('modifier').active() if e.children is None}
RECOVERY_PROGRAMMES = {i:LEGACY_IDEAS[f'SPA_national_recovery_{i}'] for i in range(1,8)}
MODS = sorted({k for f in FOCUSES for field in ('modifiers', 'conditionalModifiers') for k in f.get(field, {})} | {
    'economy.industrial_capacity_factory', 'economy.industrial_capacity_dockyard',
    'economy.production_speed_buildings_factor', 'economy.consumer_goods_factor'} |
    {key for values in LEGACY_IDEAS.values() for key in values} |
    {key for values in RECOVERY_PENALTIES.values() for key in values})
OUT = {}
LOC = {}
FOCUS_BLOCK_BEGIN = '# TFR_SPA_GENERATED_FOCUSES_BEGIN'
FOCUS_BLOCK_END = '# TFR_SPA_GENERATED_FOCUSES_END'


def dependency_order(items, identity, parent):
    """Emit every relative anchor before its children, keeping unrelated order."""
    by_id = {identity(item): item for item in items}
    ordered, done, active = [], set(), set()
    def visit(item):
        name = identity(item)
        if name in done:
            return
        if name in active:
            raise ValueError('Relative focus cycle: '+name)
        active.add(name)
        anchor = parent(item)
        if anchor in by_id:
            visit(by_id[anchor])
        active.remove(name)
        done.add(name)
        ordered.append(item)
    for item in items:
        visit(item)
    return ordered


def merge_country_focuses(generated):
    """Preserve legacy focus bodies while satisfying the native read order."""
    text = (ROOT/'common/national_focus/spain.txt').read_text(encoding='utf-8-sig')
    if FOCUS_BLOCK_BEGIN in text:
        start = text.rfind('\n', 0, text.index(FOCUS_BLOCK_BEGIN))+1
        end = text.find('\n', text.index(FOCUS_BLOCK_END))+1
        text = text[:start]+text[end:]
    tree = native_parse(text).entries('focus_tree')[0]
    old_links = [e for e in tree.value.entries('shared_focus')
                 if e.value in ('TFR_SPA_volunteer_spain', 'TFR_SPA_war_spain')]
    text = replace_spans(text, [(e.start, e.end, '') for e in old_links])
    text = text.replace('# TFR_SPA_POSTWAR_REWORK: shared roots include their connected descendants.',
                        '# TFR_SPA_POSTWAR_REWORK: generated focuses follow the original tree.')
    tree = native_parse(text).entries('focus_tree')[0]
    focuses = tree.value.entries('focus')
    ordered = dependency_order(focuses, lambda e:e.value.get('id'),
                               lambda e:e.value.get('relative_position_id'))
    text = replace_spans(text, [(slot.start, slot.end, text[item.start:item.end])
                               for slot,item in zip(focuses,ordered)])
    tree = native_parse(text).entries('focus_tree')[0]
    end = tree.end-1
    addition = '\t'+FOCUS_BLOCK_BEGIN+'\n'
    addition += ''.join('\t'+line+'\n' if line else '\n' for line in generated.splitlines())
    addition += '\t'+FOCUS_BLOCK_END+'\n'
    return text[:end]+addition+text[end:]


def block(name, body):
    return name + ' = {\n' + '\n'.join('\t' + s if s else '' for s in body.strip().splitlines()) + '\n}\n'


def emit(path, text):
    OUT[path] = ('# Generated by tools/generate_spain_rework.py.\n\n' + text).encode('utf-8')


def choose(condition, yes, no=''):
    return block('if', 'limit = { ' + condition + ' }\n' + yes) + (block('else', no) if no else '')


def v(key, base=False):
    return 'TFR_SPA_' + ('base_' if base else '') + key.replace('.', '_')


def addmod(key, value, base=True):
    return f'add_to_variable = {{ {v(key, base)} = {value:g} }}'


def modifier_tip(key):
    modifier = key.split('.')[1]
    return {'planning_speed':'planning_speed_factor_tt', 'motorized_defence_factor':'TFR_SPA_motorized_defence_tt', 'navy_fuel_consumption_factor':'TFR_SPA_navy_fuel_consumption_tt', 'stability_weekly':'TFR_SPA_weekly_stability_tt'}.get(modifier,modifier+'_tt')


def modifier_preview(values, header=None):
    """Native formatted values for conditional/profile changes, display only."""
    body = f'custom_effect_tooltip = {header}\n' if header else ''
    for bucket in dict.fromkeys(k.split('.')[0] for k in values):
        if not header:
            body += f'custom_effect_tooltip = TFR_SPA_{bucket}_modifier_tt\n'
        for key,value in values.items():
            # AI diplomatic scoring has no useful player-facing bonus label.
            if key.startswith(bucket+'.') and not key.split('.')[1].startswith('ai_'):
                body += block('add_to_variable',f'{v(key)} = {value:g}\ntooltip = {modifier_tip(key)}')
    body += 'custom_effect_tooltip = generic_skip_one_line_tt\n'
    return block('effect_tooltip',body)


def grant_with_credit(target, credit, amount):
    """Old-save rewards are credited once against purchases in the new tree."""
    positive = amount > 0
    matching = '>' if positive else '<'
    # HoI4's compact variable syntax supports only =, < and >. Using >= or
    # <= desynchronizes the native parser and discards subsequent focus blocks.
    enough = 'greater_than_or_equals' if positive else 'less_than_or_equals'
    return (f'set_temp_variable = {{ TFR_SPA_grant = {amount:g} }}\n' +
        choose(f'check_variable = {{ {credit} {matching} 0 }}',
            choose(f'check_variable = {{ var = {credit} value = {amount:g} compare = {enough} }}',
                f'subtract_from_variable = {{ {credit} = {amount:g} }}\nset_temp_variable = {{ TFR_SPA_grant = 0 }}',
                f'subtract_from_temp_variable = {{ TFR_SPA_grant = {credit} }}\nset_variable = {{ {credit} = 0 }}')) +
        f'add_to_variable = {{ {target} = TFR_SPA_grant }}\n')


def tech(code, category):
    return f'add_tech_bonus = {{ name = {BY_CODE[code]["id"]} bonus = 0.5 uses = 1 category = {category} }}'


RESEARCH = {
    'D09': ['support_tech'], 'D10': ['dd_tech'], 'D11': ['light_air'],
    'P06': ['electronics'], 'E05': ['construction_tech'], 'E09': ['synth_resources'], 'E12': ['industry'],
    'E17': ['construction_tech'], 'E27': ['excavation_tech'],
    'M03': ['infantry_weapons', 'support_tech'], 'M04': ['artillery'],
    'M06': ['motorized_equipment'], 'M09': ['mountaineers_tech'], 'M10': ['marine_tech'],
    'M18': ['support_tech'], 'M19': ['armor'], 'A03': ['light_air'],
    'A06': ['light_air'], 'A07': ['medium_air'], 'A08': ['radar_tech'],
    'N09': ['dd_tech'], 'N10': ['ca_tech'], 'N13': ['ss_tech'],
    'N16': ['dd_tech'], 'N17': ['bb_tech'],
}


# A small set of focus-gated projects; no parallel copies of existing
# diplomatic events or inherited Spanish resource-extraction decisions.
PROJECTS = [
    dict(id='TFR_SPA_rebuild_asturias', name='Rebuild Asturias', category='TFR_SPA_regional_reconstruction', focus='E03', cost=35, days=45, state=790),
    dict(id='TFR_SPA_rebuild_aragon', name='Reconnect Western Aragon', category='TFR_SPA_regional_reconstruction', focus='E03', cost=35, days=45, state=166),
    dict(id='TFR_SPA_rebuild_andalusia', name='Restore Andalusian Infrastructure', category='TFR_SPA_regional_reconstruction', focus='E03', cost=35, days=45, state=169),
    dict(id='TFR_SPA_standardise_subcontractors', name='Standardise Industrial Subcontractors', category='TFR_SPA_development_projects', focus='E21', cost=75, days=60, modifiers={'economy.line_change_production_efficiency_factor':.05}),
    dict(id='TFR_SPA_motor_pool_trials', name='Conduct Motor Pool Trials', category='TFR_SPA_development_projects', focus='M14', cost=75, days=60, modifiers={'army.army_fuel_consumption_factor':-.025}),
]
CAMPAIGN = 'TFR_SPA_national_service_campaign'
MODS = sorted(set(MODS) | {key for project in PROJECTS for key in project.get('modifiers',{})})


def placements(building, count, levels=1, cap=5, coastal=False, extra=''):
    """Distinct states; never silently lose an infrastructure reward at its cap."""
    eligible = f'is_owned_and_controlled_by = PREV is_core_of = PREV NOT = {{ has_state_flag = TFR_SPA_placement }} free_building_slots = {{ building = {building} size > 0 }}'
    if coastal:
        eligible += ' is_coastal = yes'
    eligible += ' ' + extra
    result = ''
    for _ in range(count):
        action = f'set_state_flag = TFR_SPA_placement\nadd_building_construction = {{ type = {building} level = 1 instant_build = yes }}'
        for _ in range(levels - 1):
            action += '\n' + block('if', f'limit = {{ free_building_slots = {{ building = {building} size > 0 }} }}\nadd_building_construction = {{ type = {building} level = 1 instant_build = yes }}')
        result += choose(f'any_owned_state = {{ {eligible} }}', block('random_owned_controlled_state', f'limit = {{ {eligible} }}\n{action}'), 'add_political_power = 25')
    result += 'every_owned_state = { clr_state_flag = TFR_SPA_placement }\n'
    return result


SPECIAL = {
    'D01': 'set_country_flag = TFR_SPA_volunteer_mode\nset_country_flag = accessible_shared_tree\nhidden_effect = { TFR_SPA_initialize = yes }\ncustom_effect_tooltip = TFR_SPA_recovery_import_tt\nTFR_SPA_enforce_volunteer_rules = yes\ncustom_effect_tooltip = TFR_SPA_volunteer_role_tt',
    'D02': 'set_country_flag = TFR_SPA_war_mode\nhidden_effect = { TFR_SPA_initialize = yes }\ncustom_effect_tooltip = TFR_SPA_recovery_import_tt\ncustom_effect_tooltip = TFR_SPA_war_role_tt',
    'D04': 'TFR_SPA_request_axis_membership = yes\ncustom_effect_tooltip = TFR_SPA_membership_tt',
    'D05': 'TFR_SPA_portugal_agreement = yes\ncustom_effect_tooltip = TFR_SPA_resource_rights_tt',
    'D06': 'TFR_SPA_begin_relocation = yes\ncustom_effect_tooltip = TFR_SPA_relocation_tt',
    'D07': 'create_wargoal = { type = annex_everything target = NPR }',
    'D08': '\n'.join(f'{s} = {{ add_core_of = ROOT }}' for s in (112,179,180,181,795)) + '\nset_cosmetic_tag = ESU_POR_unified',
    'D12': 'custom_effect_tooltip = TFR_SPA_war_commitment_tt',
    'D13': 'custom_effect_tooltip = TFR_SPA_war_coordination_tt',
    'P01': 'TFR_SPA_start_recovery_programme = yes\ncustom_effect_tooltip = TFR_SPA_recovery_import_tt\ncustom_effect_tooltip = TFR_SPA_recovery_programme_1_tt',
    'P03': '\n'.join(f'{s} = {{ if = {{ limit = {{ is_owned_and_controlled_by = ROOT }} '+''.join(f'if = {{ limit = {{ has_dynamic_modifier = {d} }} remove_dynamic_modifier = {{ modifier = {d} }} }} ' for d in ('autonomous_state','semi_autonomous_state'))+'} }' for s in (165,171,792)),
    'P04': 'if = { limit = { check_variable = { TFR_SPA_recovery_stage < 2 } } set_variable = { TFR_SPA_recovery_stage = 2 } }\nTFR_SPA_advance_recovery_programme_2 = yes\ncustom_effect_tooltip = TFR_SPA_recovery_2_tt\ncustom_effect_tooltip = TFR_SPA_recovery_programme_2_tt',
    'P05': 'TFR_SPA_advance_recovery_programme_3 = yes\ncustom_effect_tooltip = TFR_SPA_recovery_programme_3_tt',
    'P07': 'if = { limit = { NOT = { has_idea = war_economy } NOT = { has_idea = tot_economic_mobilisation } } add_ideas = war_economy }',
    'P08': choose('has_country_flag = TFR_SPA_war_mode',
        choose('NOT = { OR = { has_idea = extensive_conscription has_idea = service_by_requirement has_idea = all_adults_serve has_idea = scraping_the_barrel } }', 'add_ideas = extensive_conscription'),
        choose('OR = { has_idea = disarmed_nation has_idea = volunteer_only }', 'add_ideas = limited_conscription')),
    'P09': 'if = { limit = { check_variable = { TFR_SPA_recovery_stage < 3 } } set_variable = { TFR_SPA_recovery_stage = 3 } }\ncustom_effect_tooltip = TFR_SPA_recovery_3_tt',
    'P10': 'set_variable = { TFR_SPA_recovery_stage = 4 }\ncustom_effect_tooltip = TFR_SPA_recovery_clear_tt',
    'P12': 'if = { limit = { has_country_leader = { character = SPA_francisco_franco ruling_only = yes } } swap_ruler_traits = { remove = caudillo_1 add = caudillo_2 } }',
    'E03': placements('infrastructure', 3),
    'E18': placements('infrastructure', 2),
    'E16': '175 = { if = { limit = { is_owned_and_controlled_by = ROOT infrastructure < 5 } add_building_construction = { type = infrastructure level = 1 instant_build = yes } } }',
    'E08': 'TFR_SPA_upgrade_supply_railways = yes',
    'E27': '''every_owned_state = { clr_state_flag = TFR_SPA_placement }
    TFR_SPA_add_domestic_steel = yes
    TFR_SPA_add_domestic_steel = yes
    every_owned_state = { clr_state_flag = TFR_SPA_placement }''',
    'A05': '\n'.join(block(str(state),choose('is_owned_and_controlled_by = ROOT air_base < 10','add_building_construction = { type = air_base level = 2 instant_build = yes }')) for state in (167,169)),
    'N04': 'TFR_SPA_expand_naval_bases = yes',
    'N05': 'add_equipment_to_stockpile = { type = convoy amount = 40 producer = ROOT }',
}


def reward(f):
    code = f['code']
    visible, hidden = [], []
    for bucket in dict.fromkeys(key.split('.')[0] for key in f.get('modifiers', {})):
        visible.append(f'custom_effect_tooltip = TFR_SPA_{bucket}_modifier_tt')
        for key, value in f.get('modifiers', {}).items():
            if not key.startswith(bucket+'.'):
                continue
            # Match Mongolia: the actual constant variable change carries the
            # native modifier tooltip. Credit compensation stays hidden; the
            # final value still grants only the unclaimed old-save reward.
            visible.append(block('add_to_variable',f'{v(key,True)} = {value:g}\ntooltip = {modifier_tip(key)}'))
            hidden.append(f'subtract_from_variable = {{ {v(key,True)} = {value:g} }}\n'+grant_with_credit(v(key,True),'TFR_SPA_credit_'+key.replace('.','_'),value))
        visible.append('custom_effect_tooltip = generic_skip_one_line_tt')
    for allocation in f.get('buildingStates', []):
        state,kind,count = (allocation[k] for k in ('state','kind','count'))
        hidden.append(grant_with_credit(f'TFR_SPA_pending_{state}_{kind}',f'TFR_SPA_credit_building_{kind}',count))
        # Show the normal state/slots/construction effects. The persistent
        # ledger executes this exact allocation once, including after occupation
        # or a temporarily full state; preview effects never grant a second copy.
        visible.append(block('effect_tooltip',block(str(state),f'add_extra_state_shared_building_slots = {count}\nadd_building_construction = {{ type = {TYPES[kind]} level = {count} instant_build = yes }}')))
    for key, amount in f.get('politics', {}).items():
        visible.append({'pp': f'add_political_power = {amount}', 'stability_pp':f'add_stability = {amount/100:g}', 'war_support_pp':f'add_war_support = {amount/100:g}'}[key])
    visible.extend(tech(code,c) for c in RESEARCH.get(code, []))
    if 'researchSlotTarget' in f:
        n=f['researchSlotTarget']
        visible.append(f'if = {{ limit = {{ NOT = {{ amount_research_slots > {n-1} }} }} set_research_slots = {n} }}')
    special = SPECIAL.get(code,'')
    if code in ('P01','P04','P05','P09','P10'):
        # Programme transitions remain real scripted effects; their previews
        # use the same variable tooltip format as ordinary dynamic upgrades.
        for tip in ('recovery_2','recovery_3','recovery_programme_1','recovery_programme_2','recovery_programme_3'):
            special = special.replace(f'custom_effect_tooltip = TFR_SPA_{tip}_tt','')
        hidden.append(special)
        if code in ('P04','P09'):
            stage = 2 if code=='P04' else 3
            visible.append(choose(f'check_variable = {{ TFR_SPA_recovery_stage < {stage} }}',modifier_preview(RECOVERY_PENALTIES[stage],'TFR_SPA_recovery_penalties_tt')))
        if code in ('P01','P04','P05'):
            stage = {'P01':1,'P04':2,'P05':3}[code]
            condition = f'NOT = {{ has_country_flag = TFR_SPA_recovery_programme_expired }} check_variable = {{ TFR_SPA_recovery_programme < {stage} }}'
            if stage>1:
                condition += ' check_variable = { TFR_SPA_recovery_programme > 0 }'
            visible.append(choose(condition,modifier_preview(RECOVERY_PROGRAMMES[stage],'TFR_SPA_recovery_programme_tt')))
        if code=='P01':
            visible.append('custom_effect_tooltip = TFR_SPA_recovery_import_tt')
        elif code=='P10':
            visible.append('custom_effect_tooltip = TFR_SPA_recovery_clear_tt')
    elif f.get('conditionalModifiers'):
        visible += ['custom_effect_tooltip = TFR_SPA_main_war_tt',modifier_preview(f['conditionalModifiers'])]
        hidden.append(special)
    else:
        visible.append(special)
    if code=='E03':
        visible.append('unlock_decision_category_tooltip = TFR_SPA_regional_reconstruction')
    else:
        visible += [f'unlock_decision_tooltip = {{ decision = {p["id"]} show_effect_tooltip = yes }}' for p in PROJECTS if p['focus']==code]
    if code=='P08':
        visible.append(f'unlock_decision_tooltip = {{ decision = {CAMPAIGN} show_effect_tooltip = yes }}')
    if code=='P05':
        visible.append('country_event = { id = TFR_spain_rework.5 days = 1 }')
    for bucket, first_code in BRANCH_MODIFIERS.items():
        if code == first_code:
            # Publish the first bonus before displaying the modifier's tooltip.
            visible += ['hidden_effect = { TFR_SPA_refresh_modifiers = yes }',
                        f'add_dynamic_modifier = {{ modifier = TFR_SPA_{bucket}_dynamic }}']
    if f.get('specialization'):
        hidden.append(f'set_country_flag = TFR_SPA_{f["specialization"]}_specialization')
    hidden += ['TFR_SPA_flush_building_rewards = yes', 'TFR_SPA_refresh_modifiers = yes']
    return block('if', f'limit = {{ NOT = {{ has_country_flag = TFR_SPA_reward_{code} }} }}\nhidden_effect = {{ TFR_SPA_apply_balance_revision = yes }}\nset_country_flag = TFR_SPA_reward_{code}\n' + '\n'.join(visible) + '\n' + block('hidden_effect','\n'.join(hidden)))


def available(f):
    c = f['code']; s = []
    # Keep the Academy compact: additional training/support requirements appear
    # in the native tooltip without drawing long lines across other branches.
    s += ['has_completed_focus = '+BY_CODE[code]['id'] for code in f.get('requiredCompletedFocuses',[])]
    s += ['OR = { '+' '.join('has_completed_focus = '+BY_CODE[code]['id'] for code in group)+' }' for group in f.get('requiredCompletedFocusGroups',[])]
    if c in ('D01','D02'):
        s = ['custom_trigger_tooltip = { tooltip = TFR_SPA_postwar_ready_tt TFR_SPA_postwar_tree_ready = yes }']
    if c == 'D01':
        s += ['is_in_faction = no', 'has_war = no', 'is_subject = no', 'NPR = { exists = yes }']
    if c == 'D02':
        s += ['is_subject = no', 'OR = { is_in_faction = no is_in_faction_with = GER }']
    if c == 'D04':
        s += ['OR = { is_in_faction = no is_in_faction_with = GER }','GER = { exists = yes is_faction_leader = yes has_government = fascism }','NOT = { has_war_with = GER }']
    if c in ('D05','D06'):
        s += ['NPR = { exists = yes is_subject = no has_war = no }']
        s += [f'{state} = {{ is_owned_and_controlled_by = NPR }}' for state in (112,179,180,181,795)]
    if c in ('D05','D07','P11'):
        s += ['date > 1938.12.31']
    if c == 'D07':
        s += ['NPR = { exists = yes }', 'NOT = { has_global_flag = TFR_SPA_portugal_relocation_started }']
    if c == 'D08':
        s += [f'{state} = {{ is_owned_and_controlled_by = ROOT }}' for state in (112,179,180,181,795)]
    if c == 'D12':
        s += ['TFR_SPA_main_axis_war = yes']
    if c == 'D14':
        s += ['OR = { has_country_flag = TFR_SPA_relocation_complete has_completed_focus = TFR_SPA_integrate_portugal }']
    def gated_1940(code):
        return any('1940.1.1' in x for x in BY_CODE[code].get('conditions',[])) or any(all(gated_1940(p) for p in group) for group in BY_CODE[code]['prerequisites'])
    if any('1940.1.1' in x for x in f.get('conditions',[])) and not any(all(gated_1940(p) for p in group) for group in f['prerequisites']):
        s += ['date > 1939.12.31']
    if c in ('D09','E10'):
        s += ['GER = { exists = yes }', 'NOT = { has_war_with = GER }']
    if c == 'D10':
        s += ['ITA = { exists = yes }','NOT = { has_war_with = ITA }']
    return '\n'.join(s)


def generate_focuses():
    # Native loading resolves relative anchors immediately. Keep every generated
    # focus in the country tree, after original anchors, in dependency order.
    text = ''
    for f in dependency_order(FOCUSES, lambda f:f['id'], lambda f:f['relative_position_id']):
        c=f['code']
        body = f'id = {f["id"]}\nicon = {f["icon"]}\n'
        if 'relative_position_id' in f:
            body += f'relative_position_id = {f["relative_position_id"]}\n'
        body += f'x = {f["x"]}\ny = {f["y"]}\ncost = {f["days"]/7:g}\navailable_if_capitulated = no\ncancel_if_invalid = yes\n'
        # Visibility is static. Dates, identity, civil-war outcome and choices
        # belong in available/prerequisites, never in branch visibility.
        body += 'allow_branch = { always = yes }\n'
        if conditions := available(f):
            body += block('available',conditions)
        if c == 'D07':
            body += block('bypass','has_country_flag = TFR_SPA_war_mode\nNPR = { exists = no }\n'+'\n'.join(f'{s} = {{ is_owned_and_controlled_by = ROOT }}' for s in (112,179,180,181,795)))
        for group in f['prerequisites']:
            body += 'prerequisite = { ' + ' '.join('focus = '+BY_CODE[p]['id'] for p in group) + ' }\n'
        if f.get('exclusiveWith'):
            body += 'mutually_exclusive = { ' + ' '.join('focus = '+BY_CODE[p]['id'] for p in f['exclusiveWith']) + ' }\n'
        body += 'ai_will_do = { factor = 1 }\n' + block('completion_reward',reward(f))
        text += block('focus',body)+'\n'
        LOC[f['id']]=f['name']
        LOC[f['id']+'_desc']=''
    OUT['common/national_focus/spain.txt'] = merge_country_focuses(text).encode('utf-8')
    OUT['common/national_focus/TFR_spain_rework.txt'] = (
        '# Postwar focuses are generated inside spain.txt, after their relative anchors.\n'
    ).encode('utf-8')


def generate_modifiers():
    text=''
    for bucket,name in [('economy','Spanish Economy'),('army','Spanish Armed Forces'),('air','Spanish Air Force'),('navy','Spanish Navy')]:
        icon={'economy':'GFX_idea_generic_production_bonus','army':'GFX_idea_generic_army_war_college','air':'GFX_idea_generic_air_fighter','navy':'GFX_idea_generic_navy_bonus'}[bucket]
        body = f'enable = {{ has_country_flag = TFR_SPA_rework_initialized }}\nicon = {icon}\n'
        if bucket in BRANCH_MODIFIERS:
            body = body.replace('has_country_flag = TFR_SPA_rework_initialized',
                                f'has_country_flag = TFR_SPA_rework_initialized TFR_SPA_{bucket}_branch_started = yes')
        for key in MODS:
            if key.startswith(bucket+'.'):
                body+= f'{key.split(".")[1]} = var:{v(key)}\n'
        text += block('TFR_SPA_'+bucket+'_dynamic',body)+'\n'
        LOC['TFR_SPA_'+bucket+'_dynamic']=name
        LOC['TFR_SPA_'+bucket+'_dynamic_desc']='Developed through the national focus tree.'
    emit('common/dynamic_modifiers/TFR_spain_rework.txt',text)


def generate_runtime():
    effects = ''
    # Existing rework saves store permanent rewards as variables. Rebase only
    # rewards already paid under the previous balance, once. Do this before a
    # newly completed focus is marked paid, and never touch recovery profiles.
    deltas=BALANCE_REVISION['permanent_reward_deltas']
    rebalance=''
    positive_keys={key for code in deltas for key,value in BY_CODE[code]['modifiers'].items() if key in deltas[code] and value>0}
    for key in sorted(positive_keys):
        rebalance+=f'set_temp_variable = {{ TFR_SPA_balance_before_{key.replace(".","_")} = {v(key,True)} }}\n'
    for code,values in deltas.items():
        rebalance+=choose(f'has_country_flag = TFR_SPA_reward_{code}','\n'.join(addmod(key,delta) for key,delta in values.items()))
    for key in sorted(positive_keys):
        before='TFR_SPA_balance_before_'+key.replace('.','_')
        rebalance+='set_temp_variable = { TFR_SPA_balance_floor = 0 }\n'
        for idea,values in LEGACY_IDEAS.items():
            if not idea.startswith('SPA_national_recovery_') and values.get(key,0)>0:
                rebalance+=choose(f'has_completed_focus = {idea}',f'add_to_temp_variable = {{ TFR_SPA_balance_floor = {values[key]:g} }}')
        rebalance+=choose(f'check_variable = {{ var = TFR_SPA_balance_floor value = {before} compare = greater_than }}',f'set_temp_variable = {{ TFR_SPA_balance_floor = {before} }}')
        # If an old focus consumed an imported reward, preserve that imported
        # benefit and return unused credit instead of weakening the old idea.
        rebalance+=choose(f'check_variable = {{ var = {v(key,True)} value = TFR_SPA_balance_floor compare = less_than }}',
            f'set_temp_variable = {{ TFR_SPA_balance_restore = TFR_SPA_balance_floor }}\nsubtract_from_temp_variable = {{ TFR_SPA_balance_restore = {v(key,True)} }}\nadd_to_variable = {{ TFR_SPA_credit_{key.replace(".","_")} = TFR_SPA_balance_restore }}\nset_variable = {{ {v(key,True)} = TFR_SPA_balance_floor }}')
    rebalance+=f'set_country_flag = TFR_SPA_balance_revision_{BALANCE_REVISION["revision"]}\n'
    effects+=block('TFR_SPA_apply_balance_revision',choose(f'has_country_flag = TFR_SPA_rework_initialized NOT = {{ has_country_flag = TFR_SPA_balance_revision_{BALANCE_REVISION["revision"]} }}',rebalance))+'\n'
    # Positive National Recovery and negative Recovering from the Civil War are
    # separate components of the same economy modifier. Keep every numeric field
    # from the original ideas, including AI diplomacy and faction tension.
    expire=choose('check_variable = { TFR_SPA_recovery_programme > 0 } OR = { AND = { has_country_flag = TFR_SPA_recovery_legacy_clock any_state = { has_state_flag = { flag = SPA_national_recovery_2civ days > 1824 } } } AND = { NOT = { has_country_flag = TFR_SPA_recovery_legacy_clock } has_country_flag = { flag = TFR_SPA_recovery_programme_started days > 1824 } } }',
        'set_variable = { TFR_SPA_recovery_programme = 0 }\nset_country_flag = TFR_SPA_recovery_programme_expired')
    effects+=block('TFR_SPA_expire_recovery_programme',expire)+'\n'
    start=choose('NOT = { has_country_flag = TFR_SPA_recovery_programme_started } NOT = { has_country_flag = TFR_SPA_recovery_programme_expired }',
        'set_country_flag = TFR_SPA_recovery_programme_started\nset_variable = { TFR_SPA_recovery_programme = 1 }')
    effects+=block('TFR_SPA_start_recovery_programme',start)+'\n'
    for stage in (2,3):
        effects+=block(f'TFR_SPA_advance_recovery_programme_{stage}',choose(f'NOT = {{ has_country_flag = TFR_SPA_recovery_programme_expired }} check_variable = {{ TFR_SPA_recovery_programme > 0 }} check_variable = {{ TFR_SPA_recovery_programme < {stage} }}',f'set_variable = {{ TFR_SPA_recovery_programme = {stage} }}'))+'\n'
    refresh = 'TFR_SPA_apply_balance_revision = yes\nTFR_SPA_expire_recovery_programme = yes\n'+'\n'.join(f'set_variable = {{ {v(k)} = {v(k,True)} }}' for k in MODS)+'\n'
    # Apply after rebuilding the displayed value so daily refreshes cannot stack it.
    refresh += 'subtract_from_variable = { TFR_SPA_army_planning_speed = 0.025 }\n'
    # Project saved rewards onto the permitted specialisations. Old saves may
    # have completed both sides before mutual exclusion existed. Resolve those
    # to infantry/artillery, without rewriting their earned base variables or
    # touching recovery, logistics, economic upgrades or third-party modifiers.
    for choice in PLAN.get('militaryChoices',[]):
        preferred=choice['legacyPreferred']
        for option in choice['options']:
            if option['root']==preferred:continue
            for code in option['focuses']:
                adjustment='\n'.join(addmod(key,-value,False) for key,value in BY_CODE[code].get('modifiers',{}).items())
                if adjustment:
                    refresh+=choose(f'has_country_flag = TFR_SPA_reward_{preferred} has_country_flag = TFR_SPA_reward_{code}',adjustment)
    # Consumer-goods reductions are the same welfare programme as the planned
    # permanent reductions: apply the stronger benefit, without adding a second
    # copy. Other fields remain distinct bonuses, preserving mixed old saves.
    for stage,values in RECOVERY_PROGRAMMES.items():
        profile=''
        for key,value in values.items():
            if key=='economy.consumer_goods_factor':
                profile+=choose(f'check_variable = {{ {v(key)} > {value:g} }}',f'set_variable = {{ {v(key)} = {value:g} }}')
            else:
                profile+=addmod(key,value,False)
        refresh+=choose(f'check_variable = {{ TFR_SPA_recovery_programme = {stage} }}',profile)
    for stage,values in RECOVERY_PENALTIES.items():
        body = f'limit = {{ check_variable = {{ TFR_SPA_recovery_stage = {stage} }} }}\n'
        body += '\n'.join(addmod(k,val,False) for k,val in values.items())
        refresh+=block('if',body)
    refresh+=choose('check_variable = { TFR_SPA_recovery_stage < 4 }',
        'set_rule = { can_decline_call_to_war = yes }\nset_country_flag = TFR_SPA_recovery_decline_override',
        choose('has_country_flag = TFR_SPA_recovery_decline_override',
            choose('NOT = { has_country_flag = TFR_SPA_volunteer_mode }','clear_rule = { can_decline_call_to_war = yes }')+'clr_country_flag = TFR_SPA_recovery_decline_override'))
    for f in FOCUSES:
        if f.get('conditionalModifiers'):
            refresh+=block('if',f'limit = {{ has_completed_focus = {f["id"]} TFR_SPA_main_axis_war = yes }}\n'+'\n'.join(addmod(k,val,False) for k,val in f['conditionalModifiers'].items()))
    # Migrate existing saves that received all four modifiers at mode selection.
    # Reward flags work during completion; completed focuses cover older saves.
    for bucket in BRANCH_MODIFIERS:
        modifier = f'TFR_SPA_{bucket}_dynamic'
        refresh += choose('has_country_flag = TFR_SPA_rework_initialized',
            choose(f'TFR_SPA_{bucket}_branch_started = yes',
                choose(f'NOT = {{ has_dynamic_modifier = {{ modifier = {modifier} }} }}',
                       f'add_dynamic_modifier = {{ modifier = {modifier} }}'),
                choose(f'has_dynamic_modifier = {{ modifier = {modifier} }}',
                       f'remove_dynamic_modifier = {{ modifier = {modifier} }}')))
    # A country's modifiers are updated immediately after effects, then daily by the engine.
    effects+=block('TFR_SPA_refresh_modifiers',refresh)+'\n'
    init='limit = { NOT = { has_country_flag = TFR_SPA_rework_initialized } }\nset_country_flag = TFR_SPA_rework_initialized\n'
    init+='\n'.join(f'set_variable = {{ {v(k,True)} = 0 }}\nset_variable = {{ TFR_SPA_credit_{k.replace(".","_")} = 0 }}' for k in MODS)+'\n'
    init+='set_variable = { TFR_SPA_recovery_stage = 4 }\nset_variable = { TFR_SPA_recovery_programme = 0 }\n'
    for stage,suffix in [(1,''),(2,'_2'),(3,'_3')]:
        init+=f'if = {{ limit = {{ has_idea = SPA_recovering_from_civil_war{suffix} }} set_variable = {{ TFR_SPA_recovery_stage = {stage} }} }}\n'
    init+='\n'.join('remove_ideas = '+i for i in ('SPA_recovering_from_civil_war','SPA_recovering_from_civil_war_2','SPA_recovering_from_civil_war_3'))+'\n'
    # Import only effects already earned in old saves. New-tree purchases of these
    # migrated rewards are marked paid without repeating buildings, PP or stats.
    for old,values in LEGACY_IDEAS.items():
        if old.startswith('SPA_national_recovery_'):
            stage=int(old.rsplit('_',1)[1])
            init+=choose(f'has_idea = {old}', f'set_variable = {{ TFR_SPA_recovery_programme = {stage} }}\nset_country_flag = TFR_SPA_recovery_programme_started\n'+choose('any_state = { has_state_flag = SPA_national_recovery_2civ }','set_country_flag = TFR_SPA_recovery_legacy_clock')+f'remove_ideas = {old}')
            continue
        import_stats='\n'.join(addmod(k,val)+'\n'+f'add_to_variable = {{ TFR_SPA_credit_{k.replace(".","_")} = {val:g} }}' for k,val in values.items())
        init+=choose(f'has_idea = {old}',import_stats+f'\nremove_ideas = {old}')
    legacy_factories={
        'SPA_the_national_and_popular_army_of_spain_2mil':('mil',2),
        'SPA_support_the_war_industry_1civ':('civ',1),
        'SPA_expand_the_war_industry_2mil':('mil',2),
        'SPA_national_recovery_2civ':('civ',2),
        'SPA_ensure_agricultural_self_sufficiency_2civ':('civ',2),
        'SPA_invest_in_naval_infrastructure_3DY':('dock',3),
        'SPA_expand_the_slipways_3DY':('dock',3),
    }
    for flag,(kind,n) in legacy_factories.items():
        init+=block('every_owned_state',f'limit = {{ has_state_flag = {flag} }}\nPREV = {{ add_to_variable = {{ TFR_SPA_credit_building_{kind} = {n} }} }}')
    init+='TFR_SPA_refresh_modifiers = yes\n'+'\n'.join('add_dynamic_modifier = { modifier = TFR_SPA_'+b+'_dynamic }' for b in ('economy','army'))+'\nmark_focus_tree_layout_dirty = yes'
    effects+=block('TFR_SPA_initialize',block('if',init))+'\n'
    effects+=block('TFR_SPA_enforce_volunteer_rules','''set_rule = {
        desc = TFR_SPA_volunteer_role_tt
        can_not_declare_war = yes
        can_join_factions = no
        can_create_factions = no
        can_decline_call_to_war = yes
    }
    if = { limit = { is_in_faction = yes } leave_faction = yes }''')+'\n'
    # Factory queues survive save/load, occupation, and temporarily missing coasts.
    # A successful placement is measured before consuming the queued unit.
    flush=''
    for state,kind in BUILDING_DESTINATIONS:
        building=TYPES[kind]
        pending=f'TFR_SPA_pending_{state}_{kind}'
        eligible=f'is_owned_and_controlled_by = ROOT is_core_of = ROOT free_building_slots = {{ building = {building} size > 0 include_locked = yes }} {building} < '+('3' if kind=='refinery' else '20')
        if kind=='dock':eligible+=' is_coastal = yes'
        action=f'''set_variable = {{ TFR_SPA_before = building_level@{building} }}
            add_extra_state_shared_building_slots = 1
            add_building_construction = {{ type = {building} level = 1 instant_build = yes }}
            if = {{ limit = {{ check_variable = {{ var = building_level@{building} value = TFR_SPA_before compare = greater_than }} }}
                ROOT = {{ subtract_from_variable = {{ {pending} = 1 }} }}
            }}
            else = {{ ROOT = {{ set_temp_variable = {{ TFR_SPA_queue_break = 1 }} }} }}'''
        flush+=block('while_loop_effect',f'limit = {{ check_variable = {{ {pending} > 0 }} {state} = {{ {eligible} }} }}\nbreak = TFR_SPA_queue_break\n'+block(str(state),action))
        flush+='set_temp_variable = { TFR_SPA_queue_break = 0 }\n'
    # Retain the previous version's generic queues for saves with rewards
    # already pending before destinations were made explicit.
    for kind,building in TYPES.items():
        eligible=f'is_owned_and_controlled_by = PREV is_core_of = PREV free_building_slots = {{ building = {building} size > 0 include_locked = yes }}'
        if kind=='dock': eligible+=' is_coastal = yes'
        # Shared slots are supplied immediately before construction, so existing
        # states can receive factories even when their normal shared slots are full.
        eligible += f' {building} < '+('3' if kind=='refinery' else '20')
        action=f'''limit = {{ {eligible} }}
        set_variable = {{ TFR_SPA_before = building_level@{building} }}
        add_extra_state_shared_building_slots = 1
        add_building_construction = {{ type = {building} level = 1 instant_build = yes }}
        if = {{ limit = {{ check_variable = {{ var = building_level@{building} value = TFR_SPA_before compare = greater_than }} }}
            PREV = {{ subtract_from_variable = {{ TFR_SPA_pending_{kind} = 1 }} }}
        }}
        else = {{ PREV = {{ set_temp_variable = {{ TFR_SPA_queue_break = 1 }} }} }}'''
        flush+=block('while_loop_effect',f'limit = {{ check_variable = {{ TFR_SPA_pending_{kind} > 0 }} any_owned_state = {{ {eligible} }} }}\nbreak = TFR_SPA_queue_break\n'+block('random_owned_controlled_state',action))
        flush+='set_temp_variable = { TFR_SPA_queue_break = 0 }\n'
    flush+='TFR_SPA_flush_naval_arsenals = yes\n'
    effects+=block('TFR_SPA_flush_building_rewards',flush)+'\n'
    arsenals=''
    for part,other in [('a','b'),('b','a')]:
        flag='TFR_SPA_naval_arsenal_'+part
        otherflag='TFR_SPA_naval_arsenal_'+other
        choose_state=choose(f'NOT = {{ any_owned_state = {{ has_state_flag = {flag} }} }}',
            block('random_owned_controlled_state',f'limit = {{ is_core_of = PREV is_coastal = yes dockyard < 18 free_building_slots = {{ building = dockyard size > 2 include_locked = yes }} NOT = {{ has_state_flag = {otherflag} }} }}\nset_state_flag = {flag}'))
        eligible=f'has_state_flag = {flag} is_owned_and_controlled_by = PREV is_core_of = PREV is_coastal = yes dockyard < 20 free_building_slots = {{ building = dockyard size > 0 include_locked = yes }}'
        place=block('random_owned_controlled_state',f'''limit = {{ {eligible} }}
            set_variable = {{ TFR_SPA_before = building_level@dockyard }}
            add_extra_state_shared_building_slots = 1
            add_building_construction = {{ type = dockyard level = 1 instant_build = yes }}
            if = {{ limit = {{ check_variable = {{ var = building_level@dockyard value = TFR_SPA_before compare = greater_than }} }} PREV = {{ subtract_from_variable = {{ TFR_SPA_pending_naval_arsenal_{part} = 1 }} }} }}
            else = {{ PREV = {{ set_temp_variable = {{ TFR_SPA_queue_break = 1 }} }} }}''')
        arsenals+=choose(f'check_variable = {{ TFR_SPA_pending_naval_arsenal_{part} > 0 }}',
            choose_state+block('while_loop_effect',f'limit = {{ check_variable = {{ TFR_SPA_pending_naval_arsenal_{part} > 0 }} any_owned_state = {{ {eligible} }} }}\nbreak = TFR_SPA_queue_break\n'+place)+'set_temp_variable = { TFR_SPA_queue_break = 0 }')
    effects+=block('TFR_SPA_flush_naval_arsenals',arsenals)+'\n'
    effects+=block('TFR_SPA_request_axis_membership',choose('is_in_faction_with = GER',
        'set_country_flag = TFR_SPA_axis_membership_accepted',
        choose('TFR_SPA_axis_membership_eligible = yes NOT = { has_country_flag = TFR_SPA_axis_request_pending }',
            'set_country_flag = { flag = TFR_SPA_axis_request_pending days = 30 }\nGER = { country_event = { id = TFR_spain_rework.1 days = 1 } }')))+'\n'
    effects+=block('TFR_SPA_portugal_agreement','''save_event_target_as = TFR_SPA_recipient
    NPR = {
        every_owned_state = {
            limit = { is_owned_and_controlled_by = NPR }
            set_building_level = { type = infrastructure level = 5 }
            save_event_target_as = TFR_SPA_portuguese_state
            NPR = { give_resource_rights = { receiver = event_target:TFR_SPA_recipient state = event_target:TFR_SPA_portuguese_state } }
        }
    }''')+'\n'
    effects+=block('TFR_SPA_begin_relocation','''if = {
        limit = { NOT = { has_global_flag = TFR_SPA_portugal_relocation_started } }
        set_global_flag = TFR_SPA_portugal_relocation_started
        set_country_flag = TFR_SPA_relocating_industry
        NPR = {
            set_country_flag = TFR_SPA_stop_portuguese_industry_growth
            every_owned_state = {
                set_state_flag = TFR_SPA_industry_source
                set_variable = { TFR_SPA_owed_civ = building_level@industrial_complex }
                set_variable = { TFR_SPA_owed_mil = building_level@arms_factory }
                set_variable = { TFR_SPA_owed_dock = building_level@dockyard }
            }
        }
    }
    TFR_SPA_process_relocation = yes''')+'\n'
    relocation='save_event_target_as = TFR_SPA_recipient\n'
    for kind,building in TYPES.items():
        if kind=='refinery':continue
        eligible=f'is_owned_and_controlled_by = PREV is_core_of = PREV {building} < 20 free_building_slots = {{ building = {building} size > 0 include_locked = yes }}'+(' is_coastal = yes' if kind=='dock' else '')
        move=f'''limit = {{ is_owned_and_controlled_by = NPR has_state_flag = TFR_SPA_industry_source }}
        # Never recreate factories destroyed or moved by another mechanic.
        if = {{ limit = {{ check_variable = {{ var = TFR_SPA_owed_{kind} value = building_level@{building} compare = greater_than }} }} set_variable = {{ TFR_SPA_owed_{kind} = building_level@{building} }} }}
        save_event_target_as = TFR_SPA_industry_source
        while_loop_effect = {{
            limit = {{ check_variable = {{ TFR_SPA_owed_{kind} > 0 }} event_target:TFR_SPA_recipient = {{ any_owned_state = {{ {eligible} }} }} }}
            break = TFR_SPA_transfer_break
            event_target:TFR_SPA_recipient = {{
                random_owned_controlled_state = {{
                    limit = {{ {eligible} }}
                    set_variable = {{ TFR_SPA_before = building_level@{building} }}
                    add_extra_state_shared_building_slots = 1
                    add_building_construction = {{ type = {building} level = 1 instant_build = yes }}
                    if = {{
                        limit = {{ check_variable = {{ var = building_level@{building} value = TFR_SPA_before compare = greater_than }} }}
                        event_target:TFR_SPA_industry_source = {{
                            remove_building = {{ type = {building} level = 1 }}
                            subtract_from_variable = {{ TFR_SPA_owed_{kind} = 1 }}
                        }}
                        event_target:TFR_SPA_recipient = {{ add_to_variable = {{ TFR_SPA_transferred_{kind} = 1 }} }}
                    }}
                    else = {{ event_target:TFR_SPA_industry_source = {{ set_temp_variable = {{ TFR_SPA_transfer_break = 1 }} }} }}
                }}
            }}
        }}
        set_temp_variable = {{ TFR_SPA_transfer_break = 0 }}'''
        relocation+=block('NPR',block('every_owned_state',move))
    relocation+='''if = {
        limit = {
            has_country_flag = TFR_SPA_relocating_industry
            NOT = { has_country_flag = TFR_SPA_relocation_complete }
            NOT = { any_state = { has_state_flag = TFR_SPA_industry_source OR = { check_variable = { TFR_SPA_owed_civ > 0 } check_variable = { TFR_SPA_owed_mil > 0 } check_variable = { TFR_SPA_owed_dock > 0 } } } }
        }
        clr_country_flag = TFR_SPA_relocating_industry
        set_country_flag = TFR_SPA_relocation_complete
        country_event = { id = TFR_spain_rework.4 days = 1 }
    }'''
    effects+=block('TFR_SPA_process_relocation',relocation)+'\n'
    effects+=block('TFR_SPA_add_domestic_steel',choose('any_owned_state = { is_owned_and_controlled_by = PREV is_core_of = PREV NOT = { has_state_flag = TFR_SPA_placement } OR = { industrial_complex > 0 arms_factory > 0 } }', '''random_owned_controlled_state = {
            limit = { is_core_of = PREV NOT = { has_state_flag = TFR_SPA_placement } OR = { industrial_complex > 0 arms_factory > 0 } }
            set_state_flag = TFR_SPA_placement
            add_resource = { type = steel amount = 6 }
        }''', 'add_political_power = 25'))+'\n'
    # Increment an existing internal supply corridor by one, maximum level three.
    rail=''
    for target in (171,165):
        connection=f'start_state = 41 target_state = {target} build_only_on_allied = yes'
        rail+=choose(f'41 = {{ is_owned_and_controlled_by = ROOT }} {target} = {{ is_owned_and_controlled_by = ROOT }}',
            choose(f'has_railway_level = {{ state = 41 level = 3 }} has_railway_level = {{ state = {target} level = 3 }}', 'add_political_power = 50',
                choose(f'OR = {{ has_railway_level = {{ state = 41 level = 2 }} has_railway_level = {{ state = {target} level = 2 }} }}', f'build_railway = {{ {connection} level = 3 }}', f'build_railway = {{ {connection} level = 2 }}')),
            'add_political_power = 50')
    effects+=block('TFR_SPA_upgrade_supply_railways',rail)+'\n'
    naval=''
    # Existing Spanish naval-base provinces, not random ports in captured territory.
    for province,state in ((758,171),(1048,169),(10024,168)):
        test=f'any_province_building_level = {{ province = {{ id = {province} }} building = naval_base level < 10 }}'
        one=choose(test, f'add_building_construction = {{ type = naval_base province = {province} level = 1 instant_build = yes }}')
        naval+=choose(f'{state} = {{ is_owned_and_controlled_by = ROOT {test} }}', f'{state} = {{ '+one+one+' }', 'add_political_power = 25')
    effects+=block('TFR_SPA_expand_naval_bases',naval)+'\n'
    emit('common/scripted_effects/TFR_spain_rework.txt',effects)


def generate_triggers_actions():
    emit('common/scripted_triggers/TFR_spain_rework.txt','''TFR_SPA_postwar_tree_ready = {
        has_focus_tree = spanish_focus
        original_tag = SPR
        has_global_flag = scw_over
        has_civil_war = no
        OR = { has_government = fascism has_government = neutrality }
        OR = {
            has_country_flag = TFR_SPA_rework_initialized
            has_completed_focus = SPA_con_paquito
            has_completed_focus = SPA_unify_the_nationalist_front
            has_country_leader = { character = SPA_francisco_franco ruling_only = yes }
        }
    }
    TFR_SPA_main_axis_war = {
        has_country_flag = TFR_SPA_war_mode
        is_in_faction_with = GER
        GER = { exists = yes has_war = yes }
        any_enemy_country = { is_major = yes NOT = { original_tag = NPR } has_war_with = GER }
    }
    TFR_SPA_can_retry_axis_request = {
        TFR_SPA_axis_membership_eligible = yes
        has_completed_focus = TFR_SPA_join_the_axis
        NOT = { has_country_flag = TFR_SPA_axis_request_pending }
    }
    TFR_SPA_axis_membership_eligible = {
        has_country_flag = TFR_SPA_war_mode
        is_in_faction = no
        is_subject = no
        NOT = { has_war_with = GER }
        GER = { exists = yes has_government = fascism is_faction_leader = yes }
    }\n\n'''+''.join(block(f'TFR_SPA_{bucket}_branch_started',
        f'OR = {{ has_country_flag = TFR_SPA_reward_{code} has_completed_focus = {BY_CODE[code]["id"]} }}')
        for bucket,code in BRANCH_MODIFIERS.items()))
    daily='''if = {
        limit = { original_tag = SPR has_focus_tree = spanish_focus }
        if = {
            limit = { has_country_flag = TFR_SPA_rework_initialized }
            # The shipped LAR_NewsEvents recovery idea lasts 2190 days. Use the
            # existing war-end flag date so late mode selection and old saves
            # cannot restart that clock.
            if = { limit = { has_global_flag = { flag = scw_over days > 2189 } } set_variable = { TFR_SPA_recovery_stage = 4 } }
            TFR_SPA_flush_building_rewards = yes
            if = { limit = { has_country_flag = TFR_SPA_relocating_industry } TFR_SPA_process_relocation = yes }
            TFR_SPA_refresh_modifiers = yes
            if = { limit = { has_country_flag = TFR_SPA_volunteer_mode } TFR_SPA_enforce_volunteer_rules = yes }
        }
    }'''
    emit('common/on_actions/TFR_spain_rework.txt',block('on_actions',block('on_daily',block('effect',daily))))


def generate_events_decisions():
    text='add_namespace = TFR_spain_rework\n\n'
    text+=block('country_event','''id = TFR_spain_rework.1
        title = TFR_spain_rework.1.t
        desc = TFR_spain_rework.1.d
        picture = GFX_report_event_generic_handshake
        is_triggered_only = yes
        trigger = { tag = GER FROM = { has_country_flag = TFR_SPA_axis_request_pending TFR_SPA_axis_membership_eligible = yes } }
        option = {
            name = TFR_spain_rework.1.a
            ai_chance = { factor = 95 }
            # Recheck after a player has left the request open: diplomacy may change.
            if = {
                limit = { FROM = { has_country_flag = TFR_SPA_axis_request_pending TFR_SPA_axis_membership_eligible = yes } }
                add_to_faction = FROM
                FROM = { clr_country_flag = TFR_SPA_axis_request_pending set_country_flag = TFR_SPA_axis_membership_accepted country_event = { id = TFR_spain_rework.2 days = 1 } }
            }
            else = {
                FROM = { clr_country_flag = TFR_SPA_axis_request_pending country_event = { id = TFR_spain_rework.3 days = 1 } }
            }
        }
        option = {
            name = TFR_spain_rework.1.b
            ai_chance = { factor = 5 }
            FROM = { clr_country_flag = TFR_SPA_axis_request_pending country_event = { id = TFR_spain_rework.3 days = 1 } }
        }''')+'\n'
    for n in (2,3,4):
        picture = 'GFX_report_event_generic_factory' if n == 4 else 'GFX_report_event_generic_handshake'
        text+=block('country_event',f'id = TFR_spain_rework.{n}\ntitle = TFR_spain_rework.{n}.t\ndesc = TFR_spain_rework.{n}.d\npicture = {picture}\nis_triggered_only = yes\noption = {{ name = TFR_spain_rework.continue }}')+'\n'
    text+=block('country_event','''id = TFR_spain_rework.5
        title = TFR_spain_rework.5.t
        desc = TFR_spain_rework.5.d
        picture = GFX_report_event_generic_handshake
        is_triggered_only = yes
        fire_only_once = yes
        trigger = {
            has_completed_focus = TFR_SPA_national_labour_accords
            NOT = { has_country_flag = TFR_SPA_labour_accord_resolved }
        }
        option = {
            name = TFR_spain_rework.5.a
            ai_chance = { factor = 70 }
            if = {
                limit = { NOT = { has_country_flag = TFR_SPA_labour_accord_resolved } }
                add_stability = 0.05
                set_country_flag = TFR_SPA_labour_accord_resolved
            }
        }
        option = {
            name = TFR_spain_rework.5.b
            ai_chance = { factor = 30 }
            if = {
                limit = { NOT = { has_country_flag = TFR_SPA_labour_accord_resolved } }
                add_war_support = 0.1
                add_stability = -0.025
                set_country_flag = TFR_SPA_labour_accord_resolved
            }
        }''')+'\n'
    emit('events/TFR_spain_rework.txt',text)
    categories='TFR_SPA_diplomatic_cooperation = { icon = generic_political_actions allowed = { original_tag = SPR } visible = { has_country_flag = TFR_SPA_rework_initialized } }\n'
    categories+=block('TFR_SPA_regional_reconstruction',f'icon = generic_industry\nallowed = {{ original_tag = SPR }}\nvisible = {{ has_completed_focus = {BY_CODE["E03"]["id"]} }}\nvisible_when_empty = no')
    development_gates=' '.join(f'has_completed_focus = {BY_CODE[c]["id"]}' for c in ('P08','E21','M14'))
    categories+=block('TFR_SPA_development_projects',f'icon = generic_political_actions\nallowed = {{ original_tag = SPR }}\nvisible = {{ OR = {{ {development_gates} }} }}\nvisible_when_empty = no')
    emit('common/decisions/categories/TFR_spain_rework.txt',categories)
    decisions='''TFR_SPA_diplomatic_cooperation = {
        TFR_SPA_renew_axis_request = {
            icon = generic_political_actions
            visible = { has_country_flag = TFR_SPA_war_mode has_completed_focus = TFR_SPA_join_the_axis is_in_faction = no }
            available = { TFR_SPA_can_retry_axis_request = yes }
            cost = 25
            days_re_enable = 30
            complete_effect = { TFR_SPA_request_axis_membership = yes }
            ai_will_do = { factor = 1 }
        }
    }'''
    projects=collections.defaultdict(str)
    for project in PROJECTS:
        name=project['id'];done=name+'_completed';cost=project['cost']
        body=f'icon = generic_industry\nvisible = {{ has_completed_focus = {BY_CODE[project["focus"]]["id"]} NOT = {{ has_country_flag = {done} }} }}\ncost = {cost}\ndays_remove = {project["days"]}\ndays_re_enable = 1\n'
        if 'state' in project:
            state=project['state']
            controlled=f'{state} = {{ is_owned_and_controlled_by = ROOT }}'
            body+=f'available = {{ {state} = {{ is_owned_and_controlled_by = ROOT infrastructure < 5 }} }}\n'
            body+=f'highlight_states = {{ highlight_state_targets = {{ state = {state} }} }}\n'
            body+=block('cancel_trigger','NOT = { '+controlled+' }')
            body+=f'cancel_effect = {{ add_political_power = {cost} }}\n'
            effect=block(str(state),'add_extra_state_shared_building_slots = 1\n'+choose('infrastructure < 5','add_building_construction = { type = infrastructure level = 1 instant_build = yes }'))
            effect=choose(controlled,effect+f'set_country_flag = {done}',f'add_political_power = {cost}')
        else:
            effect=''
            for key,value in project['modifiers'].items():
                effect+=f'custom_effect_tooltip = TFR_SPA_{key.split(".")[0]}_modifier_tt\n'
                effect+=block('add_to_variable',f'{v(key,True)} = {value:g}\ntooltip = {modifier_tip(key)}')
            effect+=f'hidden_effect = {{ set_country_flag = {done} TFR_SPA_refresh_modifiers = yes }}\n'
        body+=block('remove_effect',choose(f'NOT = {{ has_country_flag = {done} }}',effect))
        body+='ai_will_do = { factor = 1 }\n'
        projects[project['category']]+=block(name,body)
        LOC[name]=project['name']
        LOC[name+'_desc']=('Fund a regional reconstruction project. On completion, the highlighted state gains one building slot and one infrastructure level. The political power cost is refunded if control is lost.' if 'state' in project else 'Fund a one-time development project. Its permanent improvements are integrated into the national dynamic modifier when the project finishes.')
    projects['TFR_SPA_development_projects']+=block(CAMPAIGN,f'''icon = generic_political_actions
        visible = {{ has_completed_focus = {BY_CODE['P08']['id']} }}
        available = {{ has_stability > 0.3 NOT = {{ has_war_support > 0.89 }} }}
        cost = 35
        days_re_enable = 120
        complete_effect = {{ add_war_support = 0.05 add_stability = -0.02 }}
        ai_will_do = {{ factor = 1 }}''')
    decisions+='\n'+''.join(block(category,body) for category,body in projects.items())
    emit('common/decisions/TFR_spain_rework.txt',decisions)
    LOC.update({
        'TFR_SPA_volunteer_role_tt':'Spain permanently supports its partners through volunteers. Cannot join or create factions, declare wars, or join foreign wars. Defensive wars remain possible. Portugal remains independent.',
        'TFR_SPA_postwar_ready_tt':"Finish the Spanish Civil War as Franco's Nationalist Spain before starting this focus.",
        'TFR_SPA_war_role_tt':'Spain may join the Axis and participate directly in its wars. The Portuguese annexation and integration route is available from 1939.',
        'TFR_SPA_membership_tt':'Germany receives a membership request and may accept or refuse it. A refused request can be renewed through decisions.',
        'TFR_SPA_resource_rights_tt':'Gain resource rights to all Portuguese resources, including coal. Portuguese infrastructure becomes level 5.',
        'TFR_SPA_relocation_tt':'Move the civilian factories, military factories and dockyards actually present in mainland Portugal into Spain, with building slots. Remove the transferred buildings from Portugal and end its scripted industry growth. Any pending transfer is retried daily.',
        'TFR_SPA_main_war_tt':'The additional wartime modifiers apply only while Spain and Germany fight the same enemy major power as members of the same faction. War against Portugal alone does not qualify.',
        'TFR_SPA_war_commitment_tt':'Additional factory output and army organization apply while Spain and Germany fight the same enemy major power in the same faction. War against Portugal alone does not qualify.',
        'TFR_SPA_war_coordination_tt':'Additional army recovery applies while Spain and Germany fight the same enemy major power in the same faction. War against Portugal alone does not qualify.',
        'TFR_SPA_recovery_import_tt':'The current recovery stage is preserved in Spanish Economy. Existing research slots and more advanced mobilisation laws are preserved.',
        'TFR_SPA_recovery_2_tt':'Recovery advances to at least stage 2: factory and dockyard output -14%, construction speed -7%, consumer goods factor +15%.',
        'TFR_SPA_recovery_3_tt':'Recovery advances to at least stage 3: factory and dockyard output -7%, construction speed -4%, consumer goods factor +10%.',
        'TFR_SPA_recovery_clear_tt':'Remove all remaining civil war economic recovery penalties.',
        'TFR_SPA_recovery_programme_1_tt':'Start the original five-year National Recovery programme in Spanish Economy: weekly stability +0.20% and consumer goods factor -15%. A more advanced existing programme is preserved.',
        'TFR_SPA_recovery_programme_2_tt':'Advance National Recovery to at least stage 2: retain its consumer goods and weekly stability bonuses and gain +10% infrastructure construction speed. The original programme expiry date is preserved.',
        'TFR_SPA_recovery_programme_3_tt':'Advance National Recovery to at least stage 3: consumer goods factor -25% and infrastructure construction speed +10%, replacing the temporary weekly stability bonus. Equivalent permanent consumer-goods bonuses do not stack twice.',
        'TFR_SPA_diplomatic_cooperation':'Spanish Diplomatic Cooperation',
        'TFR_SPA_renew_axis_request':'Renew the Axis Membership Request',
        'TFR_SPA_renew_axis_request_desc':'Ask Germany to reconsider Spanish membership of the Axis.',
        'TFR_SPA_regional_reconstruction':'Regional Reconstruction',
        'TFR_SPA_regional_reconstruction_desc':'Restore transport and development capacity in regions damaged by the civil war.',
        'TFR_SPA_development_projects':'National Development Projects',
        'TFR_SPA_development_projects_desc':'Turn the programmes established by our national focuses into practical improvements.',
        CAMPAIGN:'Promote National Service',
        CAMPAIGN+'_desc':'Build public support for national service at the expense of domestic stability.',
        'TFR_spain_rework.1.t':'Spain Requests Axis Membership',
        'TFR_spain_rework.1.d':'Spain has committed to direct participation in the Axis war effort and requests admission to our faction.',
        'TFR_spain_rework.1.a':'Welcome Spain into the Axis.',
        'TFR_spain_rework.1.b':'Refuse the request.',
        'TFR_spain_rework.2.t':'Germany Accepts Spanish Membership',
        'TFR_spain_rework.2.d':'Spain has joined the Axis. Participation in its wars can now be arranged through normal diplomacy.',
        'TFR_spain_rework.3.t':'Germany Refuses Spanish Membership',
        'TFR_spain_rework.3.d':'Germany has declined our request, or changed diplomatic circumstances have prevented admission. We can renew our request through diplomatic decisions when eligible.',
        'TFR_spain_rework.4.t':'Portuguese Industry Relocated',
        'TFR_spain_rework.4.d':'The agreed civilian, military and naval production facilities have been moved into Spain. Portugal remains independent and its resource agreement remains in force.',
        'TFR_spain_rework.5.t':'The National Labour Accords',
        'TFR_spain_rework.5.d':'Employers and labour representatives have agreed on a framework for rebuilding Spain. The government must now decide whether to reassure exhausted communities or demand greater sacrifices for national mobilisation. The economic recovery programme will continue under either settlement.',
        'TFR_spain_rework.5.a':'Prioritise reconciliation and social peace.',
        'TFR_spain_rework.5.b':'Ask the nation to prepare for greater sacrifices.',
        'TFR_spain_rework.continue':'Understood.',
    })


def generate_ai():
    excluded = {'D02','D04','D07','D08','D12','D13','N17'} | {f'M{i:02}' for i in range(13,33)}
    queue='\n'.join(f['id'] for f in FOCUSES if f['code'] not in excluded)
    emit('common/ai_strategy_plans/TFR_spain_rework.txt',block('TFR_SPA_postwar_volunteer_plan','''name = "Spanish postwar development"
        desc = "Volunteer support, economic development and convoy protection"
        allowed = { original_tag = SPR }
        enable = { TFR_SPA_postwar_tree_ready = yes NOT = { has_country_flag = TFR_SPA_war_mode } }
        abort = { OR = { has_country_flag = TFR_SPA_war_mode NOT = { TFR_SPA_postwar_tree_ready = yes } } }
        weight = { factor = 100 }
        '''+block('ai_national_focuses',queue)))


def generate():
    OUT.clear(); LOC.clear()
    for bucket,name in [('economy','Spanish Economy'),('army','Spanish Armed Forces'),('air','Spanish Air Force'),('navy','Spanish Navy')]:
        LOC[f'TFR_SPA_{bucket}_modifier_tt'] = f'Modify §Y{name}§! by:'
    LOC['TFR_SPA_motorized_defence_tt'] = ' $MODIFIER_MOTORIZED_DEFENCE_FACTOR$: $RIGHT|+=%1$'
    LOC['TFR_SPA_navy_fuel_consumption_tt'] = ' $MODIFIER_NAVY_FUEL_CONSUMPTION_FACTOR$: $RIGHT|-=%1$'
    LOC['TFR_SPA_weekly_stability_tt'] = ' $MODIFIER_STABILITY_WEEKLY$: $RIGHT|+=%2$'
    LOC['TFR_SPA_recovery_penalties_tt'] = 'Civil-war recovery in §YSpanish Economy§! becomes:'
    LOC['TFR_SPA_recovery_programme_tt'] = 'National Recovery in §YSpanish Economy§! becomes:'
    generate_focuses(); generate_modifiers(); generate_runtime(); generate_triggers_actions(); generate_events_decisions(); generate_ai()
    text='l_english:\n'+'\n'.join(' '+key+':0 '+json.dumps(val,ensure_ascii=False) for key,val in LOC.items())+'\n'
    # json.dumps doubles the literal localization newline escape.
    text=text.replace('\\\\n','\\n')
    OUT['localisation/replace/TFR_spain_rework_l_english.yml']=b'\xef\xbb\xbf'+text.encode('utf-8')
    return OUT


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    changed=[]
    generated=generate()
    # Write the country tree last, after its scripted dependencies.
    for rel,data in sorted(generated.items(),key=lambda item:item[0]=='common/national_focus/spain.txt'):
        path=ROOT/rel
        if not path.exists() or path.read_bytes()!=data:
            changed.append(rel)
            if not args.check:
                path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    print(json.dumps({'check':args.check,'changed':changed},indent=2))
    if args.check and changed: raise SystemExit(1)
