# Modificarea codului nativ HOI4 exclusiv prin Steam Workshop

Data investigatiei: 2026-11-09.

Continuare: [inventarul Lua extins si modulele native observate la pornire](lua-bindings-and-startup-modules.md).
Proba include acum NDefines si doua porniri valide comparate prin Windows Debug API.
Nu a fost demonstrat un bootstrap nativ din mod.

## Rezultat

A fost confirmat un punct normal de extensie nativ -> script: triggerul
`DIPLOMACY_GUARANTEE_ENABLE_TRIGGER_OVERRIDES_GAME_TRIGGER` este evaluat de
rutina nativa de eligibilitate a garantiei. Rezultatul poate omite anumite
verificari native. Doua campanii locale izolate au confirmat diferenta de
eligibilitate afisata cand doar corpul acestui trigger se schimba din `false`
in `true`. Detaliile si limitele sunt in
[proba callback-ului](<C:/Program Files (x86)/Steam/steamapps/workshop/content/394360/3513811852/docs/engine-script-callback-proof.md>).

Nu a fost identificata o metoda functionala pentru inlocuirea sau interceptarea
arbitrara a functiilor native respectand exclusiv fluxul Workshop cerut.
Callback-ul confirmat schimba logica unui punct expus de motor; nu modifica
codul C++ si nu este o interfata pentru orice functie nativa.
Calea obisnuita Lua pentru incarcarea unui DLL este dezactivata in executabilul
local analizat. Loaderele native gasite necesita instalare separata.
Verificarea suplimentara a identificat un incarcator nativ intern pentru pluginuri
de imagini `.fip`, dar cautarea lui este ancorata in directorul executabilului;
nu a fost identificata o legatura intre aceasta cautare si directorul Workshop.
Un test real cu un mod local minim a confirmat executia automata Lua din
`common/defines`, dar nu a identificat o interfata pentru modificarea functiilor
native. Proba adaugata in `script/autoexec.lua` nu s-a executat la pornirea testata.

Aceasta este concluzia unei investigatii delimitate, nu o demonstratie a absentei
oricarei vulnerabilitati sau a oricarui mecanism nedocumentat din intregul motor.

## Cerinta verificata

Jucatorul se aboneaza la unul sau cel mult doua moduri si porneste jocul normal,
fara alt pas de activare a unei componente native.
Modul trebuie sa poata inlocui sau intercepta functii native ale motorului, fara
instalare manuala, copiere de DLL-uri, modificarea optiunilor de lansare sau
pornirea unui program auxiliar. Ajustarea defines sau a regulilor prin script
nu reprezinta, singura, indeplinirea acestei cerinte.

## Identitatea artefactelor

- Mod: `Their Finest Rehost(TFR)`, versiunea `2.0`, Workshop `3513811852`.
- Descriptorul declara `supported_version="1.19.*"`.
- Executabil local: `C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV\hoi4.exe`.
- Dimensiune: 56,535,160 octeti; format PE x86-64.
- SHA-256: `bccc62909b6a1ec2c1d5a46ef18608e4d0c7cdc89ad341b7402a23c40f7a8037`.
- Sirul de versiune din executabil: `Operation Postern v1.19.4.2.2da5`.
- `hoi4_rev.txt`: `2da5926752c96c473d7d307bb2d6f51576221558`.

Identitatea de mai sus delimiteaza analiza; concluziile nu sunt o verificare a
tuturor versiunilor sau platformelor HOI4.

## Cai de incarcare verificate

| Cale | Constatare | Respecta cerinta? |
| --- | --- | --- |
| Continut Workshop | Steam descarca un director; jocul decide cum interpreteaza fisierele din el. Abonarea nu ofera, prin ea insasi, o interfata pentru interceptarea functiilor native. | Distributie da; incarcare nativa nedemonstrata. |
| `common/defines/*.lua` | Executia automata a fost confirmata printr-un test real. Mediul observat contine Lua 5.1, bibliotecile obisnuite permise si tabelele NDefines; nu a expus o interfata de modificare a memoriei sau codului nativ. | Nu demonstreaza cerinta. |
| HoI4Mod-Loader, Builder-HD | Documentatia cere `version.dll` si `loader_config.ini` in directorul jocului. | Nu: instalare manuala. |
| HOI4ModLoader, green1052 | Documentatia cere .NET 10 si fisiere in directorul jocului. | Nu: dependente si instalare manuala. |
| `hoi4_lua`, ari-20 | Foloseste un DLL injectat si propriul `hoi4_launcher.exe`. Lua suplimentar este furnizat de extensie. | Nu: pornire prin program auxiliar. |
| `installscript.vdf` inclus in mod | Valve cere ca scriptul sa faca parte dintr-un depot al aplicatiei, sa fie marcat in manifest si procesat prin sistemul SteamPipe. | Nu: un fisier Workshop nu devine astfel script de instalare. |

Windows are propria ordine de cautare a DLL-urilor. Directorul unui item Workshop
nu devine automat director de cautare doar pentru ca HOI4 ii monteaza resursele.
Aceasta este o distinctie intre accesul la resursele modului si incarcarea nativa;
nu este o dovada ca toate caile interne de incarcare au fost auditate.

## Pista istorica Lua

Anuntul oficial Paradox din 7 februarie 2020 spune ca versiunea 1.8.2 a reparat o
problema de securitate legata de incarcarea bibliotecilor Lua pentru moduri.
Anuntul stabileste existenta si repararea problemei istorice. Nu stabileste
existenta unei cai echivalente in executabilul local 1.19.4.2 si nu poate fi folosit
drept demonstratie ca metoda functioneaza astazi.

## Verificarea statica a caii Lua

S-a folosit Ghidra 12.1.4 pentru disasamblare si decompilare selectiva, pe o copie
cu acelasi SHA-256 ca executabilul original. Functiile au fost delimitate cu
intrari din tabelul PE `.pdata`; adresele de mai jos sunt adrese statice pentru
image base `0x140000000`, nu adrese observate intr-un proces pornit.

| Observatie | Locatie in artefact | Interpretare si limita |
| --- | --- | --- |
| Constructorul mediului Lua apeleaza initializarea bibliotecilor. | `0x1420d5ae0`, apel la `0x1422150f0` | Legatura dintre mediul folosit de joc si tabelul de biblioteci este confirmata static. |
| Initializarea parcurge tabelul de perechi nume/functie. | Functie `0x1422150f0`, tabel `0x142ba9120` | Structura corespunde initializarii bibliotecilor din Lua 5.1. |
| Intrarea `io` indica spre `0x1402b3e00`. | Perechea de la `0x142ba9150` | Codul destinatiei este `mov eax, 1; ret`; biblioteca nu este initializata de aceasta intrare. |
| Intrarea `os` indica spre aceeasi functie. | Perechea de la `0x142ba9160` | Aceeasi restrictie ca pentru `io`. |
| `package.loadlib` este inregistrata printr-un tabel care indica spre `0x142225f90`. | Perechea de la `0x142bab1f8` | Prezenta numelui nu inseamna ca incarcarea nativa este activata. |
| Invelisul `loadlib` apeleaza `0x142226980` si considera doar codul zero drept succes. | Functie `0x142225f90` | Conventia corespunde implementarii Lua 5.1; numele functiilor interne sunt identificari prin comparatie, nu simboluri originale recuperate. |
| Backendul returneaza `1` pe ambele iesiri normale; nu are ramura de succes. | `0x142226980` pana la `0x142226a62`; instructiuni `mov eax, 1` la `0x1422269d1` si `0x142226a58` | In aceasta cale, cererea nu poate produce functia C asteptata de `loadlib`. Comparatia cu Lua 5.1 identifica `1` drept eroarea `ERRLIB`. |
| Incarcatorul de defines creeaza acest mediu, incarca fisierele si citeste `NDefines`. | Functie `0x140792cf0`; constante `common/defines`, `lua`, `NDefines` | Legatura cu defines este stabilita prin apeluri si constante, nu doar prin numele unui fisier. |
| La sfarsitul incarcarii defines este apelata curatarea mediului. | Apel la `0x1420d5bb0` din `0x140792cf0` | Rutina de curatare apeleaza `0x142213ba0` si pune pointerul mediului pe zero. |

Prin urmare, simpla adaugare a unui DLL in mod si invocarea caii normale Lua nu
ofera un bootstrap nativ in acest build. Nu a fost construita sau rulata o
incercare de ocolire a acestor restrictii.

Probe detaliate, pastrate in afara directorului Workshop:

- `C:\Users\mihai\.codex\analysis\hoi4-workshop-engine-20261109\focused-0x1422150f0.c`: initializarea bibliotecilor, `package`, invelisul `loadlib`, citirea unui script.
- `C:\Users\mihai\.codex\analysis\hoi4-workshop-engine-20261109\focused-0x142226980.c`: backendul de incarcare si curatarea mediului, inclusiv disasamblare.
- `C:\Users\mihai\.codex\analysis\hoi4-workshop-engine-20261109\focused-0x1420d5ae0.c`: constructorul Lua si incarcatorul de defines.
- Scriptul `FocusedLua.java` si jurnalele Ghidra din acelasi director permit refacerea analizei selective.

Aceste probe sunt rezultate Ghidra si citiri de octeti prin shell, nu rezultate
REA Evidence. Primele incercari REA au depasit limitele de 300/330 secunde in
timpul analizei automate; aceste intreruperi nu sunt probe despre functionalitatea
jocului. O incercare ulterioara cu termen extins a fost oprita dupa obtinerea
probelor selective, fara rezultate suplimentare. Nicio concluzie de mai sus nu
este derivata dintr-un timeout sau din absenta unui rezultat REA.

## Verificarea suplimentara: extensii din interfata si biblioteca de imagini

Au fost inspectate separat puncte de extensie din afara caii Lua `defines`, fara
reluarea analizei automate complete care depasise limitele instrumentului.

### Pluginuri native pentru imagini

In executabil exista un incarcator nativ de pluginuri `.fip`, identificat prin
codul de initializare, enumerarea fisierelor si apelurile Windows. Comportamentul
corespunde mecanismului FreeImage; comparatia de sursa nu este tratata drept
dovada ca versiunea publicata a bibliotecii este identica cu cea din joc.

- Punctul de intrare al rutinei analizate este `0x1424c7bf0`.
- La `0x142292c03` apelantul pune argumentul `ECX` pe zero, apoi apeleaza aceasta
  rutina la `0x142292c05`; ramura de cautare a pluginurilor externe este astfel
  permisa de acest apel.
- Rutina obtine calea executabilului prin `GetModuleFileNameW(NULL, ...)`, elimina
  numele fisierului si foloseste `SetCurrentDirectoryW` pentru directorul rezultat.
- Tabelul de cautare de la `0x143138810` are doua intrari: sirul gol si `plugins\`.
  Numarul de intrari de la `0x143138828` este doi.
- Cautarea adauga masca `*.fip`. Apelul `LoadLibraryA` este la `0x1424c7ebe`.
- Calea analizata foloseste cautarea de fisiere a runtime-ului Windows si
  incarcatorul Windows; nu foloseste resolverul virtual de resurse al modurilor.
- La sfarsit restaureaza directorul de lucru anterior, daca schimbarea a reusit.

Acest mecanism confirma existenta unui incarcator nativ intern, dar nu satisface
cerinta Workshop: un item descarcat in directorul Workshop nu este, prin acest
mecanism, cautat in directorul executabilului sau in `plugins\` de langa el.
Nu a fost gasita o setare a modului care sa schimbe aceasta legatura.

Probe: `focused-0x1424c7bf0_0x1424c7f86.c`, `native-loading-imports.json` si
`native-loading-owner-strings.json`, in directorul de analiza mentionat mai sus.
Ultimele doua provin din parsarea PE si disasamblare Capstone. Enumerarea
apelurilor directe prin IAT nu acopera toate apelurile indirecte sau rezolvate
dinamic.

Pentru aceasta rutina au fost urmarite intrarile `.pdata` cu
`UNW_FLAG_CHAININFO`. Ele descriu fragmente ale aceleiasi proceduri, nu functii
independente; decompilarea finala le reuneste la intrarea `0x1424c7bf0`.
Fragmentele preliminare `focused-0x1424c7d76.c` nu trebuie folosite ca semnaturi
ale unor functii originale separate. Pentru punctele Lua principale analizate
anterior s-a verificat separat absenta flagului `CHAININFO`.

### Chei Lua ale interfetei

Inregistrarile numelor `luafunction_buttonclick` si `luaClick` au fost urmarite
din initializarea catalogului de chei. `luaClick` este acceptat de parserul
inspectat: ramura pentru identificatorul `0x14f` din `0x1422c01e0` citeste un sir
in campul obiectului de la offsetul `0x1f0`.

Aceasta confirma parsarea proprietatii, nu executarea unui callback si nici
accesul la memoria nativa. Nu a fost demonstrat un lant de la acest camp la
incarcarea unui DLL sau la inlocuirea arbitrara a unei functii C++.
Pista ramane partial verificata; nu este clasificata drept functionalitate
absenta doar fiindca anumite obiecte de catalog nu au referinte directe.

Proba selectiva: `focused-0x141cc6310.c`, sectiunea procedurii `0x1422c01e0`.

Verificarea suplimentara a tipurilor a identificat definitia prin RTTI drept
`CButtonType`. Pentru `luafunction_buttonclick` (`0x143`), lantul de parsere
`0x1422c01e0` -> `0x14235b570` -> `0x1425416b0` -> `0x142544af0` ajunge la calea
`Unexpected token`. Aceasta constatare este limitata la lantul `CButtonType`
inspectat, nu la orice clasa GUI posibila.

Fabrica creeaza `CButtonStandard` sau `CCallbackButtonStandard`, pastrand un
pointer la definitie in obiectul runtime la offsetul `0x100`. Caile de eveniment
inspectate folosesc observatori nativi. Nu s-a stabilit un consumator de executie
al sirului `CButtonType+0x1f0`. Accesari la `runtime+0x1f0` care pareau promitatoare
s-au dovedit a fi alt camp, folosit pentru un handle de eveniment; nu au fost
tratate ca probe de executie Lua.

Raportul selectiv complet, cu limitele cautarii si artefactele de decompilare:
`C:\Users\mihai\.codex\analysis\hoi4-workshop-engine-20261109\gui-lua-bindings-findings-20261109.json`.

### Moduri suplimentare si pachetul CAPIE livrat de Steam

Cu autorizarea utilizatorului de a folosi si alte abonari, CAPIE a fost observat
ca abonat in clientul Steam si pachetul descarcat a fost inspectat local.
Nu s-a executat un installer sau o componenta nativa CAPIE. Testul ulterior al
jocului descris mai jos nu a activat CAPIE.

Itemul Workshop `3819929471`, versiunea descriptorului `1.1.2`, contine exact:

| Fisier | Octeti | SHA-256 |
| --- | ---: | --- |
| `descriptor.mod` | 130 | `71137892adf665eb3a67c7112a933bda54d648409864f2f972eaaa3db598f123` |
| `thumbnail.png` | 139745 | `d4bb22a36f572d354e49dcfb54dcf03f03bf844517f261ff2b9bc2d94cfd66fe` |

Nu exista scripturi, DLL-uri sau un installer in acest pachet livrat.
Descrierea Workshop actuala spune ca itemul este comutatorul pentru launcherul
CAPIE instalat separat. Release-ul oficial CAPIE `v1.6.1` exista si vizeaza exact
buildul local 1.19.4.2, inclusiv acelasi SHA-256 al executabilului, dar bootstrap-ul
nativ este distribuit separat. Compatibilitatea versiunii nu elimina pasul de
instalare. Pachetul descarcat confirma concret distinctia dintre comutator si
componenta nativa.

Unele pagini README/site CAPIE sunt vechi si afirma ca nu exista release sau
Workshop item. Aceste afirmatii sunt contrazise de release-ul `v1.6.1`, pagina
Workshop actuala si pachetul descarcat. Concluzia nu se bazeaza pe aceste pagini
vechi; cerinta bootstrap-ului separat este confirmata de sursele curente.

Au mai fost verificate sursele proiectelor green1052/HOI4ModLoader,
Builder-HD/HoI4Mod-Loader, Razzyk/hoi4-injector, MyresMkG/HOI4-Mod-Injector si ale
altor prototipuri concrete. Niciun proiect verificat nu documenteaza un bootstrap
nativ exclusiv prin abonare Workshop; sunt necesare fisiere in directorul
jocului, un injector sau optiuni de lansare configurate de un installer.

Probe suplimentare, in afara directorului Workshop al TFR:

- `capie-workshop-package-evidence.json`: inventarul pachetului si hash-urile.
- `native-mod-research.md`: surse primare si cerintele fiecarui proiect verificat.

La verificare, `dlc_load.json` nu includea CAPIE in lista `enabled_mods`. Abonarea
a ramas prezenta; aceasta investigatie nu a activat itemul si nu a instalat
launcherul lui. Inventarul local si celelalte rezultate nu constituie un audit
al tuturor modurilor publice, private sau indisponibile.

### Compilare C in scriptul jocului

Autorul modului DOOM documenteaza explicit traseul C -> WASM -> script pe pagina
Workshop. Este o alternativa pentru implementarea unor algoritmi proprii prin
scripturi distribuite ca mod. Nu demonstreaza acces la codul masinii gazda sau
interceptarea functiilor motorului HOI4. Nu a fost prezentata ca satisfacand
cerinta de modificare arbitrara a codului nativ.

## Test real de pornire automata

S-a creat un mod local separat, `TFR Automatic Lua Capability Probe`, in afara
directorului TFR. Contine un script in `common/defines`, descriptorul si o copie
a `script/autoexec.lua` original cu proba adaugata la final. Proba inventariaza
tipurile globalelor si bibliotecilor, scrie markeri prin `print` si solicita
`package.loadlib` pentru un nume de DLL deliberat inexistent. Nu contine DLL,
payload nativ, modificari de defines sau operatii asupra salvarilor.

Jocul existent a fost pornit o singura data, cu un profil temporar separat:
`C:\Users\mihai\AppData\Local\Temp\hoi4probe20261109`. Argumentul `-userdir=...`
si capturarea stdout/stderr sunt instrumente ale experimentului, nu o solutie
propusa jucatorului. Nu a fost publicat un item Workshop; acest test local nu
reprezinta validarea unui flux complet Subscribe -> Play pentru un patch nativ.

Rezultate observate:

- Markerii `TFR_AUTOSTART_PROBE BEGIN` si `END` confirma ca scriptul din defines
  a rulat automat, inaintea oricarei intrari UI in joc. S-a observat o singura
  inventariere completa. `game.log` raporteaza `4489 defines loaded`.
- `_VERSION` este `Lua 5.1`; `io`, `os` si globala `luabind` sunt `nil`.
  Sunt prezente bibliotecile `debug`, `package`, `string`, `table`, `math`,
  `coroutine`, functiile standard Lua si `class`/`property`/`super`.
  Tabelele de configurare sunt `NDefines`, `NDefines_CareerProfile`,
  `NDefines_Graphics`. Inventarul global nu a aratat functii de patch nativ.
- Apelul protejat `package.loadlib` a returnat `nil`, o valoare de eroare de tip
  userdata si categoria `open`. Un fisier inexistent ar esua si cu un loader
  functional, deci acest rezultat singur nu dovedeste dezactivarea loaderului.
  Concluzia despre backendul dezactivat provine din analiza statica de mai sus.
- Nu a aparut niciun marker `TFR_AUTOEXEC_PROBE` pana la meniul principal si
  inchiderea jocului. Comentariul din fisierul original care promite executie
  la pornire nu este astfel confirmat pentru acest traseu/build. Nu s-au testat
  toate modurile de joc sau contexte posibile.
- Jocul a ajuns la meniul principal; `setup.log` raporteaza pornire de 72796 ms.
  A fost inchis prin `Quit`, fara incarcarea sau pornirea unei partide.
- SHA-256 pentru executabil, `settings.txt` si `dlc_load.json` din profilul normal
  a ramas identic cu valorile inregistrate inaintea lansarii. Procesul de test
  si fereastra jocului nu mai existau dupa inchidere.

Instalatia locala contine deja componente Steam native terte si a afisat un
avertisment de verificare a proprietatii DLC. Proba verifica incarcarea Lua in
aceasta instalatie, nu portabilitatea unui patch pe o instalatie Steam curata.

Artefacte in `C:\Users\mihai\.codex\analysis\hoi4-workshop-engine-20261109`:
`startup-probe/`, `run-startup-probe.py`, `startup-probe-manifest.json`,
`startup-probe-result.json`, `startup-probe-stdout.txt`, `startup-probe-stderr.txt`
si analiza statica selectiva din `startup-lua-probe/`. Harness-ul Python este
exclusiv pentru capturarea experimentului; jucatorului nu i se propune rularea lui.

## Proba suplimentara: registrul si metatabelele Lua

O a doua pornire, cu un alt mod minim si profil temporar separat
`C:\Users\mihai\AppData\Local\Temp\hoi4registryprobe20261109`, a inventariat
registrul Lua, metatabelele accesibile si metadatele functiilor. Scriptul nu a
invocat functiile descoperite, nu a modificat obiectele si nu a instalat hooks.

Proba a raportat `ok=true`, markeri BEGIN/END, 10 intrari in registrul de nivel
superior si 56 identificatori de obiect. Nu s-au atins limitele configurate de
adancime, numar de obiecte sau intrari. Tabelele standard si NDefines au fost
recunoscute si omise din parcurgerea recursiva.

Intrari observate: `_LOADLIB`, `_LOADED`, `__luabind_class_map`,
`__luabind_cast_graph`, `__luabind_class_id_map`, `__luabind_classes`, trei
metatabele numerotate si o pereche cu cheie userdata. Metatabelele contin
operatori/interfete Lua/luabind (`__index`, `__newindex`, `__call`, `__gc` etc.).
Obiectele userdata cu numele interne luabind expun prin metatabela numai `__gc`.
`_LOADED` contine numai cele sapte module standard deja observate la primul test.
Nu s-a identificat o metoda de gameplay sau o interfata de patch nativ.

Aceasta observatie nu arata continutul brut al obiectelor userdata si nu dovedeste
ca structurile native sunt goale. In aceasta proba, mediile functiilor/userdata
nu au fost parcurse recursiv; proba ulterioara de mai jos acopera aceasta lacuna.
Pentru unele functii C, metadatele raporteaza doua upvalues,
dar `debug.getupvalue` nu le returneaza. Comportamentul este compatibil cu
[implementarea de referinta Lua 5.1.5, `auxupvalue`](https://www.lua.org/source/5.1/ldblib.c.html),
care exclude upvalues ale functiilor C; comparatia nu identifica exact sursa
originala a jocului. Prezenta functiilor C pentru mecanismele Lua nu demonstreaza
acces la orice functie C++ din motor.

Jocul a ajuns la meniul principal (`Startup time: 31286ms`) si a fost inchis prin
Quit. Hash-urile executabilului, setarilor normale si listei normale de moduri au
ramas identice. Procesul si fereastra probei au disparut dupa inchidere.
Artefacte suplimentare in directorul de analiza: `registry-probe/`,
`run-registry-probe.py`, `registry-probe-manifest.json`, `registry-probe-result.json`,
`registry-probe-inventory.txt` si capturile stdout/stderr. Si acest experiment
este local, nu un flux Subscribe -> Play validat pentru un patch nativ.

## Inventar extins al mecanismelor normale de extensie

Utilizatorul a cerut continuarea auditului incarcatoarelor, apoi a raportat un
mesaj de limitare a continutului din platforma si a cerut alta abordare.
Continuarea a fost limitata la inventare pasive si mecanisme normale de extensie;
nu s-a incercat ocolirea limitarii, exploatarea unui parser sau construirea unui
payload nativ.

Inventarul extins al executabilului a parcurs instructiunile din sectiunile
executabile si a clasificat referinte RIP-relative la importuri, inclusiv
posibile citiri de pointeri in registre. Au fost identificate 536 importuri;
directorul PE de delay imports este absent. Pentru `LoadLibraryA/W/ExW`,
`GetProcAddress` si `SetCurrentDirectoryW`, nu s-au gasit referinte suplimentare
fata de inventarul initial: 31 apeluri de incarcare de biblioteci in total,
90 referinte `GetProcAddress` si doua `SetCurrentDirectoryW`.

Aceasta este extinderea inventarului de referinte, nu o dovada ca toate caile
indirecte sau argumentele fiecarei functii au fost inchise. Disasamblarea liniara
poate decoda date ca instructiuni sau pierde cod; au fost raportati 9902 octeti
sariti de decodor. Nume calculate, pointeri copiati prin memorie, implementari
custom si unii apelanti ai wrapperelor SDL raman in afara acoperirii complete.
Nu s-a continuat aceasta directie prin abuzarea incarcatoarelor normale.

Inventarul middleware a adaugat analiza DLL-ului PDXSDK, SHA-256
`933e92b20ad5193d05249507355a732b90f4769470d495520035c5a36558fcdf`.
Nu are importuri `LoadLibrary`/`LdrLoadDll` sau delay imports. Cele trei apeluri
directe `GetProcAddress` observate rezolva numai API-uri de compatibilitate
Windows: `CreateSymbolicLinkW`, `SleepConditionVariableCS` si
`WakeAllConditionVariable`. Numele exportului `SetModsRootDirectory` este un
setter tipizat de configurare, nu dovada unui incarcator de extensii native.

SDL are o extensie nativa normala controlata de variabila de mediu
`SDL_DYNAMIC_API`; nu s-a gasit o legatura de la resursele montate ale modului
catre aceasta configurare. PhysicsFS ofera inregistrarea unor callback-uri
native furnizate de aplicatie; montarea unui director de date nu inregistreaza
astfel de callback-uri. Nu s-a identificat un bootstrap nativ din Workshop.

Artefacte suplimentare in directorul de analiza:
`native_loader_audit.py`, `native-loader-extended-audit.json`,
`native-loader-direct-edges.json`, `middleware-native-loader-audit.md`,
`middleware-native-loader-audit.json` si inventarele/slice-urile aferente.
Nu s-a pornit jocul pentru acest pas; nu s-a modificat sau incarcat un DLL.

## Proba suplimentara: mediile functiilor si obiectelor Lua

La cererea utilizatorului, lacuna mediilor asociate a fost verificata printr-o
a treia pornire, cu mod local separat si profilul temporar
`C:\Users\mihai\AppData\Local\Temp\hoi4environmentprobe20261109`.
Scriptul foloseste citiri `debug.getfenv`, registrul, metatabelele si metadatele
functiilor; nu invoca functiile descoperite si nu schimba mediile.

Rezultate observate: markeri BEGIN/END, `ok=true`, zero erori si zero limite
atinse, 167 identificatori de obiect si 145 citiri de mediu. Au fost inventariate
139 functii raportate de Lua drept C si sase valori userdata.

- 137 medii sunt identice cu `_G`.
- Sase functii au ca mediu exact tabelul `package`, identificat prin acelasi ID
  de obiect ca `_G.package` si `registry._LOADED.package`: `require`, `module`
  si `package.loaders[1..4]`. Tabelul era deja cunoscut si a fost parcurs.
- Doua valori userdata din perechea cu cheie userdata nu returneaza mediu
  (`nil`). Nu s-a dedus continutul lor nativ din aceasta observatie.

Nu a aparut un tabel de mediu nou sau o functie suplimentara de acces la motor.
Proba acopera obiectele accesibile in acest context automat de defines, nu
orice context posibil din joc. Tabelele NDefines de configurare au fost omise
intentionat; continutul brut al userdata si datele private ale functiilor C
nu au fost citite sau executate.

Jocul a ajuns la meniul principal (`Startup time: 69429ms`) si a fost inchis prin
Quit, fara pornirea/incarcarea unei partide. Hash-urile executabilului, setarilor
normale si listei normale de moduri au ramas identice. Procesul si fereastra
probei au disparut dupa inchidere.

Artefacte in directorul de analiza: `environment-probe/`,
`run-environment-probe.py`, `environment-probe-manifest.json`,
`environment-probe-result.json`, `environment-probe-inventory.txt` si stdout/stderr.
Nici aceasta proba locala nu constituie o validare Subscribe -> Play a unui patch
nativ.

## SDL: argumentele si apelantii incarcatorului

A doua lacuna ceruta de utilizator a fost verificata prin analiza statica
selectiva, fara pornirea incarcatorului SDL, schimbarea mediului sau plasarea
vreunui DLL. Rutina canonica `0x142155160..0x142155223` reuneste trei fragmente
chained-unwind, converteste numele UTF-8 in UTF-16 si apeleaza `LoadLibraryW`.
Nu foloseste VFS-ul modurilor. Rutina de simboluri `0x1421550f0..0x142155156`
apeleaza `GetProcAddress`.

Au fost clasificate 19 apeluri directe catre incarcator, in 11 functii canonice.
Sursele observate ale numelor sunt:

- Literale Windows: USER32, SHCORE, D3D9, DXGI, D3D11, IMM32 si DSOUND.
- Pentru interfata IME: rezultatul API-ului Windows `ImmGetIMEFileNameA`.
- OpenGL/Vulkan: parametru explicit al API-ului nativ, variabila de mediu SDL
  corespunzatoare sau numele implicit OPENGL32/vulkan-1.
- EGL/GLES: parametru nativ, variabile de mediu SDL, lista interna de hints SDL
  si valori implicite pentru bibliotecile grafice/compilator.

Cititorul concret `0x1421671f0..0x142167281` apeleaza `GetEnvironmentVariableA`.
Getterul de hints `0x142148180..0x1421481fa` consulta mediul si lista interna
SDL. Nu s-a identificat aici un parser de fisiere sau o sursa din resursele unui
mod. Provenienta tuturor scrierilor programatice in lista de hints nu a fost
urmarita exhaustiv.

Cele doua apeluri directe cunoscute ale API-ului GL si cele doua ale API-ului
Vulkan transmit `NULL` drept cale explicita. Cazurile interne EGL/GLES urmarite
transmit de asemenea `NULL`. Au fost rezolvate sloturile de dispatch si thunk-urile
pentru LoadObject, LoadFunction, GL_LoadLibrary si Vulkan_LoadLibrary; inventarul
salvat nu contine apeluri/salturi directe catre cele patru thunk-uri.

Acest rezultat inchide sursa argumentelor pentru apelurile directe identificate.
Nu inchide toate invocarile indirecte prin tabelele driverului video, toti
apelantii care ar lua o adresa dinamic sau toate originile scrierilor de hints.
Analiza nu demonstreaza o punte normala Workshop -> nume de biblioteca nativa si
nu constituie o dovada universala a absentei oricarei cai indirecte.

Raportul separat `sdl-loader-gap-findings.md` si JSON-ul omonim pastreaza toate
adresele, intervalele semi-deschise ale functiilor, sursele argumentelor si
hash-urile a 41 de fisiere de probe. Artefactele selective sunt in subdirectorul
`sdl-loader-gap/` al directorului de analiza. Acestea sunt rezultate Ghidra/PE/
Capstone, nu o observatie de executie a loaderului. Procesele Ghidra s-au incheiat
si proiectul a fost eliberat.

## Continuarea configurarii SDL: resursele text livrate

La o noua cerere de continuare s-au verificat numele concrete pentru selectarea
bibliotecilor SDL si posibilele apeluri textuale SetHint in resursele instalate.
Scanarea read-only cu ripgrep a acoperit 8415 fisiere text selectate din joc si
28676 din directoarele Workshop HOI4 instalate. Au fost incluse extensiile
txt/json/lua/gui/gfx/asset/mod/ini/yml/yaml, excluzand directoarele docs/tools/.git
si fisierele de licenta.

Nu s-au gasit aparitii textuale ale numelor SDL_DYNAMIC_API,
SDL_OPENGL_LIBRARY, SDL_VULKAN_LIBRARY, SDL_VIDEO_GL_DRIVER,
SDL_VIDEO_EGL_DRIVER, SDL_VIDEO_WIN_D3DCOMPILER sau SetHint/SetHintWithPriority
in aceasta selectie. Absenta unui literal nu exclude un nume construit dinamic,
un alt parser sau alte extensii/directoare; nu este o dovada generala de absenta.

`settings-layout.json` livrat contine un furnizor `sdl` pentru displayMode,
displayIndex, vsync, rezolutii si refreshRate. Lista rendererului contine
dx11/dx9_compat/opengl. Aceste etichete de configurare nu demonstreaza o interfata
pentru orice hint SDL sau un parametru de cale catre o biblioteca nativa.
Fisierul are SHA-256
`beaa3fe51114f8b1f4f6d7b181625fc145493a9016aa007f320759c469c07081`.

Procedura si rezultatul complet sunt in `resource_hint_config_audit.py` si
`resource-hint-config-audit.json` din directorul de analiza. Nu s-a pornit jocul
si nu s-au modificat configuratii pentru aceasta scanare.

## SDL: provenienta scrierilor de hints

Continuarea a urmarit separat toti utilizatorii obisnuiti identificati ai listei
de hints SDL de la `0x1434fddb8`. Numele API de mai jos sunt identificari prin
comportament, nu simboluri originale recuperate.

Rutinele identificate sunt AddHintCallback (`0x142147e40`), ClearHints
(`0x142148010`), DelHintCallback (`0x142148090`), SetHintWithPriority
(`0x142148240`) si SetHint (`0x142148390`), pe langa getterul deja verificat.
Inregistrarea unui callback poate crea un nod cu nume, dar valoarea noului nod
este NULL; eliminarea callback-urilor si curatarea listei nu furnizeaza valori
pentru nume de biblioteci. Setterele accepta siruri din API-ul nativ si nu
parseaza fisiere sau cai VFS ale modurilor.

In inventarul cunoscut, SetHintWithPriority are zero apeluri directe, iar
SetHint are doua. Acestea sunt implementari separate, nu un wrapper SetHint
care ar introduce un salt direct omis catre SetHintWithPriority. Cele doua
apeluri SetHint sunt in constructia rendererului `0x1421a5090`: cheia este
literalul SDL_RENDER_VSYNC; valorile sunt "1"/"0", alese dintr-un bit al unui
argument nativ, apoi sirul gol dupa crearea ferestrei. Nu sunt nume de fisiere.

Cele 25 de apeluri directe AddHintCallback identificate folosesc nume fixe de
optiuni pentru fereastra, evenimente, input, timer si controllere. Un apel
parcurge un tabel HID cu noua intrari initializate in imagine. Inregistrarea
acestora furnizeaza notificari, nu o valoare noua a hintului.

Pentru fiecare cheie concreta de selectie a bibliotecilor, referinta obisnuita
gasita este citirea deja verificata in loader; nu s-a gasit o scriere directa
a acestor chei. Patru chei citesc direct mediul procesului, fara lista SDL de
hints. SDL_VIDEO_WIN_D3DCOMPILER foloseste getterul care combina mediul si hints.
Au fost rezolvate cinci perechi slot/thunk pentru API-urile de mutare a listei;
inventarul salvat nu contine apeluri/salturi directe catre aceste thunk-uri.

Nu s-a identificat un traseu normal de la o resursa de mod la perechea nume/
valoare a unui setter. Raman limitele apelurilor indirecte, acceselor prin baze
de tabele, pointerilor copiati si callback-urilor care nu au fost auditate
exhaustiv. Rezultatul nu este o demonstratie a absentei tuturor apelurilor
native posibile.

Raportul `sdl-hint-writer-findings.md`, JSON-ul omonim si subdirectorul
`sdl-hint-writers/` pastreaza intervalele, apelantii, cheile, dovezile si
hash-urile. Analiza a fost exclusiv statica; nu s-a pornit jocul, nu s-au
schimbat variabile de mediu si nu s-au incarcat sau plasat DLL-uri. Proiectul
Ghidra a fost eliberat la final.

## Piste publice si intrari documentate suplimentare

O noua cautare a exclus explicit proiectele deja verificate, pentru a nu
prezenta aceleasi loadere sub alte nume drept piste noi. Nu a aparut un candidat
nou care sa documenteze bootstrap nativ exclusiv prin Workshop.

Proiectul nou [a212075116/hoi4plugins](https://github.com/a212075116/hoi4plugins/blob/main/README.md)
ofera extensii native de efecte/trigger/numerice, dar documenteaza un carrier
DLL si instalare/depunere separata in directorul jocului, pentru 1.19.3.
Nu indeplineste restrictia. Alte rezultate noi sunt aplicatii de autorare sau
control externe: HOI4 Live Tools, editorul de harta, HPL/HCL si alte generatoare.
Pluginurile acestor aplicatii nu sunt un API de pluginuri al jocului.

[JevAI](https://github.com/zwh20081/hoi4-jevai) livreaza continut si prin Workshop,
dar README cere pornirea/instalarea runnerului sau din directorul modului.
[saslifat-gif/hoi4-mcp](https://github.com/saslifat-gif/hoi4-mcp) cere dependente,
instalatoare/launcher si atasarea unor module native. Niciuna dintre aceste
cerinte nu a fost executata in investigatie si niciun proiect nu este propus
drept solutie pentru abonare + Play.

Agentul de cercetare a verificat si inregistrarile oficiale Steam pentru
patch-urile 1.19.4/1.19.2/1.19.1. Adaugirile Modding identificate sunt capabilitati
fixe de script/date; nu anunta un bootstrap de pluginuri native sau inlocuire
arbitrara a functiilor motorului. Absenta unui anunt nu este dovada de absenta
a unei implementari nedocumentate. Sursele primare, identitatile blob-urilor si
inregistrarile oficiale sunt retinute in `new-public-leads-20261109.md`, JSON-ul
omonim si `new-public-leads-official-news.json`.

Separat, documentatia generata livrata in instalatia curenta a fost inventariata:
564 sectiuni de efecte, 432 sectiuni de comenzi consola si 84 nume in lista
on_actions. Lista on_actions declara explicit ca a fost actualizata 2024-11,
deci nu este tratata drept catalog complet al buildului actual.

Comanda `run` este documentata ca ruland un fisier cu o lista de comenzi.
Aceasta descriere scurta nu stabileste sintaxa fisierului, executie de comenzi
OS, incarcare de DLL sau declansare automata dintr-un mod. `eval_effect` si
`eval_trigger` sunt intrari de consola. Nu s-a identificat prin aceste documente
o punte automata mod -> consola sau o interfata pentru apeluri native arbitrare.

Efectele `set_rule`, `set_relation_rule`, `add_relation_rule_override` si
callback-urile on_actions sunt puncte normale de control al comportamentului.
Pot constitui piste pentru o corectie specifica permisa de API-ul de script;
nu demonstreaza metoda generala ceruta de inlocuire a codului C++.
Nu s-a schimbat obiectivul investigatiei si nu s-a modificat gameplay-ul.

Inventarul local, sectiunile exacte si hash-urile surselor se afla in
`documented_entrypoint_audit.py` si `documented-entrypoint-audit.json`.
Acest pas nu a pornit jocul, nu a instalat componente si nu a publicat/subscris
itemuri Workshop.

## Rezultat pozitiv delimitat: validare nativa prin trigger scriptat

Ramura nativ -> script a fost investigata separat de Lua/SDL. Intersectia dintre
2510 nume de script din 107 fisiere livrate si literalele executabilului a produs
13 candidati. Existenta unui nume in ambele parti nu a fost tratata drept
dovada de executie. Consumatorul verificat este CGuaranteeAction pentru
`DIPLOMACY_GUARANTEE_ENABLE_TRIGGER_OVERRIDES_GAME_TRIGGER`.

La incarcarea normala a datelor, baza de scripted triggers compileaza corpurile
si rezolva numele intr-un pointer de template memorat. Rutina nativa construieste
ROOT/FROM si apeleaza evaluatorul triggerului la verificarea eligibilitatii.
Booleanul returnat controleaza ramificatii care omit verificarea ideologiei si
o verificare de tensiune. Triggerul normal de enable si celelalte cerinte
politice/relatii/putere/razboi raman active.

Proba comparativa a folosit doua moduri locale fara componente native, cu
suprascrierea aceluiasi fisier virtual, pastrand toate celelalte definitii.
Singura diferenta functionala a fisierului de triggers este corpul callback-ului:
`always = no` versus `always = yes`. Setup-ul identic din on_startup a pregatit
doar campaniile temporare: Germania -> Belgia, 1936-01-01 ora12, pauza, 1000PP
si100% tensiune.

- Referinta: tooltipul garantiei arata motivul rosu `Can only guarantee Fascist nations.`
- Override: acel motiv dispare; raman descrierea si costul15.
- In ambele cazuri erau zero natiuni garantate. Nu s-a trimis o garantie si nu
  s-au testat comanda finala sau executia/validarea multiplayer.

Analiza statica demonstreaza ca este o ramificatie a validarii native cu iesire
de tooltip optionala; observatia runtime demonstreaza diferenta afisata de
eligibilitate. Aceste probe nu sunt confundate cu observarea unei mutatii
efective a garantiei sau cu un hook nativ general.

Definitiile se incarca la pornirea normala a datelor. Callback-ul demonstrat
ruleaza ulterior, la evaluarea actiunii in campanie, fara buton de activare a
modificarii. Nu s-a demonstrat executia lui numai prin ajungerea la meniul
principal. Modurile de proba nu au fost publicate/subscrise prin Workshop si
instalatia locala contine componente Steam native terte preexistente.

Ambele campanii au fost inchise fara salvare manuala; procesele si ferestrele
lor au disparut. Executabilul, setarile normale si lista normala de moduri au
ramas identice dupa fiecare rulare. Nu au fost modificate fisierele de gameplay
TFR. Harness-ul este numai instrumentul laboratorului pentru izolare/lansare;
nu este continutul modului si nu este cerut jucatorului.

Probe: `native-script-callback-findings.md`/JSON si66 fisiere hash-uite,
`native-script-callback-candidates.json`, `callback-baseline-probe/`,
`callback-override-probe/`, manifestele/observatiile UI aferente si
`callback-comparison-result.json`, toate in directorul privat de analiza.
Documentul separat din `docs/engine-script-callback-proof.md` explica reproducerea
si distinctia dintre punct de extensie expus si inlocuire arbitrara de cod.

## Acoperire si limite

Pentru cerinta ulterioara de10x atac prin schimbarea formulei native, nu a fost
identificat un override si nu s-a realizat un test cu formula inlocuita.
Modificatorii si defines au fost exclusi explicit de utilizator ca solutie.
Verificarile si limitele sunt in
[evaluarea formulei de atac](<C:/Program Files (x86)/Steam/steamapps/workshop/content/394360/3513811852/docs/attack-formula-assessment.md>).

Scanarea ASCII a executabilului a identificat `common/defines/`, `script/`,
`luafunction_buttonclick`, `luaClick`, `loadlib`, `luaopen_%s` si identificatori
Lua 5.1/luabind. Acestea sunt siruri de octeti din artefact, nu observatii de
executie. Biblioteci compilate in executabil pot ramane neexpuse scripturilor;
un identificator de interfata poate apartine unei functionalitati nefolosite.

- Distribuirea prin Workshop si cerintele de instalare ale loaderelor: verificate in surse primare.
- Calea standard Lua pentru biblioteci native si mediul defines: verificata static in buildul local.
- Executia automata din defines si inventarul globalelor: observate intr-o pornire reala, intr-un profil separat; proba autoexec nu a fost observata in acest traseu.
- Registrul, metatabelele accesibile si metadatele functiilor: inventariate intr-o a doua pornire; mediile asociate au fost citite recursiv intr-o a treia pornire. Nu a fost identificata o interfata pentru patch nativ. Continutul brut al userdata ramane neexaminat.
- Incarcatorul SDL, cei 11 apelanti directi identificati, argumentele GL/Vulkan cunoscute si aliasurile de dispatch au fost analizate static. Nu s-a gasit o punte din resurse de mod; toate invocarile indirecte si toate originile scrierilor de hints nu sunt rezolvate exhaustiv.
- Scrierile directe cunoscute de hints SDL au fost clasificate intr-o continuare separata: cele doua valori scrise folosesc numai SDL_RENDER_VSYNC si valori fixe. Nu s-a identificat o scriere directa a cheilor de selectie a bibliotecilor sau o sursa din resurse de mod. Limitele apelurilor indirecte raman explicite.
- Un callback de eligibilitate pentru garantii a fost urmarit din nativ pana la corpul de script si testat comparativ in doua campanii locale. Schimbarea motivului de eligibilitate este confirmata; comanda finala, multiplayer si inlocuirea arbitrara a functiilor native nu sunt demonstrate.
- Inregistrarea cheilor GUI, tipul `CButtonType` si parsarea `luaClick`: verificate; calea `luafunction_buttonclick` este respinsa in lantul inspectat; consumatorul de executie `luaClick` ramane nestabilit.
- Pachetul CAPIE livrat efectiv prin Workshop: inventariat si hash-uit; bootstrap-ul separat este confirmat de sursele curente.
- Toate caile Win32 de incarcare de biblioteci, toate parserele si toate vulnerabilitatile posibile ale motorului: nu au fost auditate exhaustiv.
- Compatibilitatea cu alte builduri, Linux/macOS si functionarea multiplayer: nu au fost testate.

Jocul a fost pornit pentru experimentul izolat de mai sus. Executabilul si
fisierele de gameplay ale TFR nu au fost modificate. SHA-256 al executabilului
original a fost reverificat dupa inchidere si a ramas identic.

## Surse primare

- [Valve: Steam Workshop Implementation Guide](https://partner.steamgames.com/doc/features/workshop/implementation)
- [Valve: Creating and using InstallScripts](https://partner.steamgames.com/doc/sdk/installscripts?l=english)
- [Microsoft: Dynamic-link library search order](https://learn.microsoft.com/en-gb/windows/win32/dlls/dynamic-link-library-search-order)
- [Paradox: Patch 1.8.2, Security Fix, 7 februarie 2020](https://store.steampowered.com/news/posts/?appids=394360&enddate=1582122553&feed=steam_community_announcements)
- [Builder-HD: HoI4Mod-Loader, instalare](https://github.com/Builder-HD/HoI4Mod-Loader#install)
- [green1052: HOI4ModLoader, instalare](https://github.com/green1052/HOI4ModLoader#installation)
- [ari-20: hoi4_lua](https://github.com/ari-20/hoi4_lua)
- [Lua: implementarea de referinta 5.1, loadlib.c](https://www.lua.org/source/5.1/loadlib.c.html)
- [Lua: implementarea de referinta 5.1, linit.c](https://www.lua.org/source/5.1/linit.c.html)
- [FreeImage: codul bibliotecii din distributia WinMerge, Plugin.cpp](https://github.com/WinMerge/freeimage/blob/master/Source/FreeImage/Plugin.cpp)
- [Microsoft: x64 exception handling si chained unwind](https://learn.microsoft.com/en-us/cpp/build/exception-handling-x64?view=msvc-170)
- [Yard1: pagina Workshop DOOM, descrierea traseului C -> WASM -> script](https://steamcommunity.com/sharedfiles/filedetails/?id=3800765971)
- [Yard1: sursa compilarii Wasm din ramura hoi4](https://github.com/Yard1/doomgeneric/blob/hoi4/doomgeneric/Makefile.hoi4-wasm)
- [CAPIE: itemul Workshop verificat](https://steamcommunity.com/sharedfiles/filedetails/?id=3819929471)
- [CAPIE: release-ul oficial v1.6.1](https://github.com/capie-mods/capie/releases/tag/v1.6.1)
- [CAPIE: descrierea Workshop, sursa publicata](https://github.com/capie-mods/capie/blob/0350d1f6cd662d75936f8cce43afedbcc6b81544/docs/assets/promo/workshop/capie.bbcode)
- [CAPIE: decizia de separare a distributiei Workshop/native](https://github.com/capie-mods/capie/blob/0350d1f6cd662d75936f8cce43afedbcc6b81544/docs/adr/0002-distribution-model.md)
