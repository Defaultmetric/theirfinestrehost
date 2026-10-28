# Simplified aircraft research

Implemented 2026-10-28 for the By Blood Alone aircraft designer. The designer,
airframes, module statistics, historical variants and starting production are
preserved. Automatic aircraft templates are intentionally pending the user's
configurations; this implementation creates no new aircraft variants.

The four main research families are small, medium and large airframes, plus
transport planes. Mothership upgrades form an independent horizontal branch
below the airframes and transport planes; their special-project gate remains.
The centrifugal-jet special technology is in the same lower area of the air
tree and provides helicopter support-company bonuses. Modern airframes retain
their axial-jet project requirements. The legacy tree without By Blood Alone is
unchanged. The transport technologies run left to right below the airframes.
Interwar airframe technologies remain in the database and country histories but
are hidden; the 1936 airframes are independent visible roots, including for
countries that did not already possess an interwar airframe technology.
The airframe positions and year labels are shifted up one row so 1936 occupies
the former 1933 row; grid origins stay inside the background during scrolling.
The columns are centered within the horizontal space between the year labels.

After the first in-game screenshot, the columns were spaced further apart,
their grid widths were made consistent, and the titles were aligned and made
white for readability. Restart the game to see the corrected layout.

## Automatic modules

Shared modules follow the highest researched airframe generation in any of the
three designer families. Transport research does not advance designer modules.
Researching a later generation directly also grants earlier module generations.
No airframes are granted for free and the change does not revoke technologies
already held in country history or a save.

| Best airframe | Automatic modules |
|---|---|
| Base, including countries without airframes | Engine I, light machine guns/turrets, ordinary bomb mounts/bays and reconnaissance camera |
| Basic / 1936 | Engine II, first torpedo mounting, armor-piercing bombs, fuel tanks, drop tanks and ordinary aircraft construction modules; first tank-buster cannon, radio navigation and bomb sight |
| Improved / 1939 | Engine III, second torpedo mounting, heavy bomb locks, heavy machine guns/turrets, first aircraft cannon, armor and self-sealing tanks; second tank-buster cannon, rocket rails, improved radio navigation and bomb sight |
| Advanced / 1941 | Engine IV, third torpedo mounting, large aircraft cannon and cannon turrets |
| Modern / 1943 | Improved aircraft cannons |

Plane radar I also requires an improved or later airframe and completion of the
air radar project. Plane radar II requires advanced or later airframes and the
same project. Aircraft-only hidden support technologies unlock the relevant
modules without granting the global artillery/electronics technologies, their
buildings or their other bonuses. Those existing technologies can still unlock
the same modules normally if researched earlier.

Jet and rocket engines, guided weapons and project-reward modules keep their
existing project/research requirements. The focus-only suicide-charge module
is not granted automatically. The 19 ordinary BBA module technology IDs and
their module lists remain for history, focus, AI and special-project references;
their separate research nodes and paths are removed.

Research hooks apply module unlocks immediately. Startup handles country
history, and the monthly check handles technologies granted by focuses,
released countries, existing campaigns and radar projects completed later.
Grants are guarded and cannot stack bonuses. The shared scripted effect is
`TFR_air_unlock_modules`; later templates can use a separate creation helper.

## Verification and recovery

Run `python tools/validate_air_research.py` for technology definitions,
preserved project gates, 60 progression/DLC/family/project scenarios,
idempotence, startup/monthly hooks and the surrounding research UI.
`python tools/validate_naval_startup.py` also passes after this change.

Validation is static and simulates the scripted unlock conditions; it is not
an in-game runtime test. Restart HOI4 to load the changed database and GUI.
A new campaign applies the startup grants; an existing campaign receives
missing eligible modules at its next monthly check after loading the mod.

The backup location, changed runtime files and tier mapping are recorded in
`air-research-simplified.json`. The backup includes the original research GUI,
the installed vanilla BBA technology source and a manifest identifying newly
created files. Aircraft equipment, module and history files were not edited.
