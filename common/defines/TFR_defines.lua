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
NDefines.NProduction.LICENSE_EQUIPMENT_BASE_SPEED = 0
NDefines.NProduction.LICENSE_EQUIPMENT_TECH_SPEED_PER_YEAR = 0
NDefines.NProduction.LICENSE_EQUIPMENT_TECH_SPEED_MAX_YEARS = 4
NDefines.NProduction.LICENSE_EQUIPMENT_SPEED_NOT_FACTION = 0
NDefines.NProduction.LICENSE_EQUIPMENT_UPGRADE_XP_FACTOR = 1.0
NDefines.NProduction.LICENSE_EQUIPMENT_SPEED_NO_LICENSE = 0
NDefines.NProduction.CONVERSION_SPEED_BONUS = 0
NDefines.NProduction.EQUIPMENT_MODULE_ADD_XP_COST = 5.0
NDefines.NProduction.EQUIPMENT_MODULE_REPLACE_XP_COST = 2.0				-- XP cost for replacing one equipment module with an unrelated module when creating an equipment variant.
NDefines.NProduction.EQUIPMENT_MODULE_CONVERT_XP_COST = 1.0				-- XP cost for converting one equipment module to a related module when creating an equipment variant.
NDefines.NProduction.EQUIPMENT_MODULE_REMOVE_XP_COST = 1.0
NDefines.NProduction.MINIMUM_NUMBER_OF_FACTORIES_TAKEN_BY_CONSUMER_GOODS_PERCENT = 0.00 -- 0.05	-- The minimum number of factories we have to put on consumer goods, in percent. (Vanilla is 0.1)
		


NDefines.NTechnology.BASE_RESEARCH_POINTS_SAVED = 50.0
NDefines.NTechnology.BASE_YEAR_AHEAD_PENALTY_FACTOR = 4
NDefines.NTechnology.BASE_TECH_COST = 80
NDefines.NTechnology.MAX_TECH_SHARING_BONUS = 0.5
NDefines.NTechnology.LICENSE_PRODUCTION_TECH_BONUS = 0.5

NDefines.NFocus.MAX_SAVED_FOCUS_PROGRESS = 30

NDefines.NIndustrialOrganisation.ASSIGN_DESIGN_TEAM_PP_COST_PER_DAY = 0.0

NDefines.NMilitary.RELIABILTY_RECOVERY = 0.1
--NDefines.NMilitary.ATTRITION_EQUIPMENT_LOSS_CHANCE = 0.2
NDefines.NMilitary.TRAINING_ATTRITION = 0.00
NDefines.NMilitary.MAX_ARMY_EXPERIENCE = 999
NDefines.NMilitary.MAX_NAVY_EXPERIENCE = 999
NDefines.NMilitary.MAX_AIR_EXPERIENCE = 999
NDefines.NMilitary.EXPERIENCE_COMBAT_FACTOR = 0.10
NDefines.NMilitary.UNIT_EXPERIENCE_PER_COMBAT_HOUR = 0.0002
NDefines.NMilitary.EXPERIENCE_LOSS_FACTOR = 0,7

NDefines.NMilitary.UNIT_LEADER_USE_NONLINEAR_XP_GAIN = false
NDefines.NMilitary.BASE_DIVISION_BRIGADE_GROUP_COST = 3 	--Base cost to unlock a regiment slot
NDefines.NMilitary.BASE_DIVISION_BRIGADE_CHANGE_COST = 2	--Base cost to change a regiment column.
NDefines.NMilitary.BASE_DIVISION_SUPPORT_SLOT_COST = 2 	--Base cost to unlock a support slot
NDefines.NMilitary.ENEMY_AIR_SUPERIORITY_IMPACT = -0.15   -- effect on defense due to enemy air superiorty
NDefines.NMilitary.LAND_AIR_COMBAT_MAX_PLANES_PER_ENEMY_WIDTH = 2 -- how many CAS/TAC can enter a combat depending on enemy width there
NDefines.NMilitary.LAND_AIR_COMBAT_ORG_DAMAGE_MODIFIER = 0.025    -- global damage modifier
NDefines.NMilitary.LAND_AIR_COMBAT_STR_DAMAGE_MODIFIER = 0.030    -- air global damage modifier
NDefines.NMilitary.LAND_COMBAT_STR_DAMAGE_MODIFIER = 0.062        -- global damage modifier... but some equipment is returned at end of battles see : EQUIPMENT_COMBAT_LOSS_FACTOR
NDefines.NMilitary.LAND_COMBAT_ORG_DAMAGE_MODIFIER = 0.042        -- global damage modifier
NDefines.NMilitary.COMBAT_STACKING_PENALTY = -0.05                -- how much stackign penalty per division
NDefines.NMilitary.PIERCING_THRESHOLDS = {					-- Our piercing / their armor must be this value to deal damage fraction equal to the index in the array below [higher number = higher penetration]. If armor is 0, 1.00 will be returned.
	1.00,
	0.9,
	0.8,
	0.7,
	0.6,
	0.5,
	0.4,
	0.3,
	0.0, --there isn't much point setting this higher than 0
}
NDefines.NMilitary.PIERCING_THRESHOLD_DAMAGE_VALUES = {	-- 0 armor will always receive maximum damage (so add overmatching at your own peril). the system expects at least 2 values, with no upper limit.
	1.00,
	0.85,
	0.70,
	0.60,
	0.50,
	0.40,
	0.30,
	0.20,
	0.10,
}



NDefines.NProduction.BASE_FACTORY_SPEED_MIL = 3.5				-- Base factory speed multiplier (how much hoi3 style IC each factory gives).
NDefines.NResistance.GARRISON_STR_POW_EQUIPMENT = 1.5	--Scales impact of euqipment deficiency by raising that deficiency to the number here. Formula: efficiency = 1.0 - equipment_deficiency^GARRISON_STR_POW_EQUIPMENT

NDefines.NDoctrines.BASE_MASTERY_GAIN_TARGET_MANPOWER = 10000.0           -- Beyond this amount of manpower contributing to mastery, mastery gain will start having diminishing returns (see doctrines documentation)
NDefines.NDoctrines.TRAINING_MASTERY_GAIN_FACTOR = 1                     -- How much training contributes to doctrine mastery relative to combat/missions
NDefines.NDoctrines.MAX_MONTHLY_MASTERY_GAIN = 50                       -- Monthly mastery gain will not exceed this value
NDefines.NDoctrines.MIN_MASTERY_GAIN_PER_DAY = 0.5		-- If we have any mastery gain, it will be boosted to be at least this much per day (lower cap)
NDefines.NDoctrines.DEFAULT_REWARD_MASTERY = 75

NDefines.NNavy.NAVAL_INVASION_PREPARE_HOURS = 72

