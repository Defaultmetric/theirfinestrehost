NDefines.NGame.GAME_SPEED_SECONDS = { 1000.0, 0.19, 0.10, 0.06, 0.0 } 
NDefines.NGame.LAG_DAYS_FOR_LOWER_SPEED = 999				-- Days of client lag for decrease of gamespeed
NDefines.NGame.LAG_DAYS_FOR_PAUSE = 999				-- Days of client lag for pause of gamespeed.

NDefines.NGame.COMBAT_LOG_MAX_MONTHS = 12
NDefines.NGame.EVENT_TIMEOUT_DEFAULT = 15						-- Default days before an event times out if not scripted
NDefines.NGame.MISSION_REMOVE_FROM_INTERFACE_DEFAULT = 15		-- Default days before a mission is removed from the interface after having failed or completed
NDefines.NGame.HANDS_OFF_START_TAG = "VEN"
NDefines.NGame.ALERT_SFX_COOLDOWN_DAYS = 3					-- After playing an alert sound, don't play the same sound for XXX days, even if it fires again.
NDefines.NGame.TRADE_ROUTE_RECALCULATE_FREQUENCY_DAYS = 7 -- Max recalculation time for all trade routes (0 means we do not recalucate prediodically trade routes)

NDefines.NCountry.EVENT_PROCESS_OFFSET = 40						-- Events are checked every X day per country or state (1 is ideal but CPU heavy)
NDefines.NCountry.AIR_SCORE_MULTIPLIER = 0.0						-- Based on number of planes (which is typically a lot).

NDefines.NGeography.MEDITERRANEAN_SEA_REGIONS = { 15, 29, 68, 69, 168, 169, 202, 299, 300, 301 }

NDefines.NProduction.BASE_LICENSE_IC_COST = 0
NDefines.NProduction.LICENSE_IC_COST_YEAR_INCREASE = 0
NDefines.NProduction.LICENSE_EQUIPMENT_UPGRADE_XP_FACTOR = 1.0
NDefines.NProduction.LICENSE_EQUIPMENT_SPEED_NO_LICENSE = 0

NDefines.NTechnology.BASE_RESEARCH_POINTS_SAVED = 50.0
NDefines.NTechnology.BASE_YEAR_AHEAD_PENALTY_FACTOR = 3
NDefines.NTechnology.BASE_TECH_COST = 80
NDefines.NTechnology.MAX_TECH_SHARING_BONUS = 0.5
NDefines.NTechnology.LICENSE_PRODUCTION_TECH_BONUS = 0.5

NDefines.NCountry.MAX_COMMAND_POWER = 120.0						-- Max command power a country can have

NDefines.NFocus.MAX_SAVED_FOCUS_PROGRESS = 30

NDefines.NIndustrialOrganisation.ASSIGN_DESIGN_TEAM_PP_COST_PER_DAY = 0.0