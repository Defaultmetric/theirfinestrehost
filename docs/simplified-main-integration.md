# Simplified integration without the Spanish rework

Main receives the changes from `Mihai'sNavySimplified` through commit
`71be7ec3ea174d5c7d6bca00d3816b03f597455c`, with the nationalist Spanish focus
rework deferred at the user's request.

The Spanish shared focuses, dynamic modifiers, decisions, events, AI plan,
localization, generator, plan and rework-specific tests/audits are excluded.
The existing Spanish tree, shared Axis placement, Portuguese industry growth,
Portuguese surrender annexation and historical Spanish AI are restored to their
state immediately before the rework. Shared diplomacy retains the Bulgarian
volunteer fix and corrected sender/receiver scopes, without the new Spanish role
restrictions. Volunteer-capacity cleanup in Spanish national spirits remains.

The allocation UI/system, simplified navy, doctrine switching, other focus
balance changes and compatibility fixes from the source branch remain included.
Unpublished Workshop changes after that source commit are outside this merge.

The merge records the source commit as integrated. To enable the Spanish rework
later, explicitly reintroduce its full files and shared-file changes from the
then-current simplified branch; merging only later incremental changes will not
restore the files deferred here. The source branch still retains the rework.

Validation before publication:

- All 19 volunteer/allocation/capacity regression tests pass.
- Doctrine checks pass: 40 scenarios, 120 repeated switches and 240 mastery snapshots.
- Naval startup checks pass: 43 designs, 33 research hooks and 267 production records.
- Active scripts contain no `TFR_SPA_` / `TFR_spain_rework` references.
- Compared with the source branch, only the seven documented shared-file
  reversions, 26 deferred new files and this integration note differ.
- The existing Case Anton validator fails at its expectation of a second Vichy
  identity OR clause (`original_tag = FRA` / `tag = VIC`). The validator and
  involved runtime files match the source branch exactly; this pre-existing
  mismatch is preserved, rather than changing Case Anton during this merge.
- The merged main checkout was not loaded into the running HOI4 instance.

## Main merged back into the simplified branch (2026-10-25)

`origin/main` at `4531e487` is merged into `Mihai'sNavySimplified`, starting
from `312a8cce`. The earlier Spain deferral applies to main; this branch keeps
its complete Spanish rework and the seven shared-file integrations needed by it.
The Latin Bloc faction-template update from main is retained in the shared
Spanish tree, and its preservation test explicitly accounts for that update.
Both audit JSON conflicts retain the simplified branch's reports, matching its
naval setup and shared Axis layout.

Main's remaining changes include the German gold-reserve guards, occupation-law
scope guards, Japanese faction-demand fallback, aircraft/tank entity fixes and
removal of guerrilla warfare's war-support bonus. Existing balance and toolbar
changes already present on the simplified branch remain integrated.

Validation: all 74 regression tests pass; generated Spanish scripts reproduce
exactly after restoring LF line endings; doctrine checks pass 40 scenarios,
120 repeated switches and 240 mastery snapshots. Naval startup validation passes
43 designs, 33 research hooks, 518 historical variants, 1,189 MTG fleet entries
and 267 production lines. The unchanged Case Anton validator still has the
previously documented Vichy-identity assertion failure. No in-game test was run.
