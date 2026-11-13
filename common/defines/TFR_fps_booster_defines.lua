-- FPS BOOSTER (Steam Workshop 3765424442) integrated into TFR.
-- Keys that TFR already sets more aggressively, or that TFR sets on purpose for MP hosting,
-- are NOT repeated here; conflicting graphics keys were merged into TFR_graphics_defines.lua.

-- [no-op: EVENT_PROCESS_OFFSET lives in NCountry, not NGame. TFR already sets NDefines.NCountry.EVENT_PROCESS_OFFSET = 40]
-- [TFR keeps its own value] NDefines.NGame.COMBAT_LOG_MAX_MONTHS = 3 -- Default 12.
-- [TFR keeps its own value] NDefines.NGame.LAG_DAYS_FOR_LOWER_SPEED = 25 -- Default 10. Wait longer before auto-dropping from speed 5.

NDefines.NNavy.CONVOY_LOSS_HISTORY_TIMEOUT_MONTHS = 3 -- Default 24.
NDefines.NNavy.NAVAL_COMBAT_RESULT_TIMEOUT_YEARS = 0.25 -- Default 2 years. (0.25 years = 3 months)

NDefines.NResistance.GARRISON_LOG_MAX_MONTHS = 3 -- Default 12.

NDefines.NMilitary.GENERATE_AI_DIV_COMMAND_HISTORY_ENTRIES = false -- Default true. Stop recording AI division paths.

NDefines.NAir.BOMBERS_DIVISION_FACTOR = 200 -- Default 30. Draw 1 visual plane per 200 real planes.
NDefines.NAir.FIGHTERS_DIVISION_FACTOR = 200 -- Default 30.
NDefines.NAir.MISSILES_DIVISION_FACTOR = 200 -- Default 60.
NDefines.NAir.TRANSPORT_DIVISION_FACTOR = 200 -- Default 30.

-- GRAPHICS OPTIMIZATIONS --
-- [TFR already sets the same value] NDefines.NGraphics.DRAW_SHADOWS_CUTOFF = 0 -- Default 400. Shadows disabled.
-- [applied in TFR_graphics_defines.lua] NDefines.NGraphics.TREE_FADE_NEAR = 0 -- Default 250. Trees disabled.
-- [applied in TFR_graphics_defines.lua] NDefines.NGraphics.TREE_FADE_FAR = 0 -- Default 350. Trees disabled.
-- [applied in TFR_graphics_defines.lua] NDefines.NGraphics.UNITS_DISTANCE_CUTOFF = 90 -- Default 120. 3D models turn into 2D boxes earlier when zooming out.
-- [applied in TFR_graphics_defines.lua] NDefines.NGraphics.SHIPS_DISTANCE_CUTOFF = 100 -- Default 240. 3D ships turn into 2D boxes earlier.
-- [TFR is already stricter] NDefines.NGraphics.WEATHER_DISTANCE_CUTOFF = 400 -- Default 1500. Weather particles stop rendering when zoomed out.
-- [applied in TFR_graphics_defines.lua] NDefines.NGraphics.WEATHER_DISTANCE_FADE_LENGTH = 100 -- Default 400.
-- [TFR already sets the same value] NDefines.NGraphics.DRAW_REFRACTIONS_CUTOFF = 0 -- Default 250. Water refractions disabled.
NDefines.NGraphics.MAX_TRAIN_WAGON_COUNT = 3 -- Default 6. Less wagons per train.
-- [TFR is already stricter] NDefines.NGraphics.MAPICON_GROUP_PASSES = 10 -- Default 20. Faster UI icon grouping.
NDefines.NGraphics.TRADE_ROUTE_MAX_LINES = 3 -- Default 6. Less dashed lines in oceans.
-- [reverted: kept vanilla, map buildings/city sprawl stay visible] NDefines.NGraphics.MAP_BUILDINGS_SHRINK_DISTANCE = 0 -- Default 180. Civilian 3D buildings disabled.
-- [reverted: kept vanilla, map buildings/city sprawl stay visible] NDefines.NGraphics.CITY_SPRAWL_SHRINK_DISTANCE = 0 -- Default 220. City sprawl textures disabled.
-- [TFR already sets the same value] NDefines.NGraphics.DRAW_FOW_CUTOFF = 0 -- Default 400. Visual Fog of War completely disabled.
NDefines.NGraphics.PROVINCE_NAME_DRAW_DISTANCE = 250 -- Default 500. Small province text hidden earlier.
-- [applied in TFR_graphics_defines.lua] NDefines.NGraphics.GRADIENT_BORDERS_REFRESH_FREQ = 0.30 -- Default 0.12. Borders repaint less often to reduce stutter.
NDefines.NGraphics.NAVAL_MINES_DISTANCE_CUTOFF = 400 -- Default 800. Naval mines disappear at half distance.

-- AI OPTIMIZATIONS --
NDefines.NAI.DAYS_BETWEEN_CHECK_BEST_TEMPLATE = 30 -- Default 7. AI calculates template designs less frequently.
-- [TFR keeps its own value] NDefines.NDiplomacy.DIPLOMACY_HOURS_BETWEEN_REQUESTS = 96 -- Default 24. AI diplomacy and trade evaluation restricted to every 4 days. AI sends diplomacy requests less frequently.
NDefines.NAI.REMOVE_OBSOLETE_TEMPLATE_DAYS = 90 -- Default 180. AI cleans up empty unused templates faster to save RAM.
NDefines.NAI.DAYS_BETWEEN_CHECK_BEST_DOCTRINE = 90 -- Default 30. AI checks for doctrine upgrades less frequently.
NDefines.NAI.RESEARCH_DAYS_BETWEEN_WEIGHT_UPDATE = 20 -- Default 7.
NDefines.NAI.REFIT_SHIP_RELUCTANCE = 90 -- Default 28.
NDefines.NAI.DAYS_BETWEEN_CHECK_BEST_EQUIPMENT = 30 -- Default 7.
NDefines.NAI.UPGRADE_DIVISION_RELUCTANCE = 14 -- Default 7.
NDefines.NAI.MAX_STATE_TARGETS_TO_EVALUATE_PER_HOUR = 20 -- Default 50.
NDefines.NNavy.NAVAL_ACCIDENTS_DAYS_TO_LIVE = 30 -- Default 120. Reduce naval accident log memory bloat.
NDefines.NAI.AI_OBJECTIVE_DEFAULT_TARGET_RECALC_DAYS = 7 -- Default 5. Naval/Air targeting pathfinding restricted to 1 week.
NDefines.NAI.STRIKE_FORCE_TARGET_RECALC_DAYS = 7 -- Default 5. Naval strike force pathfinding restricted.
