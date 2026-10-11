# Standard starting naval designs

At the 1936 Man the Guns start, every country's scripted naval variants match
the fixed research templates exactly. The 348 historical variants previously
created at start are no longer created in that scenario, including 26 for the UK.
Land and air designs are unaffected. Naval research continues to create the
standard model for the researched hull, including national and project designs
when their existing requirements are satisfied.

The eight previously compacted fleets already used the standard designs and
retain their counts and IC budgets. The remaining 83 ships in AST, BRA, CAN,
CHL, COL, FIN, MEX, PRU, ROM, SIA and URG now reference the corresponding
standard 1936 design. Their names, counts, experience, officers, flagships,
ports, surface/submarine grouping and non-naval effects are preserved.

Those eleven smaller fleets adopt the standard ships' stats and IC costs;
they are not compacted again. Their combined model IC changes from 146,579.50
to 219,140.38. The per-country values and exact before/after bindings are in
`naval-standard-start-designs.json`.

Templates required by an existing fleet are created before its naval OOB is
loaded, with their one-time design flags set to prevent duplicate startup
creation. The shared Finnish OOB has a separate standard 1936 copy so its
1939 fleet remains intact. Historical variants remain available to the 1939
scenario and games without Man the Guns, rather than being loaded in the
simplified 1936 start.

Validation: `python tools/validate_standard_start_designs.py`, together with
the naval startup, compaction, grouping and integrated-bonus validators.
Use a new campaign after restarting the game; existing saves retain their
stored equipment variants.
