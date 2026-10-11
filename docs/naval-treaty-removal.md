# Naval treaty removal

The London/Washington naval treaty system is removed for every country, with
and without Man the Guns, in both country-history start dates.

- Removed the four MTG treaty spirits and Japan's legacy London Treaty spirit.
- Removed treaty spirit grants and signatory/conference flags from country history.
- Shadowed vanilla's entire treaty decision and event files with empty mod overrides.
- Removed the treaty decision category, withdrawal/cheating/invitation/warning
  decisions, reduction/renewal missions and escalator clause.
- Removed Britain's enforcement decision/category and the reduction mission
  that it imposed on other countries, including associated war-goal events.
- Removed Japan's additional legacy withdrawal decision.
- Removed the British and Japanese treaty focuses. Japan's China non-aggression
  focus now follows the former treaty focus's parent, preserving the rest of
  the branch. Removed obsolete treaty restrictions from four Japanese naval focuses.
- Removed deleted focuses from AI planning and obsolete treaty exceptions
  from faction goals and the expired-war-goal event.
- Removed treaty news events; unrelated Britain events remain intact.
- Removed the identical cruiser/heavy/carrier IC caps copied into South America's
  naval-arms-race spirit. Its other naval/economic penalties remain intact.
- Kept the shared treaty trigger permanently false and its removal helper empty
  for compatibility with harmless scripted-localisation references.

Historical descriptions and shared treaty artwork may remain as unused assets;
they do not activate treaty mechanics. The Greek–Turkish diplomatic pact and
other unrelated treaties are outside the London/Washington restriction system.

The existing fleet ledger only updates hashes for the four explicitly edited
country histories. Ship designs, deployed fleet counts, technology bonuses and
IC budgets remain unchanged. Per-file hashes and the complete scope of edits
are recorded in `naval-treaty-removal.json`.

Validate with `python tools/validate_naval_treaty_removal.py`, then the existing
naval startup, integrated-bonus and compacted-fleet validators. In-game testing
requires restarting the mod and starting a new campaign; already saved national
spirits and active missions are not a supported migration path.
