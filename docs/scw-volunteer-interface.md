# Spanish volunteer allocation interface

The panel allocates permission and maximum numbers. It does not create units or
choose the divisions or aircraft that players send through the normal game menus.

Germany's eligible list is GER, ITA, ROM, HUN and BUL. The UK list is ENG, FRA,
CAN, AST, SAF, RAJ, BRA and MEX. FIN, MON, JAP, SIA, NZL, USA and CHI are excluded.
The Axis pool is 16 divisions and 600 aircraft; the Allied
pool is 12 divisions and 300 aircraft including the Soviet reservation (up to six
divisions).

Axis quotas authorize only Nationalist Spain; Allied and Soviet quotas authorize
only Republican Spain. Recipient checks use the native SPR_nationalist_spain_flag
and SPR_republican_spain_flag (or their scw_no_lar equivalents), also used by the
SPA/SPD aliases. The original SPR tag and ruling ideology do not identify a camp.
The send-volunteers permission tooltip explains the destinations. The on-send
guard also recalls ground volunteers sent to the wrong camp through a bypass.

Bulgaria uses Germany's confirmed allocation without Bulgarian focus or rearmament
requirements. Zero or unconfirmed allocations and exhausted quotas cannot authorize
new sends. The diplomatic entry point evaluates ROOT as the sender and FROM as the
Spanish receiver; the managed branch takes priority over the general game rules.
The obsolete Bulgarian SCW focus restrictions have been removed. The generator
also upgrades the scope check in previously generated files.

Legacy capacity rewards and focus permissions have also been removed from loaded
country scripts while retaining their other rewards and decision mechanics. The
French intervention focus still unlocks its war-support/stability policies. See
[volunteer-capacity-cleanup.md](volunteer-capacity-cleanup.md) for the removed focus
nodes, preserved mechanics, inherited overrides, backups, and acceptance checks.

USSR must explicitly confirm its first reservation, including a zero reservation,
before UK can edit or confirm Allied allocations. While waiting, the Allied tab
shows "Soviet has not picked". From 1 August 1936, UK can allocate without waiting
for USSR. Any late Soviet reservation must fit the remaining confirmed Allied
pool. Soviet AI no longer automatically reserves six divisions at initialization.

All eligible donors and Spanish civil-war tags can view both Axis and Allies tabs.
Only Germany edits Axis allocations; only UK edits Allied allocations. The Soviet
card in Allies is always read-only, even for UK and USSR. Only USSR sees and edits
its separate "My reservation" tab. Observers see approved quotas, while each
manager sees its editable draft. Existing excluded donors lose old permissions
and modifiers on the next daily update.

The opening button sits immediately above the native raids header on the right.
It reuses the native 82 x 39 winged frame and 32 x 32 round button, with the existing
Spanish-coloured helmet displayed at scale 0.75. Only the round centre is clickable;
the frame and helmet are transparent to mouse input. The scripted GUI attaches to
`raid_filter`, with a five-pixel gap above its header, so it follows the native
panel's dynamic height and resolution anchoring. It no longer occupies a top-bar
slot. Opening remains country-scoped and therefore shared between co-op players.

Countries appear in three columns of cards with live country flags and names. Ground allocation
uses a horizontal stepped bar; air allocation uses a vertical stepped bar, with
higher quotas above lower quotas. Click a step to select it. Dragging is not
implemented: the game's documented scripted GUI API exposes button clicks and
dynamic positions, but no scrollbar-value or drag callback.

Ground steps are individual divisions. Aircraft steps are 100 aircraft. Both
include a zero position. The Allied list fits in three rows. Header,
country cards, instructions and confirmation controls occupy separate areas.

Slider effects recheck permissions before assigning a quota. Available capacity
is calculated as pool minus draft total plus the country's old quota, so replacing
an allocation does not accidentally consume the old quota twice. Positions and
capacity are refreshed after draft edits and when opening the panel. Open viewers
are refreshed after commits, monthly unlocking and the August deadline. The GUI
uses a dirty variable instead of recalculating every frame.

Source: tools/generate_scw_volunteers.py. Run it with Python and Pillow to rebuild
the interface, scripts, localization and eight small DDS interface textures.
Existing generated files are backed up outside the mod before replacement.

Validation: tools/test_scw_volunteers.py executes the generated effects, GUI click
handlers and triggers in a small scoped state evaluator. Ten tests cover Soviet
priority, explicit zero selection, the August boundary, shared ground/air budgets,
late Soviet selection, observer permissions and reducing a draft after a Soviet
commit, recipient routing for both original and dynamic Spanish countries and
on-send rejection of the wrong camp, guarded zero-quota modifier cleanup, Bulgaria's
actual diplomatic entry point with confirmed/unconfirmed/exhausted quotas, and
generator migration/idempotence. Camp tests use sender scope and available quota;
native deployed-unit updates and notification rendering are outside this evaluator.
Native deployed-unit checks, modifier arithmetic and GUI rendering are outside this
evaluator. Effective native volunteer and aircraft caps still require full gameplay
validation.

Previous in-game UI check (HOI4 1.19.3, 2560 x 1440): flags, card layout,
texts and confirmation button rendered correctly on a copied Spanish Civil War
save. Monthly editing unlocked after advancing the test copy. Direct selection
of 8 and 16 divisions moved the ground marker correctly; selecting 600 aircraft
moved the air marker to the top. Extra allocations to Italy were blocked when
the corresponding shared pool was full. No SCW interface/script errors appeared
in the game's error log. This predates the revised country lists, tabs and Soviet
priority deadline and the raids-style opening button.

Opening-button check (2026-10-23, HOI4 1.19.3, UI scale 1.0): verified in-game
at 1920 x 1080 and 2560 x 1440 in fresh paused German campaigns. The Spanish
helmet uses the native raids frame immediately above the raids button, with no
overlap. Opening and closing the allocation panel worked at both resolutions;
the taller Allied panel also fitted fully at 1080p. Collapsing and expanding the
native raids categories moved the Spanish button with the header. No SCW or
raid_filter errors appeared in error.log. The original video settings were restored.

Current in-game check (HOI4 1.19.3, 2560 x 1440): fresh UK game on 1 January
1936 shows the red "Soviet has not picked" message, the revised Allied list and
the read-only Soviet card. Clicking UK quota 12 leaves the draft at zero while
USSR has not confirmed. Switching UK to Axis shows the five-country list, hides
the confirm control and leaves Germany's quota unchanged on an attempted edit.
Tabs, flags, header/status text, all three Allied rows and footer fit without
overlap. A clean game startup produced no SCW-related errors in error.log.
On a copied 6 August 1936 save with the Spanish Civil War active and no Soviet
confirmation, UK sees the yellow deadline-passed message and can select and
confirm 12 divisions / 300 aircraft. Approved totals update correctly. USSR
remains zero and its Allied card cannot be edited from UK. No time was advanced
and no units were created or sent during this check.

Error-log investigation on 12 October 2026: the user reported global leader and
formable changes after using decision.nochecks to accelerate Spain. The log has
205 invalid AI select_decision_command attempts and errors from unrelated Hungarian,
German and other national decisions. The Soviet pan-Slavic declaration and vanilla
Hungary's Habsburg-on-the-Spanish-throne decision contain the exact reported
cosmetic/leader changes. This strongly indicates global decision-check bypass
while time advances; an in-game reproduction without the cheat was not performed.
SCW allocation effects contain no cosmetic-tag or leader-changing effects.

A separate SCW issue logged 20 attempts to remove an absent volunteer modifier
when confirming zero quotas. Native-limit removal now checks whether the modifier
is installed, including zero-quota confirmation, expiry and excluded-donor cleanup.
The regression test executes zero-quota application with and without an installed
modifier and verifies that repeated cleanup does not attempt a second removal.
For console testing, keep the game paused while decision.nochecks is enabled and
toggle it off before advancing time. Global changes already made by decisions
require returning to an earlier save or starting a fresh test game.
