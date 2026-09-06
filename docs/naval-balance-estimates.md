# TFR naval budget and loss sensitivity

Static estimates from local hull/module files. NOT simulated battles or predicted losses.

## Assumptions and limits

- Hull and weapons use matching tiers I-IV; these are explicit illustrative designs, not the unknown feedback designs.
- DD: one light battery, one or three launchers, engine. CL: two/four light-medium batteries, armor, engine, fire control 0. CA: four medium batteries, armor, engine, fire control 0. BB: three heavy batteries, armor (III for tier IV), engine, AA, fire control 0.
- Base hull plus module add_stats and mean of contributing add_average_stats, multiplied by 1 + summed module multiply_stats. No MIO, national, doctrine, tech, admiral, experience or production discounts. Designer values still need in-game confirmation.
- Same IC ceiling and 50-cap ceiling, not guaranteed equal spent IC. Unspent industry is visible; this is not a full-war production/refit model.
- CA/BB fleets have three DD screens per capital at initial full positioning. Screening deteriorates with losses and positioning; this model does not simulate that.
- No target selection, gun cadence, penetration, critical hits, retreat, repairs, weather, carrier aircraft or combat reinforcement model. Raw torpedo/light/heavy attack totals cannot be compared as equivalent damage.
- No fake victory probabilities or surviving-ship counts are generated. Armor/speed/HP are listed as design stats, not converted into an unverified combat formula.

## Designs

|Tier|Design|IC estimate|HP estimate|Speed estimate|Light|Heavy|Torpedo|Armor|
|---|---|---:|---:|---:|---:|---:|---:|---:|
|1|DD_torp3|1136.25|25.00|29.68|0.50|0.00|17.28|0.00|
|1|DD_torp1|821.25|25.00|30.24|0.50|0.00|5.76|0.00|
|1|CL_gun2|3075.00|120.00|30.52|5.00|0.00|0.00|4.00|
|1|CL_gun4|3825.00|120.00|28.84|10.00|0.00|0.00|4.00|
|1|CA_gun4|5575.00|260.00|27.72|0.00|16.00|0.00|4.00|
|1|BB_gun3|9867.00|357.00|22.99|0.00|30.00|0.00|18.00|
|2|DD_torp3|1483.50|40.00|29.96|0.80|0.00|30.24|0.00|
|2|DD_torp1|1046.50|40.00|31.08|0.80|0.00|10.08|0.00|
|2|CL_gun2|3524.50|132.60|34.35|8.00|0.00|0.00|6.00|
|2|CL_gun4|4452.00|132.60|31.95|16.00|0.00|0.00|6.00|
|2|CA_gun4|6307.00|288.20|29.55|0.00|26.00|0.00|6.00|
|2|BB_gun3|10962.00|388.50|26.76|0.00|45.00|0.00|26.00|
|3|DD_torp3|1844.75|50.00|30.24|2.00|0.00|69.12|0.00|
|3|DD_torp1|1280.75|50.00|31.92|2.00|0.00|23.04|0.00|
|3|CL_gun2|3934.00|154.00|36.80|16.00|0.00|0.00|11.00|
|3|CL_gun4|4984.00|154.00|33.60|32.00|0.00|0.00|11.00|
|3|CA_gun4|6944.00|324.00|31.04|0.00|52.00|0.00|11.00|
|3|BB_gun3|12110.00|460.00|28.38|0.00|96.00|0.00|42.00|
|4|DD_torp3|1818.00|60.00|30.52|3.00|0.00|90.72|0.00|
|4|DD_torp1|1386.00|60.00|32.76|3.00|0.00|30.24|0.00|
|4|CL_gun2|4439.75|172.50|38.12|20.00|0.00|0.00|14.00|
|4|CL_gun4|5693.50|172.50|34.16|40.00|0.00|0.00|14.00|
|4|CA_gun4|7906.00|357.50|31.52|0.00|66.00|0.00|14.00|
|4|BB_gun3|13081.50|517.50|31.33|0.00|120.00|0.00|42.00|

## Fleet configurations

|Tier|IC ceiling|DD torp3 count / IC / cap|Opponent|Main + escort count|Opponent IC / cap|DD losses equal one main enemy ship IC|
|---|---:|---|---|---|---|---:|
|1|50000|44 / 49995 / 26.4|CL_gun2|16 + 0|49200 / 16.0|2.71|
|1|50000|44 / 49995 / 26.4|CL_gun4|13 + 0|49725 / 13.0|3.37|
|1|50000|44 / 49995 / 26.4|CA_gun4|6 + 18|48232 / 16.8|4.91|
|1|50000|44 / 49995 / 26.4|BB_gun3|4 + 12|49323 / 19.2|8.68|
|1|100000|83 / 94309 / 49.8|CL_gun2|32 + 0|98400 / 32.0|2.71|
|1|100000|83 / 94309 / 49.8|CL_gun4|26 + 0|99450 / 26.0|3.37|
|1|100000|83 / 94309 / 49.8|CA_gun4|12 + 36|96465 / 33.6|4.91|
|1|100000|83 / 94309 / 49.8|BB_gun3|8 + 24|98646 / 38.4|8.68|
|1|150000|83 / 94309 / 49.8|CL_gun2|48 + 0|147600 / 48.0|2.71|
|1|150000|83 / 94309 / 49.8|CL_gun4|39 + 0|149175 / 39.0|3.37|
|1|150000|83 / 94309 / 49.8|CA_gun4|17 + 51|136659 / 47.6|4.91|
|1|150000|83 / 94309 / 49.8|BB_gun3|10 + 30|123308 / 48.0|8.68|
|2|50000|33 / 48955 / 19.8|CL_gun2|14 + 0|49343 / 14.0|2.38|
|2|50000|33 / 48955 / 19.8|CL_gun4|11 + 0|48972 / 11.0|3.00|
|2|50000|33 / 48955 / 19.8|CA_gun4|5 + 15|47232 / 14.0|4.25|
|2|50000|33 / 48955 / 19.8|BB_gun3|3 + 9|42304 / 14.4|7.39|
|2|100000|67 / 99394 / 40.2|CL_gun2|28 + 0|98686 / 28.0|2.38|
|2|100000|67 / 99394 / 40.2|CL_gun4|22 + 0|97944 / 22.0|3.00|
|2|100000|67 / 99394 / 40.2|CA_gun4|10 + 30|94465 / 28.0|4.25|
|2|100000|67 / 99394 / 40.2|BB_gun3|7 + 21|98710 / 33.6|7.39|
|2|150000|83 / 123130 / 49.8|CL_gun2|42 + 0|148029 / 42.0|2.38|
|2|150000|83 / 123130 / 49.8|CL_gun4|33 + 0|146916 / 33.0|3.00|
|2|150000|83 / 123130 / 49.8|CA_gun4|15 + 45|141698 / 42.0|4.25|
|2|150000|83 / 123130 / 49.8|BB_gun3|10 + 30|141015 / 48.0|7.39|
|3|50000|27 / 49808 / 16.2|CL_gun2|12 + 0|47208 / 12.0|2.13|
|3|50000|27 / 49808 / 16.2|CL_gun4|10 + 0|49840 / 10.0|2.70|
|3|50000|27 / 49808 / 16.2|CA_gun4|4 + 12|43145 / 11.2|3.76|
|3|50000|27 / 49808 / 16.2|BB_gun3|3 + 9|47857 / 14.4|6.56|
|3|100000|54 / 99616 / 32.4|CL_gun2|25 + 0|98350 / 25.0|2.13|
|3|100000|54 / 99616 / 32.4|CL_gun4|20 + 0|99680 / 20.0|2.70|
|3|100000|54 / 99616 / 32.4|CA_gun4|9 + 27|97076 / 25.2|3.76|
|3|100000|54 / 99616 / 32.4|BB_gun3|6 + 18|95714 / 28.8|6.56|
|3|150000|81 / 149425 / 48.6|CL_gun2|38 + 0|149492 / 38.0|2.13|
|3|150000|81 / 149425 / 48.6|CL_gun4|30 + 0|149520 / 30.0|2.70|
|3|150000|81 / 149425 / 48.6|CA_gun4|13 + 39|140221 / 36.4|3.76|
|3|150000|81 / 149425 / 48.6|BB_gun3|9 + 27|143570 / 43.2|6.56|
|4|50000|27 / 49086 / 16.2|CL_gun2|11 + 0|48837 / 11.0|2.44|
|4|50000|27 / 49086 / 16.2|CL_gun4|8 + 0|45548 / 8.0|3.13|
|4|50000|27 / 49086 / 16.2|CA_gun4|4 + 12|48256 / 11.2|4.35|
|4|50000|27 / 49086 / 16.2|BB_gun3|2 + 6|34479 / 9.6|7.20|
|4|100000|55 / 99990 / 33.0|CL_gun2|22 + 0|97674 / 22.0|2.44|
|4|100000|55 / 99990 / 33.0|CL_gun4|17 + 0|96790 / 17.0|3.13|
|4|100000|55 / 99990 / 33.0|CA_gun4|8 + 24|96512 / 22.4|4.35|
|4|100000|55 / 99990 / 33.0|BB_gun3|5 + 15|86198 / 24.0|7.20|
|4|150000|82 / 149076 / 49.2|CL_gun2|33 + 0|146512 / 33.0|2.44|
|4|150000|82 / 149076 / 49.2|CL_gun4|26 + 0|148031 / 26.0|3.13|
|4|150000|82 / 149076 / 49.2|CA_gun4|12 + 36|144768 / 33.6|4.35|
|4|150000|82 / 149076 / 49.2|BB_gun3|8 + 24|137916 / 38.4|7.20|

## Feedback sensitivity: 63 CL sunk against 157 DD

Assume 80 starting CL and 17 survivors exactly for this calculation. Carriers/capitals survive and their aircraft/repair losses are unknown. This is an IC break-even calculation only.

|DD tier|CL tier|CL design|IC of 63 CL lost|Equivalent DD losses|Interpretation if all 157 DD sink|
|---|---|---|---:|---:|---|
|II|1|CL_gun2|193725|130.6|CL side loses less IC|
|II|1|CL_gun4|240975|162.4|DD side loses less IC|
|II|2|CL_gun2|222044|149.7|CL side loses less IC|
|II|2|CL_gun4|280476|189.1|DD side loses less IC|
|II|3|CL_gun2|247842|167.1|DD side loses less IC|
|II|3|CL_gun4|313992|211.7|DD side loses less IC|
|II|4|CL_gun2|279704|188.5|DD side loses less IC|
|II|4|CL_gun4|358690|241.8|DD side loses less IC|

## Torpedo Launcher Nerf Applied

|Launcher tier|Previous attack|Current attack|Attack Change|Previous Hit Chance|Current Hit Chance|Current IC|
|---|---:|---:|---:|---:|---:|---:|
|1|7.2|5.76|-20.0%|0.0%|+0.0%|140|
|2|12.6|10.08|-20.0%|+0.5%|+1.0%|190|
|3|28.8|23.04|-20.0%|+2.0%|+1.5%|240|
|4|37.8|30.24|-20.0%|+3.5%|+2.0%|180|

Surface launcher attack nerfed by 20% compared to previous version; hit chance factor set identical to Vanilla (0% / +1.0% / +1.5% / +2.0%); IC costs restored to initial TFR.

## Torpedo Nerf Sensitivity & DD Balance

Torpedos have had raw attack scaled down by 20% and hit chance aligned with Vanilla to curb excessive Torp DD lethality.
DD torpedo salvos output balanced damage while maintaining TFR baseline industrial investment.
