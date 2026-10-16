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
