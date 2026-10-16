# HOI4 1.19 compatibility repairs

The October 12 error-log audit found removed vanilla content still referenced by
the mod overlay, conflicting Australian state filenames, and naval designs created
before their hull technologies. All repairs live in the mod. Steam's base files
are unchanged. Original files and the pre-repair log are saved under the backup
directory recorded in `log-compatibility-repairs.json`.

- State files 870, 871, 873 and 1074 now use the exact current vanilla filenames,
  so the mod overrides each state once. Their contents, province lists, owners,
  categories, resources, manpower and buildings are byte-for-byte unchanged.
- Checks for absent Australian and Indonesian focuses and the removed Australian
  monarchist intervention idea now return `always = no`. This disables only
  removed branches; existing historical advisor alternatives remain in place.
  No empty substitute focuses or ideas were added.
- Nine mine-module assignments in Portugal's decisions and Indonesia/Siam naval
  rewards now use empty optional slots. Mining modules remain disabled as intended
  by TFR. Other modules and ship-reward counts are unchanged.
- Siam no longer requests a tooltip for the absent Pan-Tai formable decision.
- Eight major-country histories initialize the hull technologies needed by their
  existing standard starting fleets before creating the variants. HOI4 previously
  force-unlocked these same hull technologies itself and emitted warnings. Hull,
  variant, module and fleet definitions are unchanged. In TFR, carrier hull_1 is
  unlocked by basic_ship_hull_carrier, not early_ship_hull_carrier.

`python tools/repair_log_compatibility.py --check` checks script braces, targeted
references, every effective state ID/province and the naval initialization order.
It also verifies renamed states against their original content hashes. The
one-shot `--apply` operation was driven by the captured pre-repair error log;
the JSON manifest records the concrete changes and their original backup.

Validation passed for all 20 scripts, 1081 effective states and 10297 province
assignments, as well as all eight SCW volunteer regression checks. A clean game
restart and a new German campaign advanced from January 1 to March 25, 1936
without any recurrence of the repaired references, state conflicts, mining
modules, missing tooltip or naval technology warnings.

`AI tried to post an invalid command: unlock_trait_command` recurred once on
March 18 in that test. It does not identify a country, trait or script location;
its cause remains unresolved. No speculative trait-balance change was made.
The log also retains Steam DLC/backend/checksum messages and five missing
super-heavy tank graphic entity references, which these repairs do not address.
The user's September 9 German session and pre-test autosave were preserved.
