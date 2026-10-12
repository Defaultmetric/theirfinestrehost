from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]

def parse(path):
    tokens=re.findall(r'#[^\n]*|"(?:\\.|[^"\\])*"|>=|<=|!=|[{}=<>]|[^\s{}=<>]+',path.read_text(encoding='utf-8-sig'))
    tokens=[t for t in tokens if not t.startswith('#')]
    pos=0
    def block():
        nonlocal pos
        entries=[]
        while pos<len(tokens) and tokens[pos]!='}':
            if tokens[pos+1] not in ['=','<','>','>=','<=','!=']:
                entries.append(('_','=',tokens[pos])); pos+=1; continue
            key,op=tokens[pos:pos+2]; pos+=2
            assert op in ['=','<','>','>=','<=','!='],(key,op)
            if tokens[pos]=='{':
                pos+=1; value=block(); assert tokens[pos]=='}'; pos+=1
            else:
                value=tokens[pos].strip('"'); pos+=1
            entries.append((key,op,value))
        return entries
    result=block()
    assert pos==len(tokens)
    return result

TRIGGERS={k:v for k,_,v in parse(ROOT/'common/scripted_triggers/tfr_scw_volunteers.txt')}
EFFECTS={k:v for k,_,v in parse(ROOT/'common/scripted_effects/tfr_scw_volunteers.txt')}
GUIS={k:v for k,_,v in parse(ROOT/'common/scripted_guis/tfr_scw_volunteers.txt')[0][2]}
ON_ACTIONS={k:v for k,_,v in parse(ROOT/'common/on_actions/tfr_scw_volunteers.txt')[0][2]}
AXIS=['GER','ITA','ROM','HUN','BUL']
ALLIES=['ENG','FRA','CAN','AST','SAF','RAJ','BRA','MEX']

def get(block,key):
    return next(v for k,_,v in block if k==key)

class World:
    def __init__(self,date='1936.7.31'):
        self.date=tuple(map(int,date.split('.')))
        self.global_flags=set()
        self.flags={}
        self.vars={}
        self.original_tags={}
        self.dynamic_modifiers={}
        self.from_scope=None
        self.civil_wars=set()
        self.recalls=[]
        self.modifier_removals=[]
    def value(self,value,scope):
        if value.count('.')>=2 and value.replace('.','').isdigit(): return tuple(map(int,value.split('.')))
        try: return float(value)
        except ValueError: pass
        if '.' in value: scope,value=value.split('.',1)
        return self.vars.get((scope,value),0)
    def check(self,entries,scope):
        def one(k,op,v):
            if k=='OR': return any(one(*e) for e in v)
            if k=='AND': return self.check(v,scope)
            if k=='NOT': return not self.check(v,scope)
            if k=='original_tag': return self.original_tags.get(scope,scope)==v
            if k=='tag': return scope==v
            if k=='FROM':
                assert self.from_scope is not None
                return self.check(v,self.from_scope)
            if k=='exists': return v=='yes'
            if k=='has_global_flag': return v in self.global_flags
            if k=='has_country_flag': return v in self.flags.get(scope,set())
            if k=='has_dynamic_modifier': return v in self.dynamic_modifiers.get(scope,set())
            if k=='has_civil_war': return (scope in self.civil_wars)==(v=='yes')
            if k=='date': left,right=self.date,self.value(v,scope)
            elif k=='check_variable':
                var,op,value=v[0]; left,right=self.value(var,scope),self.value(value,scope)
            elif k in ('TFR_scw_ground_within_draft','TFR_scw_air_within_draft'):
                # These tests have no deployed volunteers; native count limits are tested in game separately.
                return True
            elif k=='TFR_scw_sent_above_quota':
                # Routing tests assume the sender is within its native quota.
                return False
            elif k in TRIGGERS: return self.check(TRIGGERS[k],scope)==(v=='yes')
            elif re.fullmatch('[A-Z]{3}',k): return self.check(v,k)
            else: raise AssertionError(('unsupported trigger',k))
            return {'=':left==right,'<':left<right,'>':left>right,'<=':left<=right,'>=':left>=right,'!=':left!=right}[op]
        return all(one(*entry) for entry in entries)
    def effect(self,entries,scope):
        previous_if=None
        for k,_,v in entries:
            if k=='if':
                previous_if=self.check(get(v,'limit'),scope)
                if previous_if: self.effect([e for e in v if e[0]!='limit'],scope)
            elif k=='else':
                if previous_if is False: self.effect(v,scope)
            elif k in ('set_global_flag','clr_global_flag'):
                (self.global_flags.add if k=='set_global_flag' else self.global_flags.discard)(v)
            elif k in ('set_country_flag','clr_country_flag'):
                flags=self.flags.setdefault(scope,set())
                (flags.add if k=='set_country_flag' else flags.discard)(v)
            elif k.endswith('_variable') and k in ['set_variable','add_to_variable','subtract_from_variable','multiply_variable','divide_variable']:
                var,_,value=v[0]; key=(scope,var); value=self.value(value,scope); old=self.vars.get(key,0)
                self.vars[key]={'set_variable':lambda:value,'add_to_variable':lambda:old+value,'subtract_from_variable':lambda:old-value,'multiply_variable':lambda:old*value,'divide_variable':lambda:old/value}[k]()
            elif k=='clamp_variable':
                var=get(v,'var'); self.vars[(scope,var)]=max(self.value(get(v,'min'),scope),min(self.value(get(v,'max'),scope),self.value(var,scope)))
            elif k=='recall_volunteers_from':
                assert v=='FROM'
                self.recalls.append((scope,self.from_scope))
            elif k=='remove_dynamic_modifier':
                modifier=get(v,'modifier')
                assert modifier in self.dynamic_modifiers.get(scope,set()), 'Attempt to remove an absent native modifier'
                self.dynamic_modifiers[scope].remove(modifier)
                self.modifier_removals.append((scope,modifier))
            elif k=='remove_ideas':
                pass  # Native idea storage is not needed for the cleanup guard test.
            elif k in ['TFR_scw_apply_donor','TFR_scw_refresh_views']:
                if k=='TFR_scw_apply_donor':
                    for kind in ['land','air']: self.vars[(scope,'TFR_scw_'+kind)]=self.value('TFR_scw_draft_'+kind,scope)
                # Native modifier installation / GUI drawing are outside this state-machine test.
            elif k in EFFECTS: self.effect(EFFECTS[k],scope)
            elif re.fullmatch('[A-Z]{3}',k): self.effect(v,k)
            else: raise AssertionError(('unsupported effect',k))
    def run(self,name,scope): self.effect(EFFECTS[name],scope)
    def click(self,pane,name,scope): self.effect(get(get(GUIS[pane],'effects'),name+'_click'),scope)

class VolunteerTests(unittest.TestCase):
    def test_zero_quota_cleanup_only_removes_installed_modifier(self):
        for installed in [False,True]:
            w=World(); w.flags['ITA']={'TFR_scw_committed_donor'}
            w.vars[('ITA','TFR_scw_land')]=4; w.vars[('ITA','TFR_scw_air')]=100
            if installed: w.dynamic_modifiers['ITA']={'TFR_scw_volunteer_limits'}
            # Execute the actual apply effect, rather than the commit-test native stub.
            w.run('TFR_scw_apply_donor','ITA')
            self.assertEqual(w.value('TFR_scw_land','ITA'),0)
            self.assertEqual(w.value('TFR_scw_air','ITA'),0)
            self.assertNotIn('TFR_scw_committed_donor',w.flags['ITA'])
            self.assertEqual(w.modifier_removals,[('ITA','TFR_scw_volunteer_limits')] if installed else [])
            w.run('TFR_scw_remove_native_limits','ITA')  # Repeated cleanup is harmless.
            self.assertEqual(len(w.modifier_removals),int(installed))

    def test_wrong_camp_is_recalled_on_send(self):
        for sender,donor_camp in [('GER','axis'),('ENG','allied'),('SOV','allied')]:
            for target_camp in ['nationalist','republican','carlist']:
                w=World('1936.8.6'); w.from_scope='D01'
                w.global_flags.add('TFR_scw_manager_initialized')
                w.original_tags['D01']='SPR'; w.civil_wars.add('D01')
                w.flags['D01']={f'SPR_{target_camp}_spain_flag'}
                w.flags[sender]={'TFR_scw_committed_donor',f'TFR_scw_{donor_camp}_donor'}
                w.dynamic_modifiers[sender]={'TFR_scw_volunteer_limits'}
                w.vars[(sender,'TFR_scw_land')]=4
                w.vars[(sender,'modifier@send_volunteer_size')]=4
                w.vars[(sender,'modifier@send_volunteer_factor')]=-1000
                w.effect(get(ON_ACTIONS['on_send_volunteers'],'effect'),sender)
                correct=(donor_camp=='axis' and target_camp=='nationalist') or (donor_camp=='allied' and target_camp=='republican')
                self.assertEqual(w.recalls,[] if correct else [(sender,'D01')],(sender,target_camp))

    def test_recipient_camp_including_original_spain_tag(self):
        w=World('1936.8.6')
        for sender in AXIS+ALLIES+['SOV']:
            w.flags[sender]={'TFR_scw_committed_donor', 'TFR_scw_axis_donor' if sender in AXIS else 'TFR_scw_allied_donor'}
            w.dynamic_modifiers[sender]={'TFR_scw_volunteer_limits'}
            w.vars[(sender,'TFR_scw_land')]=4
            w.vars[(sender,'modifier@send_volunteer_size')]=4
            w.vars[(sender,'modifier@send_volunteer_factor')]=-1000
        # Actual country identity can be SPR or a dynamic civil-war country.
        # The native camp flags (also used by SPA/SPD aliases) identify each side.
        for recipient in ['SPR','D01']:
            w.original_tags[recipient]='SPR'
            for camp_flag,axis_target in [('SPR_nationalist_spain_flag',True),('scw_no_lar_nationalists',True),('SPR_republican_spain_flag',False),('scw_no_lar_republicans',False)]:
                w.flags[recipient]={camp_flag}
                for sender in AXIS+ALLIES+['SOV']:
                    w.from_scope=sender
                    self.assertEqual(w.check(TRIGGERS['TFR_scw_volunteer_permission'],recipient), (sender in AXIS)==axis_target,(recipient,camp_flag,sender))
            for other_flag in [None,'SPR_carlist_spain_flag','SPR_anarchist_spain_flag']:
                w.flags[recipient]={other_flag} if other_flag else set()
                for sender in ['GER','ENG','SOV']:
                    w.from_scope=sender
                    self.assertFalse(w.check(TRIGGERS['TFR_scw_volunteer_permission'],recipient))
        w.flags['SPR']={'SPR_nationalist_spain_flag'}
        w.from_scope='GER'; w.flags['GER'].discard('TFR_scw_committed_donor')
        self.assertFalse(w.check(TRIGGERS['TFR_scw_volunteer_permission'],'SPR'))

    def test_deadline_and_soviet_priority(self):
        w=World()
        self.assertFalse(w.check(TRIGGERS['TFR_scw_uk_priority_ready'],'ENG'))
        w.click('TFR_scw_allies','ENG_land_set_1','ENG')
        self.assertEqual(w.value('TFR_scw_draft_land','ENG'),0)
        w.vars[('SOV','TFR_scw_draft_land')]=6
        w.vars[('SOV','TFR_scw_draft_air')]=100
        w.run('TFR_scw_soviet_commit','SOV')
        self.assertIn('TFR_scw_soviet_confirmed',w.global_flags)
        self.assertEqual(w.value('TFR_scw_live_total_land','ENG'),6)
        self.assertEqual(w.value('TFR_scw_draft_total_air','ENG'),100)
        self.assertTrue(w.check(TRIGGERS['TFR_scw_uk_priority_ready'],'ENG'))
        w.click('TFR_scw_allies','ENG_land_set_6','ENG')
        self.assertEqual(w.value('TFR_scw_draft_land','ENG'),6)
        w.click('TFR_scw_allies','FRA_land_set_1','ENG')
        self.assertEqual(w.value('TFR_scw_draft_land','FRA'),0)
    def test_august_without_soviet_choice(self):
        for date,ready in [('1936.7.31',False),('1936.8.1',True),('1936.8.2',True)]:
            w=World(date); w.run('TFR_scw_allies_prepare','ENG')
            self.assertEqual(w.check(TRIGGERS['TFR_scw_uk_priority_ready'],'ENG'),ready)
            w.click('TFR_scw_allies','ENG_land_set_12','ENG')
            self.assertEqual(w.value('TFR_scw_draft_land','ENG'),12 if ready else 0)
            if ready:
                w.click('TFR_scw_allies','ENG_air_set_300','ENG'); w.run('TFR_scw_allies_commit','ENG')
                self.assertEqual(w.value('TFR_scw_live_total_land','ENG'),12)
                self.assertEqual(w.value('TFR_scw_live_total_air','ENG'),300)
                w.vars[('SOV','TFR_scw_draft_land')]=1
                w.run('TFR_scw_soviet_commit','SOV')
                self.assertNotIn('TFR_scw_soviet_confirmed',w.global_flags)
                self.assertEqual(w.value('TFR_scw_land','SOV'),0)
    def test_explicit_zero_choice_unlocks_uk(self):
        w=World(); w.run('TFR_scw_soviet_commit','SOV')
        self.assertIn('TFR_scw_soviet_confirmed',w.global_flags)
        self.assertTrue(w.check(TRIGGERS['TFR_scw_uk_priority_ready'],'ENG'))
    def test_authority_and_viewers(self):
        w=World('1936.8.1'); w.run('TFR_scw_axis_prepare','GER'); w.run('TFR_scw_allies_prepare','ENG')
        for actor in AXIS+ALLIES+['SOV','SPR','SPA','SPB','SPC','SPD']:
            self.assertTrue(w.check(TRIGGERS['TFR_scw_can_view'],actor),actor)
        for actor in ['FIN','MON','JAP','SIA','NZL','USA','CHI']:
            self.assertFalse(w.check(TRIGGERS['TFR_scw_eligible_donor'],actor),actor)
        for pane,leader,button,donor in [('TFR_scw_axis','GER','ROM_land_set_4','ROM'),('TFR_scw_allies','ENG','FRA_land_set_4','FRA'),('TFR_scw_soviet','SOV','SOV_land_set_4','SOV')]:
            for actor in ['ROM','ITA','FRA','SPR']:
                old=dict(w.vars); w.click(pane,button,actor); self.assertEqual(w.vars,old,actor)
            w.run('TFR_scw_soviet_prepare','SOV')
            w.click(pane,button,leader); self.assertEqual(w.value('TFR_scw_draft_land',donor),4)
        self.assertFalse(any(k.startswith('SOV_land_set_') or k.startswith('SOV_air_set_') for k,_,_ in get(GUIS['TFR_scw_allies'],'effects')))
    def test_pending_draft_can_be_reduced_after_soviet_choice(self):
        w=World('1936.8.1')
        for actor in ['ENG','FRA','CAN']: w.vars[(actor,'TFR_scw_draft_land')]=4
        w.vars[('SOV','TFR_scw_draft_land')]=6; w.run('TFR_scw_soviet_commit','SOV')
        self.assertEqual(w.value('TFR_scw_draft_total_land','ENG'),18)
        w.click('TFR_scw_allies','ENG_land_set_0','ENG')
        w.click('TFR_scw_allies','FRA_land_set_2','ENG')
        self.assertEqual(w.value('TFR_scw_draft_total_land','ENG'),12)
        self.assertTrue(w.check(TRIGGERS['TFR_scw_allies_can_commit'],'ENG'))

if __name__=='__main__': unittest.main(verbosity=2)
