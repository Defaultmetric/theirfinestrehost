"""Execute the generated scripts in a small deterministic native-effect harness.

This verifies routing, ledgers and balance arithmetic, not the HoI4 executable or
multiplayer UI. Unsupported commands fail rather than silently becoming no-ops.
"""
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
import json
import re
import unittest

import cleanup_volunteer_capacity as syntax
import generate_spain_rework as generator
from test_scw_volunteers import parse, get

ROOT = Path(__file__).resolve().parents[1]
EFFECTS = {k:v for k,_,v in parse(ROOT/'common/scripted_effects/TFR_spain_rework.txt')}
TRIGGERS = {k:v for k,_,v in parse(ROOT/'common/scripted_triggers/TFR_spain_rework.txt')}
FOCUSES = {get(v,'id'):v for k,_,v in parse(ROOT/'common/national_focus/spain.txt')[0][2]
           if k=='focus' and get(v,'id').startswith('TFR_SPA_')}
BY_CODE = {f['code']:FOCUSES[f['id']] for f in generator.FOCUSES}
DECISIONS = {name:body for _,_,category in parse(ROOT/'common/decisions/TFR_spain_rework.txt') for name,_,body in category}
EVENTS = {get(body,'id'):body for kind,_,body in parse(ROOT/'events/TFR_spain_rework.txt') if kind=='country_event'}
PORTUGAL = (112,179,180,181,795)
MAIN_FOCUSES = {get(v,'id'):v for k,_,v in parse(ROOT/'common/national_focus/spain.txt')[0][2] if k=='focus'}


def absolute_position(name, focuses=None, active=None):
    focuses = FOCUSES if focuses is None else focuses
    active = set() if active is None else active
    if name in active:raise AssertionError(('relative position cycle',name))
    active.add(name)
    body=focuses[name] if name in focuses else MAIN_FOCUSES[name]
    p=[int(next((v for key,_,v in body if key==k),'0')) for k in ('x','y')]
    if parent:=next((v for key,_,v in body if key=='relative_position_id'),None):
        q=absolute_position(parent,focuses,active);p=[p[i]+q[i] for i in range(2)]
    active.remove(name)
    return tuple(p)


def plan_position(f):
    return absolute_position(f['id'])


class World:
    def __init__(self):
        self.countries = {t:{'flags':set(),'flag_ages':defaultdict(int),'ideas':set(),'completed':set(),'vars':defaultdict(float),'dynamic':set(),'rules':{},'wars':set(),'faction':None,'major':False,'slots':3,'pp':0,'stability':0,'war_support':0,'tech':set(),'leader':False} for t in ['SPR','GER','ITA','NPR','ENG','ROM']}
        self.states={}
        self.targets={}
        self.global_flags={'scw_over'}
        self.days_since_scw=0
        self.events=[]
        self.rights=[]
        self.research=[]
        self.stockpile=defaultdict(int)
        self.wargoals=[]
        self.from_scope=None
        self.date=(1941,1,1)
        self.countries['SPR']['leader']=True
        for s in (41,165,171,792,169,168,166):self.state(s,'SPR',s in (171,169,168,166))
        for s in (167,175,176,790):self.state(s,'SPR',s in (167,790))
        for s in PORTUGAL:self.state(s,'NPR',True)
        self.countries['GER']['faction']='axis';self.countries['GER']['major']=True
        self.countries['ENG']['major']=True

    def state(self, id, owner, coast=False, **buildings):
        self.states[str(id)]={'owner':owner,'controller':owner,'cores':{owner},'coast':coast,'flags':set(),'flag_ages':defaultdict(int),'vars':defaultdict(float),'buildings':defaultdict(int,buildings),'dynamic':set(),'extra':0,'steel':0,'rail':1}

    def obj(self,scope):
        return self.states[scope] if scope in self.states else self.countries[scope]

    def target(self,name,scope,prev,root):
        if name=='ROOT':return root
        if name=='PREV':return prev
        if name=='THIS':return scope
        if name=='FROM':return self.from_scope
        if name.startswith('event_target:'):return self.targets[name.split(':')[1]]
        return name

    def value(self,x,scope):
        if x.startswith('building_level@'):return self.states[scope]['buildings'][x.split('@')[1]]
        try:return float(x)
        except ValueError:return self.obj(scope)['vars'][x]

    def compare(self,a,op,b):
        if isinstance(a,tuple):return {'=':a==b,'>':a>b,'<':a<b,'>=':a>=b,'<=':a<=b,'!=':a!=b}[op]
        return {'=':a==b,'>':a>b+1e-9,'<':a<b-1e-9,'>=':a>=b-1e-9,'<=':a<=b+1e-9,'!=':a!=b}[op]

    def check(self,entries,scope='SPR',prev=None,root=None):
        root=root or scope
        obj=self.obj(scope)
        def one(k,op,v):
            if k=='OR':return any(one(*e) for e in v)
            if k=='AND':return self.check(v,scope,prev,root)
            if k=='NOT':return not self.check(v,scope,prev,root)
            if k=='always':return v=='yes'
            if k=='custom_trigger_tooltip':return self.check([e for e in v if e[0]!='tooltip'],scope,prev,root)
            if k=='has_country_flag' or k=='has_state_flag':
                if isinstance(v,list):
                    name=get(v,'flag');key,operator,days=next(e for e in v if e[0]=='days')
                    return name in obj['flags'] and self.compare(obj['flag_ages'][name],operator,int(days))
                return v in obj['flags']
            if k=='has_global_flag':
                if isinstance(v,list):
                    key,operator,value=next(e for e in v if e[0]=='days')
                    return get(v,'flag') in self.global_flags and self.compare(self.days_since_scw,operator,int(value))
                return v in self.global_flags
            if k=='has_completed_focus':return v in obj['completed']
            if k=='has_idea':return v in obj['ideas']
            if k=='has_tech':return v in obj['tech']
            if k=='has_dynamic_modifier':return (get(v,'modifier') if isinstance(v,list) else v) in obj['dynamic']
            if k=='has_focus_tree':return scope=='SPR' and v=='spanish_focus'
            if k=='original_tag':return scope==v
            if k=='tag':return scope==self.target(v,scope,prev,root)
            if k=='has_country_leader':return obj['leader']
            if k=='has_government':return v=='fascism'
            if k in ('has_civil_war','is_subject'):return v=='no'
            if k=='is_ai':return (obj.get('is_ai',False))==(v=='yes')
            if k=='exists':return (scope in self.countries)==(v=='yes')
            if k=='is_faction_leader':return (scope=='GER')==(v=='yes')
            if k=='is_major':return obj['major']==(v=='yes')
            if k=='is_in_faction':return (obj['faction'] is not None)==(v=='yes')
            if k=='is_in_faction_with':return obj['faction'] is not None and obj['faction']==self.countries[self.target(v,scope,prev,root)]['faction']
            if k=='has_war':return bool(obj['wars'])==(v=='yes')
            if k=='has_war_with':
                target=self.target(v,scope,prev,root)
                return target in obj['wars'] or scope in self.countries[target]['wars']
            if k=='is_owned_and_controlled_by':return obj['owner']==obj['controller']==self.target(v,scope,prev,root)
            if k=='is_core_of':return self.target(v,scope,prev,root) in obj['cores']
            if k=='is_coastal':return obj['coast']==(v=='yes')
            if k=='any_owned_state':return any(self.check(v,s,scope,root) for s,state in self.states.items() if state['owner']==scope)
            if k=='any_state':return any(self.check(v,s,scope,root) for s in self.states)
            if k=='any_enemy_country':return any(self.check(v,t,scope,root) for t in obj['wars'])
            if k=='date':return self.compare(self.date,op,tuple(map(int,v.split('.'))))
            if k=='amount_research_slots':return self.compare(obj['slots'],op,int(v))
            if k in ('has_stability','has_war_support'):return self.compare(obj['stability' if k=='has_stability' else 'war_support'],op,float(v))
            if k=='free_building_slots':
                typ=get(v,'building');cap={'infrastructure':5,'air_base':10,'radar_station':2,'anti_air_building':5,'synthetic_refinery':3}.get(typ,20)
                available=cap-obj['buildings'][typ]
                if typ in generator.TYPES.values():available=min(available,25-sum(obj['buildings'][b] for b in generator.TYPES.values()))
                key,operator,size=next(e for e in v if e[0]=='size')
                return self.compare(available,operator,int(size))
            if k=='any_province_building_level':
                key,op,val=next(e for e in v if e[0]=='level')
                return self.compare(obj['buildings'][get(v,'building')],op,int(val))
            if k=='has_railway_level':return self.states[get(v,'state')]['rail']>=int(get(v,'level'))
            if k=='check_variable':
                if any(e[0]=='var' for e in v):
                    key=get(v,'var');value=get(v,'value');op={'greater_than':'>','less_than':'<','equals':'=','greater_than_or_equals':'>=','less_than_or_equals':'<=','not_equals':'!='}[get(v,'compare')]
                else:key,op,value=v[0]
                return self.compare(self.value(key,scope),op,self.value(value,scope))
            if k in (*generator.TYPES.values(),'infrastructure','air_base'):return self.compare(obj['buildings'][k],op,int(v))
            if k in TRIGGERS:return self.check(TRIGGERS[k],scope,prev,root)==(v=='yes')
            if k in ('ROOT','PREV','FROM') or k.startswith('event_target:') or k in self.countries or k in self.states:
                return self.check(v,self.target(k,scope,prev,root),scope,root)
            raise AssertionError(('unsupported trigger',k,scope))
        return all(one(*e) for e in entries)

    def effect(self,entries,scope='SPR',prev=None,root=None):
        root=root or scope;obj=self.obj(scope);taken=None
        for k,_,v in entries:
            if k=='if':
                taken=self.check(get(v,'limit'),scope,prev,root)
                if taken:self.effect([e for e in v if e[0]!='limit'],scope,prev,root)
            elif k=='else':
                if taken is False:self.effect(v,scope,prev,root)
            elif k=='hidden_effect':self.effect(v,scope,prev,root)
            elif k in ('set_variable','set_temp_variable','add_to_variable','add_to_temp_variable','subtract_from_variable','subtract_from_temp_variable'):
                key,_,amount=v[0];value=self.value(amount,scope)
                if k.startswith('set_'):obj['vars'][key]=value
                elif k in ('add_to_variable','add_to_temp_variable'):obj['vars'][key]+=value
                else:obj['vars'][key]-=value
            elif k in ('set_country_flag','set_state_flag','clr_country_flag','clr_state_flag'):
                flag=get(v,'flag') if isinstance(v,list) else v
                (obj['flags'].discard if k.startswith('clr_') else obj['flags'].add)(flag)
            elif k in ('set_global_flag','clr_global_flag'):
                (self.global_flags.discard if k.startswith('clr_') else self.global_flags.add)(v)
            elif k=='while_loop_effect':
                for _ in range(501):
                    if not self.check(get(v,'limit'),scope,prev,root):break
                    self.effect([e for e in v if e[0] not in ('limit','break')],scope,prev,root)
                    if self.value(get(v,'break'),scope):break
                else:raise AssertionError('Unbounded loop')
            elif k in ('every_owned_state','random_owned_controlled_state'):
                targets=[s for s,state in self.states.items() if state['owner']==scope and (k=='every_owned_state' or state['controller']==scope)]
                limit=next((a for key,_,a in v if key=='limit'),[])
                targets=[s for s in targets if self.check(limit,s,scope,root)]
                if k.startswith('random'):targets=targets[:1]
                for s in targets:self.effect([e for e in v if e[0]!='limit'],s,scope,root)
            elif k=='save_event_target_as':self.targets[v]=scope
            elif k=='add_extra_state_shared_building_slots':obj['extra']+=int(v)
            elif k=='add_building_construction':
                typ=get(v,'type');n=int(get(v,'level'));cap={'synthetic_refinery':3,'air_base':10,'infrastructure':5}.get(typ,20)
                obj['buildings'][typ]=min(cap,obj['buildings'][typ]+n)
            elif k=='remove_building':
                typ=get(v,'type');obj['buildings'][typ]-=int(get(v,'level'));assert obj['buildings'][typ]>=0
            elif k=='set_building_level':obj['buildings'][get(v,'type')]=int(get(v,'level'))
            elif k=='give_resource_rights':self.rights.append((scope,self.target(get(v,'receiver'),scope,prev,root),self.target(get(v,'state'),scope,prev,root),next((a for key,_,a in v if key=='resources'),None)))
            elif k=='set_rule':obj['rules'].update({key:a for key,_,a in v if key!='desc'})
            elif k=='clear_rule':
                for key,_,a in v:obj['rules'].pop(key,None)
            elif k=='leave_faction':obj['faction']=None
            elif k=='add_to_faction':self.countries[self.target(v,scope,prev,root)]['faction']=obj['faction']
            elif k=='remove_ideas':obj['ideas'].discard(v)
            elif k=='add_ideas':
                for group in [('disarmed_nation','volunteer_only','limited_conscription','extensive_conscription','service_by_requirement','all_adults_serve','scraping_the_barrel'),('civilian_economy','low_economic_mobilisation','partial_economic_mobilisation','war_economy','tot_economic_mobilisation')]:
                    if v in group:obj['ideas'].difference_update(group)
                obj['ideas'].add(v)
            elif k=='set_research_slots':obj['slots']=int(v)
            elif k=='add_dynamic_modifier':obj['dynamic'].add(get(v,'modifier'))
            elif k=='remove_dynamic_modifier':
                assert get(v,'modifier') in obj['dynamic'];obj['dynamic'].remove(get(v,'modifier'))
            elif k=='country_event':self.events.append((scope,get(v,'id')))
            elif k=='create_wargoal':self.wargoals.append((scope,get(v,'target')))
            elif k=='add_political_power':obj['pp']+=float(v)
            elif k=='add_stability':obj['stability']+=float(v)
            elif k=='add_war_support':obj['war_support']+=float(v)
            elif k=='add_tech_bonus':self.research.append((scope,get(v,'category')))
            elif k=='add_resource':obj[get(v,'type')]+=int(get(v,'amount'))
            elif k=='add_equipment_to_stockpile':self.stockpile[(scope,get(v,'type'))]+=int(get(v,'amount'))
            elif k=='build_railway':
                for key in ('start_state','target_state'):
                    state=self.states[get(v,key)];state['rail']=max(state['rail'],int(get(v,'level')))
            elif k=='add_core_of':obj['cores'].add(self.target(v,scope,prev,root))
            elif k in ('custom_effect_tooltip','effect_tooltip','unlock_decision_tooltip','unlock_decision_category_tooltip','mark_focus_tree_layout_dirty','swap_ruler_traits','set_cosmetic_tag'):pass
            elif k in EFFECTS:self.effect(EFFECTS[k],scope,prev,root)
            elif k in ('ROOT','PREV','FROM') or k.startswith('event_target:') or k in self.countries or k in self.states:
                self.effect(v,self.target(k,scope,prev,root),scope,root)
            else:raise AssertionError(('unsupported effect',k,scope))

    def run(self,name,scope='SPR'):self.effect(EFFECTS[name],scope)
    def focus(self,code):
        self.countries['SPR']['completed'].add(get(BY_CODE[code],'id'))
        self.effect(get(BY_CODE[code],'completion_reward'))
    def can_start(self,code):
        focus=BY_CODE[code];completed=self.countries['SPR']['completed']
        available=next((v for k,_,v in focus if k=='available'),[])
        return self.check(available) and all(any(value in completed for _,_,value in group) for k,_,group in focus if k=='prerequisite') and not any(value in completed for k,_,group in focus if k=='mutually_exclusive' for _,_,value in group)
    def stat(self,key):return self.countries['SPR']['vars'][generator.v(key)]
    def total(self,building,owner=None):return sum(s['buildings'][building] for s in self.states.values() if owner is None or s['owner']==owner)


class SpainStructureTests(unittest.TestCase):
    def test_native_variable_grammar_does_not_use_combined_comparison_tokens(self):
        # The generic test parser accepts >= and <=; HoI4 1.19's script lexer
        # does not. This caused the native load failure at D09, line 308.
        for rel,data in generator.generate().items():
            if not rel.endswith('.txt'):continue
            active=re.sub(r'#[^\n]*','',data.decode())
            if rel=='common/national_focus/spain.txt':
                active=data.decode().split(generator.FOCUS_BLOCK_BEGIN)[1].split(generator.FOCUS_BLOCK_END)[0]
                active=re.sub(r'#[^\n]*','',active)
            self.assertIsNone(re.search(r'>=|<=',active),rel)
        for amount,comparison in [(0.05,'greater_than_or_equals'),(-0.05,'less_than_or_equals')]:
            text=generator.grant_with_credit('test_reward','test_credit',amount)
            self.assertIn('compare = '+comparison,text)

    def test_all_rework_focuses_are_always_visible_and_availability_is_inherited(self):
        for phase in ('before_civil_war','during_civil_war','after_civil_war'):
            w=World()
            if phase!='after_civil_war':
                w.global_flags.clear();w.countries['SPR']['leader']=False
            if phase=='during_civil_war':w.global_flags.add('spanish_civil_war')
            for name,focus in FOCUSES.items():
                self.assertEqual(get(focus,'allow_branch'),[('always','=','yes')],name)
                self.assertTrue(w.check(get(focus,'allow_branch')),name)
                if phase!='after_civil_war':
                    self.assertFalse(w.can_start(next(c for c,f in BY_CODE.items() if f is focus)),name)
        for c,focus in BY_CODE.items():
            text=str(next((v for k,_,v in focus if k=='available'),[]))
            if c in ('D01','D02'):self.assertIn('TFR_SPA_postwar_tree_ready',text)
            else:self.assertNotIn('TFR_SPA_postwar_tree_ready',text)
            self.assertNotIn('TFR_SPA_volunteer_mode',text)
            self.assertNotIn('TFR_SPA_war_mode',text)

    def test_replaced_legacy_branches_are_permanently_hidden(self):
        scope=json.loads((ROOT/'tools/spain_rework_legacy_scope.json').read_text())
        tree=parse(ROOT/'common/national_focus/spain.txt')[0][2]
        focuses={get(v,'id'):v for key,_,v in tree if key=='focus'}
        self.assertEqual(len(scope['nationalist']),37)
        self.assertEqual(len(scope['disabled_branch_roots']),8)
        for name in scope['nationalist']+scope['disabled_branch_roots']+scope.get('hidden_civil_war',[]):
            self.assertEqual(get(focuses[name],'allow_branch'),[('always','=','no')],name)

    def test_all_twenty_complete_paths_match_the_reviewed_budget(self):
        scenarios=json.loads((ROOT/'tools/spain_focus_expected_totals.json').read_text())['scenarios']
        self.assertEqual(len(scenarios),20)
        for scenario in scenarios:
            with self.subTest(mode=scenario['mode'],specialization=scenario['specialization'],navy=scenario['navy'],armyLine=scenario['armyLine'],armySupport=scenario['armySupport']):
                choices={'D01' if scenario['mode']=='volunteer' else 'D02', 'E13' if scenario['specialization']=='economy' else 'M13','N16' if scenario['navy']=='escort' else 'N17'}
                exclusive={'D01','D02','E13','M13','N16','N17'}
                if scenario['specialization']=='military':
                    choices.add('M16' if scenario['armyLine']=='infantry' else 'M19')
                    choices.add('M17' if scenario['armySupport']=='artillery' else 'M18')
                    exclusive.update(('M16','M19','M17','M18'))
                excluded=exclusive-choices
                reached=[]
                while True:
                    additions=[]
                    for f in generator.FOCUSES:
                        if f['code'] in reached or f['code'] in excluded:continue
                        # Read the shipped prerequisites, rather than the plan's copy.
                        groups=[body for key,_,body in BY_CODE[f['code']] if key=='prerequisite']
                        ids={generator.BY_CODE[code]['id'] for code in reached}
                        if all(any(value in ids for _,_,value in group) for group in groups):additions.append(f['code'])
                    if not additions:break
                    reached+=additions
                for code in reached:
                    self.assertFalse(set(generator.BY_CODE[code].get('exclusiveWith',[])) & set(reached),code)
                if scenario['specialization']=='military':self.assertIn('M32',reached)
                self.assertEqual(set(reached),set(scenario['reachable']))
                self.assertEqual(len(reached),scenario['count'])
                self.assertEqual(sum(float(get(BY_CODE[c],'cost'))*7 for c in reached),scenario['focus_days'])
                w=World()
                for code in reached:
                    if code=='D08':
                        for state in PORTUGAL:w.states[str(state)]['owner']=w.states[str(state)]['controller']='SPR'
                    if code=='D12':
                        w.countries['SPR']['faction']='axis';w.countries['SPR']['wars'].add('ENG');w.countries['GER']['wars'].add('ENG')
                    w.focus(code)
                # The approved totals describe permanent upgrades. A full path
                # takes more than five years; the original five-year recovery
                # programme has expired by then.
                w.countries['SPR']['flag_ages']['TFR_SPA_recovery_programme_started']=1825
                w.run('TFR_SPA_refresh_modifiers')
                for key,value in scenario['stats'].items():self.assertAlmostEqual(w.stat(key),value,msg=key)
                for kind,value in scenario['buildings'].items():self.assertEqual(w.total(generator.TYPES[kind],'SPR'),value,kind)
                # The total must remain within the explicit budget even after
                # every project available to this permanent specialization.
                for project in generator.PROJECTS:
                    if project['focus'] in reached and project.get('modifiers'):
                        w.effect(get(DECISIONS[project['id']],'remove_effect'))
                limits=json.loads((ROOT/'tools/spain_balance_limits.json').read_text())
                for key,maximum in limits['upper'].items():self.assertLessEqual(w.stat(key),maximum+1e-9,key)
                for key,minimum in limits['lower'].items():self.assertGreaterEqual(w.stat(key),minimum-1e-9,key)

    def test_generator_is_reproducible_and_scripts_are_closed(self):
        for rel,data in generator.generate().items():
            self.assertEqual((ROOT/rel).read_bytes(),data,rel)
            if rel.endswith('.txt'):
                for e in syntax.walk(syntax.parse(data.decode())):
                    self.assertTrue(e.closed,rel)
                    self.assertNotEqual((e.key,e.value),('_','}'),rel)

    def test_nodes_unique_positions_and_references(self):
        self.assertEqual(len(FOCUSES),119)
        def position(name):
            return absolute_position(name)
        positions=set()
        for name,f in FOCUSES.items():
            pos=position(name);self.assertNotIn(pos,positions);positions.add(pos)
            for key,_,body in f:
                if key in ('prerequisite','mutually_exclusive'):
                    for _,_,target in body:self.assertIn(target,FOCUSES)
        self.assertEqual(sum(key=='mutually_exclusive' for f in FOCUSES.values() for key,_,v in f),10)

    def test_presentation_has_nine_air_focuses_and_compact_local_links(self):
        abs_pos=plan_position
        air=[f for f in generator.FOCUSES if f['code'].startswith('A')]
        self.assertEqual([f['code'] for f in air],[f'A{i:02}' for i in range(1,10)])
        self.assertEqual(sum(len(f.get('modifiers',{})) for f in air),8)
        self.assertGreaterEqual(len({get(f,'icon') for f in FOCUSES.values()}),100)
        self.assertLessEqual(max(abs_pos(f)[0] for f in generator.FOCUSES)-min(abs_pos(f)[0] for f in generator.FOCUSES),44)
        self.assertLessEqual(max(abs_pos(f)[1] for f in generator.FOCUSES),19)
        for f in generator.FOCUSES:
            for group in f['prerequisites']:
                for c in group:
                    parent=generator.BY_CODE[c]
                    self.assertLess(abs_pos(parent)[1],abs_pos(f)[1],(c,f['code']))
        for a in generator.FOCUSES:
            for b in generator.FOCUSES:
                pos_a,pos_b=abs_pos(a),abs_pos(b)
                if a['code']!=b['code'] and pos_a[1]==pos_b[1]:
                    self.assertGreaterEqual(abs(pos_a[0]-pos_b[0]),2,(a['code'],b['code']))

    def test_dynamic_rewards_use_native_variable_tooltips(self):
        for f in generator.FOCUSES:
            entries=list(syntax.walk(syntax.parse(generator.reward(f))))
            for key,value in f.get('modifiers',{}).items():
                candidates=[e for e in entries if e.key=='add_to_variable' and e.get(generator.v(key,True)) and e.get('tooltip')]
                self.assertEqual(len(candidates),1,f['code'])
                self.assertAlmostEqual(float(candidates[0].get(generator.v(key,True)).value),value)
                self.assertEqual(candidates[0].get('tooltip').value,generator.modifier_tip(key))
            loc=generator.LOC.get(f['id']+'_effect_tt','')
            self.assertNotIn('%',loc,f['code'])

    def test_neighbouring_focuses_have_different_complete_rewards(self):
        abs_pos=plan_position
        def signature(f):
            return (f.get('modifiers',{}),f.get('conditionalModifiers',{}),f.get('buildings',{}),f.get('politics',{}),generator.RESEARCH.get(f['code'],[]),generator.SPECIAL.get(f['code'],''),f.get('researchSlotTarget'))
        for i,f in enumerate(generator.FOCUSES):
            for g in generator.FOCUSES[i+1:]:
                pos_f,pos_g=abs_pos(f),abs_pos(g)
                if abs(pos_f[0]-pos_g[0])<=3 and abs(pos_f[1]-pos_g[1])<=1:
                    self.assertNotEqual(signature(f),signature(g),(f['code'],g['code']))

    def test_decision_unlocks_resolve_without_duplicating_existing_diplomacy(self):
        self.assertEqual(len(DECISIONS),7)
        self.assertEqual(set(EVENTS),{f'TFR_spain_rework.{n}' for n in range(1,6)})
        categories={name for name,_,body in parse(ROOT/'common/decisions/categories/TFR_spain_rework.txt')}
        for focus in FOCUSES.values():
            for entry in syntax.walk(syntax.parse(generator.reward(generator.BY_CODE[next(c for c,f in BY_CODE.items() if f is focus)]))):
                if entry.key=='unlock_decision_tooltip':self.assertIn(entry.get('decision').value,DECISIONS)
                if entry.key=='unlock_decision_category_tooltip':self.assertIn(entry.value,categories)

    def test_reconstruction_is_centered_and_reachable_from_either_role(self):
        a,b,shared=(generator.BY_CODE[c] for c in ('D01','D02','P01'))
        self.assertLessEqual(min(plan_position(a)[0],plan_position(b)[0]),plan_position(shared)[0])
        self.assertLessEqual(plan_position(shared)[0],max(plan_position(a)[0],plan_position(b)[0]))
        self.assertEqual(plan_position(shared)[1],plan_position(a)[1]+2)
        self.assertEqual(shared['prerequisites'],[['D01','D02']])
        for role in ('D01','D02'):
            w=World();self.assertFalse(w.can_start('P01'));w.focus(role)
            self.assertTrue(w.can_start('P01'));w.focus('P01')
            self.assertTrue(w.can_start('D09'))

    def test_reconstruction_continuation_is_centered_and_branches_do_not_cross_portugal(self):
        by=generator.BY_CODE;root=by['P01'];left=by['P02'];right=by['P04']
        self.assertEqual(plan_position(left)[1],plan_position(root)[1]+1)
        self.assertEqual(plan_position(right)[1],plan_position(left)[1])
        self.assertEqual((plan_position(left)[0]+plan_position(right)[0])/2,plan_position(root)[0])
        self.assertEqual(left['prerequisites'],[['P01']])
        self.assertEqual(right['prerequisites'],[['P01']])
        self.assertEqual(by['E01']['prerequisites'],[['P02']])
        self.assertLess(plan_position(by['E01'])[0],plan_position(left)[0])
        self.assertEqual(by['M01']['prerequisites'],[['P04']])
        self.assertGreater(plan_position(by['M01'])[0],plan_position(right)[0])
        for code in ('A01','N01'):self.assertEqual(by[code]['prerequisites'],[['M01']])
        # Portugal stays outside the reconstruction connectors at the same levels.
        self.assertLessEqual(plan_position(by['D06'])[0],plan_position(by['D09'])[0]-3)
        for code in ('D07','D08','D12','D13'):
            self.assertGreater(plan_position(by[code])[0],plan_position(by['M01'])[0])
        common_army=[f for f in generator.FOCUSES if f['code'].startswith('M') and int(f['code'][1:])<=12]
        air=[f for f in generator.FOCUSES if f['code'].startswith('A')]
        navy=[f for f in generator.FOCUSES if f['code'].startswith('N')]
        self.assertEqual(min(plan_position(f)[0] for f in air)-max(plan_position(f)[0] for f in common_army),3)
        self.assertEqual(min(plan_position(f)[0] for f in navy)-max(plan_position(f)[0] for f in air),3)
        self.assertEqual(by['D14']['prerequisites'],[['D09']])
        # The Portugal agreement/integration gate still applies to partnership.
        w=World();w.focus('D01');w.focus('P01');w.focus('D09')
        self.assertFalse(w.can_start('D14'))
        w.countries['SPR']['flags'].add('TFR_SPA_relocation_complete')
        self.assertTrue(w.can_start('D14'))

    def test_building_rewards_show_native_effects_in_their_actual_destinations(self):
        for f in generator.FOCUSES:
            allocations=f.get('buildingStates',[])
            if not f.get('buildings'):continue
            totals=defaultdict(int)
            w=World();w.focus('D01');w.focus(f['code'])
            for allocation in allocations:
                state,kind,count=(allocation[k] for k in ('state','kind','count'))
                totals[kind]+=count
                self.assertEqual(w.states[str(state)]['buildings'][generator.TYPES[kind]],count)
                self.assertEqual(w.states[str(state)]['extra'],count)
            self.assertEqual(dict(totals),f['buildings'])
            self.assertNotIn(f['id']+'_effect_tt',generator.LOC)
            previews=[e for e in syntax.walk(syntax.parse(generator.reward(f))) if e.key=='effect_tooltip']
            state_previews={int(e.key):e for preview in previews for e in preview.active() if e.key.isdigit()}
            for allocation in allocations:
                preview=state_previews[allocation['state']]
                self.assertEqual(int(preview.get('add_extra_state_shared_building_slots').value),allocation['count'])
                self.assertEqual(preview.get('add_building_construction').get('type').value,generator.TYPES[allocation['kind']])

    def test_other_spanish_routes_are_unchanged(self):
        scope=json.loads((ROOT/'tools/spain_rework_legacy_scope.json').read_text())
        backup=Path((ROOT/'tools/spain_rework_backup_path.txt').read_text())
        if not backup.exists():self.skipTest('Local pre-rework backup unavailable')
        old=parse(backup/'common/national_focus/spain.txt')[0][2];new=parse(ROOT/'common/national_focus/spain.txt')[0][2]
        old={get(v,'id'):v for k,_,v in old if k=='focus'};new={get(v,'id'):v for k,_,v in new if k=='focus'}
        # Main migrated the Latin Bloc to its faction-logo template.
        # Preserve every other field when comparing with the pre-rework backup.
        reward=get(old['SPA_the_latin_bloc'],'completion_reward')
        previous=('create_faction','=','SPA_latin_bloc')
        replacement=('create_faction_from_template','=','faction_template_tfr_spa_latin_bloc')
        self.assertIn(previous,reward)
        reward[reward.index(previous)]=replacement
        for name in scope['untouched']:self.assertEqual(old[name],new[name],name)
        for name in scope['civil_war']:
            allowed=scope.get('civil_war_edits',{}).get(name,[])
            self.assertEqual([e for e in old[name] if e[0] not in allowed],[e for e in new[name] if e[0] not in allowed],name)
        for name in scope['nationalist']+scope['disabled_branch_roots']:
            self.assertEqual([e for e in old[name] if e[0]!='allow_branch'],[e for e in new[name] if e[0]!='allow_branch'],name)

    def test_new_branches_do_not_overlap_the_original_civil_war_focuses(self):
        scope=json.loads((ROOT/'tools/spain_rework_legacy_scope.json').read_text())
        tree=parse(ROOT/'common/national_focus/spain.txt')[0][2]
        old={get(v,'id'):v for key,_,v in tree if key=='focus'}
        def position(name):
            f=old[name];p=[int(get(f,k)) if any(key==k for key,_,v in f) else 0 for k in ('x','y')]
            parent=next((v for key,_,v in f if key=='relative_position_id'),None)
            if parent:
                q=position(parent);p=[p[i]+q[i] for i in range(2)]
            return p
        def position_focus(name):
            return absolute_position(name)
        hidden=set(scope.get('hidden_civil_war',[]))
        for name,focus in FOCUSES.items():
            x,y=position_focus(name)
            for legacy in scope['civil_war']:
                if legacy in hidden:continue
                a,b=position(legacy)
                self.assertFalse(y==b and abs(x-a)<2,(name,legacy))

    def test_focus_descriptions_are_blank_and_no_xp_or_volunteer_capacity(self):
        loc=(ROOT/'localisation/replace/TFR_spain_rework_l_english.yml').read_text(encoding='utf-8-sig')
        for name in FOCUSES:self.assertIn(' '+name+'_desc:0 ""',loc)
        generated='\n'.join((d.decode('utf-8-sig').split(generator.FOCUS_BLOCK_BEGIN)[1].split(generator.FOCUS_BLOCK_END)[0]
                             if p=='common/national_focus/spain.txt' else d.decode('utf-8-sig'))
                            for p,d in generator.generate().items() if p.endswith('.txt'))
        self.assertFalse(re.search(r'\b(?:army_experience|navy_experience|air_experience|experience_gain_\w+|send_volunteer_size|send_volunteer_factor|air_volunteer_cap)\s*=',generated))

    def test_daily_hook_stays_in_native_country_scope(self):
        text=(ROOT/'common/on_actions/TFR_spain_rework.txt').read_text()
        self.assertNotIn('every_country',text)
        self.assertIn('original_tag = SPR',text)

    def test_fake_industry_growth_is_unchanged_outside_portugal(self):
        backup=Path((ROOT/'tools/spain_rework_backup_path.txt').read_text())
        if not backup.exists():self.skipTest('Local pre-rework backup unavailable')
        old={k:v for k,_,v in parse(backup/'common/scripted_effects/TFR_fake_industry_growth.txt')}
        new={k:v for k,_,v in parse(ROOT/'common/scripted_effects/TFR_fake_industry_growth.txt')}
        for name in old:
            if name!='TFR_NPR_apply_logged_industry_growth':self.assertEqual(old[name],new[name],name)
        wrapper=new['TFR_NPR_apply_logged_industry_growth']
        self.assertEqual(len(wrapper),1)
        body=wrapper[0][2]
        self.assertEqual([e for e in body if e[0]!='limit'],old['TFR_NPR_apply_logged_industry_growth'])

    def test_new_diplomatic_guards_only_restrict_volunteer_spain(self):
        diplomacy={k:v for k,_,v in parse(ROOT/'common/scripted_triggers/diplomacy_scripted_triggers.txt')}
        for key,scope in [('WAR','ROOT'),('GENERATE_WARGOAL','ROOT'),('JOIN_ALLY','ROOT'),('CALL_ALLY','FROM'),('JOIN_FACTION','ROOT'),('OFFER_JOIN_FACTION','FROM'),('GUARANTEE','ROOT')]:
            entry=diplomacy['DIPLOMACY_'+key+'_ENABLE_TRIGGER']
            guard=next(e for e in entry if e[0]==scope and 'TFR_SPA_volunteer_mode' in str(e))
            for volunteer in (False,True):
                w=World();w.from_scope='SPR';sender='SPR' if scope=='ROOT' else 'GER'
                if volunteer:w.countries['SPR']['flags'].add('TFR_SPA_volunteer_mode')
                self.assertEqual(w.check([guard],sender,root=sender),not volunteer)


class SpainRuntimeTests(unittest.TestCase):
    def test_military_specialisations_block_the_opposite_and_keep_the_capstone_reachable(self):
        for line in ('M16','M19'):
            for support in ('M17','M18'):
                w=World();w.focus('M13');w.focus('M14')
                other='M19' if line=='M16' else 'M16'
                self.assertTrue(w.can_start(line));self.assertTrue(w.can_start(other))
                w.focus(line);self.assertFalse(w.can_start(other))
                other='M18' if support=='M17' else 'M17'
                self.assertTrue(w.can_start(support));self.assertTrue(w.can_start(other))
                w.focus(support);self.assertFalse(w.can_start(other))
                for c in (['M24'] if line=='M16' else ['M20','M21','M26','M29','M31']):
                    self.assertTrue(w.can_start(c),c);w.focus(c)
                self.assertFalse(w.can_start('M28'))
                for c in ('M15','M23'):w.focus(c)
                self.assertFalse(w.can_start('M28'))
                end='M27' if support=='M17' else 'M25'
                self.assertTrue(w.can_start(end));w.focus(end)
                self.assertTrue(w.can_start('M28'));w.focus('M28')
                self.assertTrue(w.can_start('M30'));w.focus('M30')
                self.assertTrue(w.can_start('M32'))

    def test_academy_availability_cannot_skip_common_training_or_support(self):
        # Non-drawn availability conditions remain mandatory in existing saves.
        for line_end in ('M24','M31'):
            for support_end in ('M27','M25'):
                w=World();w.focus(line_end)
                self.assertFalse(w.can_start('M28'))
                self.assertFalse(w.can_start('M30'))
                w.focus('M15');w.focus('M23')
                self.assertFalse(w.can_start('M28'))
                w.focus(support_end)
                self.assertTrue(w.can_start('M28'));w.focus('M28')
                self.assertTrue(w.can_start('M30'));w.focus('M30')
                self.assertTrue(w.can_start('M32'))

    def test_existing_stacked_military_rewards_keep_only_one_side_of_each_choice(self):
        w=World();w.focus('D01')
        for c in ('M16','M24','M19','M20','M21','M26','M29','M31','M17','M27','M18','M25'):w.focus(c)
        before=dict(w.countries['SPR']['vars'])
        self.assertAlmostEqual(w.stat('army.army_infantry_attack_factor'),.05)
        self.assertAlmostEqual(w.stat('army.army_artillery_attack_factor'),.075)
        self.assertAlmostEqual(w.stat('army.army_artillery_defence_factor'),.05)
        for key in ('army_armor_attack_factor','army_armor_speed_factor','motorized_attack_factor','mechanized_attack_factor','breakthrough_factor','org_loss_when_moving','army_fuel_consumption_factor','special_forces_attack_factor','special_forces_cap','special_forces_defence_factor'):
            self.assertAlmostEqual(w.stat('army.'+key),0,msg=key)
        w.run('TFR_SPA_refresh_modifiers');self.assertEqual(dict(w.countries['SPR']['vars']),before)
        # Compatible common training/recovery still works around the projection.
        w.focus('M04');w.focus('M09');w.focus('M10')
        self.assertAlmostEqual(w.stat('army.special_forces_cap'),.05)
        self.assertAlmostEqual(w.stat('army.special_forces_attack_factor'),.025)
        self.assertAlmostEqual(w.stat('army.army_artillery_defence_factor'),.075)

    def test_balance_revision_rebases_existing_rewards_once(self):
        w=World();w.focus('D01');country=w.countries['SPR']
        country['flags'].discard('TFR_SPA_balance_revision_1')
        country['flags'].update('TFR_SPA_reward_'+c for c in ('E26','E32','M14','M30','N20'))
        for key,value in [('economy.industrial_capacity_factory',.25),('army.army_org_factor',.15),('economy.industrial_capacity_dockyard',.2)]:country['vars'][generator.v(key,True)]=value
        country['vars']['TFR_SPA_recovery_programme']=3
        country['flag_ages']['TFR_SPA_recovery_programme_started']=200
        w.run('TFR_SPA_refresh_modifiers')
        for key,value in [('economy.industrial_capacity_factory',.2),('army.army_org_factor',.1),('economy.industrial_capacity_dockyard',.125)]:self.assertAlmostEqual(w.stat(key),value)
        w.run('TFR_SPA_refresh_modifiers')
        self.assertAlmostEqual(w.stat('economy.industrial_capacity_factory'),.2)
        self.assertEqual(country['vars']['TFR_SPA_recovery_programme'],3)
        self.assertEqual(country['flag_ages']['TFR_SPA_recovery_programme_started'],200)

    def test_balance_revision_preserves_imported_ideas_and_restores_unused_credit(self):
        w=World();w.focus('D01');country=w.countries['SPR']
        country['flags'].discard('TFR_SPA_balance_revision_1')
        country['flags'].add('TFR_SPA_reward_N20')
        country['completed'].add('SPA_italian_shipbuilding_expertise')
        country['vars'][generator.v('economy.industrial_capacity_dockyard',True)]=.1
        w.run('TFR_SPA_refresh_modifiers')
        self.assertAlmostEqual(w.stat('economy.industrial_capacity_dockyard'),.1)
        self.assertAlmostEqual(country['vars']['TFR_SPA_credit_economy_industrial_capacity_dockyard'],.075)
        w.focus('D10');w.focus('N03')
        self.assertAlmostEqual(w.stat('economy.industrial_capacity_dockyard'),.1)

    def test_revision_runs_before_a_new_focus_reward_can_be_reduced_twice(self):
        w=World();w.focus('D01');w.countries['SPR']['flags'].discard('TFR_SPA_balance_revision_1')
        w.focus('E32');self.assertAlmostEqual(w.stat('economy.industrial_capacity_factory'),.075)
        w.run('TFR_SPA_refresh_modifiers');self.assertAlmostEqual(w.stat('economy.industrial_capacity_factory'),.075)

    def test_air_utility_additions_do_not_increase_combat_stats_or_exceed_airfield_cap(self):
        w=World();w.focus('D01');w.focus('A01');w.focus('A02');w.focus('A03')
        combat={key:w.stat(key) for key in ('air.air_mission_efficiency','air.air_agility_factor','air.air_cas_present_factor')}
        w.states['167']['buildings']['air_base']=9
        w.focus('A04');w.focus('A05')
        for key,value in combat.items():self.assertAlmostEqual(w.stat(key),value)
        self.assertAlmostEqual(w.stat('air.air_accidents_factor'),-.1)
        self.assertAlmostEqual(w.stat('air.air_fuel_consumption_factor'),-.05)
        self.assertEqual(w.states['167']['buildings']['air_base'],10)
        self.assertEqual(w.states['169']['buildings']['air_base'],2)
        self.assertEqual(w.total('arms_factory','SPR'),3)

    def test_projects_are_focus_gated_and_grant_only_once_after_completion(self):
        for project in generator.PROJECTS:
            with self.subTest(project=project['id']):
                w=World();w.focus('D01');decision=DECISIONS[project['id']]
                self.assertFalse(w.check(get(decision,'visible')))
                w.focus(project['focus']);self.assertTrue(w.check(get(decision,'visible')))
                self.assertEqual(int(get(decision,'cost')),project['cost'])
                self.assertEqual(int(get(decision,'days_remove')),project['days'])
                w.countries['SPR']['pp']-=project['cost']
                before={k:w.stat(k) for k in project.get('modifiers',{})}
                w.effect(get(decision,'remove_effect'))
                self.assertFalse(w.check(get(decision,'visible')))
                if 'state' in project:
                    state=w.states[str(project['state'])]
                    self.assertEqual(state['extra'],1)
                    # E03 may already have improved this state once.
                    level=state['buildings']['infrastructure']
                    w.effect(get(decision,'remove_effect'))
                    self.assertEqual(state['extra'],1)
                    self.assertEqual(state['buildings']['infrastructure'],level)
                else:
                    for key,value in project['modifiers'].items():self.assertAlmostEqual(w.stat(key)-before[key],value)
                    w.effect(get(decision,'remove_effect'))
                    for key,value in project['modifiers'].items():self.assertAlmostEqual(w.stat(key)-before[key],value)

    def test_regional_projects_cancel_and_refund_when_control_is_lost(self):
        for project in generator.PROJECTS:
            if 'state' not in project:continue
            w=World();decision=DECISIONS[project['id']];w.focus(project['focus'])
            w.countries['SPR']['pp']=100-project['cost']
            state=w.states[str(project['state'])];state['controller']='ENG'
            self.assertTrue(w.check(get(decision,'cancel_trigger')))
            w.effect(get(decision,'cancel_effect'))
            self.assertEqual(w.countries['SPR']['pp'],100)
            self.assertEqual(state['extra'],0)
            self.assertNotIn(project['id']+'_completed',w.countries['SPR']['flags'])

    def test_national_service_campaign_has_cost_cooldown_and_tradeoff(self):
        w=World();decision=DECISIONS[generator.CAMPAIGN]
        self.assertFalse(w.check(get(decision,'visible')))
        w.focus('P08');self.assertTrue(w.check(get(decision,'visible')))
        w.countries['SPR']['stability']=.4;w.countries['SPR']['war_support']=.3
        self.assertTrue(w.check(get(decision,'available')))
        self.assertEqual(get(decision,'cost'),'35');self.assertEqual(get(decision,'days_re_enable'),'120')
        w.effect(get(decision,'complete_effect'))
        self.assertAlmostEqual(w.countries['SPR']['stability'],.38)
        self.assertAlmostEqual(w.countries['SPR']['war_support'],.35)
        w.countries['SPR']['stability']=.3;self.assertFalse(w.check(get(decision,'available')))
        w.countries['SPR']['stability']=.4;w.countries['SPR']['war_support']=.9
        self.assertFalse(w.check(get(decision,'available')))

    def test_labour_event_offers_one_political_choice_without_changing_recovery(self):
        event=EVENTS['TFR_spain_rework.5']
        options=[body for kind,_,body in event if kind=='option']
        self.assertEqual(len(options),2)
        for i in (0,1):
            w=World();w.focus('D01');w.focus('P01');w.focus('P04');w.focus('P05')
            self.assertEqual(w.events.count(('SPR','TFR_spain_rework.5')),1)
            self.assertTrue(w.check(get(event,'trigger')))
            before=w.stat('economy.consumer_goods_factor')
            option_effect=[e for e in options[i] if e[0] not in ('name','ai_chance')]
            w.effect(option_effect)
            self.assertAlmostEqual(w.countries['SPR']['stability'],.05 if i==0 else -.025)
            self.assertAlmostEqual(w.countries['SPR']['war_support'],0 if i==0 else .1)
            self.assertAlmostEqual(w.stat('economy.consumer_goods_factor'),before)
            self.assertEqual(w.countries['SPR']['vars']['TFR_SPA_recovery_programme'],3)
            w.effect([e for e in options[1-i] if e[0] not in ('name','ai_chance')])
            self.assertAlmostEqual(w.countries['SPR']['stability'],.05 if i==0 else -.025)
            self.assertFalse(w.check(get(event,'trigger')))

    def test_role_tooltips_hide_legacy_idea_removal_without_losing_recovery(self):
        def visible(entries):
            for key,_,body in entries:
                if key=='hidden_effect':continue
                yield key,body
                if key in EFFECTS:yield from visible(EFFECTS[key])
                elif isinstance(body,list):yield from visible(body)
        for role in ('D01','D02'):
            shown=list(visible(get(BY_CODE[role],'completion_reward')))
            self.assertFalse(any(key=='remove_ideas' for key,body in shown))
            self.assertEqual(sum(key=='custom_effect_tooltip' and body=='TFR_SPA_recovery_import_tt' for key,body in shown),1)
            for stage,suffix in ((1,''),(2,'_2'),(3,'_3')):
                w=World();idea='SPA_recovering_from_civil_war'+suffix
                w.countries['SPR']['ideas'].add(idea);w.focus(role)
                self.assertNotIn(idea,w.countries['SPR']['ideas'])
                self.assertEqual(w.countries['SPR']['vars']['TFR_SPA_recovery_stage'],stage)
                for key,value in generator.RECOVERY_PENALTIES[stage].items():
                    self.assertAlmostEqual(w.stat(key),value)

    def test_every_original_positive_and_negative_recovery_profile_is_preserved(self):
        # Independent oracle: read the original idea modifiers, rather than the
        # generator's numeric maps, and compare every field after migration.
        text=(ROOT/'common/ideas/spain_nationalist.txt').read_text(encoding='utf-8-sig')
        ideas={e.key:e for e in syntax.walk(syntax.parse(text)) if e.get('modifier')}
        for positive in range(0,8):
            for negative in range(1,5):
                with self.subTest(positive=positive,negative=negative):
                    names=[]
                    if positive:names.append(f'SPA_national_recovery_{positive}')
                    if negative<4:names.append('SPA_recovering_from_civil_war'+('' if negative==1 else '_'+str(negative)))
                    expected=defaultdict(float)
                    for name in names:
                        for entry in ideas[name].get('modifier').active():expected['economy.'+entry.key]+=float(entry.value)
                    w=World();w.countries['SPR']['ideas'].update(names);w.focus('D01')
                    for key,value in expected.items():self.assertAlmostEqual(w.stat(key),value,msg=key)
                    self.assertFalse(w.countries['SPR']['ideas'] & set(names))

    def test_positive_recovery_progresses_in_dynamic_and_expires_without_reset(self):
        w=World();w.countries['SPR']['ideas'].add('SPA_recovering_from_civil_war');w.focus('D01');w.focus('P01')
        self.assertAlmostEqual(w.stat('economy.consumer_goods_factor'),.05)
        self.assertAlmostEqual(w.stat('economy.stability_weekly'),.002)
        self.assertEqual(w.stat('economy.ai_join_ally_desire_factor'),-300)
        w.countries['SPR']['flag_ages']['TFR_SPA_recovery_programme_started']=1000
        w.focus('P04');self.assertAlmostEqual(w.stat('economy.production_speed_infrastructure_factor'),.1)
        self.assertEqual(w.stat('economy.ai_join_ally_desire_factor'),-200)
        w.focus('P05');self.assertEqual(w.stat('economy.stability_weekly'),0)
        self.assertAlmostEqual(w.stat('economy.consumer_goods_factor'),-.1)
        self.assertEqual(w.countries['SPR']['flag_ages']['TFR_SPA_recovery_programme_started'],1000)
        w.focus('P09');w.focus('P10');self.assertAlmostEqual(w.stat('economy.consumer_goods_factor'),-.25)
        self.assertEqual(w.stat('economy.join_faction_tension'),0)
        w.countries['SPR']['flag_ages']['TFR_SPA_recovery_programme_started']=1825;w.run('TFR_SPA_refresh_modifiers')
        self.assertAlmostEqual(w.stat('economy.consumer_goods_factor'),-.1)
        w.focus('P12');self.assertAlmostEqual(w.stat('economy.consumer_goods_factor'),-.15)
        self.assertEqual(w.stat('economy.production_speed_infrastructure_factor'),0)
        self.assertIn('TFR_SPA_recovery_programme_expired',w.countries['SPR']['flags'])

    def test_migration_uses_original_positive_recovery_state_flag_date(self):
        w=World();w.countries['SPR']['ideas'].add('SPA_national_recovery_2');w.states['171']['flags'].add('SPA_national_recovery_2civ')
        w.states['171']['flag_ages']['SPA_national_recovery_2civ']=1824;w.focus('D01')
        self.assertEqual(w.countries['SPR']['vars']['TFR_SPA_recovery_programme'],2)
        w.states['171']['flag_ages']['SPA_national_recovery_2civ']=1825;w.run('TFR_SPA_refresh_modifiers')
        self.assertEqual(w.countries['SPR']['vars']['TFR_SPA_recovery_programme'],0)
        w.focus('P01');w.focus('P04');self.assertEqual(w.countries['SPR']['vars']['TFR_SPA_recovery_programme'],0)

    def test_distinct_legacy_recovery_and_industrial_bonuses_both_survive(self):
        w=World();w.countries['SPR']['ideas'].update(['SPA_national_recovery_6','SPA_the_duty_to_work'])
        w.focus('D01');self.assertAlmostEqual(w.stat('economy.industrial_capacity_factory'),.15)
        w.focus('E11');self.assertAlmostEqual(w.stat('economy.industrial_capacity_factory'),.15)

    def test_recovery_call_decline_rule_expires_for_war_but_not_support_mode(self):
        for mode in ('D01','D02'):
            w=World();w.countries['SPR']['ideas'].add('SPA_recovering_from_civil_war');w.focus(mode)
            self.assertEqual(w.countries['SPR']['rules']['can_decline_call_to_war'],'yes')
            w.focus('P10')
            self.assertEqual(w.countries['SPR']['rules'].get('can_decline_call_to_war'),'yes' if mode=='D01' else None)

    def test_recovery_expiry_uses_existing_civil_war_end_date(self):
        daily=get(get(parse(ROOT/'common/on_actions/TFR_spain_rework.txt')[0][2],'on_daily'),'effect')
        for age,expired in [(2190,True),(2189,False)]:
            w=World();w.countries['SPR']['ideas'].add('SPA_recovering_from_civil_war');w.focus('D01');w.days_since_scw=age
            w.effect(daily)
            self.assertEqual(w.countries['SPR']['vars']['TFR_SPA_recovery_stage'],4 if expired else 1)
    def test_other_spanish_identities_do_not_unlock_the_rework(self):
        w=World();w.countries['SPR']['leader']=False
        w.countries['SPR']['flags'].add('SPR_nationalist_spain_flag')
        self.assertFalse(w.check(TRIGGERS['TFR_SPA_postwar_tree_ready']))
        w.countries['SPR']['completed'].add('SPA_con_paquito')
        self.assertTrue(w.check(TRIGGERS['TFR_SPA_postwar_tree_ready']))

    def test_axis_request_acceptance_and_rejection_are_real_branches(self):
        event=next(v for k,_,v in parse(ROOT/'events/TFR_spain_rework.txt') if k=='country_event' and get(v,'id')=='TFR_spain_rework.1')
        for option in [v for k,_,v in event if k=='option']:
            w=World();w.focus('D02');w.focus('D04');self.assertEqual(w.events,[('GER','TFR_spain_rework.1')]);self.assertIsNone(w.countries['SPR']['faction'])
            w.from_scope='SPR'
            w.effect([e for e in option if e[0] not in ('name','ai_chance')],'GER')
            accepted=get(option,'name').endswith('.a')
            self.assertEqual(w.countries['SPR']['faction'],'axis' if accepted else None)
            self.assertNotIn('TFR_SPA_axis_request_pending',w.countries['SPR']['flags'])
            self.assertEqual(w.check(TRIGGERS['TFR_SPA_can_retry_axis_request']),not accepted)

    def test_recovery_import_and_advancement_never_regress(self):
        for stage,suffix in [(1,''),(2,'_2'),(3,'_3'),(4,None)]:
            w=World()
            if suffix is not None:w.countries['SPR']['ideas'].add('SPA_recovering_from_civil_war'+suffix)
            w.focus('D01');w.focus('P01')
            self.assertEqual(w.countries['SPR']['vars']['TFR_SPA_recovery_stage'],stage)
            w.focus('P04');self.assertEqual(w.countries['SPR']['vars']['TFR_SPA_recovery_stage'],max(stage,2))
            w.focus('P09');self.assertEqual(w.countries['SPR']['vars']['TFR_SPA_recovery_stage'],max(stage,3))
            w.focus('P10');self.assertEqual(w.countries['SPR']['vars']['TFR_SPA_recovery_stage'],4)
            self.assertAlmostEqual(w.stat('economy.consumer_goods_factor'),-.15)

    def test_old_economic_ideas_import_without_stacking_new_rewards(self):
        w=World();w.countries['SPR']['ideas'].update(['SPA_the_duty_to_work','SPA_fascist_economic_aid','SPA_national_recovery_3'])
        w.focus('D01')
        self.assertAlmostEqual(w.stat('economy.industrial_capacity_factory'),.1)
        self.assertAlmostEqual(w.stat('economy.consumer_goods_factor'),-.25)
        w.focus('E11');w.focus('E24');w.focus('E29');w.focus('P05');w.focus('P10')
        self.assertAlmostEqual(w.stat('economy.industrial_capacity_factory'),.1)
        self.assertAlmostEqual(w.stat('economy.production_speed_arms_factory_factor'),.1)
        self.assertAlmostEqual(w.stat('economy.consumer_goods_factor'),-.25)
        self.assertFalse(w.countries['SPR']['ideas'] & set(generator.LEGACY_IDEAS))

    def test_old_factory_flags_credit_only_existing_nationalist_rewards(self):
        w=World();w.states['171']['flags'].add('SPA_national_recovery_2civ');w.states['171']['buildings']['industrial_complex']=2
        w.focus('D01');w.focus('E02')
        self.assertEqual(w.total('industrial_complex','SPR'),2)
        w.focus('E05');self.assertEqual(w.total('industrial_complex','SPR'),3)

    def test_research_slots_and_laws_never_downgrade(self):
        for mode in ('D01','D02'):
            for starting in (3,4,5,6):
                w=World();w.focus(mode);w.countries['SPR']['slots']=starting;w.focus('P06');self.assertEqual(w.countries['SPR']['slots'],max(4,starting));w.focus('P11');self.assertEqual(w.countries['SPR']['slots'],max(5,starting))
            w=World();w.focus(mode);w.countries['SPR']['ideas'].update(['tot_economic_mobilisation','all_adults_serve']);w.focus('P07');w.focus('P08')
            self.assertTrue({'tot_economic_mobilisation','all_adults_serve'}<=w.countries['SPR']['ideas'])
            w=World();w.focus(mode);w.countries['SPR']['ideas'].add('volunteer_only');w.focus('P08')
            self.assertIn('limited_conscription' if mode=='D01' else 'extensive_conscription',w.countries['SPR']['ideas'])

    def test_mutually_exclusive_modes_and_main_war_condition(self):
        w=World();w.focus('D02');w.countries['SPR']['faction']='axis'
        w.countries['SPR']['wars'].add('NPR');w.countries['GER']['wars'].add('NPR')
        self.assertFalse(w.check(TRIGGERS['TFR_SPA_main_axis_war']))
        w.countries['SPR']['wars'].add('ENG');self.assertFalse(w.check(TRIGGERS['TFR_SPA_main_axis_war']))
        w.countries['GER']['wars'].add('ENG');self.assertTrue(w.check(TRIGGERS['TFR_SPA_main_axis_war']))
        w.focus('D12');w.focus('D13');self.assertAlmostEqual(w.stat('army.army_org_factor'),.025)
        self.assertAlmostEqual(w.stat('army.army_morale_factor'),.025);self.assertEqual(w.total('arms_factory','SPR'),4)
        w.countries['GER']['wars'].remove('ENG');w.run('TFR_SPA_refresh_modifiers');self.assertEqual(w.stat('army.army_org_factor'),0)
        w.focus('D12');self.assertEqual(w.total('arms_factory','SPR'),4)

    def test_factory_rewards_queue_without_coastal_destinations(self):
        w=World();w.focus('D01')
        for s in w.states.values():
            if s['owner']=='SPR':s['coast']=False
        w.focus('N02');self.assertEqual(w.total('dockyard','SPR'),0)
        self.assertEqual(w.countries['SPR']['vars']['TFR_SPA_pending_171_dock'],3)
        w=deepcopy(w);w.states['171']['coast']=True;w.run('TFR_SPA_flush_building_rewards')
        self.assertEqual(w.total('dockyard','SPR'),3);w.focus('N02');self.assertEqual(w.total('dockyard','SPR'),3)

    def test_full_states_retain_rewards_until_shared_slots_become_available(self):
        w=World();w.focus('D01')
        for s in w.states.values():
            if s['owner']=='SPR':s['buildings'].update(industrial_complex=10,arms_factory=15)
        old=w.total('industrial_complex','SPR');w.focus('E02')
        self.assertEqual(w.total('industrial_complex','SPR'),old)
        self.assertEqual(w.countries['SPR']['vars']['TFR_SPA_pending_790_civ'],2)
        w.states['790']['buildings']['industrial_complex']-=2;w.run('TFR_SPA_flush_building_rewards')
        self.assertEqual(w.total('industrial_complex','SPR'),old)
        self.assertEqual(w.countries['SPR']['vars']['TFR_SPA_pending_790_civ'],0)

    def test_fixed_destination_waits_for_control_without_granting_to_enemy(self):
        w=World();w.focus('D01');w.states['790']['controller']='ENG';w.focus('E02')
        self.assertEqual(w.total('industrial_complex','SPR'),0)
        self.assertEqual(w.countries['SPR']['vars']['TFR_SPA_pending_790_civ'],2)
        w=deepcopy(w);w.states['790']['controller']='SPR';w.run('TFR_SPA_flush_building_rewards')
        self.assertEqual(w.states['790']['buildings']['industrial_complex'],2)
        self.assertEqual(w.states['790']['extra'],2)
        w.run('TFR_SPA_flush_building_rewards')
        self.assertEqual(w.total('industrial_complex','SPR'),2)

    def test_infrastructure_goes_to_three_distinct_states_below_cap(self):
        w=World();w.focus('D01')
        for s in w.states.values():
            if s['owner']=='SPR':s['buildings']['infrastructure']=3
        w.focus('E03')
        self.assertEqual(sum(s['buildings']['infrastructure']==4 for s in w.states.values() if s['owner']=='SPR'),3)

    def test_naval_arsenals_expand_two_distinct_coastal_states(self):
        w=World();w.focus('D01');w.focus('N12')
        affected=[s for s in w.states.values() if s['owner']=='SPR' and s['buildings']['dockyard']]
        self.assertEqual(sorted(s['buildings']['dockyard'] for s in affected),[3,3])

    def test_relocation_conserves_actual_industry_and_survives_reload(self):
        w=World();w.focus('D01');w.states['112']['buildings'].update(industrial_complex=15,arms_factory=5,dockyard=10)
        initial={b:w.total(b) for b in ('industrial_complex','arms_factory','dockyard')}
        for s in w.states.values():
            if s['owner']=='SPR':s['coast']=False
        w.focus('D05');self.assertEqual(len(w.rights),5);self.assertTrue(all(r[1]=='SPR' and r[3] is None for r in w.rights))
        self.assertTrue(all(w.states[str(s)]['buildings']['infrastructure']==5 for s in PORTUGAL))
        w.focus('D06');self.assertEqual(w.total('industrial_complex','NPR'),0);self.assertEqual(w.total('arms_factory','NPR'),0);self.assertEqual(w.total('dockyard','NPR'),10)
        self.assertIn('TFR_SPA_stop_portuguese_industry_growth',w.countries['NPR']['flags'])
        self.assertNotIn('TFR_SPA_relocation_complete',w.countries['SPR']['flags'])
        w=deepcopy(w);w.states['171']['coast']=True;w.run('TFR_SPA_process_relocation')
        self.assertIn('TFR_SPA_relocation_complete',w.countries['SPR']['flags'])
        for b,n in initial.items():self.assertEqual(w.total(b),n);self.assertEqual(w.total(b,'NPR'),0)
        w.focus('D06');w.run('TFR_SPA_flush_building_rewards')
        for b,n in initial.items():self.assertEqual(w.total(b),n)
        self.assertEqual({s['owner'] for k,s in w.states.items() if int(k) in PORTUGAL},{'NPR'})

    def test_relocation_does_not_take_occupied_portuguese_factories(self):
        w=World();w.focus('D01');w.states['112']['buildings']['industrial_complex']=4;w.states['112']['controller']='ENG'
        w.run('TFR_SPA_begin_relocation');self.assertEqual(w.total('industrial_complex','NPR'),4)
        self.assertIn('TFR_SPA_relocating_industry',w.countries['SPR']['flags'])
        w.states['112']['controller']='NPR';w.run('TFR_SPA_process_relocation');self.assertEqual(w.total('industrial_complex','SPR'),4)

    def test_volunteer_rules_and_annexation_are_separate(self):
        w=World();w.focus('D01');self.assertEqual(w.countries['SPR']['rules']['can_not_declare_war'],'yes');self.assertEqual(w.countries['SPR']['rules']['can_join_factions'],'no')
        self.assertFalse(w.can_start('D07'))
        w=World();w.focus('D02');self.assertNotIn('can_not_declare_war',w.countries['SPR']['rules'])
        self.assertFalse(w.can_start('D07'));w.focus('D04')
        self.assertTrue(w.can_start('D07'));w.focus('D07');self.assertEqual(w.wargoals,[('SPR','NPR')])

    def test_autonomy_integration_only_changes_owned_controlled_regions(self):
        w=World();w.focus('D01');w.states['165']['dynamic'].add('autonomous_state');w.states['171']['dynamic'].add('semi_autonomous_state');w.states['171']['controller']='ENG'
        w.focus('P03');self.assertFalse(w.states['165']['dynamic']);self.assertIn('semi_autonomous_state',w.states['171']['dynamic'])

    def test_all_rework_focuses_use_relative_positions_without_moving(self):
        for f in generator.FOCUSES:
            expected = (generator.BY_CODE[f['prerequisites'][0][0]]['id']
                        if f['prerequisites'] else 'SPA_a_great_spain')
            self.assertEqual(f.get('relative_position_id'),expected,f['code'])
            self.assertEqual(get(FOCUSES[f['id']],'relative_position_id'),expected,f['code'])
        report=json.loads((ROOT/'docs/native-log-repairs-20261025.json').read_text())
        baseline=report['focusPositionsBeforeRepair']
        self.assertEqual(set(baseline),set(FOCUSES))
        for name,expected in baseline.items():
            self.assertEqual(absolute_position(name),tuple(expected),name)

    def test_native_focus_definition_order_has_no_forward_relative_references(self):
        tree=parse(ROOT/'common/national_focus/spain.txt')[0][2]
        seen=set()
        for key,_,body in tree:
            if key!='focus':continue
            name=get(body,'id')
            parent=next((value for field,_,value in body if field=='relative_position_id'),None)
            if parent:self.assertIn(parent,seen,(name,parent))
            self.assertNotIn(name,seen)
            seen.add(name)
        self.assertTrue(set(FOCUSES).issubset(seen))
        self.assertFalse(parse(ROOT/'common/national_focus/TFR_spain_rework.txt'))

    def test_air_extension_requires_both_lines_and_keeps_existing_rewards(self):
        for mode in ('D01','D02'):
            w=World();w.focus(mode);w.focus('P01');w.focus('P04');w.focus('M01')
            for code in ('A01','A02','A03','A04','A05'):
                self.assertTrue(w.can_start(code),code);w.focus(code)
            original={key:w.stat(key) for key in ('air.air_mission_efficiency','air.air_agility_factor','air.air_cas_present_factor','air.air_accidents_factor','air.air_fuel_consumption_factor')}
            factories=w.total('arms_factory','SPR')
            self.assertFalse(w.can_start('A08'));self.assertFalse(w.can_start('A09'))
            self.assertTrue(w.can_start('A06'));w.focus('A06')
            self.assertTrue(w.can_start('A08'));w.focus('A08')
            self.assertFalse(w.can_start('A09'))
            self.assertTrue(w.can_start('A07'));w.focus('A07')
            self.assertTrue(w.can_start('A09'));w.focus('A09')
            self.assertAlmostEqual(w.stat('air.air_range_factor'),.05)
            self.assertAlmostEqual(w.stat('air.air_night_penalty'),-.05)
            self.assertAlmostEqual(w.stat('air.air_weather_penalty'),-.05)
            self.assertEqual(factories,w.total('arms_factory','SPR'))
            for key,value in original.items():self.assertEqual(w.stat(key),value,key)
            self.assertIn(('SPR','light_air'),w.research)
            self.assertIn(('SPR','medium_air'),w.research)
            self.assertIn(('SPR','radar_tech'),w.research)


    def test_volunteer_spain_unlocks_axis_shared_tree(self):
        w = World()
        w.focus('D01')
        self.assertIn('accessible_shared_tree', w.countries['SPR']['flags'])
        axis_shared = parse(ROOT/'common/national_focus/axis_shared.txt')
        joint_alliance = next(v for k, _, v in axis_shared if k == 'shared_focus' and get(v, 'id') == 'AXIS_joint_alliance')
        bypass = next(v for k, _, v in joint_alliance if k == 'bypass')
        self.assertTrue(w.check(bypass, 'SPR'))
        shared_opt = (ROOT/'common/on_actions/shared_tree_optimization.txt').read_text()
        self.assertIn('has_completed_focus = TFR_SPA_volunteer_spain', shared_opt)


if __name__=='__main__':unittest.main()

