# Switching Grand Doctrine while keeping active mastery

Restart the game with this mod enabled. Open the doctrine screen and click
**Change Grand Doctrine Keep Subdoctrines** below the main Grand Doctrine
button. The selector offers all ten land,
naval and air Grand Doctrines. Clicking a choice switches immediately for
100 XP from that service. The current doctrine and choices without an existing
Grand Doctrine or sufficient XP are disabled. Doctrine cost discounts do not
change this cost. Click the doctrine tab after switching to refresh the native
header. The preserving decisions remain available as an alternative.

The selector reads the selected subdoctrines and their total mastery before
switching. It then restores them to their original slots, including partial
progress and unlocked rewards. Completed tracks receive the new Grand Doctrine's
milestones. Existing achievement counters are retained and snapshot variables
are cleared before the action finishes. Other doctrine branches are untouched.

The original selector opened by clicking the Grand Doctrine crest still resets
mastery. Use the new button underneath it to retain it. The preserving actions do not
preserve **Reserved Mastery** (the bank shown on completed or empty tracks),
which has no documented script getter or setter in the installed game. Special
Forces are not included: their subdoctrines can occupy either of two tracks, and
the documented `has_doctrine` trigger cannot identify the occupied slot.

## Repair on 2026-10-15

The previous implementation passed its Python model but was rejected by the
actual game. Its error log reported unsupported `is_ai` in decision `allowed`,
parameterized scripted-effect calls interpreted as invalid `TRACK` effects,
and (after those were corrected) an invalid `while` effect. These are replaced
with `allowed = { always = yes }`, human-only `visible` conditions, concrete
per-track helpers called with `= yes`, and `while_loop_effect`.

The first live switch after fixing the syntax still restored zero mastery.
The old scaled-number calculation assumed script variables could safely store
mastery * 100000 and multiply by 0.00001. The replacement uses only integer
variables: it searches the whole amount, then each of five decimal digits,
and constructs the literal amount as text for `has_mastery` and `add_mastery`.
This keeps the doctrine engine's five-place precision without fractional
script-variable arithmetic. Zero snapshots skip `add_mastery`, which rejects
an amount of zero.

The standard doctrine-screen warning now points to the preserving selector.
It still explicitly warns that the native switch resets mastery.

## Verification

Run `python tools/generate_doctrine_switch.py` after changing definitions or
the template at `tools/doctrine_switch_effects.template.txt`, then run
`python tools/verify_doctrine_switch.py`. The model checks all selectable
subdoctrines, 120 repeated switches, 240 fractional snapshots, empty tracks,
XP costs, counter preservation, variable cleanup, and the engine syntax
mistakes that the old verifier accepted. Script arithmetic is deliberately
modeled with only three decimal places; mastery retains five places.
The verifier also executes all ten GUI callbacks, checks their sequence against
the tested decisions, and checks exact XP and ownership guard boundaries.

For an actual engine regression, use a disposable save and run
`python tools/generate_doctrine_runtime_test.py --install` before launching.
Click `TFR_DOCTRINE_RUNTIME_TEST` at the top of Decisions. It changes all three
doctrine branches and emits PASS/FAIL assertions to the game's `game.log`.
The assertions check the selected grand doctrine, all four subdoctrines, and
both bounds of each exact mastery amount, including 0.00001, 74.99999,
123.45678, and 375. Remove the temporary decision afterwards with
`python tools/generate_doctrine_runtime_test.py --remove` and reload the
original save. The test is not part of the normal playable mod.

Final engine regression on 2026-10-15: **30 PASS, 0 FAIL** across all ten
grand doctrines and all twelve tracks, including zero and fractional mastery.
No doctrine-related parsing or runtime errors were logged in the final run.
Recorded engine results are in `docs/doctrine-runtime-verification.log`.
The original game state was saved separately as
`TFR_DOCTRINE_BEFORE_FIX_20261015.hoi4`; pre-existing saves were retained.

## Native-button investigation on 2026-10-15

Initially the user requested the original selector and buttons, with no added
interface. The experimental selector was removed during that investigation.
The user subsequently accepted the new selector, which is now included. It
attaches to the native view. A small layout override now lowers the tracks by
44 pixels to make room for the preserving button under the main header.

An activation-order probe was tested through the original Grand Doctrine
selector and its Unlock button in 1.19.3. Starting from Grand Battleplan,
Assault Infantry at 375 Mastery and 799 Army XP, selecting Mobile Warfare
for preview did not execute its activation effect. Clicking Unlock charged
100 XP and executed the Grand Doctrine activation effect. At that moment,
`has_doctrine = new_mobile_warfare` was true, but Assault Infantry, its 375
Mastery and the previous Grand Doctrine were already absent. All tracks
were empty. The documented activation effect therefore runs too late to
capture the original values. The temporary probe was removed afterwards.

The installed doctrine documentation and defines expose no pre-switch callback
or mastery-retention setting. A bounded ASCII-token scan of this installed
executable found no doctrine/mastery `on_*` event. This is not a decompilation:
the optional REA provider was unavailable (no configured native analysis
engine). It does not establish the absence of every undocumented mechanism.
No exact-preservation fix for the original button has been implemented.

## Accepted GUI selector

Live test on 2026-10-15: the new button opened the scripted selector.
Choosing Mobile Warfare from Grand Battleplan reduced Army XP from 799 to 699,
retained Assault Infantry with all five rewards through 375 Mastery, and granted
the Mobile Warfare infantry milestone. Clicking the Land Doctrine tab refreshed
the native header to Mobile Warfare. No new script errors were logged. The
pre-test save is reloaded afterwards; the test is not saved over it.

The GUI source is generated from `tools/doctrine_switch_gui.template.gui` into
`interface/TFR_doctrine_switch.gui` and
`common/scripted_guis/TFR_doctrine_switch.txt`. Button tooltips use a standalone
localization string to avoid unresolved nested localization keys.

The button was subsequently centered below the main header and renamed to
`Change Grand Doctrine Keep Subdoctrines`, verified in the game. The native
header still caches the previous doctrine until its folder tab is clicked.
A live test of `mark_technology_tree_layout_dirty = yes` did not refresh it;
that ineffective call was removed. No automatic native-header refresh is
claimed. The layout override is `interface/doctrines/doctrines_view.gui`, based
on the installed 1.19.3 vanilla file with only the tracks-container Y offset
changed from 145 to 189.
