# Lua–C++ si module native la pornire

## Rezultat

Cele doua verificari suplimentare din 2026-11-09 nu au furnizat un bootstrap
nativ utilizabil exclusiv prin Workshop + Play:

- Inventarul Lua a inclus acum si NDefines: 526 de obiecte, dintre care
  381 de tabele, 139 de functii raportate C si sase userdata. Zero erori si
  zero limite de parcurgere atinse. Nu a aparut o interfata suplimentara de
  incarcare a unei implementari native.
- Doua porniri valide, cu si fara modul minim de inventariere, au incarcat
  acelasi set de 130 de cai de DLL-uri. Nicio cale nu era in directorul modului
  sau in Workshop.

Acest rezultat acopera contextul Lua de defines si pornirile observate;
nu este un inventar al tuturor functiilor C++ sau contextelor posibile.
Nu s-a modificat formula atacului si nu s-a instalat un patch/hook nativ.

## Target si metoda

HOI4 Operation Postern v1.19.4.2.2da5, x64, SHA-256
`bccc62909b6a1ec2c1d5a46ef18608e4d0c7cdc89ad341b7402a23c40f7a8037`.
Adresele statice folosesc image base `0x140000000`.

Analiza statica foloseste copia privata, PE/.pdata, Capstone si Ghidra
selectiv. REA nu ofera aici observarea nativa Windows ceruta; autoanaliza
completa esuata anterior prin timeout nu a fost repetata.

Captura dinamica foloseste Windows Debug API pe procesele noi create de
harness, fara injectare de DLL-uri, breakpoints scrise de noi in aplicatie
sau modificari ale codului/memoriei targetului. DbgHelp recupereaza pana la
24 de cadre pentru fiecare incarcare. Mecanismele de observare sunt
documentate de Microsoft: [evenimentele de debugging](https://learn.microsoft.com/en-us/windows/win32/debug/debugging-events)
si [StackWalk64](https://learn.microsoft.com/en-us/windows/win32/api/dbghelp/nf-dbghelp-stackwalk64).
Harness-ul este instrumentul investigatorului, nu o solutie de instalare pentru jucator.

## 1. Legaturile Lua–C++

| Operatie identificata comportamental | Adresa | Apelanti directi gasiti |
| --- | --- | --- |
| `lua_newstate` | `0x142213c20` | 1 |
| `luaL_newstate` | `0x1422132c0` | 1 |
| Constructorul mediului folosit de joc | `0x1420d5ae0` | 1 |
| Initializarea luabind | `0x14222d020` | 1 |
| `lua_pushcclosure` | `0x1422113c0` | 38 |
| `luaL_register` | `0x1422135f0` | 8 |

Aceste identificari nu sunt simboluri originale recuperate. Constructorul
mediului este apelat direct de `0x140792cf0`, calea de defines examinata
anterior. Nu au fost gasiti pointeri literali catre aceste sase rutine in
scanarea suplimentara. Cele 38 de locuri directe de construire a C closures
identificate sunt in regiunea bibliotecilor Lua/luabind.

Scanarea perechilor nume/functie cu destinatii in regiunea Lua/luabind a
retinut 13 grupuri candidate si 137 de perechi. Acestea includ biblioteci
dezactivate si fragmente din tabela de initializare: numarul nu reprezinta
API-urile accesibile modului. Tabela de initializare de la `0x142ba9120`
contine `io` si `os`, dar ambele indica spre `0x1402b3e00`, care executa
numai `mov eax,1; ret`, fara inregistrarea bibliotecilor respective.

Initializarea luabind a fost recuperata cu toate fragmentele unwind
`0x14222d020..0x14222d346`. Construieste mecanismele de clase, metatabele si
bookkeeping cunoscute; nu a fost identificata aici inregistrarea unei
interfete de patch nativ.

### Inventarul efectiv accesibil scriptului

Modul de test foloseste numai introspectie standard asupra globals,
registrului, metatabelelor, mediilor si upvalues Lua obisnuite. Nu invoca
functiile descoperite, nu modifica obiectele gasite si nu incarca biblioteci.
NDefines/NDefines_Graphics/NDefines_CareerProfile nu mai sunt omise.

| Masuratoare | Rezultat |
| --- | --- |
| BEGIN / END | 1 / 1 |
| Status | `ok=true`, `problem_type=nil` |
| Obiecte | 526 |
| Tabele parcurse | 381 |
| Functii raportate drept C | 139 |
| Userdata | 6 |
| Citiri de mediu | 145 |
| Medii identice cu `_G` | 137 |
| Alte medii de tip tabel | 6, tabelul cunoscut `package` |
| Alte medii | 2, `nil` pentru perechea userdata cunoscuta |
| Erori / limite atinse | 0 / 0 |
| Linii emise inaintea markerilor finali | 7666 |

Includerea configuratiei nu a crescut numarul functiilor C fata de proba
anterioara. Inventarul nu a evidentiat o interfata suplimentara de extensii
native. Cupvalues private, memoria interna a userdata si contexte neatinse
de pornire nu au fost inspectate. Un callback C din biblioteca Lua nu
echivaleaza cu apelarea oricarei adrese C++ din motor.

## 2. Modulele native observate

| Masuratoare | Control fara mod | Mod de inventariere |
| --- | --- | --- |
| Rulare | `controlplain` | `inventoryplain` |
| PID propriu | 37308 | 23780 |
| Startup raportat de motor | 189784 ms | 184017 ms |
| Evenimente de incarcare DLL | 140 | 141 |
| Cai unice de DLL-uri | 130 | 130 |
| Cai nerezolvate | 0 | 0 |
| Evenimente cu cel putin un cadru HOI4 recuperat | 31 | 31 |
| Cai suplimentare fata de cealalta rulare | 0 | 0 |

Diferenta de un eveniment nu reprezinta un DLL nou: exista incarcari repetate
si descarcari. Categoriile evenimentelor sunt Windows 133/134, directorul
jocului 3/3 si Steam 4/4. Seturile de cai sunt identice. Componentele Steam
terte preexistente in instalatie nu au fost modificate sau folosite ca solutie.

Cadrele care ajung in executabil includ codul grafic `0x142496160` si rutine
de initializare/dispozitive din regiunea SDL. Sunt pastrate calea efectiva,
firul, momentul, cadrele recuperate si RVA-urile. Unde nu apare un cadru din
joc, apelantul engine exact ramane necunoscut. Nu s-a observat un DLL incarcat
din resursele modului si nu s-a stabilit o sursa din mod pentru argumentul
vreunui incarcator nativ.

Evenimentele arata imagini mapate cu succes, nu toate cererile de incarcare
esuate sau sirul exact transmis initial unui API. Probele folosesc DirectX 11,
fara partida/save; nu acopera toate rendererele, configuratiile sau modurile.
Descriptorul probei este local, in profil izolat; nu este o distributie
Subscribe + Play validata pe o instalatie curata.

## Profiluri, inchidere si verificarea modificarilor

Rularile valide au folosit profiluri temporare alfanumerice separate, cu
jurnale/cache create efectiv acolo si lista proprie de moduri. Controlul a
fost observat la meniul principal si inchis prin Quit, cu exit code 0.
Pentru proba cu mod, startup-ul este confirmat prin jurnal si inventarul Lua;
capturile grafice nu au permis o verificare independenta consistenta a
meniului. Procesul propriu a fost oprit explicit dupa captura, cu exit code
`0xffffffff`. Nu a fost incarcata o partida.

Doua incercari initiale, `baseline` si `baseline-extended`, nu au folosit
profilurile pregatite ale caror cai contineau cratime. Una a expirat in
checksum, cealalta a fost oprita. Au atins jurnalele profilului normal si
sunt excluse din comparatia control/mod. Cauza exacta din parser nu a fost
recuperata; functionarea cailor alfanumerice a fost verificata prin fisierele
create si configuratia izolata. Capturile partiale sunt pastrate.

Hash-urile `hoi4.exe`, `settings.txt` normal si `dlc_load.json` normal au ramas
identice. Nu s-au modificat fisierele TFR de gameplay. Procesele de test au
fost inchise.

## Artefacte si limite de acoperire

Director privat:
`C:\Users\mihai\.codex\analysis\hoi4-workshop-engine-20261109\binding-module-followup`.

- `lua-binding-inventory.json`, `lua-binding-table-candidates.tsv`,
  `lua-library-initializer-table.json`: inventarul static;
- `binding-function-0x1422132c0.c`,
  `binding-function-0x14222d020_0x14222d346.c`: decompilari selective;
- `inventory-mod/`: scriptul de introspectie si descriptorul;
- `full-runtime-binding-inventory.json`, `full-runtime-binding-inventory.txt`;
- `module-runtime-comparison.json`, `controlplain-events.jsonl`,
  `inventoryplain-events.jsonl`, manifestele/resultatele/stdout/stderr;
- `lifecycle-observations.json`: validari, corectia profilului si inchiderea;
- `observe_modules.py`, `inventory_bindings.py`, `summarize_results.py`:
  instrumentele reproductibile ale investigatiei.

Scanarile statice nu exclud aliasuri calculate, inlining, cai indirecte sau
alte implementari ale unui mediu de script. Inventarul efectiv este complet
pentru obiectele accesibile parcurse in contextul probei, nu pentru intregul
motor. Traseul atacului este in [attack-callpath.md](attack-callpath.md).
Nu a fost demonstrata legatura dintre un mod Workshop si instalarea unei
redirectionari a acelei rutine native.
