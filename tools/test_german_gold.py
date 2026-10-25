"""Execute gold registration, recovery and rewards against the shipped scripts."""
from copy import deepcopy
from pathlib import Path
import unittest

from hoi4_script import Block, parse, walk

ROOT=Path(__file__).resolve().parents[1]
TRIGGERS=parse((ROOT/'common/scripted_triggers/tfr_german_gold.txt').read_text()).mapping()
EFFECTS=parse((ROOT/'common/scripted_effects/tfr_german_gold.txt').read_text()).mapping()
DECISION=next(e.value for e,_ in walk(parse((ROOT/'common/decisions/GER.txt').read_text())) if e.key=='GER_seize_gold_reserves')
CAPITULATION=next(e.value for e,a in walk(parse((ROOT/'common/on_actions/00_on_actions.txt').read_text()))
                  if e.key=='effect' and any(p.key=='on_capitulation' for p in a)
                  and any(s.key=='TFR_GER_register_gold_target' for s,_ in walk(e.value)))
ARRAY='GER.GER_seize_gold_targets_array'
FLAG='GER_has_capitulated_to_germany'
LOOT='GER_seize_gold_reserves_state_flag'


class World:
    def __init__(self):
        self.countries={}
        self.states={}
        self.arrays={ARRAY:[]}
        self.globals=set()
        self.from_scope=None
        self.legacy_refreshes=0
        self.country('GER',faction='axis')
        self.country('ITA',faction='axis')
        self.country('ENG',faction='allies')

    def country(self,tag,exists=True,capitulated=False,faction=None,flags=()):
        self.countries[tag]=dict(original=tag,exists=exists,capitulated=capitulated,
                                 faction=faction,flags=set(flags),variables={},modifiers=set())
        return self.countries[tag]

    def state(self,name,target,controller='GER',continent='europe',factories=(3,4,1),flags=(),resistance=True,full=True):
        self.states[name]=dict(cores={target},controller=controller,continent=continent,
                              factories=dict(zip(('industrial_complex_level','arms_factory_level','building_level@dockyard'),factories)),
                              flags=set(flags),resistance=resistance,full=full,compliance=0,unrest=0,dynamic=set())
        return self.states[name]

    def target(self,name,scope,prev,root):
        return {'THIS':scope,'PREV':prev,'ROOT':root,'FROM':self.from_scope}.get(name,name)

    def value(self,name,scope,prev,root):
        try:return float(name)
        except ValueError:pass
        if scope in self.states and name in self.states[scope]['factories']:
            return self.states[scope]['factories'][name]
        if '.' in name:
            owner,key=name.split('.',1)
            scope=self.target(owner,scope,prev,root)
            name=key
        return self.countries[scope]['variables'].get(name,0)

    def check(self,block,scope,prev=None,root='GER'):
        def one(e):
            k,v=e.key,e.value
            obj=self.states[scope] if scope in self.states else self.countries[scope]
            if k=='OR':return any(self.check(Block([a]),scope,prev,root) for a in v.entries())
            if k=='AND':return self.check(v,scope,prev,root)
            if k=='NOT':return not self.check(v,scope,prev,root)
            if k=='any_core_state':return any(self.check(v,s,scope,root) for s,state in self.states.items() if scope in state['cores'])
            if k=='original_tag':return obj['original']==v
            if k=='is_ally_with':return obj['faction'] is not None and obj['faction']==self.countries[v]['faction']
            if k=='exists':return obj['exists']==(v=='yes')
            if k=='has_capitulated':return obj['capitulated']==(v=='yes')
            if k=='has_country_flag' or k=='has_state_flag':return v in obj['flags']
            if k=='has_global_flag':return v in self.globals
            if k=='has_dynamic_modifier':return v.get('modifier') in obj['modifiers']
            if k=='is_on_continent':return obj['continent']==v
            if k=='is_fully_controlled_by':return obj['full'] and obj['controller']==self.target(v,scope,prev,root)
            if k=='is_core_of':return self.target(v,scope,prev,root) in obj['cores']
            if k=='has_resistance':return obj['resistance']==(v=='yes')
            if k=='is_in_array':return self.target(v.get('value'),scope,prev,root) in self.arrays[v.get('array')]
            if k=='check_variable':
                test=v.entries()[0];a=self.value(test.key,scope,prev,root);b=self.value(test.value,scope,prev,root)
                return {'>':a>b,'<':a<b,'=':a==b}[test.op]
            if k=='custom_trigger_tooltip':return self.check(Block([a for a in v.entries() if a.key!='tooltip']),scope,prev,root)
            if k in TRIGGERS:return self.check(TRIGGERS[k],scope,prev,root)==(v=='yes')
            if k in ('ROOT','PREV','FROM','GER'):
                return self.check(v,self.target(k,scope,prev,root),scope,root)
            raise AssertionError(('unsupported trigger',k))
        return all(one(e) for e in block.entries())

    def effect(self,block,scope='GER',prev=None,root='GER'):
        taken=False
        for e in block.entries():
            k,v=e.key,e.value
            obj=self.states[scope] if scope in self.states else self.countries[scope]
            if k in ('if','else_if','else'):
                if k=='if':taken=False
                matched=not taken and (k=='else' or self.check(v.get('limit'),scope,prev,root))
                if matched:self.effect(Block([a for a in v.entries() if a.key!='limit']),scope,prev,root)
                taken=taken or matched
            elif k in ('every_core_state','every_possible_country'):
                targets=list(self.countries) if k=='every_possible_country' else [s for s,state in self.states.items() if scope in state['cores']]
                for t in targets:
                    if self.check(v.get('limit',Block([])),t,scope,root):
                        self.effect(Block([a for a in v.entries() if a.key!='limit']),t,scope,root)
            elif k in ('set_country_flag','set_state_flag'):obj['flags'].add(v)
            elif k=='add_to_array':self.arrays[v.get('array')].append(self.target(v.get('value'),scope,prev,root))
            elif k in ('set_temp_variable','add_to_temp_variable','divide_temp_variable','multiply_temp_variable','add_to_variable'):
                entry=next(a for a in v.entries() if a.key!='tooltip');name=entry.key;owner=scope
                if '.' in name:owner,name=name.split('.',1);owner=self.target(owner,scope,prev,root)
                variables=self.countries[owner]['variables'];value=self.value(entry.value,scope,prev,root);before=variables.get(name,0)
                variables[name]={'set_temp_variable':lambda:value,'add_to_temp_variable':lambda:before+value,
                                 'divide_temp_variable':lambda:before/value,'multiply_temp_variable':lambda:before*value,
                                 'add_to_variable':lambda:before+value}[k]()
            elif k=='add_compliance':obj['compliance']+=float(v)
            elif k=='add_resistance':obj['unrest']+=float(v)
            elif k=='add_dynamic_modifier':obj['dynamic'].add(v.get('modifier'))
            elif k=='GER_reduce_mefo_bills_penalty':self.legacy_refreshes+=1
            elif k=='custom_effect_tooltip':pass
            elif k in EFFECTS:self.effect(EFFECTS[k],scope,prev,root)
            elif k in ('ROOT','PREV','FROM','GER'):self.effect(v,self.target(k,scope,prev,root),scope,root)
            else:raise AssertionError(('unsupported effect',k))

    def recover(self):self.effect(EFFECTS['TFR_GER_recover_gold_targets'])
    def visible(self,tag):
        self.from_scope=tag
        return tag in self.arrays[ARRAY] and self.check(DECISION.get('target_trigger'),'GER')
    def seize(self,tag):
        self.from_scope=tag
        self.effect(DECISION.get('complete_effect'))


class GermanGoldTests(unittest.TestCase):
    def test_capitulation_registers_all_proxy_and_original_tags_without_a_capital(self):
        for tag in ('FNL','FBL','NPO','NDE','NNO','FCZ','FYG','NNG','FPR','NPR','HOL','BEL','POL','DEN','NOR','CZE','YUG','GRE','POR'):
            for victor in ('GER','ITA'):
                w=World();w.country(tag,capitulated=True);w.state('s',tag);w.from_scope=victor
                w.effect(CAPITULATION,tag,root=tag)
                self.assertTrue(w.visible(tag),(tag,victor))
                w.from_scope=victor;w.effect(CAPITULATION,tag,root=tag)
                self.assertEqual(w.arrays[ARRAY].count(tag),1)
        w=World();w.country('FNL',capitulated=True);w.state('s','FNL');w.from_scope='ENG'
        w.effect(CAPITULATION,'FNL',root='FNL');self.assertNotIn(FLAG,w.countries['FNL']['flags'])

    def test_old_save_repairs_flag_or_array_independently_and_is_repeat_safe(self):
        cases=[dict(capitulated=True),dict(exists=False,flags=['tfr_spawned_initial_defense']),
               dict(exists=False,flags=['TFR_GER_gold_seen_active']),dict(flags=[FLAG])]
        for fields in cases:
            w=World();w.country('FNL',**fields);w.state('s','FNL');w.recover()
            self.assertTrue(w.visible('FNL'),fields)
            w.recover();self.assertEqual(w.arrays[ARRAY],['FNL'])
        w=World();w.country('FNL',exists=False);w.state('s','FNL');w.arrays[ARRAY]=['FNL'];w.recover()
        self.assertTrue(w.visible('FNL'));self.assertEqual(w.arrays[ARRAY],['FNL'])

    def test_no_premature_loot_or_dormant_releasables(self):
        for exists in (True,False):
            w=World();w.country('FNL',exists=exists);w.state('s','FNL');w.recover()
            self.assertFalse(w.visible('FNL'))
        w=World();w.country('RKN',exists=False,capitulated=True);w.state('s','RKN');w.recover()
        self.assertFalse(w.visible('RKN'))
        w=World();c=w.country('FNL');w.state('s','FNL');w.recover();c['exists']=False;w.recover()
        self.assertTrue(w.visible('FNL'))

    def test_target_and_reward_share_control_core_protection_and_factory_filters(self):
        for reason in ('ally','enemy','partial','german_core','looted','vichy','empty','overseas'):
            w=World();w.country('FNL',capitulated=True);s=w.state('s','FNL')
            if reason=='ally':s['controller']='ITA'
            if reason=='enemy':s['controller']='ENG'
            if reason=='partial':s['full']=False
            if reason=='german_core':s['cores'].add('GER')
            if reason=='looted':s['flags'].add(LOOT)
            if reason=='vichy':s['flags'].add('VIC_dont_loot')
            if reason=='empty':s['factories']={k:0 for k in s['factories']}
            if reason=='overseas':s['continent']='asia'
            w.recover();self.assertFalse(w.visible('FNL'),reason)
            w.seize('FNL');self.assertEqual(w.countries['GER']['variables']['GER_industrial_consumer_goods_factor'],0,reason)
            self.assertEqual(s['compliance'],0);self.assertEqual(s['unrest'],0)

    def test_all_three_factory_types_reward_once_with_unrelated_states_unchanged(self):
        w=World();w.country('FNL',capitulated=True);a=w.state('a','FNL');b=w.state('b','FNL',factories=(0,0,2),resistance=False)
        bad=w.state('c','FNL',factories=(100,100,100),flags=[LOOT]);snapshot=deepcopy(bad)
        w.recover();self.assertTrue(w.visible('FNL'));w.seize('FNL')
        self.assertAlmostEqual(w.countries['GER']['variables']['GER_industrial_consumer_goods_factor'],-.05)
        self.assertEqual((a['compliance'],a['unrest']),(-5,10));self.assertEqual((b['compliance'],b['unrest']),(0,0))
        self.assertEqual(bad,snapshot);self.assertFalse(w.visible('FNL'))
        w.seize('FNL');self.assertAlmostEqual(w.countries['GER']['variables']['GER_industrial_consumer_goods_factor'],-.05)

    def test_turkish_exception_and_soviet_partial_loot(self):
        w=World();w.country('TUR',capitulated=True);w.state('s','TUR',continent='asia');w.recover()
        self.assertTrue(w.visible('TUR'));w.seize('TUR')
        self.assertAlmostEqual(w.countries['GER']['variables']['GER_industrial_consumer_goods_factor'],-.04)
        w=World();w.country('SOV',capitulated=True);w.state('city','SOV',flags=[LOOT],factories=(10,10,0));w.state('rest','SOV',factories=(4,0,0))
        w.countries['GER']['variables']['GER_reduce_russian_CG_bonus']=-.1;w.recover();w.seize('SOV')
        self.assertAlmostEqual(w.countries['GER']['variables']['GER_industrial_consumer_goods_factor'],-.02)

    def test_france_lock_and_existing_cost_policy_are_preserved(self):
        w=World();w.country('FRA');w.state('s','FRA');w.globals.add('fall_of_france');w.countries['FRA']['flags'].add('GER_dont_seize_gold_reserves_flag');w.recover()
        self.assertFalse(w.visible('FRA'));w.countries['FRA']['flags'].remove('GER_dont_seize_gold_reserves_flag');self.assertTrue(w.visible('FRA'))
        self.assertEqual(DECISION.get('cost'),'25');self.assertEqual(DECISION.get('fire_only_once'),'yes')
        self.assertIn('GER_economy_of_conquest_modifier',str(DECISION.get('target_root_trigger')))
        self.assertIn('GER_industrial_consumer_goods_factor',str(DECISION.get('available')))

    def test_daily_recovery_does_not_bypass_economy_or_positive_penalty_requirements(self):
        actions=parse((ROOT/'common/on_actions/tfr_german_gold.txt').read_text()).get('on_actions')
        self.assertEqual(actions.get('on_startup').get('effect').get('GER').get('TFR_GER_recover_gold_targets'),'yes')
        hook=actions.get('on_daily_GER').get('effect')
        w=World();w.country('FNL',capitulated=True);w.state('s','FNL')
        w.effect(hook);self.assertNotIn(FLAG,w.countries['FNL']['flags'])
        w.countries['GER']['modifiers'].add('GER_mefo_bills_modifier');w.effect(hook)
        self.assertTrue(w.visible('FNL'))
        self.assertFalse(w.check(DECISION.get('target_root_trigger'),'GER'))
        w.countries['GER']['modifiers'].add('GER_economy_of_conquest_modifier')
        self.assertTrue(w.check(DECISION.get('target_root_trigger'),'GER'))
        self.assertFalse(w.check(DECISION.get('available'),'GER'))
        w.countries['GER']['variables']['GER_industrial_consumer_goods_factor']=.15
        self.assertTrue(w.check(DECISION.get('available'),'GER'))


if __name__=='__main__':unittest.main()
