# Active focus balance

Applied only to the twelve approved focuses in TFR's permitted branches. No other
XP rewards or disabled alternate-history branches were changed.

Durations below use seven days per focus cost point, before campaign reductions.

| Focus ID | Base days | Result |
| --- | --- | --- |
| ROM_invite_german_advisors | 35 | Replace XP with one 50% infantry weapons research bonus and one 50% support technology research bonus. |
| ROM_legion_condor | Removed | Remove the XP-only volunteer focus. |
| MAN_tsr_army_modernization | 35 | One military factory and one building slot in an owned, fully controlled state. Require a valid building destination. |
| MON_legion_condor | Removed | Remove the XP-only volunteer focus. |
| SOV_transpolar_flights | Removed | Make both air branch successors roots; preserve all surviving focus positions. |
| AST_volunteers | Removed | Remove the empty focus and its campaign cost references, preserving the other campaign effects. |
| ENG_anti_non_contact_committee | 35 | Rename to Convoy Protection Committee; grant permanent +10% convoy escort efficiency. |
| SOV_mine_warfare | 35 | Rename to Fleet Maintenance; grant permanent +10% naval repair speed with or without Man the Guns. |
| CAN_rowell_sirois_commission | 35 | Grant 120 political power. |
| SAF_war_measures_act | 35 | Keep 120 political power. |
| FRA_nationalize_key_industry | 28 | Keep +10% factory output and +10% dockyard output. |
| ROM_end_the_era_of_corruption | 35 | Unchanged: +15 percentage points of stability and war support. |

The two new permanent spirits are defined in `common/ideas/TFR_focus_balance.txt`.
English names and descriptions are overridden in
`localisation/replace/TFR_focus_balance_l_english.yml`.

Australia requires mod overrides for the base-game campaign inlay and scripted
effects. Only the obsolete focus list entry and its two cost adjustments were
removed. The Soviet 1939 history no longer completes the removed air focus.

## Validation

- All 17 volunteer/allocation regression tests pass. Removed-focus checks now
  include these four deletions and focus inlay arrays.
- No active tree, AI, history or campaign references remain to the four deleted
  focus IDs in the merged game/mod scripts.
- All 10,221 surviving focus positions in the mod files match the pre-change
  snapshot. All 1,384 unrelated focuses in the edited trees are unchanged.
- Reward scripts, durations, localization encoding and unchanged Australian
  campaign effects were checked against the snapshot.
- Gameplay balance and UI appearance have not been tested in a running game.

Original files and inherited game files are backed up outside the mod at
`C:/Users/mihai/.codex/backups/tfr-focus-balance/20261016T131512`.
