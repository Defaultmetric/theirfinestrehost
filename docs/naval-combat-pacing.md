# Naval combat pacing: 30% ship attack, 10% naval air damage

Applied on 2026-10-12 to slow destructive naval battles. This is a balance
experiment; battle duration and losses require in-game comparison.

- The initial pass multiplied all 37 positive light, heavy and torpedo attack
  entries in ship modules, plus 12 positive base hull attack entries, by 0.3.
  Submarine torpedo module IV subsequently received the extra nerf below.
- Percentage bonuses from support upgrades, fire control, doctrines and MIOs
  remain unchanged; they apply to the reduced base attacks.
- Air-to-ship strength damage conversion changes from 1.0 to 0.1 and
  organization damage conversion from 1.5 to 0.15: 90% less naval air damage
  than before the initial pass. This covers land-based and carrier aircraft.
- The carrier multiplier is restored from 3.6 to its original 12.0, so the
  global 0.1 reduction applies once. Aircraft stats and other combat roles
  retain their current values. External-plane admission limits are unchanged.
- AA, anti-submarine attack, armor, piercing, HP, costs, speed and carrier
  capacity are unchanged. Ship hit chance is unchanged except for sub IV.

## Additional submarine IV nerf

- `ship_torpedo_sub_4`: attack 7.5 -> 6, an extra 20% reduction. Its final
  attack is 24% of the pre-pacing value of 25. This affects any design fitting
  this module, including the regular submarine IV and its radar variant.
- `ship_hull_submarine_4`: base visibility 16 -> 20, matching submarine III
  before fitted stealth modules, and hull torpedo hit bonus 0.10 -> 0.05.
- Submarine III keeps the initial 70% attack reduction. Anti-submarine weapons
  keep full damage. Surface torpedo launcher IV remains at its initial 0.3
  scale; it is a separate module from submarine torpedo module IV.
- The regular submarine IV keeps its existing range, HP, reliability, engine,
  modules and support upgrades. Legacy non-MTG and nuclear hull stats are
  outside this additional hull nerf.

Validation compared all modified weapon entries with external source backups:
The initial 49 positive values were verified as exactly 0.3 of their originals.
The follow-up changes only the submarine IV module attack and two ordinary
submarine IV hull stats, plus the naval air defines. Existing naval reports and
JSON audits describe the earlier balance; multiply their absolute attack
estimates by 0.3, accounting separately for designs fitting submarine torpedo
module IV. Their submarine IV visibility/hit estimates also predate this nerf.

Restart the game and use a fresh campaign for a controlled test; saved variants
may retain cached stats. Compare the same fleet designs, aircraft, admirals and
conditions over several battles. Check elapsed game hours, sunk ships and damage
to survivors. No in-game battle test has been performed by this change.
