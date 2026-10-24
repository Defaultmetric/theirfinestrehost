# Status Navy: Vanilla HOI4 + Mihai's Navy Simplified

## Rezumat arhitectură curentă (2026-10-24)

Tot importul Hearts of Oak (`OAK`) a fost eliminat complet, iar sistemul naval folosește **100% statistici Vanilla HOI4** pentru module, carene, defines și flote de start, păstrând arborele de cercetare și automatizările din `Mihai'sNavySimplified`:

1. **Arborele de cercetare naval (`Mihai'sNavySimplified`)**:
   - Tab unic vertical **Navy** (`mtgnavalfolder`) în `interface/countrytechtreeview.gui`, `common/technologies/MTG_naval.txt`, `common/technologies/MTG_naval_Support.txt`, `common/technologies/tfr_naval_project_ships.txt` și `common/technology_tags/00_technology.txt`.
   - Tehnologiile de transport (`mtg_transport`, `mtg_landing_craft`, `mtg_tank_landing_craft`) sunt mutate în `support_folder`.
   - La startul jocului (`common/on_actions/tfr_navy_simplified_on_actions.txt`), toate țările primesc automat carenele 1922/1936 și toate tehnologiile de module navale (ascunse din arborele de cercetare).

2. **Design-uri navale fixe și bonusuri de suport integrate**:
   - Cele 43 de design-uri standard (`common/scripted_effects/tfr_navy_designs.txt`) sunt create automat la start (pentru 1922/1936) și imediat la finalizarea fiecărei cercetări de carenă/proiect (`on_research_complete`).
   - Bonusurile pasive din tehnologiile de suport eliminate sunt integrate prin upgrade-uri ascunse pe variante (`common/units/equipment/upgrades/tfr_hidden_naval_support.txt`) și tehnologii globale ascunse (`common/technologies/tfr_integrated_naval_bonuses.txt`, `common/scripted_effects/tfr_integrated_naval_bonuses.txt`).

3. **100% Vanilla HOI4 pentru module, carene, defines și flote de start**:
   - `common/units/equipment/modules/00_ship_modules.txt`: 100% identic byte-for-byte cu Vanilla HOI4.
   - `common/units/equipment/ship_hull_*.txt`: statistici numerice, costuri IC, viteze, raze de acțiune și limite de module 100% Vanilla HOI4, cu anii carenelor din `Mihai'sNavySimplified` (`1940 -> 1938`, `1944 -> 1942`), sloturile `ship_heavy_battery` / `fixed_ship_fire_control_system_slot` pe `ship_hull_pre_dreadnought` și lista `upgrades` pentru bonusurile integrate (`tfr_hidden_support_*`).
   - `common/defines/TFR_defines.lua`: toate defines-urile navale și de naval strike/AI sunt 100% Vanilla HOI4, păstrând doar regulile `Mihai'sNavySimplified`:
     - Minele navale dezactivate (`NAVAL_MISSION_MINES_* = 0`, `NAVAL_MINES_PLANTING_SPEED_MULT = 0.0`, butoanele UI ascunse în `interface/naviesview.gui`).
     - Penalizarea de poziționare pentru flote mari: `NDefines.NNavy.HIGHER_SHIP_RATIO_POSITIONING_PENALTY_FACTOR = 0.5`.
   - Flotele de start, variantele istorice și liniile de producție navale din `history/countries/*.txt` și `history/units/*naval*.txt` sunt cele din Vanilla HOI4 (fără tratatele navale din Washington/Londra, eliminate prin `tools/remove_naval_treaty.py`).

## Validare rapidă

```powershell
python tools/validate_naval_startup.py
python tools/validate_integrated_naval_bonuses.py
python tools/validate_naval_treaty_removal.py
```

Backup-ul complet înainte de această tranziție se află în:
`C:\Users\mihai\.codex\backups\tfr-vanilla-navy-simplified-20261024-184000`
