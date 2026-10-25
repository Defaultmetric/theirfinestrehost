# German gold targets

The country decision requires the victim's `GER_has_capitulated_to_germany`
flag and its entry in `GER.GER_seize_gold_targets_array`. Either missing value
prevents the target from appearing. Continental Netherlands uses `FNL` in TFR.
Older German saves showed no German-capitulation flag in FNL's saved flag area,
while comparable defeated countries carried it. Those binary-save observations
do not reconstruct the precise historical capitulation event.

The former registration condition depended on the defeated country's current
capital being in Europe. It now checks European core states, preserving the
existing Turkey exception. This works when a capital has moved overseas or
the defeated country no longer has a valid capital. Registration still requires
Germany or a German ally to receive the capitulation, and duplicate array entries
are prevented.

At startup and during Germany's daily MEFO/conquest update, a repair scans possible
countries, including annexed tags. A usable German-controlled industrial core and
evidence of defeat are required. Evidence can be an existing flag/array entry,
an existing country's capitulated status, an annexed country previously observed
active, a TFR proxy's existing initial-defense flag, or France's fall flag.
Dormant releasable countries are excluded without that evidence. Unknown annexed
tags lacking any historical evidence are deliberately not inferred to be victims.

All three factory types count: civilian factories, military factories and dockyards.
The decision's visibility and actual reward use the same state filters:

- Full German control; German core states are excluded.
- European state, or the existing Turkish exception.
- At least one factory/dockyard.
- Neither already looted nor protected by `VIC_dont_loot`.

This fixes targets appearing for territory held only by an ally, and prevents
factory totals from including protected/already-looted states. Previously looted
Soviet cities are excluded by their state flags; subtracting the old city ledger
again would deduct their reward twice, so that adjustment is no longer applied
to the newly filtered total. The city decisions retain their existing ledger.
Resistance/compliance effects only run where resistance exists.

The 25 PP cost, one-use-per-target policy, −0.5 percentage points of consumer-goods
factor per eligible factory, positive-penalty requirement, Economy of Conquest
requirement and France/Vichy country lock are preserved. Recovery registers a
target; it never automatically spends PP or grants a gold reward. Existing saves
are repaired on the next German daily update after loading these scripts.

Regression coverage executes the shipped scripts for FNL, FBL, NPO, NDE, NNO,
FCZ, FYG, NNG, FPR, NPR and their original-country equivalents. It covers missing
flags/array entries, repeated recovery, dormant tags, partial control, allies,
protected/looted/empty states, all factory types, Turkey, Soviet partial looting,
France's lock and the original economy gates. This does not prove the state of a
particular loaded German campaign.

Validation on 2026-10-25: all 91 repository tests passed, including eight gold
regressions. The running game reloaded the updated scripts at 15:10:04–15:10:05
and reported no new errors. This validates script loading, not the outcome of
clicking the decision in the affected German save.
