# Integrated naval support bonuses

The 2026-10-12 pacing change scales base gun/torpedo attacks by 0.3 while keeping
the percentage bonuses below. Historical JSON final-attack estimates predate
that scaling. A follow-up separately reduces submarine torpedo module IV by
another 20% and the ordinary submarine IV hull's homing hit bonus from 0.10
to 0.05, overriding that hull's homing value described below. Other hulls keep
their homing bonuses. See `naval-combat-pacing.md`.

Compared with the installed vanilla files `MTG_naval_Support.txt` and
`MTG_naval.txt`. Numeric values come from that installation, not remembered
technology dates. The JSON audit records its source hash and every design's
original template, cost, selected technologies and expected final statistics.

## Bonuses built into standard ship designs

| Vanilla technology | Model generation | Eligible ships | Bonus |
|---|---|---|---|
| Basic light shell | 1936 and later | DD, LC, HC, BB, BC, CV | +5% light attack and light piercing |
| Improved light shell | 1942 and later | Same | Additional +5% light attack and light piercing |
| Basic heavy shell | 1936 and later | HC, BB, BC | +5% heavy attack and heavy piercing |
| Improved heavy shell | 1942 and later | Same | Additional +5% heavy attack and heavy piercing |
| Magnetic detonator | 1936 and later | DD, LC, HC, submarines | +20% torpedo attack |
| Homing torpedo | 1942 and later | Same | +0.10 torpedo hit chance factor |
| Degaussing | 1938 and later | DD, LC, HC | +10% submarine detection |
| Fire control methods I | 1936 and later | BB, BC | +5% light and heavy attack |
| Fire control methods II | 1938 and later | BB, BC / HC | Additional +10% / +5% light and heavy attack |
| Fire control methods III | 1942 and later | BB, BC / HC, LC / DD | Additional +15% / +10% / +5% light and heavy attack |

The three fire-control methods have **no `start_year` in vanilla**. Their
1936/1938/1942 assignment is a deliberate mapping to this mod's three ordinary
hull generations. All bonuses accumulate additively as technology upgrades:
for example, a 1942 battleship has +40% light/heavy attack and +10% piercing.
The total support bonus then multiplies the original fitted ship's relevant
stat. Existing module multipliers are accounted for, rather than accidentally
reducing the technology's effect. Hit chance is an additive factor, matching
the native torpedo module stat.

Locked native variant upgrades carry one package per design. They are assigned
by script and have no selectable level. Original engines and weapon modules
remain fitted, with no added module or designer slot. Extra guns or torpedo
launchers do not repeat the bonus. The additive homing chance is built into
eligible 1942 and later hulls. IC, speed, range, fuel,
resources, reliability and manpower are unchanged. Zero gun or torpedo attack
stays zero. This is not a restoration of vanilla weapon balance values.

Named 1936/1938/1942 variants use their design generation, including Torpedo
Cruiser, Ice Carrier and Submarine Carrier. Other special variants use their
hull year. The carrier submarine receives submarine torpedo bonuses. Modern
ships receive all applicable earlier bonuses. Panzerschiff, Coastal Defense
Ship and Pre-Dreadnought remain older designs without future bonuses.

The eight countries' precreated 1936 standard variants use these same packages.
Their deployed ship counts and original fleet-compaction IC ledger are unchanged.
The fleet report records the stats-only migration; its immutable original
fleet snapshot remains intact.

## Country bonuses granted on research

Each grant is guarded by the hidden technology already being held. Subsequent
research, startup checks and monthly checks cannot stack it a second time.

| Unlock | Global reward |
|---|---|
| First ordinary 1936 hull (already granted at startup) | -10% critical receive chance; -10% critical effects |
| First ordinary 1938 hull | Additional -10% to each |
| First ordinary 1942 hull | Additional -10% to each |
| First 1942 destroyer, cruiser or submarine hull | -25% torpedo reveal chance |
| Completed underway-replenishment project plus a 1938 hull | +25% replenishment range; -20% replenishment convoy cost |
| Same project plus a 1942 hull | Additional +25% range; -20% convoy cost |

Research hooks call the helper immediately through `TFR_navy_create_designs`.
Startup covers technologies already held, and monthly checks cover technology
granted by focuses/history or a project completed after the hull research.
These are **research-driven**, not calendar rewards. Country bonuses also
affect older ships, as their vanilla modifier scope requires. The later
replenishment technology's vanilla 1943 date maps to the mod's 1942 generation.

## Audit exclusions

- Smoke generators' +20% retreat speed was already retained and granted at
  startup; no duplicate bonus was added.
- Transport and landing-craft invasion bonuses remain on their visible techs.
- Mines and air-mining bonuses remain disabled with the mod's mining system.
- Special-project proximity-fuze, repair/support-ship and replenishment-choice
  bonuses were already present and retain their project conditions.
- Battery, torpedo launcher, sonar, depth-charge, engine, armor and radar
  technologies that only unlock modules are represented by the actual fitted
  modules. Module unlocks are not additional blanket percentage bonuses.
- AIP engines and improved ice-carrier decks are separate project module
  alternatives, not missing country/stat bonuses. Their optional design
  upgrades are outside this integration.

## Verification

`python tools/validate_integrated_naval_bonuses.py`: compares all 43 templates
with the audit and vanilla technology values; checks 40 hidden packages, unchanged
cost/speed/fuel, matching history templates, and 72 research/project combinations
including repeated grants and the absence of future bonuses at startup.

`python tools/validate_naval_startup.py` and
`python tools/validate_compacted_fleets.py`: check module legality, all 33
research hooks, historical templates, preserved compaction budgets/counts,
unchanged unrelated history and absence of day-one naval production.

In-game verification requires restarting the mod and starting a new campaign.
Existing saves already store their old variants and one-time design flags;
this change does not rewrite those saved ship designs.
