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
TFR_scw_approved_sender = {
 TFR_scw_eligible_donor = yes
 has_country_flag = TFR_scw_committed_donor
 has_dynamic_modifier = TFR_scw_volunteer_limits
 check_variable = { modifier@send_volunteer_size = TFR_scw_land }
 check_variable = { modifier@send_volunteer_factor < -1 }
 OR = {
  check_variable = { TFR_scw_land > 0 }
  check_variable = { TFR_scw_air > 0 }
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
TFR_scw_volunteer_permission = {
 FROM = { TFR_scw_approved_sender = yes }
 OR = {
  AND = {
   TFR_scw_axis_recipient = yes
   FROM = { has_country_flag = TFR_scw_axis_donor }
  }
  AND = {
   TFR_scw_allied_recipient = yes
   FROM = { has_country_flag = TFR_scw_allied_donor }
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

effects = '''# Scope: donor. Refresh native limits without creating free capacity from other ideas.
TFR_scw_refresh_native_limits = {
 if = {
  limit = { has_country_flag = TFR_scw_committed_donor TFR_scw_manager_in_period = yes }
  set_temp_variable = { TFR_scw_other_land = modifier@send_volunteer_size }
  subtract_from_temp_variable = { TFR_scw_other_land = TFR_scw_land_adjustment }
  set_variable = { TFR_scw_land_adjustment = TFR_scw_land }
  subtract_from_variable = { TFR_scw_land_adjustment = TFR_scw_other_land }
  set_temp_variable = { TFR_scw_other_air = modifier@air_volunteer_cap }
  subtract_from_temp_variable = { TFR_scw_other_air = TFR_scw_air_adjustment }
  set_temp_variable = { TFR_scw_native_air_base = num_deployed_planes }
  divide_temp_variable = { TFR_scw_native_air_base = 100 }
  round_temp_variable = TFR_scw_native_air_base
  add_to_temp_variable = { TFR_scw_native_air_base = 1 }
  set_variable = { TFR_scw_air_adjustment = TFR_scw_air }
  divide_variable = { TFR_scw_air_adjustment = 100 }
  subtract_from_variable = { TFR_scw_air_adjustment = TFR_scw_native_air_base }
  subtract_from_variable = { TFR_scw_air_adjustment = TFR_scw_other_air }
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
    commit += ' TFR_scw_recount_live = yes\n}\n'
    effects += block(f'TFR_scw_{side}_commit', commit)

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
}
'''
effects += block('TFR_scw_initialize', init)

ground_checks = []
over_checks = []
for quota in range(17):
    ground_checks.append(f'AND = {{ check_variable = {{ TFR_scw_draft_land = {quota} }} NOT = {{ any_country = {{ original_tag = SPR has_volunteers_amount_from = {{ tag = PREV count > {quota} }} }} }} }}')
    over_checks.append(f'AND = {{ check_variable = {{ TFR_scw_land = {quota} }} FROM = {{ has_volunteers_amount_from = {{ tag = ROOT count > {quota} }} }} }}')
triggers += block('TFR_scw_ground_within_draft', block('OR', chr(10).join(ground_checks)))
triggers += block('TFR_scw_sent_above_quota', block('OR', chr(10).join(over_checks)))
air_checks = [f'AND = {{ check_variable = {{ TFR_scw_draft_air = {quota} }} num_planes_stationed_in_regions = {{ value < {quota+1} regions = {{ 41 209 210 }} }} }}' for quota in range(0,601,100)]
triggers += block('TFR_scw_air_within_draft', block('OR', chr(10).join(air_checks)))

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
 limit = { has_country_flag = TFR_scw_committed_donor TFR_scw_manager_in_period = yes }
 TFR_scw_refresh_native_limits = yes
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
on_send = """if = {
 limit = { FROM = { TFR_scw_managed_recipient = yes } }
 if = {
  limit = {
   OR = {
    NOT = { TFR_scw_approved_sender = yes }
    TFR_scw_sent_above_quota = yes
    AND = { has_country_flag = TFR_scw_axis_donor FROM = { NOT = { TFR_scw_axis_recipient = yes } } }
    AND = { has_country_flag = TFR_scw_allied_donor FROM = { NOT = { TFR_scw_allied_recipient = yes } } }
   }
  }
  recall_volunteers_from = FROM
 }
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
gfx = ''
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
position = { x = -620 y = 4 }
size = { width = 108 height = 30 }
orientation = UPPER_RIGHT
buttonType = {
 name = "open"
 quadTextureSprite = "GFX_generic_box_96"
 position = { x = 0 y = 0 }
 scale = 1.1
 pdx_tooltip = "TFR_SCW_OPEN_TT"
 clicksound = click_ok
 oversound = ui_menu_over
}
''' + textbox('open_title', 'TFR_SCW_OPEN', 3, 4, 104, h=23))
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
dirty = TFR_scw_ui_dirty
visible = {
 TFR_scw_can_view = yes
}
''' + block('effects', open_effect))

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
for side, leader, _, _, _ in GROUPS:
    loc[f'TFR_SCW_DRAFT_{side.upper()}'] = loc[f'TFR_SCW_DRAFT_{side.upper()}'].replace('[?TFR_scw','[?'+leader+'.TFR_scw')
    loc[f'TFR_SCW_LIVE_{side.upper()}'] = f'Approved: [?{leader}.TFR_scw_live_total_land|0] divisions    [?{leader}.TFR_scw_live_total_air|0] aircraft'

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
    if side != 'soviet': layout += textbox('live', f'TFR_SCW_LIVE_{side.upper()}', 24, 108, 940, h=22)
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
        if readonly: card += textbox('soviet_readonly_note','TFR_SCW_SOV_READ_ONLY',12,142,230,'hoi_16mbs',18)
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
original = (ROOT/rel).read_bytes().decode('utf-8-sig')
marker = 'TFR_scw_managed_recipient = yes'
if marker not in original:
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
    replacement = '\n\tif = {\n\t\tlimit = { TFR_scw_managed_recipient = yes }\n\t\tcustom_trigger_tooltip = {\n\t\t\ttooltip = TFR_SCW_PERMISSION_TT\n\t\t\tTFR_scw_volunteer_permission = yes\n\t\t}\n\t}\n\telse = {\n' + body + '\n\t}\n'
    write(rel, original[:start+1]+replacement+original[end:])

backup = Path(r'C:\Users\mihai\.codex\backups\tfr-scw-volunteers') / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
backup.mkdir(parents=True, exist_ok=False)
for rel, data in FILES.items():
    p = ROOT/rel
    if p.exists():
        b = backup/rel
        b.parent.mkdir(parents=True, exist_ok=True)
        b.write_bytes(p.read_bytes())
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
print(f'Generated {len(FILES)} files; backup: {backup}')
