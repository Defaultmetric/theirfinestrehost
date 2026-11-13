# Country toolbar layout

The ten country toolbar buttons use a 55 x 41 clickable area with a 58-pixel
pitch (three pixels between buttons). This fills the row left by hiding the
International Market and moving Spain Volunteers above raids.

Faction, Decisions, Intelligence, Research, Trade, Construction, Production,
Deployment, Logistics and Officer Corps occupy consecutive slots. The faction
emblem is drawn at 24 x 24 in the top of the box, with the initiative counter below it;
the no-faction state shows the native crossed-axes icon (`faction_button_none.dds`).
Its initiative counter is transparent to mouse input. Alert badges and glows
move with their buttons. Native button names and shortcuts are retained.

The layout lives in `interface/topbar.gui`. `interface/factions/factions.gfx`
preserves the native definitions and points only the two toolbar faction frames
(member and no-faction) at `gfx/interface/topbar/toolbar/faction_button.dds`: the
native 55 x 41 toolbar box (two frames, normal and hover) with the icon removed,
so the faction emblem sits on the same background as its neighbours.
Re-diff that native file and recheck the DLC-dependent containers after updates.

Verified in HOI4 1.19.3 on 2026-10-23 at UI scale 1.0: 1920 x 1080 with UK/Allies
and 2560 x 1440 with Germany/Axis. The row fills its available space uniformly,
and clicking the enlarged faction button's right edge opens the faction panel at
both resolutions. No toolbar or faction sprite errors appeared in the final log.
Fresh paused campaigns were used without saving; original video settings restored.
