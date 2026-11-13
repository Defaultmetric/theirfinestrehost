# Starting fleet grouping

All countries with deployed ships in the active 1936 Man the Guns start have one surface fleet and one separate submarine fleet. Each fleet contains one task force. Countries without submarines have only the surface fleet.

| Country | Surface ships | Submarines | Fleets |
|---|---:|---:|---:|
| AST | 9 | 0 | 1 |
| BRA | 12 | 1 | 2 |
| CAN | 4 | 0 | 1 |
| CHL | 11 | 9 | 2 |
| COL | 2 | 0 | 1 |
| ENG | 160 | 34 | 2 |
| FIN | 2 | 5 | 2 |
| FRA | 55 | 53 | 2 |
| GER | 21 | 13 | 2 |
| ITA | 83 | 40 | 2 |
| JAP | 108 | 46 | 2 |
| MEX | 6 | 0 | 1 |
| PRU | 4 | 4 | 2 |
| ROM | 4 | 0 | 1 |
| SIA | 9 | 0 | 1 |
| SOV | 21 | 51 | 2 |
| SPR | 19 | 12 | 2 |
| URG | 1 | 0 | 1 |
| USA | 122 | 55 | 2 |

19 countries, 976 ships, 31 fleets. Eleven naval OOBs needed regrouping; the other eight already had the requested organization.

Names, owners, experience, officers, and pride-of-the-fleet status are preserved. The later standard-design cleanup changes only model references for 83 ships in eleven smaller fleets; this migration is recorded in `naval-standard-start-designs.json`. All non-naval effects and removed-production markers remain intact. Regrouped task forces use existing starting naval bases; no new base locations are introduced. The 1939 scenario is unchanged.

Original source snapshots and ship fingerprints are archived in `naval-starting-fleet-grouping.json`. The earlier fleet-compaction ledger only updates OOB hashes and records the organization-only migration. Its ship counts, model costs and IC budgets are unchanged.

Validation: `python tools/validate_grouped_fleets.py`, `python tools/validate_compacted_fleets.py`, and `python tools/validate_naval_startup.py`. Restart the mod and use a new campaign to see the new starting organization.
