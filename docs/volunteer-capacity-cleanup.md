# Volunteer capacity cleanup

The Spain Vols allocation system remains the source of approved volunteer capacity.
Legacy rewards no longer grant extra division slots, proportional capacity, air
capacity, reduced deployment thresholds, or separate country-level permissions.

The cleanup removes 445 active legacy fields across 127 script files. One French
localization file is also updated. This includes 63 inherited files copied into
the mod as overrides; the base-game installation is unchanged. Ideology defaults,
global defines, and the allocation system's own authority and dynamic caps remain.
Negative legacy permission overrides are removed too, so a focus cannot veto an
approved allocation. Unrelated penalties are preserved.

Combat experience (including experience from volunteers), manpower, conscription,
equipment, unit creation, research, political effects, factories and diplomatic
events are retained. Mixed national spirits retain their non-capacity modifiers.
In particular, the shared German/Romanian Condor spirit still grants army and air
experience, Czechoslovak revolutionary brigades retain recruitment and defense,
and India's payment for sending private military units remains functional.

## France

`FRA_intervention_in_spain` remains available and continues to unlock the original
decision category. Its tooltip now says:

> Gain access to decisions that boost War Support at the cost of Stability.

The four policies keep their original stability/war-support modifiers:

| Decision | Stability | War support |
| --- | ---: | ---: |
| Allow arms purchases | -0.10 | +0.05 |
| Allow sending weapons | -0.15 | +0.075 |
| Allow volunteer work / civilian assistance | -0.20 | +0.10 |
| Mobilize Public Support for Spain | -0.25 | +0.125 |

The last policy retains its internal ID `FRA_allow_covert_intervention` for existing
flags and scripted references. It no longer grants permission or reduces tension
requirements. Its reversal is named "End Public Mobilization for Spain" and no
longer requires deployed volunteers to return home. Civilian manpower assistance,
arms and equipment decisions, costs, policy flags and duration remain intact.

## Removed focus nodes

Only nodes reduced to no completion reward are removed. Prerequisites are rewired
to the surviving predecessors, preserving OR alternatives and any chains of
removed nodes. Layout anchors retain surviving focuses' absolute positions. AI
queues and scripted focus checks are updated as well.

| Removed focus | Surviving predecessor(s) |
| --- | --- |
| `ARG_socialist_volunteers` | `ARG_women_in_industry` |
| `ah_volunteer_corps` | `ah_interventionism_focus` |
| `ah_foreign_expeditions` | `ah_interventionism_focus` |
| `BRA_international_brigades` | `BRA_align_with_moscow` / `BRA_oust_prestes` / `BRA_cangaco_coup` |
| `ETH_peacekeeping_forces` | `ETH_expand_the_mehal_sefari` |
| `FRA_league_of_french_bolshevist_volunteers` | `FRA_loyalty_to_moscow` |
| `HOA_the_adjective_volunteer_force` | `HOA_securing_the_adjective_future` |
| `wuw_HUN_officialize_the_rakosi_battalion` | `wuw_HUN_reviving_the_spirit_of_1848` |
| `JAP_communist_volunteers` | `JAP_red_brigades` |
| `JAP_anti_communist_volunteers` | `JAP_anti_communist_bulwark` |
| `POL_dabrowszczacy` | `POL_polish_path_to_socialism` / `POL_surrender_the_east` / `POL_invest_in_the_peasantry` |
| `POL_volunteer_corps` | `POL_intervention_focus` |
| `SWI_volunteer_force` | `SWI_oasis_of_democracy` |
| `AST_citizen_military_forces` | `AST_volunteer_defence_corps` |
| `PRC_peoples_volunteer_army` | `PRC_central_military_commission` |
| `PRC_sea_peoples_volunteer_army` | `PRC_sea_central_military_commission` |
| `NZL_2nzef` | `NZL_strengthen_the_commonwealth` |
| `ROM_romanian_volunteer_brigades` | `ROM_basing_rights_for_soviet_union` |

Some spirits are retained as empty markers because other scripts check their
presence. Their assignments and associated focus nodes remain where needed to
preserve those mechanics. Empty definitions also retain existing idea IDs; saved
games are not edited by this cleanup.

## Validation and maintenance

- `python tools/test_scw_volunteers.py`: 10 passing allocation/routing tests.
- `python tools/test_volunteer_capacity_cleanup.py`: 7 passing checks for loaded
  legacy capacity, retained French policies and civilian aid, preserved mixed
  rewards, Indian payments, focus references, and the allocation authority.
- Every modified script is parsed again and its rendered syntax tree compared
  against the planned edits before writing.
- A before/after audit confirms that all non-volunteer modifier contents remain
  unchanged outside the removed nodes, and 10,972 surviving focus positions match.
- The 63 inherited originals match the installed game's bytes after the changes.
- A second dry run reports zero further changes.

Gameplay rendering, engine caps, and loading existing saves with a removed focus
in progress have not been tested in game. Restart HOI4 to load the updated scripts.

The repeatable cleanup tool is `tools/cleanup_volunteer_capacity.py`. It defaults
to a dry run; `--apply` backs up originals outside the mod before writing. Refresh
inherited overrides against the installed game when updating HOI4 versions.

Initial backup and file manifest:
`C:/Users/mihai/.codex/backups/tfr-volunteer-capacity/20261016T123455`.
