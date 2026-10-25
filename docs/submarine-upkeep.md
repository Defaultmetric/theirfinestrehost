# Submarine upkeep

Submarine production uses five fleet-size tiers. There is no construction ban.
The selected national spirit updates at startup and daily, including existing
saves, and drops back to a cheaper tier after submarine losses or transfers.
All hulls with the `ship_hull_submarine` archetype count, including special
submarines. Surface ships and convoys do not count.

| Fleet size | Germany, UK, Italy, Japan, USA | Netherlands after Rely on Submarines | Production cost modifier |
|---|---|---|---|
| Tier 1 | 0–24 | 0–8 | −80% |
| Tier 2 | 25–49 | 9–16 | −70% |
| Tier 3 | 50–74 | 17–24 | −50% |
| Tier 4 | 75–99 | 25–33 | −20% |
| Tier 5 | 100+ | 34+ | +300% |

Eligibility uses original country tags so cosmetic tags and civil-war successors
retain their country's policy. The Dutch gate uses the existing TFR
`HOL_rely_on_submarines` focus. Other countries receive no upkeep discount.
The system runs directly in country scope and does not depend on a hidden
third-country decision manager. It handles jumps across multiple tiers in one
update and leaves a stable tier unchanged.

Base hull IC is 2,000 for 1922, 2,100 for 1936, 2,200 for 1938, 2,300 for 1942,
2,500 for cruiser submarines, 2,800 for fleet submarines, 600 for midget
submarines and 3,200 for nuclear submarines. Matching legacy special hulls use
their corresponding hull's price. The ordinary legacy 1922/1936/1938/1942
submarine hulls keep their reference prices of 250/250/350/400 IC.

Three TFR-only hulls have no reference counterpart and retain their current base
IC: carrier submarine (850), rocket submarine (900), nuclear missile submarine
(1,450). They count toward upkeep and receive its production-cost modifier.
Modules, integrated bonuses, combat statistics, manpower, resource requirements,
research, starting fleets and existing production queues are preserved.

Final design IC includes the TFR modules and their cost multipliers, plus other
active country/MIO modifiers. For example, before other country/MIO modifiers,
the fixed 1936 submarine design costs 2,587.5 IC before upkeep and
517.5/776.25/1,293.75/2,070/10,350 IC across the five tiers.

`submarine-upkeep.json` records hull cost changes and the tier policy.
`tools/test_submarine_upkeep.py` executes the runtime scripts across every major
threshold, Dutch focus eligibility, large fleet losses, repeated updates,
inherited-spirit cleanup, exact cost factors and startup/daily wiring.
The native parser rejected the parameterized tier helper. It now uses five
explicit literal tier effects, without macro parameters. Script-level checks
cover the same transitions and production costs. A live database reload on
2026-10-25 at 14:07:35 reported no errors after the repair; a complete campaign
has not been tested.
