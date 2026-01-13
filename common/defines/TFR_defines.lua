NDefines.NGame.GAME_SPEED_SECONDS = { 1000.0, 0.19, 0.10, 0.06, 0.0 } 
NDefines.NGame.LAG_DAYS_FOR_LOWER_SPEED = 60				-- Days of client lag for decrease of gamespeed
NDefines.NGame.LAG_DAYS_FOR_PAUSE = 60				-- Days of client lag for pause of gamespeed.

NDefines.NGame.COMBAT_LOG_MAX_MONTHS = 36
NDefines.NGame.EVENT_TIMEOUT_DEFAULT = 15						-- Default days before an event times out if not scripted
NDefines.NGame.MISSION_REMOVE_FROM_INTERFACE_DEFAULT = 15		-- Default days before a mission is removed from the interface after having failed or completed
NDefines.NGame.HANDS_OFF_START_TAG = "VEN"
NDefines.NGame.ALERT_SFX_COOLDOWN_DAYS = 3					-- After playing an alert sound, don't play the same sound for XXX days, even if it fires again.
NDefines.NGame.TRADE_ROUTE_RECALCULATE_FREQUENCY_DAYS = 7 -- Max recalculation time for all trade routes (0 means we do not recalucate prediodically trade routes)

NDefines.NCountry.EVENT_PROCESS_OFFSET = 40						-- Events are checked every X day per country or state (1 is ideal but CPU heavy)
NDefines.NCountry.AIR_SCORE_MULTIPLIER = 0.0						-- Based on number of planes (which is typically a lot).

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
NDefines.NIndustrialOrganisation.FUNDS_FOR_SIZE_UP = 1500				-- Funds required to increase the size of the company
NDefines.NIndustrialOrganisation.FUNDS_FOR_SIZE_UP_LEVEL_FACTOR = 100	-- How much each level mutliplies the funds for size up
NDefines.NIndustrialOrganisation.FUNDS_FOR_SIZE_UP_LEVEL_POW = 1.5	-- Scaling factor for size increase cost
NDefines.NIndustrialOrganisation.FUNDS_FOR_RESEARCH_COMPLETION_PER_RESEARCH_COST = 1000     	-- Funds added to MIO when the Design Team has completed a research, multiplied by research_cost in technology template

NDefines.NMilitary.RELIABILTY_RECOVERY = 0.1
--NDefines.NMilitary.ATTRITION_EQUIPMENT_LOSS_CHANCE = 0.01
NDefines.NMilitary.REINFORCE_CHANCE = 0.02                 	   -- base chance to join combat from back line when empty
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
NDefines.NMilitary.ENEMY_AIR_SUPERIORITY_IMPACT = -0.25   -- effect on defense due to enemy air superiorty
NDefines.NMilitary.LAND_AIR_COMBAT_MAX_PLANES_PER_ENEMY_WIDTH = 2 -- how many CAS/TAC can enter a combat depending on enemy width there
NDefines.NMilitary.LAND_AIR_COMBAT_ORG_DAMAGE_MODIFIER = 0.07    -- global damage modifier
NDefines.NMilitary.LAND_AIR_COMBAT_STR_DAMAGE_MODIFIER = 0.030    -- air global damage modifier
NDefines.NMilitary.LAND_COMBAT_STR_DAMAGE_MODIFIER = 0.060        -- global damage modifier... but some equipment is returned at end of battles see : EQUIPMENT_COMBAT_LOSS_FACTOR
NDefines.NMilitary.LAND_COMBAT_ORG_DAMAGE_MODIFIER = 0.045        -- global damage modifier
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
NDefines.NDoctrines.TRAINING_MASTERY_GAIN_FACTOR = 0.5                     -- How much training contributes to doctrine mastery relative to combat/missions
NDefines.NDoctrines.MAX_MONTHLY_MASTERY_GAIN = 50                       -- Monthly mastery gain will not exceed this value
NDefines.NDoctrines.MIN_MASTERY_GAIN_PER_DAY = 0.5		-- If we have any mastery gain, it will be boosted to be at least this much per day (lower cap)
NDefines.NDoctrines.DEFAULT_REWARD_MASTERY = 75

NDefines.NNavy.NAVAL_INVASION_PREPARE_DAYS = 30								-- base days needed to prepare a naval invasion
NDefines.NNavy.NAVAL_INVASION_PLAN_CAP = 4									-- base cap of naval invasions can be planned at the same time
NDefines.NNavy.BASE_NAVAL_INVASION_DIVISION_CAP = 5							-- base cap of divisions that can be assigned in a naval invasion


-- some optimization stuff

NDefines.NDiplomacy.DIPLOMACY_HOURS_BETWEEN_REQUESTS = 12
NDefines.NDiplomacy.GUARANTEE_COST = 12
NDefines.NDiplomacy.TRUCE_PERIOD_AFTER_KICKING_FROM_FACTION = 0
NDefines.NDiplomacy.NUM_DAYS_TO_ENABLE_KICKING_NEW_MEMBERS_OF_FACTION = 0
NDefines.NDiplomacy.NUM_DAYS_TO_ENABLE_REINVITE_KICKED_NATIONS = 0
NDefines.NDiplomacy.FRONT_IS_DANGEROUS = 0

---AI
NDefines.NAI.DIPLOMACY_ACCEPT_ATTACHE_BASE = 100
NDefines.NAI.DIPLOMACY_ACCEPT_ATTACHE_OPINION_TRASHHOLD = 0
NDefines.NAI.DIPLOMACY_ACCEPT_ATTACHE_OPINION_PENALTY = 0
NDefines.NAI.GIVE_STATE_CONTROL_MIN_CONTROLLED = 0
NDefines.NAI.GIVE_STATE_CONTROL_MIN_CONTROL_DIFF = 0

--Some ai stuff 

NDefines.NAI.DEPLOY_MIN_TRAINING_PEACE_FACTOR = 1.0		-- Required percentage of training (1.0 = 100%) for AI to deploy unit in peacetime
NDefines.NAI.DEPLOY_MIN_EQUIPMENT_PEACE_FACTOR = 1.0	-- Required percentage of equipment (1.0 = 100%) for AI to deploy unit in peacetime
NDefines.NAI.PLAN_ATTACK_MIN_ORG_FACTOR_MED = 0.75		-- (LOWMEDHIGH) corresponds to the plan execution agressiveness level.
NDefines.NAI.FRONT_TERRAIN_DEFENSE_FACTOR = 5.0			-- Multiplier applied to unit defense modifier for terrain on front province multiplied by terrain importance
NDefines.NAI.AIR_WING_REINFORCEMENT_LIMIT = 150
NDefines.NAI.DESPERATE_AI_MIN_UNIT_ASSIGN_TO_ESCAPE = 8			-- AI will assign at least this amount of units to break from desperate situations
NDefines.NAI.START_TRAINING_EQUIPMENT_LEVEL = 0.9               -- ai will not start to train if equipment drops below this level
NDefines.NAI.STOP_TRAINING_EQUIPMENT_LEVEL = 0.8                -- ai will not train if equipment drops below this level
NDefines.NAI.DIVISION_DESIGN_MAX_FAILED_DAYS = 30					-- max days we keep track of since failure of a template design update
NDefines.NAI.EQUIPMENT_DESIGN_MAX_FAILED_DAYS = 30					-- max days we keep track of since failure of an equipment design update
NDefines.NAI.INVASION_COASTAL_PROVS_PER_ORDER = 12				-- AI will consider one extra invasion per number of provinces stated here (num orders = total coast / this)
NDefines.NAI.AREA_DEFENSE_BASE_IMPORTANCE = 3					-- Area defense order base importance value (used for determining order of troop selections)
NDefines.NAI.AREA_DEFENSE_CIVIL_WAR_IMPORTANCE = 10000			-- Area defense order importance value when a country is in a civil war as target or revolter.
NDefines.NAI.COMBINED_ARMS_LEVEL = 2							-- 0 = Never 1 = Infantry/Artillery 2 = Go wild
NDefines.NAI.MAX_DISTANCE_NALAV_INVASION = 200.0				-- AI is extremely unwilling to plan naval invasions above this naval distance limit.
NDefines.NAI.NEW_LEADER_EXTRA_PP_FACTOR = 2.0					-- Country must have at least this many times extra PP to get new admirals or army leaders
NDefines.NAI.MAX_UNITS_FACTOR_AREA_ORDER = 1.0					-- Factor for max number of units to assign to area defense orders
NDefines.NAI.DESIRED_UNITS_FACTOR_AREA_ORDER = 1.0				-- Factor for desired number of units to assign to area defense orders
NDefines.NAI.MAX_UNITS_FACTOR_FRONT_ORDER = 1.5					-- Factor for max number of units to assign to area front orders
NDefines.NAI.DESIRED_UNITS_FACTOR_FRONT_ORDER = 1.5				-- Factor for desired number of units to assign to area front orders
NDefines.NAI.LAND_COMBAT_OUR_COMBATS_AIR_IMPORTANCE = 55		-- Strategic importance of our armies in the combats
NDefines.NAI.LOW_PRIO_TEMPLATE_BONUS_FOR_GARRISONS = 10000		-- bonus to make ai more likely to assign low prio units to garrisons
NDefines.NAI.LOW_PRIO_TEMPLATE_PENALTY_FOR_FRONTS = 10000		-- penalty to make ai less likely to assign low prio units to fronts
NDefines.NAI.SCREENS_TO_CAPITAL_RATIO = 2.0					-- screens to capital/carrier count in carrier & capital taskforces
NDefines.NAI.MAX_SCREEN_FORCES_FOR_INVASION_SUPPORT = 0.0 -- max ratio of screens forces to be used in naval invasion missions
NDefines.NAI.MAX_CAPITAL_FORCES_FOR_INVASION_SUPPORT = 0.4 -- max ratio of capital forces to be used in naval invasion missions
NDefines.NAI.FUEL_RATIO_TO_EXIST_FUEL_SAVING_MODE = 0.10 					-- countries will exit fuel saving mode if they have more fuel ratio than this
NDefines.NAI.MAX_FUEL_CONSUMPTION_RATIO_FOR_AIR_TRAINING = 0.25			-- ai will use at most this ratio of affordable fuel for air training
NDefines.NAI.MAX_FUEL_CONSUMPTION_RATIO_FOR_NAVY_TRAINING = 0.25		-- ai will use at most this ratio of affordable fuel for naval training
NDefines.NAI.AGGRESSIVENESS_CHECK_BASE = 2.0							-- front comparison where ai will consider aggressive stance unless it is already then the number above is used
NDefines.NAI.AGGRESSIVENESS_CHECK_EASY_TARGET = -0.4					-- if target nation is flagged as easy target we also adjust down the front comparison needed
NDefines.NAI.FRONT_EVAL_UNIT_ACCURACY = 0.7								-- scale how stupid ai will act on fronts. 0 is potato
NDefines.NAI.FRONT_EVAL_UNIT_SUPPLY_AND_ORG_LACK_IMPACT = 0.0			-- scale how painful the AI thinks a combined lack of supply and organization is for units
NDefines.NAI.CONVOY_ESCORT_SCORE_FROM_CONVOYS = 15                        -- score for each convoy you have in area
NDefines.NAI.CONVOY_ESCORT_MUL_FROM_NO_CONVOYS = 0.02                     -- score multiplier when no convoys are around
NDefines.NAI.MAX_UNIT_RATIO_FOR_INVASIONS = 0.5							-- countries won't use armies more than this ratio of total units for invasions
NDefines.NAI.MAX_INVASION_FRONT_SCORE = 2000							-- max score for naval invasion front scores
NDefines.NAI.NAVAL_INVADED_AREA_PRIO_MULT = 2.0									-- fronts that belongs to recent invasions gets more prio
NDefines.NAI.MIN_NUM_CONQUERED_PROVINCES_TO_DEPRIO_NAVAL_INVADED_FRONTS = 30	-- if you conquer this amount of provinces after a naval invasion it will lose its prio status and will act as a regular front
NDefines.NAI.MIN_INVASION_PLAN_VALUE_TO_EXECUTE = 0.2				-- ai will only activate invasions if it is above this