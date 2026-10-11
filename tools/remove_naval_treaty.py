"""Remove the London/Washington treaty system from the loaded mod/vanilla overlay.

Full-file overrides stop vanilla-only definitions from falling back into the mod.
Edits preserve unrelated country/focus/event/idea content and original encodings.
"""
import json
import re

from hoi4_script import Block, overlay_files, parse, replace_spans, walk
from integrate_naval_tech_bonuses import write, sha
from naval_startup_audit import ROOT, VANILLA

REPORT = ROOT / 'docs/naval-treaty-removal.json'
IDEAS = {'MTG_naval_treaty_adherent', 'MTG_naval_treaty_cheating',
         'MTG_naval_treaty_adherent_reduced', 'MTG_naval_treaty_cheating_reduced',
         'JAP_the_london_naval_treaty'}
FOCUSES = {'ENG_enforce_the_naval_treaties', 'JAP_join_the_london_naval_treaty'}
FLAGS = {'MTG_second_london_conference', 'MTG_naval_treaty_signatories'}
CHANGES = []


def edit(relative, transform):
    target = ROOT / relative
    loaded = target if target.exists() else VANILLA / relative
    source = loaded.read_text(encoding='utf-8-sig')
    after, description = transform(source)
    if after == source:
        return
    if not target.exists():
        # Establish the vanilla BOM/newline style before the shared writer.
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(loaded.read_bytes())
    write(target, after)
    CHANGES.append(dict(source=relative, vanilla_override=loaded != target,
                        before=sha(source), after=sha(after), changes=description))


def remove_entries(source, selector):
    chosen = [(e, a) for e, a in walk(parse(source)) if selector(e, a)]
    # Drop descendants of entries already selected to avoid overlapping edits.
    outer = [(e, a) for e, a in chosen if not any(p.start <= e.start and p.end >= e.end and p is not e for p, _ in chosen)]
    return replace_spans(source, [(e.start, e.end, '') for e, _ in outer]), [e.key for e, _ in outer]


def main():
    assert not REPORT.exists(), 'Removal already applied; run the validator instead.'
    # An empty file with the identical path shadows the vanilla subsystem.
    for relative in ('common/decisions/MTG_naval_treaty.txt', 'events/MTG_naval_treaty_events.txt'):
        edit(relative, lambda s: ('# TFR: naval treaty system removed for every country. Vanilla file intentionally overridden.\n',
                                  ['removed entire treaty subsystem']))
    edit('common/decisions/categories/00_decision_categories.txt',
         lambda s: remove_entries(s, lambda e, a: not a and e.key == 'MTG_naval_treaties'))
    edit('common/decisions/categories/ENG_decision_categories.txt',
         lambda s: remove_entries(s, lambda e, a: not a and e.key == 'ENG_enforce_the_naval_treaties'))
    edit('common/decisions/ENG.txt', lambda s: remove_entries(s, lambda e, a:
         e.key == 'ENG_britain_demands_treaty_compliance' or (not a and e.key == 'ENG_enforce_the_naval_treaties')))
    edit('common/decisions/JAP.txt', lambda s: remove_entries(s, lambda e, a:
         e.key == 'JAP_break_the_london_naval_treaty' or (e.key in ('add_ideas', 'remove_ideas') and e.value in IDEAS if isinstance(e.value, str) else False)))
    for relative in ('common/ideas/zzz_generic.txt', 'common/ideas/japan.txt'):
        edit(relative, lambda s: remove_entries(s, lambda e, a: e.key in IDEAS))
    # South America's naval-arms-race spirit copied the same treaty hull caps.
    # Remove those caps while retaining all its other economic/naval effects.
    edit('common/ideas/TOA_shared_ideas.txt', lambda s: remove_entries(s, lambda e, a:
         e.key.startswith('production_cost_max_ship_hull_')))
    for path in overlay_files(ROOT, VANILLA, 'history/countries'):
        source = path.read_text(encoding='utf-8-sig')
        if not any(idea in source for idea in IDEAS) and not any(flag in source for flag in FLAGS) and 'remove_naval_treaty_effect' not in source:
            continue
        def history(s):
            def selected(e, a):
                if e.key in ('add_ideas', 'remove_ideas') and isinstance(e.value, str) and e.value in IDEAS:
                    return True
                if e.key == 'remove_naval_treaty_effect':
                    return True
                if e.key in ('set_global_flag', 'clr_global_flag', 'modify_global_flag'):
                    flag = e.value.get('flag') if isinstance(e.value, Block) else e.value
                    return flag in FLAGS
                return False
            return remove_entries(s, selected)
        edit('history/countries/' + path.name, history)
    # Keep the shared trigger/effect callable for compatibility, but no active
    # treaty ideas, signatory counter or abandoned-treaty flags remain in them.
    def trigger(s):
        e = parse(s).entries('has_naval_treaty_trigger')[0]
        return replace_spans(s, [(e.start, e.end, 'has_naval_treaty_trigger = { always = no }')]), ['treaty trigger permanently false']
    edit('common/scripted_triggers/00_scripted_triggers.txt', trigger)
    def effect(s):
        e = parse(s).entries('remove_naval_treaty_effect')[0]
        return replace_spans(s, [(e.start, e.end, 'remove_naval_treaty_effect = { } # TFR: treaty system removed.')]), ['inert compatibility helper']
    edit('common/scripted_effects/00_scripted_effects.txt', effect)
    def japan(s):
        source, descriptions = remove_entries(s, lambda e, a: e.key == 'focus' and isinstance(e.value, Block) and e.value.get('id') == 'JAP_join_the_london_naval_treaty')
        changes = []
        for e, ancestors in walk(parse(source)):
            if e.key == 'custom_trigger_tooltip' and any(x.key == 'has_idea' and x.value in IDEAS for x, _ in walk(e.value)):
                changes.append((e.start, e.end, ''))
                descriptions.append('removed obsolete treaty restriction from naval focus')
            if e.key == 'focus' and isinstance(e.value, Block) and e.value.get('id') == 'JAP_non_aggression_pact_with_china':
                for child in e.value.entries():
                    if child.key == 'prerequisite':
                        changes.append((child.start, child.end, 'prerequisite = { focus = JAP_prepare_for_war_with_the_soviet_union }'))
                    elif child.key == 'relative_position_id':
                        changes.append((child.start, child.end, 'relative_position_id = JAP_prepare_for_war_with_the_soviet_union'))
                    elif child.key == 'x':
                        changes.append((child.start, child.end, 'x = -1'))
                descriptions.append('rewired downstream focus to removed treaty focus parent')
        return replace_spans(source, changes), descriptions
    edit('common/national_focus/japan.txt', japan)
    edit('common/national_focus/uk.txt', lambda s: remove_entries(s, lambda e, a:
         e.key == 'focus' and isinstance(e.value, Block) and e.value.get('id') == 'ENG_enforce_the_naval_treaties'))
    def plan(s):
        after = re.sub(r'(?m)^\s*JAP_join_the_london_naval_treaty[ \t]*\r?\n', '', s)
        return after, ['removed deleted focus from AI plan']
    edit('common/ai_strategy_plans/JAP_alternate_strategy_plan.txt', plan)
    edit('common/ai_strategy/default.txt', lambda s: remove_entries(s, lambda e, a:
         not a and e.key == 'dont_build_capitals_if_on_treaty'))
    edit('events/MTG_Britain.txt', lambda s: remove_entries(s, lambda e, a:
         e.key == 'country_event' and isinstance(e.value, Block) and e.value.get('id') in ('mtg_britain.106', 'mtg_britain.107', 'mtg_britain.108')))
    edit('events/MTG_NewsEvents.txt', lambda s: remove_entries(s, lambda e, a:
         e.key == 'news_event' and isinstance(e.value, Block) and e.value.get('id') in ('mtg_news.17', 'mtg_news.60', 'mtg_news.61')))
    def justification(s):
        return remove_entries(s, lambda e, a: e.key == 'NOT' and
                              any(x.key == 'has_completed_focus' and x.value == 'ENG_enforce_the_naval_treaties' for x, _ in walk(e.value)))
    edit('events/WarJustification.txt', justification)
    def faction(s):
        changes = []
        for e, a in walk(parse(s)):
            if e.key == 'available' and any(x.key == 'has_idea' and x.value in IDEAS for x, _ in walk(e.value)):
                changes.append((e.start, e.end, 'available = { always = yes }'))
        return replace_spans(s, changes), ['removed obsolete treaty gate from Rule the Waves goal']
    edit('common/factions/goals/faction_goals_long_term.txt', faction)
    # Update only hashes of explicitly edited countries in the earlier fleet
    # report. Fleet templates/counts/IC and its original snapshot stay intact.
    path = ROOT / 'docs/naval-starting-fleets.json'
    fleet = json.loads(path.read_text(encoding='utf-8'))
    for change in CHANGES:
        if change['source'] in fleet['source_hashes']:
            hashes = fleet['source_hashes'][change['source']]
            assert hashes['after'] == change['before'], change['source']
            hashes['after'] = change['after']
    fleet['naval_treaty_removal'] = 'docs/naval-treaty-removal.json; treaty grants/flags only, fleet IC unchanged'
    write(path, json.dumps(fleet, indent=2, ensure_ascii=False) + '\n')
    write(REPORT, json.dumps(dict(removed_ideas=sorted(IDEAS), removed_focuses=sorted(FOCUSES),
                                files=CHANGES), indent=2, ensure_ascii=False) + '\n')
    print(f'Removed naval treaty system; {len(CHANGES)} edited/overridden script files.')


if __name__ == '__main__':
    main()
