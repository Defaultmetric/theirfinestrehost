# Experimental project research cards

The installed project definitions contain 48 projects across Land, Air,
Navy, Nuclear, Radar and Rocket files. Thirteen already had naval project
cards or a visible radar technology. The remaining 35 projects have an
informational card with the project's name, description and an appropriate
native research icon or equipment image.

The new sections are below the existing research trees:

- Land cruisers and flame tanks: Armor, with and without the tank designer.
- Armored support vehicles: Support Companies.
- Super-heavy artillery and railway guns: Artillery.
- Stronghold Network: Electronics and fortification.
- Air projects: Aviation, with and without the plane designer.
- Rocket projects: Electronics, beside the nuclear section.
- Missing naval projects: Navy, with and without the ship designer.
- Nuclear projects: Electronics.

Each card displays the original project-completion requirement and becomes
researched automatically on completion. The project itself continues to
grant its original equipment, units, buildings, modifiers and prototype
choices; the card has no duplicate rewards. Existing completed projects are
synchronized at startup and monthly in a loaded campaign. Existing naval
cards for torpedo cruisers, fleet submarines and midget submarines no longer
require Gotterdammerung when their projects do not; the escort carrier and
submarine carrier cards use their projects' No Compromise, No Surrender gate.

The Flame Tank and Land Cruiser cards use non-buildable, unassigned equipment
markers solely to select the wide tank-research layout. The projects still
control actual equipment and unit unlocks; the markers cannot be produced.

The project list, mappings and backup location are in
`experimental-project-cards.json`. Run
`python tools/validate_experimental_project_cards.py` to check coverage,
project rewards, completion markers, icon references and layout. Static
validation cannot prove game runtime rendering; restart the game and inspect
the new sections and error log after loading a campaign.
