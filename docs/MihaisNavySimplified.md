# Mihai's Navy Simplified

Status of the navy rework on this branch, and the fixed ship design rules agreed so far.

## Done

1. **Naval mines removed.** The mine mission buttons are hidden (`interface/naviesview.gui`), AI mine missions are set to 0, planting speed is 0, and all mine techs are empty stubs.
2. **Naval command cap removed.** The cap files, dynamic modifier, scripted GUI and localisation are deleted.
3. **Large fleet penalty.** `HIGHER_SHIP_RATIO_POSITIONING_PENALTY_FACTOR = 0.5` (vanilla 0.25).
4. **Hull years.** Hulls moved from 1939/1943 to 1938/1942. `common/technologies/MTG_naval.txt` is a copy of the vanilla file.
5. **Same naval tech for everyone at start.** Every country gets the 1922 and 1936 naval techs, plus all gun, torpedo, depth charge and sonar module techs. These are hidden and set in `common/on_actions/tfr_navy_simplified_on_actions.txt`.
6. **Module and bonus techs.** Techs that only gave stat bonuses (damage control, fire control methods, shells, detonators, multi-product supply ships, pykrete, snorkel, AIP) are empty stubs: `allow = { always = no }`, kept so old references load without errors. Their bonuses are to be re-added later as fixed numbers.
7. **Single "Navy" tab.** The tab scrolls vertically and has three sections:
   - **Non-armored fleet:** DD, SS and CV, each with special project cards.
   - **Armored fleet:** CR and BB with special project cards, plus national ships.
   - **Support ships:** repair ship and support ship, with their improved versions.

   Other details:
   - Special project ship cards live in `common/technologies/tfr_naval_project_ships.txt`. They are marked researched by `naval_projects.txt` when the project finishes.
   - National ships show who can unlock them through `custom_trigger_tooltip`.
   - The old naval support tab is hidden in `common/technology_tags/00_technology.txt`.
8. **Transports.** They moved to the right side of the support companies tab.

## TODO

- **Fixed designs (step 7).** Use the rules below. Create the variants with `create_equipment_variant` at start and in `on_research_complete`, and add AI templates.
- **Hide the ship designer buttons (step 8).** They are in `countrytechtreeview.gui` / `countryproductionlineview.gui`.
- **Convert pre-1936 starting fleets (step 9).** Convert them into 1936 ships of equal IC.
- **UK balance (step 10).**
- **Stat bonuses.** Re-add damage control, fire control, shells and detonators as fixed numbers.
- **Transports banner.** Add a blue banner (copy of `wonderweapons_bg.dds`) behind the transports column.
- **Before release:** delete `common/on_actions/zz_tfr_navy_design_temp_on_actions.txt`. It gives every naval tech to every country and exists only for design work.

## Fixed design rules

FC = fire control system. A radar variant is created automatically once the radar tech (engineering tree) is researched. Until then the base variant has no radar.

### Destroyers

There are three roles: LD (light), TD (torpedo) and ASW. Use FC 1/2/3 on the 1936/1938/1942 designs.

| ASW design | Sonar | Depth charges |
|---|---|---|
| 1936 | `ship_sonar_2` | `ship_depth_charge_2` |
| 1938 (Improved) | `ship_sonar_3` | `ship_depth_charge_3` |
| 1942 (Advanced) | `ship_sonar_4` | `ship_depth_charge_4` |

The full LD and TD module lists are still to be read from a text save. Set `save_as_binary=no` before saving.

### Submarines

| Design | Torpedoes | Engine | Mid slot radar |
|---|---|---|---|
| Basic | 2x `ship_torpedo_sub_2` (fixed, rear) | `sub_ship_engine_2` | - |
| Improved | 3x `ship_torpedo_sub_3` (fixed, front, rear) | `sub_ship_engine_3` | `ship_radar_2` (`cavity_magnatron`) |
| Advanced | 3x `ship_torpedo_sub_4` | `sub_ship_engine_4` | `ship_radar_3` (`phased_array`) |
| Midget | `ship_torpedo_sub_3` | `sub_ship_engine_3` | - |
| Fleet | same as Improved (range comes from the hull) | `sub_ship_engine_3` | `ship_radar_2` |

**Nuclear submarine:**

| Slot | Module |
|---|---|
| Fixed torpedo | `ship_torpedo_sub_nuclear` |
| Front 1 | `ship_torpedo_sub_nuclear` |
| Rear 2 | `ship_torpedo_sub_nuclear` |
| Rear 1 | `slbm_launcher` |
| Mid | `ship_radar_4` (`monopulse_radar`) |
| Engine | `sub_ship_nuclear_engine_1` |

Until the nuclear torpedo and missile projects are done, the base variant uses `ship_torpedo_sub_4` and no launcher.

**Cruiser submarine:** the design tier follows the best submarine hull researched, in any order. Every missing tier is created up to that hull.

| Tier | Torpedoes | Engine | Radar |
|---|---|---|---|
| Basic | 3x `ship_torpedo_sub_2` | engine 2 | - |
| Improved | 3x `ship_torpedo_sub_3` | engine 3 | `ship_radar_2` |
| Advanced | 3x `ship_torpedo_sub_4` | engine 4 | `ship_radar_3` |

### Cruisers

**Torpedo cruiser:** the tier is the lower of the submarine tier and the cruiser tier. Improved needs Improved Sub and Improved Cruiser; Advanced needs both Advanced.

| Slot | Basic | Improved | Advanced |
|---|---|---|---|
| Torpedoes x4 (front 1, mid 1, mid 2, rear 1) | `ship_torpedo_2` | `ship_torpedo_3` | `ship_torpedo_4` |
| Battery | `ship_light_battery_2` | `ship_light_battery_3` | `ship_light_battery_4` |
| FC | `ship_fire_control_system_1` | 2 | 3 |
| Radar | `ship_radar_1` | radar 2 | radar 3 |
| Engine | `cruiser_ship_engine_2` | 3 | 4 |
| Armor | `ship_armor_cruiser_2` | 3 | 4 |
| AA, secondaries, rear 2 | empty | empty | empty |

**Light cruiser (LC) and heavy cruiser (HC):** LC uses `ship_light_battery_X` and HC uses `ship_medium_battery_X`. The battery goes in the fixed battery slot and in every custom slot: 4 on Basic, 5 on Improved and Advanced.

| Slot | Basic | Improved | Advanced |
|---|---|---|---|
| Battery | level 2 | level 3 | level 4 |
| AA | `ship_anti_air_2` | 3 | 4 |
| FC | 1 | 2 | 3 |
| Radar | empty | empty | empty |
| Engine | 2 | 3 | 4 |
| Secondaries | `ship_secondaries_2` | `dp_ship_secondaries_3` | `dp_ship_secondaries_4` |
| Armor | `ship_armor_cruiser_2` | 3 | 4 |

### Battleships

`ship_heavy_battery_X` goes in the fixed slot and in every custom slot: 4 on Basic, 5 on Improved and Advanced (the extra one is mid 3).

| Slot | Basic | Improved | Advanced |
|---|---|---|---|
| Heavy battery | level 2 | level 3 | level 4 |
| AA | 2 | 3 | 4 |
| FC | 1 | 2 | 3 |
| Radar | empty | empty | empty |
| Engine | `heavy_ship_engine_2` | 3 | 4 |
| Secondaries | `ship_secondaries_2` | `dp_ship_secondaries_3` | `dp_ship_secondaries_4` |
| Armor | `ship_armor_bb_2` | `ship_armor_bb_3` | open question |

The Advanced armor is an open question because BB armor only goes up to level 3. The options are `ship_armor_bb_3` or `ship_armor_shbb`.

### Still to define

Carriers, support ships, national ships, the remaining project ships, and the full LD and TD lists.
