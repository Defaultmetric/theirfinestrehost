# Fleet size and positioning

The Navy tech tree displays **Fleet size & positioning [?]** to the right of
**NON-ARMORED FLEET**. Hover over the label to read the rule and examples.

## Current values and calculation

The mod already sets `NNavy.HIGHER_SHIP_RATIO_POSITIONING_PENALTY_FACTOR = 0.5`
in `common/defines/TFR_defines.lua`. Vanilla uses `0.25`.
The inherited `MAX_POSITIONING_PENALTY_FROM_HIGHER_SHIP_RATIO` is `0.75`,
and `BASE_POSITIONING` is `1.0`. These values and their comments come from
the installed game's `common/defines/00_defines.lua`.

Let **N** be the ships on your side of the battle and **E > 0** the ships on
the enemy side. Ships from task forces fighting together count on the same side.
For the fleet-size component alone:

```text
size_penalty = min(0.75, 0.5 * max(0, N / E - 1))
base_positioning_after_size = 1 - size_penalty
```

| Own/enemy ship ratio | Mod size penalty | Vanilla size penalty | Mod base positioning after size |
| --- | ---: | ---: | ---: |
| 1x | 0 points | 0 points | 100% |
| 1.5x | 25 points | 12.5 points | 75% |
| 2x | 50 points | 25 points | 50% |
| 2.5x | 75 points | 37.5 points | 25% |
| 4x | 75 points | 75 points | 25% |

These are percentage-point losses from base positioning, before admiral,
detection, weather, reinforcement, enemy carrier and other effects.

## A useful maximum needs a target

There is **no universal optimal maximum number of ships** implied by this define.
The penalty uses the opposing ship count, rather than a fixed fleet capacity.
The cap at 2.5x is the point where the size penalty stops growing, not a fleet
limit or an optimal fleet size. A positioning loss is not the same percentage
loss in damage: vanilla `DAMAGE_PENALTY_ON_MINIMUM_POSITIONING = 0.5` sets the
damage penalty at zero positioning to 50%. Fleet composition and survival also
matter, so optimizing positioning alone does not optimize the battle result.

For planning, without other positioning modifiers:

- Maximum with **no fleet-size penalty**: `N_max = E`.
- Maximum with **at least 75% base positioning after fleet size**:
  `N_max = floor(1.5 * E)`. This is a chosen low-penalty guideline, not a combat optimum.
- Maximum with **at least 50% base positioning after fleet size**:
  `N_max = 2 * E`.

| Enemy ships | Maximum without size penalty | Maximum for at least 75% | Maximum for at least 50% |
| ---: | ---: | ---: | ---: |
| 20 | 20 | 30 | 40 |
| 40 | 40 | 60 | 80 |
| 50 | 50 | 75 | 100 |
| 80 | 80 | 120 | 160 |
| 100 | 100 | 150 | 200 |

The enemy count can change during a battle. A fleet chosen for the opening
ratio can incur a larger penalty after enemy ships sink or disengage.
