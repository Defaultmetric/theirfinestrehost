"""Generate Spain volunteer allocation UI and guarded native limits."""
from pathlib import Path
from datetime import datetime, timezone
import re
import io
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
AXIS = ['GER', 'ITA', 'ROM', 'HUN', 'BUL']
ALLIES = ['ENG', 'FRA', 'CAN', 'AST', 'SAF', 'RAJ', 'BRA', 'MEX']
GROUPS = [('axis', 'GER', AXIS, 16, 600), ('allies', 'ENG', ALLIES, 12, 300), ('soviet', 'SOV', ['SOV'], 6, 300)]
DONORS = AXIS + ALLIES + ['SOV']
EXCLUDED = ['FIN', 'MON', 'JAP', 'SIA', 'NZL', 'USA', 'CHI']
FILES = {}

def write(rel, text, bom=False):
    FILES[rel] = (b'\xef\xbb\xbf' if bom else b'') + text.replace('\r\n', '\n').encode('utf-8')

def block(name, body):
    return name + ' = {\n' + '\n'.join('\t' + line for line in body.splitlines()) + '\n}\n'

triggers = '''TFR_scw_manager_in_period = {
 date < 1939.1.1
 NOT = { has_global_flag = scw_over }
 NOT = { has_global_flag = TFR_scw_manager_finished }
}
TFR_scw_managed_recipient = {
 has_global_flag = TFR_scw_manager_initialized
 TFR_scw_manager_in_period = yes
 original_tag = SPR
 has_civil_war = yes
}
# Tolerant on purpose: other send_volunteer_size sources (ideas, advisors) must not turn a committed donor into "not approved".
# Over-quota situations are handled by TFR_scw_update_limits (cap + warning + grace), not by this trigger.
TFR_scw_approved_sender = {
 TFR_scw_eligible_donor = yes
 has_country_flag = TFR_scw_committed_donor
 has_dynamic_modifier = TFR_scw_volunteer_limits
 OR = {
  check_variable = { TFR_scw_land > 0 }
  check_variable = { TFR_scw_air > 0 }
 }
}
# Scope: donor. Room left under its own quota and the remaining bloc pool (computed by TFR_scw_update_limits).
TFR_scw_has_room = {
 OR = {
  check_variable = { TFR_scw_land_room > 0 }
  check_variable = { TFR_scw_air_room > 0 }
 }
}
TFR_scw_axis_recipient = {
 original_tag = SPR
 OR = {
  has_country_flag = SPR_nationalist_spain_flag
  has_country_flag = scw_no_lar_nationalists
 }
}
TFR_scw_allied_recipient = {
 original_tag = SPR
 OR = {
  has_country_flag = SPR_republican_spain_flag
  has_country_flag = scw_no_lar_republicans
 }
}
# ROOT = sender, FROM = Spanish receiver (DIPLOMACY_SEND_VOLUNTEERS_ENABLE_TRIGGER). Also blocks requests when the sender
# or its bloc has no room left, so a human Spain cannot accept volunteers beyond the limit.
TFR_scw_volunteer_permission = {
 TFR_scw_approved_sender = yes
 TFR_scw_has_room = yes
 OR = {
  AND = {
   FROM = { TFR_scw_axis_recipient = yes }
   has_country_flag = TFR_scw_axis_donor
  }
  AND = {
   FROM = { TFR_scw_allied_recipient = yes }
   has_country_flag = TFR_scw_allied_donor
  }
 }
}
'''
triggers += block('TFR_scw_eligible_donor', block('OR', '\n'.join(f'original_tag = {tag}' for tag in DONORS)))
triggers += block('TFR_scw_can_view', 'TFR_scw_manager_in_period = yes\nOR = { TFR_scw_eligible_donor = yes original_tag = SPR original_tag = SPA original_tag = SPD original_tag = SPB original_tag = SPC }')
triggers += '''TFR_scw_uk_priority_ready = {
 OR = {
  has_global_flag = TFR_scw_soviet_confirmed
  NOT = { date < 1936.8.1 }
 }
}
'''

effects = '''# Scope: donor. Native limits follow TFR_scw_cap_land (own quota clamped to what is left in the bloc pool, see
# TFR_scw_update_limits). send_volunteer_factor = -1000 removes the proportional part, so the native land limit is the
# total send_volunteer_size; other sources (ideas, advisors) are cancelled out so they cannot create free capacity.
# ASSUMPTION (verify in game): the engine clamps the proportional part at 0 before adding send_volunteer_size.
# Air: the native air formula (sender planes x ratio, receiver air base capacity) cannot be read from script, so no
# guessed conversion is used: while there is air room the native air limit is left as is (over-quota air is caught by
# TFR_scw_update_limits), and once the air quota is used up air_volunteer_cap is pushed far negative to block more.
TFR_scw_refresh_native_limits = {
 if = {
  limit = { has_country_flag = TFR_scw_committed_donor TFR_scw_manager_in_period = yes }
  set_temp_variable = { TFR_scw_other_land = modifier@send_volunteer_size }
  subtract_from_temp_variable = { TFR_scw_other_land = TFR_scw_land_adjustment }
  set_variable = { TFR_scw_land_adjustment = TFR_scw_cap_land }
  subtract_from_variable = { TFR_scw_land_adjustment = TFR_scw_other_land }
  if = {
   limit = { check_variable = { TFR_scw_air_room > 0 } }
   set_variable = { TFR_scw_air_adjustment = 0 }
  }
  else = {
   set_variable = { TFR_scw_air_adjustment = -100000 }
  }
  force_update_dynamic_modifier = yes
 }
}
TFR_scw_remove_native_limits = {
 if = {
  limit = { has_dynamic_modifier = TFR_scw_volunteer_limits }
  remove_dynamic_modifier = { modifier = TFR_scw_volunteer_limits }
 }
 remove_ideas = TFR_scw_volunteer_authority
}
TFR_scw_apply_donor = {
 set_variable = { TFR_scw_land = TFR_scw_draft_land }
 set_variable = { TFR_scw_air = TFR_scw_draft_air }
 if = {
  limit = { OR = { check_variable = { TFR_scw_land > 0 } check_variable = { TFR_scw_air > 0 } } }
  set_country_flag = TFR_scw_committed_donor
  if = {
   limit = { NOT = { has_dynamic_modifier = TFR_scw_volunteer_limits } }
   set_variable = { TFR_scw_land_adjustment = 0 }
   set_variable = { TFR_scw_air_adjustment = 0 }
   add_dynamic_modifier = { modifier = TFR_scw_volunteer_limits }
  }
  add_ideas = TFR_scw_volunteer_authority
  TFR_scw_refresh_native_limits = yes
 }
 else = {
  clr_country_flag = TFR_scw_committed_donor
  TFR_scw_remove_native_limits = yes
  set_variable = { TFR_scw_land_adjustment = 0 }
  set_variable = { TFR_scw_air_adjustment = 0 }
 }
}
TFR_scw_copy_live_to_draft = {
 set_variable = { TFR_scw_draft_land = TFR_scw_land }
 set_variable = { TFR_scw_draft_air = TFR_scw_air }
}
TFR_scw_cleanup = {
 set_global_flag = TFR_scw_manager_finished
 every_country = {
  limit = { has_country_flag = TFR_scw_managed_donor }
  TFR_scw_remove_native_limits = yes
  clr_country_flag = TFR_scw_committed_donor
  clr_country_flag = TFR_scw_panel_open
  add_to_variable = { TFR_scw_ui_dirty = 1 }
 }
}
'''

for side, leader, tags, land_max, air_max in GROUPS:
    sum_body = 'set_variable = { TFR_scw_draft_total_land = 0 }\nset_variable = { TFR_scw_draft_total_air = 0 }\n'
    for tag in tags:
        sum_body += f'add_to_variable = {{ TFR_scw_draft_total_land = {tag}.TFR_scw_draft_land }}\nadd_to_variable = {{ TFR_scw_draft_total_air = {tag}.TFR_scw_draft_air }}\n'
    if side == 'allies':
        sum_body += 'add_to_variable = { TFR_scw_draft_total_land = SOV.TFR_scw_land }\nadd_to_variable = { TFR_scw_draft_total_air = SOV.TFR_scw_air }\n'
    sum_body += 'add_to_variable = { TFR_scw_ui_dirty = 1 }'
    effects += block(f'TFR_scw_{side}_recount', sum_body)
    guard = f'original_tag = {leader}\nTFR_scw_manager_in_period = yes\nNOT = {{ has_country_flag = TFR_scw_month_committed }}\n'
    if side == 'allies': guard += 'TFR_scw_uk_priority_ready = yes\n'
    guard += f'check_variable = {{ TFR_scw_draft_total_land < {land_max + 1} }}\ncheck_variable = {{ TFR_scw_draft_total_air < {air_max + 1} }}\n'
    if side == 'soviet':
        guard += '''check_variable = { TFR_scw_draft_total_land > -1 }
check_variable = { TFR_scw_draft_total_air > -1 }
check_variable = { TFR_scw_allied_new_land < 13 }
check_variable = { TFR_scw_allied_new_air < 301 }
'''
    # Numeric volunteer-count triggers do not accept scoped variable operands.
    for tag in tags:
        guard += f'{tag} = {{ TFR_scw_ground_within_draft = yes TFR_scw_air_within_draft = yes }}' + chr(10)
    triggers += block(f'TFR_scw_{side}_can_commit', guard)
    prepare = f'TFR_scw_{side}_recount = yes\n'
    for tag in tags:
        prepare += f'{tag} = {{ set_variable = {{ TFR_scw_air_check_ceiling = TFR_scw_draft_air }} add_to_variable = {{ TFR_scw_air_check_ceiling = 1 }} }}\n'
        # Cache slider positions and remaining pool capacity only when the draft changes.
        prepare += f'''set_variable = {{ TFR_scw_{tag}_land_x = {tag}.TFR_scw_draft_land }}
multiply_variable = {{ TFR_scw_{tag}_land_x = 13 }}
add_to_variable = {{ TFR_scw_{tag}_land_x = 12 }}
set_variable = {{ TFR_scw_{tag}_air_y = {tag}.TFR_scw_draft_air }}
divide_variable = {{ TFR_scw_{tag}_air_y = 100 }}
multiply_variable = {{ TFR_scw_{tag}_air_y = -13 }}
add_to_variable = {{ TFR_scw_{tag}_air_y = {56 + (air_max // 100) * 13} }}
set_variable = {{ TFR_scw_{tag}_land_available = {land_max} }}
subtract_from_variable = {{ TFR_scw_{tag}_land_available = TFR_scw_draft_total_land }}
add_to_variable = {{ TFR_scw_{tag}_land_available = {tag}.TFR_scw_draft_land }}
set_variable = {{ TFR_scw_{tag}_air_available = {air_max} }}
subtract_from_variable = {{ TFR_scw_{tag}_air_available = TFR_scw_draft_total_air }}
add_to_variable = {{ TFR_scw_{tag}_air_available = {tag}.TFR_scw_draft_air }}
'''
    if side == 'soviet':
        prepare += '''set_variable = { TFR_scw_allied_new_land = ENG.TFR_scw_live_total_land }
subtract_from_variable = { TFR_scw_allied_new_land = TFR_scw_land }
add_to_variable = { TFR_scw_allied_new_land = TFR_scw_draft_land }
set_variable = { TFR_scw_allied_new_air = ENG.TFR_scw_live_total_air }
subtract_from_variable = { TFR_scw_allied_new_air = TFR_scw_air }
add_to_variable = { TFR_scw_allied_new_air = TFR_scw_draft_air }
set_variable = { TFR_scw_SOV_land_available = 12 }
subtract_from_variable = { TFR_scw_SOV_land_available = ENG.TFR_scw_live_total_land }
add_to_variable = { TFR_scw_SOV_land_available = TFR_scw_land }
clamp_variable = { var = TFR_scw_SOV_land_available min = 0 max = 6 }
set_variable = { TFR_scw_SOV_air_available = 300 }
subtract_from_variable = { TFR_scw_SOV_air_available = ENG.TFR_scw_live_total_air }
add_to_variable = { TFR_scw_SOV_air_available = TFR_scw_air }
clamp_variable = { var = TFR_scw_SOV_air_available min = 0 max = 300 }
'''
    effects += block(f'TFR_scw_{side}_prepare', prepare)
    commit = f'TFR_scw_{side}_prepare = yes\nif = {{\n limit = {{ TFR_scw_{side}_can_commit = yes }}\n'
    for tag in tags:
        commit += f' {tag} = {{ TFR_scw_apply_donor = yes }}\n'
    commit += ' set_country_flag = TFR_scw_month_committed\n'
    if side == 'soviet': commit += ' set_global_flag = TFR_scw_soviet_confirmed\n'
    commit += ' TFR_scw_recount_live = yes\n TFR_scw_update_limits = yes\n}\n'
    effects += block(f'TFR_scw_{side}_commit', commit)

# Live volunteer accounting. Blocs share one pool: Axis (GER holds the totals) and Allies incl. USSR (ENG holds the totals).
# Everything runs from one place (TFR_scw_update_limits) in this fixed donor order, so every MP client resolves ties the same way.
SPAIN_REGIONS = '41 209 210'
GRACE_DAYS = 7
BLOCS = [('axis', 'GER', AXIS, 16, 600), ('allies', 'ENG', ALLIES + ['SOV'], 12, 300)]

count = '''# Divisions really sent to every Spanish tag. has_volunteers_amount_from only compares, so a ladder reads the value.
# ASSUMPTION (verify in game): divisions still in transit are counted. The native per-donor limit counts them anyway.
set_variable = { TFR_scw_sent_land = 0 }
every_country = {
 limit = { original_tag = SPR has_volunteers_amount_from = { tag = PREV count > 0 } }
'''
for n in range(17, 0, -1):
    head = 'if' if n == 17 else ('else' if n == 1 else 'else_if')
    lim = '' if n == 1 else f'limit = {{ has_volunteers_amount_from = {{ tag = PREV count > {n-1} }} }} '
    count += f' {head} = {{ {lim}PREV = {{ add_to_variable = {{ TFR_scw_sent_land = {n} }} }} }}\n'
count += '''}
# Planes based in the Spanish regions, rounded down to 10 (display and bloc accounting; the quota check is exact).
# A donor that controls a state in those regions (UK: Gibraltar is in region 210) has its own planes there, so its
# volunteer planes cannot be told apart: air is then not counted and not punished (quota 0 still blocks air natively).
set_variable = { TFR_scw_sent_air = 0 }
if = {
 limit = { TFR_scw_air_untracked = yes }
}
'''
for n in range(610, 0, -10):
    count += f'else_if = {{ limit = {{ num_planes_stationed_in_regions = {{ value > {n-1} regions = {{ {SPAIN_REGIONS} }} }} }} set_variable = {{ TFR_scw_sent_air = {n} }} }}\n'
effects += '# Scope: donor.\n' + block('TFR_scw_count_sent', count)
region_or = ' '.join(f'region = {r}' for r in SPAIN_REGIONS.split())
triggers += '# Scope: donor. Owns/controls a state in the Spanish regions, so planes based there are not only volunteers.\n'
triggers += block('TFR_scw_air_untracked', f'any_controlled_state = {{ OR = {{ {region_or} }} }}')
triggers += block('TFR_scw_air_over_quota', 'NOT = { TFR_scw_air_untracked = yes }\n' + block('OR', '\n'.join(
    f'AND = {{ check_variable = {{ TFR_scw_air = {q} }} num_planes_stationed_in_regions = {{ value > {q} regions = {{ {SPAIN_REGIONS} }} }} }}' for q in range(0, 601, 100))))

update = ''
for side, leader, tags, land_pool, air_pool in BLOCS:
    update += f'# {side} bloc: {land_pool} divisions / {air_pool} aircraft, totals on {leader}.\n'
    update += f'{leader} = {{ set_variable = {{ TFR_scw_bloc_sent_land = 0 }} set_variable = {{ TFR_scw_bloc_sent_air = 0 }} }}\n'
    for tag in tags:
        update += f'{tag} = {{ TFR_scw_count_sent = yes }}\n'
        update += f'{leader} = {{ add_to_variable = {{ TFR_scw_bloc_sent_land = {tag}.TFR_scw_sent_land }} add_to_variable = {{ TFR_scw_bloc_sent_air = {tag}.TFR_scw_sent_air }} }}\n'
    update += f'''{leader} = {{
 set_variable = {{ TFR_scw_bloc_free_land = {land_pool} }}
 subtract_from_variable = {{ TFR_scw_bloc_free_land = TFR_scw_bloc_sent_land }}
 clamp_variable = {{ var = TFR_scw_bloc_free_land min = 0 }}
 set_variable = {{ TFR_scw_bloc_free_air = {air_pool} }}
 subtract_from_variable = {{ TFR_scw_bloc_free_air = TFR_scw_bloc_sent_air }}
 clamp_variable = {{ var = TFR_scw_bloc_free_air min = 0 }}
 set_variable = {{ TFR_scw_bloc_left_land = {land_pool} }}
 set_variable = {{ TFR_scw_bloc_left_air = {air_pool} }}
}}
'''
    for tag in tags:
        update += f'''{tag} = {{
 # Cap shown to the native volunteer UI: what is already there + what still fits in quota and bloc pool.
 set_variable = {{ TFR_scw_cap_land = TFR_scw_sent_land }}
 add_to_variable = {{ TFR_scw_cap_land = {leader}.TFR_scw_bloc_free_land }}
 if = {{ limit = {{ check_variable = {{ TFR_scw_cap_land > TFR_scw_land }} }} set_variable = {{ TFR_scw_cap_land = TFR_scw_land }} }}
 set_variable = {{ TFR_scw_land_room = TFR_scw_cap_land }}
 subtract_from_variable = {{ TFR_scw_land_room = TFR_scw_sent_land }}
 clamp_variable = {{ var = TFR_scw_land_room min = 0 }}
 set_variable = {{ TFR_scw_cap_air = TFR_scw_sent_air }}
 add_to_variable = {{ TFR_scw_cap_air = {leader}.TFR_scw_bloc_free_air }}
 if = {{ limit = {{ check_variable = {{ TFR_scw_cap_air > TFR_scw_air }} }} set_variable = {{ TFR_scw_cap_air = TFR_scw_air }} }}
 set_variable = {{ TFR_scw_air_room = TFR_scw_cap_air }}
 subtract_from_variable = {{ TFR_scw_air_room = TFR_scw_sent_air }}
 clamp_variable = {{ var = TFR_scw_air_room min = 0 }}
 # Who is over: the pool is handed out in the fixed donor order, so a same-day race always penalises the later donor.
 set_variable = {{ TFR_scw_left_land = {leader}.TFR_scw_bloc_left_land }}
 set_variable = {{ TFR_scw_ok_land = TFR_scw_sent_land }}
 if = {{ limit = {{ check_variable = {{ TFR_scw_ok_land > TFR_scw_land }} }} set_variable = {{ TFR_scw_ok_land = TFR_scw_land }} }}
 if = {{ limit = {{ check_variable = {{ TFR_scw_ok_land > TFR_scw_left_land }} }} set_variable = {{ TFR_scw_ok_land = TFR_scw_left_land }} }}
 set_variable = {{ TFR_scw_left_air = {leader}.TFR_scw_bloc_left_air }}
 set_variable = {{ TFR_scw_ok_air = TFR_scw_sent_air }}
 if = {{ limit = {{ check_variable = {{ TFR_scw_ok_air > TFR_scw_air }} }} set_variable = {{ TFR_scw_ok_air = TFR_scw_air }} }}
 if = {{ limit = {{ check_variable = {{ TFR_scw_ok_air > TFR_scw_left_air }} }} set_variable = {{ TFR_scw_ok_air = TFR_scw_left_air }} }}
 if = {{
  limit = {{
   OR = {{
    check_variable = {{ TFR_scw_sent_land > TFR_scw_ok_land }}
    check_variable = {{ TFR_scw_sent_air > TFR_scw_ok_air }}
    TFR_scw_air_over_quota = yes
   }}
  }}
  if = {{
   limit = {{ NOT = {{ has_country_flag = TFR_scw_over_quota }} }}
   set_country_flag = TFR_scw_over_quota
   set_variable = {{ TFR_scw_over_days = 0 }}
   country_event = {{ id = tfr_scw_volunteers.2 }}
  }}
 }}
 else = {{ clr_country_flag = TFR_scw_over_quota }}
 TFR_scw_refresh_native_limits = yes
}}
{leader} = {{
 subtract_from_variable = {{ TFR_scw_bloc_left_land = {tag}.TFR_scw_ok_land }}
 subtract_from_variable = {{ TFR_scw_bloc_left_air = {tag}.TFR_scw_ok_air }}
}}
'''
update += 'TFR_scw_refresh_views = yes\n'
effects += '# Scope: any. Recount live volunteers, recompute caps/room, flag over-quota donors. Deterministic order.\n' + block('TFR_scw_update_limits', update)

tick = ''
for tag in DONORS:
    tick += f'''{tag} = {{
 if = {{
  limit = {{ has_country_flag = TFR_scw_over_quota }}
  add_to_variable = {{ TFR_scw_over_days = 1 }}
  if = {{
   limit = {{ check_variable = {{ TFR_scw_over_days > {GRACE_DAYS - 1} }} }}
   # Last resort: recall_volunteers_from takes back the whole contingent in that country.
   every_country = {{ limit = {{ original_tag = SPR exists = yes }} PREV = {{ recall_volunteers_from = PREV }} }}
   clr_country_flag = TFR_scw_over_quota
   country_event = {{ id = tfr_scw_volunteers.3 }}
  }}
 }}
}}
'''
tick += 'TFR_scw_update_limits = yes\n'
effects += f'# Scope: any. Called once a day from GER: {GRACE_DAYS} days of grace after the warning, then recall.\n' + block('TFR_scw_daily_enforce', tick)

live = ''
for side, leader, tags, _, _ in GROUPS[:2]:
    live += f'{leader} = {{\n set_variable = {{ TFR_scw_live_total_land = 0 }}\n set_variable = {{ TFR_scw_live_total_air = 0 }}\n'
    for tag in tags + (['SOV'] if side == 'allies' else []):
        live += f' add_to_variable = {{ TFR_scw_live_total_land = {tag}.TFR_scw_land }}\n add_to_variable = {{ TFR_scw_live_total_air = {tag}.TFR_scw_air }}\n'
    live += f' TFR_scw_{side}_prepare = yes\n}}\n'
live += 'SOV = { TFR_scw_soviet_prepare = yes }\nTFR_scw_refresh_views = yes\n'
effects += block('TFR_scw_recount_live', live)

init = '''if = {
 limit = { NOT = { has_global_flag = TFR_scw_manager_initialized } TFR_scw_manager_in_period = yes }
 set_global_flag = TFR_scw_manager_initialized
'''
for tag in DONORS:
    side = 'axis' if tag in AXIS else 'allied'
    init += f''' {tag} = {{
  set_country_flag = TFR_scw_managed_donor
  set_country_flag = TFR_scw_{side}_donor
  set_variable = {{ TFR_scw_land = 0 }}
  set_variable = {{ TFR_scw_air = 0 }}
  TFR_scw_copy_live_to_draft = yes
 }}
'''
init += ''' TFR_scw_recount_live = yes
 SOV = { TFR_scw_soviet_prepare = yes }
 TFR_scw_update_limits = yes
}
'''
effects += block('TFR_scw_initialize', init)

ground_checks = []
for quota in range(17):
    ground_checks.append(f'AND = {{ check_variable = {{ TFR_scw_draft_land = {quota} }} NOT = {{ any_country = {{ original_tag = SPR has_volunteers_amount_from = {{ tag = PREV count > {quota} }} }} }} }}')
triggers += block('TFR_scw_ground_within_draft', block('OR', chr(10).join(ground_checks)))
air_checks = [f'AND = {{ check_variable = {{ TFR_scw_draft_air = {quota} }} num_planes_stationed_in_regions = {{ value < {quota+1} regions = {{ 41 209 210 }} }} }}' for quota in range(0,601,100)]
triggers += block('TFR_scw_air_within_draft', block('OR', 'TFR_scw_air_untracked = yes' + chr(10) + chr(10).join(air_checks)))

write('common/scripted_effects/tfr_scw_volunteers.txt', effects)
write('common/scripted_triggers/tfr_scw_volunteers.txt', triggers)
write('common/dynamic_modifiers/tfr_scw_volunteers.txt', '''TFR_scw_volunteer_limits = {
 enable = { TFR_scw_manager_in_period = yes has_country_flag = TFR_scw_committed_donor }
 send_volunteer_factor = -1000
 send_volunteer_size = var:TFR_scw_land_adjustment
 air_volunteer_cap = var:TFR_scw_air_adjustment
 send_volunteers_tension = -100
 send_volunteer_divisions_required = -1
}
''')
write('common/ideas/tfr_scw_volunteers.txt', '''ideas = {
 country = {
  TFR_scw_volunteer_authority = {
   allowed = { always = no }
   picture = generic_infantry_bonus
   removal_cost = -1
   cancel = { NOT = { TFR_scw_manager_in_period = yes } }
   rule = { can_send_volunteers = yes }
  }
 }
}
''')

monthly = ''
for side, leader, tags, _, _ in GROUPS:
    monthly += f'''if = {{
 limit = {{ tag = {leader} TFR_scw_manager_in_period = yes }}
 clr_country_flag = TFR_scw_month_committed
'''
    for tag in tags: monthly += f' {tag} = {{ TFR_scw_copy_live_to_draft = yes }}\n'
    monthly += f' TFR_scw_{side}_prepare = yes\n TFR_scw_refresh_views = yes\n}}\n'
daily = '''if = {
 limit = { tag = GER }
 if = {
  limit = { NOT = { TFR_scw_manager_in_period = yes } NOT = { has_global_flag = TFR_scw_manager_finished } }
  TFR_scw_cleanup = yes
 }
 else = { TFR_scw_initialize = yes }
}
if = {
 limit = { tag = GER TFR_scw_manager_in_period = yes has_global_flag = TFR_scw_manager_initialized }
 TFR_scw_daily_enforce = yes
}
if = {
 limit = { NOT = { TFR_scw_eligible_donor = yes } has_country_flag = TFR_scw_managed_donor }
 TFR_scw_remove_native_limits = yes
 clr_country_flag = TFR_scw_committed_donor
 clr_country_flag = TFR_scw_axis_donor
 clr_country_flag = TFR_scw_allied_donor
 clr_country_flag = TFR_scw_managed_donor
 set_variable = { TFR_scw_land = 0 }
 set_variable = { TFR_scw_air = 0 }
 set_variable = { TFR_scw_draft_land = 0 }
 set_variable = { TFR_scw_draft_air = 0 }
 TFR_scw_recount_live = yes
}
'''
daily += '''if = {
 limit = { tag = GER TFR_scw_manager_in_period = yes NOT = { date < 1936.8.1 } NOT = { has_global_flag = TFR_scw_august_fallback_notified } }
 set_global_flag = TFR_scw_august_fallback_notified
 TFR_scw_refresh_views = yes
}
'''
on_send = """# ROOT = sender, FROM = receiver. Immediate recall only when the sender may not send at all (no confirmed quota,
# not a managed donor, or the wrong side). Over-quota sends go through the cap/warning/grace path of TFR_scw_update_limits.
if = {
 limit = { FROM = { TFR_scw_managed_recipient = yes } }
 if = {
  limit = {
   OR = {
    NOT = { TFR_scw_approved_sender = yes }
    AND = { has_country_flag = TFR_scw_axis_donor FROM = { NOT = { TFR_scw_axis_recipient = yes } } }
    AND = { has_country_flag = TFR_scw_allied_donor FROM = { NOT = { TFR_scw_allied_recipient = yes } } }
   }
  }
  recall_volunteers_from = FROM
  country_event = { id = tfr_scw_volunteers.4 }
 }
 else = { TFR_scw_update_limits = yes }
}
"""
write('common/on_actions/tfr_scw_volunteers.txt', block('on_actions', block('on_startup', block('effect', 'GER = { TFR_scw_initialize = yes }')) + block('on_daily', block('effect', daily)) + block('on_monthly', block('effect', monthly)) + block('on_send_volunteers', block('effect', on_send))))

# Old saves can also explicitly initialize through a harmless console test event.
write('events/tfr_scw_volunteers.txt', '''add_namespace = tfr_scw_volunteers
country_event = {
 id = tfr_scw_volunteers.1
 hidden = yes
 is_triggered_only = yes
 immediate = { TFR_scw_initialize = yes }
}
# Donor is over its quota or over its share of the bloc pool.
country_event = {
 id = tfr_scw_volunteers.2
 title = tfr_scw_volunteers.2.t
 desc = tfr_scw_volunteers.2.d
 picture = GFX_report_event_soldiers_marching
 is_triggered_only = yes
 option = { name = tfr_scw_volunteers.2.a }
}
# Grace period over: the whole contingent was recalled.
country_event = {
 id = tfr_scw_volunteers.3
 title = tfr_scw_volunteers.3.t
 desc = tfr_scw_volunteers.3.d
 picture = GFX_report_event_soldiers_marching
 is_triggered_only = yes
 option = { name = tfr_scw_volunteers.3.a }
}
# Sender had no right to send (no confirmed quota or wrong side): recalled at once.
country_event = {
 id = tfr_scw_volunteers.4
 title = tfr_scw_volunteers.4.t
 desc = tfr_scw_volunteers.4.d
 picture = GFX_report_event_soldiers_marching
 is_triggered_only = yes
 option = { name = tfr_scw_volunteers.4.a }
}
''')

loc = {
 'TFR_SCW_OPEN': 'Spain Volunteers',
 'TFR_SCW_OPEN_TT': 'Allocate Spanish Civil War volunteers. Active until the war ends or 1 January 1939.',
 'TFR_SCW_AXIS_TITLE': 'AXIS | SPAIN VOLUNTEERS',
 'TFR_SCW_ALLIES_TITLE': 'ALLIES | SPAIN VOLUNTEERS',
 'TFR_SCW_SOVIET_TITLE': 'USSR | FIRST RESERVATION',
 'TFR_SCW_DRAFT_AXIS': 'Draft: [?TFR_scw_draft_total_land|0]/16 divisions    [?TFR_scw_draft_total_air|0]/600 aircraft',
 'TFR_SCW_DRAFT_ALLIES': 'Draft + USSR: [?TFR_scw_draft_total_land|0]/12 divisions    [?TFR_scw_draft_total_air|0]/300 aircraft',
 'TFR_SCW_DRAFT_SOVIET': 'Reservation: [?TFR_scw_draft_total_land|0]/6 divisions    [?TFR_scw_draft_total_air|0]/300 aircraft',
 'TFR_SCW_LIVE': 'Active: [?TFR_scw_live_total_land|0] divisions    [?TFR_scw_live_total_air|0] aircraft',
 'TFR_SCW_HELP': 'Set quotas, then confirm. Unselected countries cannot send to Spain.\nQuotas can be revised each calendar month.',
 'TFR_SCW_ALLIED_HELP': 'USSR chooses first; its quota counts toward 12 divisions and 300 aircraft.',
 'TFR_SCW_HEADERS': 'COUNTRY                         DIVISIONS                         AIRCRAFT',
 'TFR_SCW_APPLY': 'Confirm quotas',
 'TFR_SCW_CLOSE': 'Close',
 'TFR_SCW_APPLY_TT': 'Confirm this month\'s quotas. Totals must fit the budget. Withdraw excess volunteers before reducing a quota. UK must wait for USSR\'s first reservation.',
 'TFR_SCW_LOCKED': 'Confirmed for this month',
 'TFR_SCW_PERMISSION_TT': 'Requires a confirmed quota. Axis may send only to Nationalist Spain; Allies and USSR may send only to Republican Spain.',
 'TFR_scw_volunteer_limits': 'Spanish Volunteer Quota',
 'TFR_scw_volunteer_authority': 'Approved Spanish Volunteers',
 'TFR_scw_volunteer_authority_desc': 'Your country has a confirmed volunteer quota. Germany allocates the Axis pool; the United Kingdom allocates the Allied pool after the Soviet reservation.',
}

# UI textures are simple interface primitives, generated with the UI source.
def ui_texture(name, size, fill, border, thumb=False):
    im = Image.new('RGBA', size, fill)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, size[0]-1, size[1]-1), outline=border, width=1)
    if thumb:
        d.line((size[0]//2, 3, size[0]//2, size[1]-4), fill=(255, 245, 206, 255), width=2)
    buf = io.BytesIO()
    im.save(buf, format='DDS')
    FILES[f'gfx/interface/tfr_scw/{name}.dds'] = buf.getvalue()

textures = [
    ('open_button', (224,44), (74,79,49,255), (215,185,105,255), False),
    ('card', (312,160), (27,32,35,245), (72,80,81,255), False),
    ('land_step', (13,24), (43,48,50,255), (82,88,88,255), False),
    ('land_fill', (13,24), (112,96,52,255), (183,158,91,255), False),
    ('land_thumb', (13,28), (186,151,71,255), (255,229,155,255), True),
    ('air_step', (24,13), (43,48,50,255), (82,88,88,255), False),
    ('air_fill', (24,13), (52,108,115,255), (95,177,187,255), False),
    ('air_thumb', (24,13), (81,155,172,255), (173,231,241,255), True),
]
# scw_volunteers_button.dds (2 frames 55x41, Spanish-coloured helmet on a transparent background, from vanilla
# goal_generic_axis_build_infantry.dds) is hand-made; it is not regenerated here.
gfx = block('spriteType', 'name = "GFX_TFR_scw_volunteers_button"\ntexturefile = "gfx/interface/tfr_scw/scw_volunteers_button.dds"\nnoOfFrames = 2\n')
gfx += block('spriteType', 'name = "GFX_TFR_scw_raids_button"\ntexturefile = "gfx/interface/military_raids/map_icons/raid_round_bg_button.dds"\neffectFile = "gfx/FX/buttonstate.lua"\n')
for name, size, fill, border, thumb in textures:
    ui_texture(name, size, fill, border, thumb)
    gfx += block('spriteType', f'name = "GFX_TFR_scw_{name}"\ntexturefile = "gfx/interface/tfr_scw/{name}.dds"\n' + ('effectFile = "gfx/FX/buttonstate.lua"\n' if name in ('open_button','land_step','air_step') else ''))
write('interface/tfr_scw_volunteers.gfx', block('spriteTypes', gfx))

loc.update({
    'TFR_SCW_OPEN': 'Spain Vols',
    'TFR_SCW_AXIS_TITLE': 'AXIS - SPAIN VOLUNTEERS',
    'TFR_SCW_ALLIES_TITLE': 'ALLIES - SPAIN VOLUNTEERS',
    'TFR_SCW_SOVIET_TITLE': 'USSR - FIRST RESERVATION',
    'TFR_SCW_COUNTRY': 'COUNTRY',
    'TFR_SCW_DIVISIONS': 'Divisions',
    'TFR_SCW_AIRCRAFT': 'Aircraft',
    'TFR_SCW_HELP': 'Click a slider step to set a quota, then confirm.\nChoose your actual divisions and air wings in the normal volunteer menus.',
    'TFR_SCW_MONTHLY_HELP': 'Quotas can be revised each calendar month. Countries with zero quotas cannot send.',
    'TFR_SCW_ALLIED_HELP': 'USSR reserves first: [?SOV.TFR_scw_land|0] divisions / [?SOV.TFR_scw_air|0] aircraft, included in the Allied pool.',
})

def textbox(name, text, x, y, w=650, font='hoi_18mbs', h=24, align='left'):
    return f'instantTextboxType = {{ name = "{name}" position = {{ x = {x} y = {y} }} font = "{font}" text = "{text}" maxWidth = {w} maxHeight = {h} fixedsize = yes multiline = yes format = {align} alwaystransparent = yes }}\n'

def button(name, text, x, y, sprite='GFX_small_button_71x26', tooltip=None):
    tip = f' pdx_tooltip = "{tooltip}"' if tooltip else ''
    return f'buttonType = {{ name = "{name}" position = {{ x = {x} y = {y} }} quadTextureSprite = "{sprite}" buttonText = "{text}" buttonFont = "hoi_18mbs" clicksound = click_ok{tip} }}\n'

def icon(name, sprite, x, y):
    return f'iconType = {{ name = "{name}" position = {{ x = {x} y = {y} }} spriteType = "{sprite}" alwaystransparent = yes }}\n'

gui = 'guiTypes = {\n' + block('containerWindowType', '''name = "TFR_scw_open_window"
# Follow the native raid filter, whose height changes with the available raid categories.
# Its header starts at (-2, -38); leave a five-pixel gap above that header.
position = { x = -2 y = -82 }
size = { width = 82 height = 39 }
iconType = {
 name = "raids_style_frame"
 spriteType = "GFX_raids_filter_header_button"
 position = { x = 0 y = 0 }
 alwaystransparent = yes
}
buttonType = {
 name = "open"
 quadTextureSprite = "GFX_TFR_scw_raids_button"
 position = { x = 25 y = 4 }
 pdx_tooltip = "TFR_SCW_OPEN_TT"
 clicksound = click_ok
 oversound = ui_menu_over
}
iconType = {
 name = "spanish_helmet"
 spriteType = "GFX_TFR_scw_volunteers_button"
 frame = 1
 position = { x = 20 y = 4 }
 scale = 0.75
 alwaystransparent = yes
}
''')
open_effect = '''open_click = {
 if = { limit = { has_country_flag = TFR_scw_panel_open } clr_country_flag = TFR_scw_panel_open }
 else = { set_country_flag = TFR_scw_panel_open }
 if = {
  limit = { NOT = { check_variable = { TFR_scw_view > 0 } } }
  set_variable = { TFR_scw_view = 2 }
  if = { limit = { original_tag = GER } set_variable = { TFR_scw_view = 1 } }
  if = { limit = { original_tag = SOV } set_variable = { TFR_scw_view = 3 } }
 }
'''
for side, leader, _, _, _ in GROUPS:
    open_effect += f' if = {{ limit = {{ tag = {leader} }} TFR_scw_{side}_prepare = yes }}\n'
open_effect += ' TFR_scw_sync_view = yes\n}\n'
script_gui = block('TFR_scw_open', '''context_type = player_context
window_name = "TFR_scw_open_window"
parent_window_name = "raid_filter"
dirty = TFR_scw_ui_dirty
# No visible trigger: the button is always shown. When the quota panels do not apply (war over, period ended, or the
# country takes no part), TFR_scw_info explains why instead.
''' + block('effects', open_effect))
gui += block('containerWindowType', 'name = "TFR_scw_info_window"\nposition = { x = -270 y = -95 }\norientation = CENTER\nsize = { width = 540 height = 190 }\nmoveable = yes\nbackground = { name = "background" spriteType = "GFX_tiled_window_thin_border" }\n'
    + textbox('title', 'TFR_SCW_INFO_TITLE', 24, 13, 490, 'hoi_24header', 28)
    + textbox('over_text', 'TFR_SCW_INFO_OVER', 24, 56, 490, 'hoi_18mbs', 80)
    + textbox('none_text', 'TFR_SCW_INFO_NONE', 24, 56, 490, 'hoi_18mbs', 80)
    + button('close', 'TFR_SCW_CLOSE', 196, 140, 'GFX_button_148x34'))
script_gui += block('TFR_scw_info', '''context_type = player_context
window_name = "TFR_scw_info_window"
dirty = TFR_scw_ui_dirty
visible = { has_country_flag = TFR_scw_panel_open NOT = { TFR_scw_can_view = yes } }
''' + block('effects', 'close_click = { clr_country_flag = TFR_scw_panel_open add_to_variable = { TFR_scw_ui_dirty = 1 } }')
    + block('triggers', 'over_text_visible = { NOT = { TFR_scw_manager_in_period = yes } }\nnone_text_visible = { TFR_scw_manager_in_period = yes }'))
loc.update({
    'TFR_SCW_INFO_TITLE': 'SPANISH VOLUNTEERS',
    'TFR_SCW_INFO_OVER': 'The Spanish Civil War is over. Volunteer quotas are no longer managed.',
    'TFR_SCW_INFO_NONE': 'Your country takes no part in the Spanish volunteer quotas. Germany allocates the Axis pool, the United Kingdom the Allied pool and the USSR its own reservation.',
})

# Synchronize positions in each viewer's own scope. Observers see approved quotas.
sync = ''
for side, leader, tags, _, airmax in GROUPS:
    for tag in tags + (['SOV'] if side == 'allies' else []):
        for kind in ['land','air']:
            name = f'TFR_scw_{side}_{tag}_{kind}_position'
            editable = not (side == 'allies' and tag == 'SOV')
            if editable:
                sync += f'if = {{ limit = {{ original_tag = {leader} }} set_variable = {{ {name} = {tag}.TFR_scw_draft_{kind} }} }}\nelse = {{ set_variable = {{ {name} = {tag}.TFR_scw_{kind} }} }}\n'
            else:
                sync += f'set_variable = {{ {name} = {tag}.TFR_scw_{kind} }}\n'
            if kind == 'land':
                sync += f'multiply_variable = {{ {name} = 13 }}\nadd_to_variable = {{ {name} = 12 }}\n'
            else:
                sync += f'divide_variable = {{ {name} = 100 }}\nmultiply_variable = {{ {name} = -13 }}\nadd_to_variable = {{ {name} = {56+airmax//100*13} }}\n'
sync += 'add_to_variable = { TFR_scw_ui_dirty = 1 }\n'
effects += block('TFR_scw_sync_view',sync)
effects += block('TFR_scw_refresh_views','every_country = { limit = { TFR_scw_can_view = yes has_country_flag = TFR_scw_panel_open } TFR_scw_sync_view = yes }')
write('common/scripted_effects/tfr_scw_volunteers.txt',effects)

loc.update({
    'TFR_SCW_TAB_AXIS': 'Axis',
    'TFR_SCW_TAB_ALLIES': 'Allies',
    'TFR_SCW_TAB_SOVIET': 'My reservation',
    'TFR_SCW_READ_ONLY': 'View only. Germany controls Axis quotas; UK controls Allied quotas; USSR chooses its own reservation.',
    'TFR_SCW_SOV_READ_ONLY': 'Soviet reservation - view only',
    'TFR_SCW_SOV_PENDING': '§RSoviet has not picked.§! UK must wait until USSR confirms or 1 August 1936.',
    'TFR_SCW_SOV_PENDING_AUGUST': '§YSoviet has not picked.§! August deadline passed: UK may allocate the full remaining pool.',
    'TFR_SCW_ALLIED_HELP': 'Soviet reservation: [?SOV.TFR_scw_land|0] divisions / [?SOV.TFR_scw_air|0] aircraft, included in the Allied pool.',
    'TFR_SCW_APPLY_TT': 'Confirm this month\'s quotas. Withdraw excess volunteers before reducing a quota. Before 1 August 1936, UK must wait for the Soviet reservation.',
    'TFR_SCW_HELP': 'Click a slider step to set a quota, then confirm.\nChoose actual divisions and air wings in the normal volunteer menus.',
})
loc.update({
    'TFR_SCW_HELP': f'Set quotas with the sliders, then confirm. Send the actual divisions and air wings from the normal volunteer menus.\nAbove quota or bloc pool: {GRACE_DAYS} days to withdraw the excess, then the whole contingent is recalled.',
    'TFR_SCW_MONTHLY_HELP': f'Quotas can be revised each calendar month. Above quota: {GRACE_DAYS} days to withdraw, then the whole contingent is recalled.',
    'TFR_SCW_PERMISSION_TT': 'Requires a confirmed quota with room left (own quota and bloc pool). Axis may send only to Nationalist Spain; Allies and USSR only to Republican Spain.',
    'tfr_scw_volunteers.2.t': 'Volunteers above the Spanish quota',
    'tfr_scw_volunteers.2.d': f'Our volunteers in Spain exceed our confirmed quota or our share of the bloc pool.\nDivisions: [?ROOT.TFR_scw_sent_land|0] sent, [?ROOT.TFR_scw_ok_land|0] allowed. Aircraft based in Spain: about [?ROOT.TFR_scw_sent_air|0], [?ROOT.TFR_scw_ok_air|0] allowed (quota [?ROOT.TFR_scw_air|0]).\nWithdraw the excess within {GRACE_DAYS} days, otherwise the whole contingent will be recalled.',
    'tfr_scw_volunteers.2.a': 'We will withdraw the excess.',
    'tfr_scw_volunteers.3.t': 'Spanish volunteers recalled',
    'tfr_scw_volunteers.3.d': f'Our volunteers stayed above the quota for {GRACE_DAYS} days. The whole contingent has been recalled from Spain.',
    'tfr_scw_volunteers.3.a': 'Understood.',
    'tfr_scw_volunteers.4.t': 'Volunteers sent back',
    'tfr_scw_volunteers.4.d': 'We have no confirmed Spanish volunteer quota, or we sent volunteers to the wrong side. They have been recalled.',
    'tfr_scw_volunteers.4.a': 'Understood.',
})
for side, leader, _, land_pool, air_pool in GROUPS:
    loc[f'TFR_SCW_DRAFT_{side.upper()}'] = loc[f'TFR_SCW_DRAFT_{side.upper()}'].replace('[?TFR_scw','[?'+leader+'.TFR_scw')
    if side == 'soviet':
        loc['TFR_SCW_LIVE_SOVIET'] = 'Reserved: [?SOV.TFR_scw_land|0] div / [?SOV.TFR_scw_air|0] aircraft    Sent: [?SOV.TFR_scw_sent_land|0] div, ~[?SOV.TFR_scw_sent_air|0] aircraft'
    else:
        loc[f'TFR_SCW_LIVE_{side.upper()}'] = f'Approved: [?{leader}.TFR_scw_live_total_land|0] div / [?{leader}.TFR_scw_live_total_air|0] aircraft    Sent: [?{leader}.TFR_scw_bloc_sent_land|0]/{land_pool} div, ~[?{leader}.TFR_scw_bloc_sent_air|0]/{air_pool} aircraft'

for view, (side, leader, donors, landmax, airmax) in enumerate(GROUPS,1):
    tags = donors + (['SOV'] if side == 'allies' else [])
    rows = (len(tags)+2)//3
    view_height = min(rows,3)*170
    height = 168 + view_height + 84
    layout = f'''name = "TFR_scw_{side}_window"
position = {{ x = -500 y = -{height//2} }}
orientation = CENTER
size = {{ width = 1000 height = {height} }}
moveable = yes
background = {{ name = "background" spriteType = "GFX_tiled_window_thin_border" }}
'''
    layout += textbox('title', f'TFR_SCW_{side.upper()}_TITLE', 24, 13, 900, 'hoi_24header', 28)
    ef = 'close_click = { clr_country_flag = TFR_scw_panel_open add_to_variable = { TFR_scw_ui_dirty = 1 } }\n'
    ef += f'apply_click = {{ if = {{ limit = {{ original_tag = {leader} }} TFR_scw_{side}_commit = yes }} }}\n'
    tg = f'apply_click_enabled = {{ TFR_scw_{side}_can_commit = yes }}\napply_visible = {{ original_tag = {leader} }}\n'
    tg += f'locked_visible = {{ original_tag = {leader} has_country_flag = TFR_scw_month_committed }}\n'
    tg += f'draft_visible = {{ original_tag = {leader} }}\nread_only_visible = {{ NOT = {{ original_tag = {leader} }} }}\n'
    tg += 'tab_soviet_visible = { original_tag = SOV }\n'
    for tab_view, tab_side in enumerate(['axis','allies','soviet'],1):
        layout += button(f'tab_{tab_side}', f'TFR_SCW_TAB_{tab_side.upper()}', 24+(tab_view-1)*158, 44, 'GFX_button_148x34')
        authority = 'TFR_scw_can_view = yes' + (' original_tag = SOV' if tab_side == 'soviet' else '')
        ef += f'tab_{tab_side}_click = {{ if = {{ limit = {{ {authority} }} set_variable = {{ TFR_scw_view = {tab_view} }} TFR_scw_sync_view = yes }} }}\n'
        tg += f'tab_{tab_side}_click_enabled = {{ {authority} }}\n'
    layout += textbox('draft', f'TFR_SCW_DRAFT_{side.upper()}', 24, 84, 940, h=22)
    layout += textbox('read_only', 'TFR_SCW_READ_ONLY', 24, 84, 940, 'hoi_16mbs', 22)
    layout += textbox('live', f'TFR_SCW_LIVE_{side.upper()}', 24, 108, 940, h=22)
    if side == 'allies':
        layout += textbox('priority', 'TFR_SCW_ALLIED_HELP', 24, 134, 940, 'hoi_16mbs', 24)
        layout += textbox('soviet_pending', 'TFR_SCW_SOV_PENDING', 24, 134, 940, 'hoi_16mbs', 24)
        layout += textbox('soviet_pending_august', 'TFR_SCW_SOV_PENDING_AUGUST', 24, 134, 940, 'hoi_16mbs', 24)
        tg += '''priority_visible = { has_global_flag = TFR_scw_soviet_confirmed }
soviet_pending_visible = { NOT = { has_global_flag = TFR_scw_soviet_confirmed } date < 1936.8.1 }
soviet_pending_august_visible = { NOT = { has_global_flag = TFR_scw_soviet_confirmed } NOT = { date < 1936.8.1 } }
'''
    else: layout += textbox('monthly', 'TFR_SCW_MONTHLY_HELP', 24, 134, 940, 'hoi_16mbs', 24)
    props = ''
    content = ''
    for i, tag in enumerate(tags):
        readonly = side == 'allies' and tag == 'SOV'
        cardland = 6 if readonly else landmax
        card = f'name = "card_{tag}"\nposition = {{ x = {(i%3)*322} y = {(i//3)*170} }}\nsize = {{ width = 312 height = 160 }}\n'
        card += icon(f'background_{tag}', 'GFX_TFR_scw_card', 0, 0)
        card += icon(f'flag_{tag}', 'GFX_flag_small2', 12, 14)
        props += f'flag_{tag} = {{ image = "[{tag}.GetFlag]" }}\n'
        card += textbox(f'name_{tag}', f'[{tag}.GetName]', 65, 13, 174, 'hoi_16mbs', 38)
        card += textbox(f'land_label_{tag}', 'TFR_SCW_DIVISIONS', 12, 60, 140, 'hoi_16mbs')
        card += textbox(f'air_label_{tag}', 'TFR_SCW_AIRCRAFT', 242, 13, 66, 'hoi_16mbs', 24, 'center')
        for kind, maximum, step in [('land',cardland,1),('air',airmax,100)]:
            xval,yval,wval,align = (183,60,48,'right') if kind=='land' else (242,34,66,'center')
            card += textbox(f'{kind}_live_{tag}', f'[?{tag}.TFR_scw_{kind}|0]', xval, yval, wval, h=24, align=align)
            if not readonly:
                card += textbox(f'{kind}_draft_{tag}', f'[?{tag}.TFR_scw_draft_{kind}|0]', xval, yval, wval, h=24, align=align)
                tg += f'{kind}_draft_{tag}_visible = {{ original_tag = {leader} }}\n'
                tg += f'{kind}_live_{tag}_visible = {{ NOT = {{ original_tag = {leader} }} }}\n'
            for value in range(0,maximum+1,step):
                name = f'{tag}_{kind}_set_{value}'
                x,y = (12+value*13,92) if kind=='land' else (263,56+(maximum-value)//100*13)
                if readonly:
                    card += icon(name, f'GFX_TFR_scw_{kind}_step', x,y)
                else:
                    tip = f'TFR_SCW_{kind.upper()}_{value}_TT'
                    loc[tip] = f'Set quota: {value} '+('divisions' if kind=='land' else 'aircraft')
                    card += button(name,'',x,y,f'GFX_TFR_scw_{kind}_step',tip)
                    permission = f'original_tag = {leader} TFR_scw_manager_in_period = yes NOT = {{ has_country_flag = TFR_scw_month_committed }} {tag} = {{ exists = yes }} OR = {{ check_variable = {{ TFR_scw_{tag}_{kind}_available > {value-1} }} {tag} = {{ check_variable = {{ TFR_scw_draft_{kind} > {value-1} }} }} }}'
                    if side == 'allies': permission += ' TFR_scw_uk_priority_ready = yes'
                    tg += f'{name}_click_enabled = {{ {permission} }}\n'
                    ef += f'''{name}_click = {{
 if = {{
  limit = {{ {permission} }}
  {tag} = {{ set_variable = {{ TFR_scw_draft_{kind} = {value} }} }}
  TFR_scw_{side}_prepare = yes
  TFR_scw_refresh_views = yes
 }}
}}
'''
                if value>0:
                    card += icon(name+'_fill', f'GFX_TFR_scw_{kind}_fill',x,y)
                    check = f'{tag} = {{ check_variable = {{ TFR_scw_{kind} > {value-1} }} }}' if readonly else f'OR = {{ AND = {{ original_tag = {leader} {tag} = {{ check_variable = {{ TFR_scw_draft_{kind} > {value-1} }} }} }} AND = {{ NOT = {{ original_tag = {leader} }} {tag} = {{ check_variable = {{ TFR_scw_{kind} > {value-1} }} }} }} }}'
                    tg += f'{name}_fill_visible = {{ {check} }}\n'
            card += icon(f'{tag}_{kind}_thumb',f'GFX_TFR_scw_{kind}_thumb',12 if kind=='land' else 263,90 if kind=='land' else 56+maximum//100*13)
            props += f'{tag}_{kind}_thumb = {{ '+('x' if kind=='land' else 'y')+f' = TFR_scw_{side}_{tag}_{kind}_position }}\n'
        for value in range(0,cardland+1,4):
            card += textbox(f'{tag}_tick_{value}',str(value),8+value*13,125,26,'hoi_16mbs')
        if cardland%4: card += textbox(f'{tag}_tick_max',str(cardland),8+cardland*13,125,26,'hoi_16mbs')
        # Live sent / allowed (allowed = own quota clamped to what is left in the bloc pool). Red while over quota.
        loc[f'TFR_SCW_SENT_{tag}'] = f'Sent [?{tag}.TFR_scw_sent_land|0]/[?{tag}.TFR_scw_cap_land|0] div  ~[?{tag}.TFR_scw_sent_air|0]/[?{tag}.TFR_scw_cap_air|0] air'
        loc[f'TFR_SCW_OVER_{tag}'] = f'§ROver: [?{tag}.TFR_scw_sent_land|0]/[?{tag}.TFR_scw_ok_land|0] div  ~[?{tag}.TFR_scw_sent_air|0]/[?{tag}.TFR_scw_ok_air|0] air§!'
        card += textbox(f'sent_{tag}', f'TFR_SCW_SENT_{tag}', 12, 142, 228, 'hoi_16mbs', 18)
        card += textbox(f'over_{tag}', f'TFR_SCW_OVER_{tag}', 12, 142, 228, 'hoi_16mbs', 18)
        tg += f'sent_{tag}_visible = {{ NOT = {{ {tag} = {{ has_country_flag = TFR_scw_over_quota }} }} }}\n'
        tg += f'over_{tag}_visible = {{ {tag} = {{ has_country_flag = TFR_scw_over_quota }} }}\n'
        content += block('containerWindowType',card)
    viewport=f'name = "countries_viewport"\nposition = {{ x = 20 y = 168 }}\nsize = {{ width = 970 height = {view_height} }}\n'
    if rows>3: viewport+='verticalScrollbar = "right_vertical_slider"\n'
    viewport+=block('containerWindowType',f'name = "countries_content"\nposition = {{ x = 0 y = 0 }}\nsize = {{ width = 966 height = {rows*170} }}\n'+content)
    layout+=block('containerWindowType',viewport)
    layout+=textbox('help','TFR_SCW_HELP',24,168+view_height+4,940,'hoi_16mbs',34)
    layout+=textbox('locked','TFR_SCW_LOCKED',200,height-34,450)
    layout+=button('apply','TFR_SCW_APPLY',24,height-40,'GFX_button_148x34','TFR_SCW_APPLY_TT')
    layout+=button('close','TFR_SCW_CLOSE',826,height-40,'GFX_button_148x34')
    gui+=block('containerWindowType',layout)
    access='TFR_scw_can_view = yes' + (' original_tag = SOV' if side=='soviet' else '')
    sg=f'''context_type = player_context
window_name = "TFR_scw_{side}_window"
dirty = TFR_scw_ui_dirty
visible = {{ {access} has_country_flag = TFR_scw_panel_open check_variable = {{ TFR_scw_view = {view} }} }}
'''
    sg+=block('effects',ef)+block('triggers',tg)+block('properties',props)
    script_gui+=block(f'TFR_scw_{side}',sg)
gui += '}\n'
script_gui = script_gui.replace('context_type = player_context', 'context_type = player_context' + chr(10) + 'ai_enabled = { always = no }')
write('interface/tfr_scw_volunteers.gui', gui)
write('common/scripted_guis/tfr_scw_volunteers.txt', block('scripted_gui', script_gui))
escaped_loc = {k: v.replace(chr(10), chr(92) + 'n') for k,v in loc.items()}
write('localisation/english/tfr_scw_volunteers_l_english.yml', 'l_english:' + chr(10) + chr(10).join(f' {k}:0 "{v}"' for k,v in escaped_loc.items()) + chr(10), True)

# Preserve all original rules outside the managed Spanish Civil War.
rel = 'common/scripted_triggers/diplomacy_scripted_triggers.txt'
def prepare_volunteer_diplomacy(original):
    # Bulgaria uses Germany's confirmed SCW allocation, without legacy focus gates.
    original = re.sub(
        r'\t\telse_if = \{ #Bulgarian volunteers in SCW \(with La Resistance\).*?(?=\t\telse_if = \{ #Soviet volunteers to China)',
        '', original, flags=re.S)
    marker = 'TFR_scw_managed_recipient = yes'
    if marker in original:
        # Upgrade files already wrapped by older versions of this generator.
        return original.replace('limit = { TFR_scw_managed_recipient = yes }',
                                'limit = { FROM = { TFR_scw_managed_recipient = yes } }')
    match = re.search(r'(?m)^DIPLOMACY_SEND_VOLUNTEERS_ENABLE_TRIGGER\s*=\s*\{', original)
    start = original.index('{', match.start())
    depth = 0
    for tok in re.finditer(r'"(?:\\.|[^"\\])*"|#[^\r\n]*|[{}]',original[start:]):
        if tok.group()=='{': depth += 1
        elif tok.group()=='}':
            depth -= 1
            if depth==0:
                end=start+tok.start()
                break
    body = original[start+1:end]
    replacement = '\n\tif = {\n\t\tlimit = { FROM = { TFR_scw_managed_recipient = yes } }\n\t\tcustom_trigger_tooltip = {\n\t\t\ttooltip = TFR_SCW_PERMISSION_TT\n\t\t\tTFR_scw_volunteer_permission = yes\n\t\t}\n\t}\n\telse = {\n' + body + '\n\t}\n'
    return original[:start+1]+replacement+original[end:]

write(rel, prepare_volunteer_diplomacy((ROOT/rel).read_bytes().decode('utf-8-sig')))

backup = Path(r'C:\Users\mihai\.codex\backups\tfr-scw-volunteers') / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
backup.mkdir(parents=True, exist_ok=False)
for rel, data in FILES.items():
    p = ROOT/rel
    if p.exists() and (p.read_bytes() == data or (p.suffix in ('.txt', '.gui', '.gfx', '.yml') and p.read_bytes().decode('utf-8-sig').replace('\r\n', '\n') == data.decode('utf-8-sig'))):
        continue
    if p.exists():
        b = backup/rel
        b.parent.mkdir(parents=True, exist_ok=True)
        b.write_bytes(p.read_bytes())
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
print(f'Generated {len(FILES)} files; backup: {backup}')
