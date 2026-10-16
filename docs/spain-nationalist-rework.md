# Rework: Spania naționalistă

Implementarea cuprinde 115 de focusuri după războiul civil: 14 de diplomație,
12 de reconstrucție, 32 economice, 32 militare, 5 aeriene și 20 navale.
Numele și tooltipurile sunt localizate în engleză. Descrierile focusurilor sunt goale.

Cele 115 de focusuri noi sunt vizibile permanent. Cele două alegeri de rol cer
ruta lui Franco și încheierea războiului civil; descendenții moștenesc această
restricție prin prerequisite, fără repetarea ei la fiecare focus. Cele 37 de focusuri vechi
înlocuite sunt ascunse permanent, păstrând ID-urile pentru compatibilitate cu
salvările și referințele vechi. Cele 29 de focusuri originale de război civil
sunt păstrate integral. Opt intrări ale rutelor alternative deja blocate au
acum `always = no`, în locul condiției dependente de un focus sovietic.
Celelalte 210 definiții păstrează conținutul original.

## Alegeri permanente

- Arsenal of the Axis / Our Place in the New Order (sprijin prin voluntari /
  participare directă la război).
- Specializare economică / specializare militară. Primele 12 focusuri ale
  fiecărei ramuri rămân comune.
- Escort Fleet Doctrine / Surface Fleet Doctrine.

Arsenal of the Axis păstrează Spania în afara facțiunilor; nu poate declara sau accepta
războaie externe prin diplomație. Sunt blocate și garanțiile noi, care ar putea
provoca intrarea automată într-un război. Războaiele defensive rămân posibile.
Nu primește capacitate suplimentară de voluntari și nu schimbă alocările SCW.

Our Place in the New Order permite solicitarea aderării Germaniei, care poate accepta sau refuza.
Un refuz permite o nouă cerere prin decizie. Bonusurile de război din D12 și
D13 cer un adversar major comun cu Germania, în aceeași facțiune; NPR nu califică.
Vizibilitatea pingurilor în multiplayer trebuie verificată în joc.

## Portugalia

Din 1939, ruta de sprijin primește drepturi asupra tuturor resurselor NPR,
iar infrastructura statelor portugheze devine 5/5. Relocarea mută fabricile
civile, militare și șantierele existente efectiv, cu sloturi, fără anexe teritoriale.
Clădirile sunt eliminate din NPR numai după plasarea lor în Spania.
Registrul transferului persistă în salvare; transferurile fără destinație
eligibilă sunt reluate zilnic. Creșterea industrială scriptată se oprește numai
pentru NPR, la începerea relocării.

Ruta de participare directă păstrează atacul, anexarea la capitulare și integrarea
celor cinci state portugheze. Anexarea automată este condiționată de această alegere.

## Modificatori și salvări

Spanish Economy, Spanish Armed Forces, Spanish Air Force și Spanish Navy sunt
modificatori dinamici. Bonusurile economice vechi relevante sunt importate o
singură dată și creditate față de recompensele echivalente ale arborelui nou.
Fabricile vechi marcate prin state flags beneficiază de aceeași protecție.
Sloturile de cercetare și legile mai avansate nu sunt retrogradate.

Recuperarea economică păstrează treapta existentă. Expirarea folosește data
flagului existent `scw_over` și durata originală de 2190 de zile din
`events/LAR_NewsEvents.txt`; alegerea târzie a modului nu repornește perioada.
Focusurile de reconstrucție pot elimina penalizările mai devreme.

National Recovery este componenta pozitivă a aceluiași modifier economic.
P01 începe profilul 1, P04 avansează la profilul 2, iar P05 la profilul 3,
continuând bonusurile originale de stabilitate săptămânală, consumer goods și
construcție de infrastructură. Programul durează 1825 de zile, fără resetarea
termenului la trecerea între etape. La migrarea unei salvări, data vechiului
state flag este folosită dacă există. Toate cele șapte variante vechi pot fi
importate; variantele rutelor alternative nu sunt deblocate în arborele nou.
Reducerea de consumer goods a programului și bonusurile permanente echivalente
folosesc beneficiul mai puternic, fără dublare. Celelalte efecte distincte se
păstrează împreună. Penalizările includ și efectele originale asupra AI și
pragului de tensiune pentru facțiuni. Regula de refuz al chemării la război se
păstrează cât timp este activă recuperarea.

Nicio ramură nouă nu își schimbă vizibilitatea la încheierea războiului civil
sau la alegerea modului Spaniei. Datele, rolurile și specializările sunt
verificate prin condiții și legături, fără ascunderea arborelui. Ramurile noi
sunt așezate în dreapta ramurii originale de război civil, fără suprapuneri.

## Verificare

Schema și bugetele aprobate sunt în `tools/spain_focus_plan.json` și
`tools/spain_focus_expected_totals.json`. Generatorul rescrie numai fișierele
noi generate; nu repetă migrările fișierelor vechi.

```powershell
python -B tools/generate_spain_rework.py --check
python -B -m unittest discover -s tools -p 'test_*.py' -v
```

Testele execută scripturile într-un simulator determinist: cele opt trasee
complete, recuperarea, legile, aderarea, transferul și conservarea industriei,
recompensele în așteptare și izolarea celorlalte rute. Simulatorul nu înlocuiește
încărcarea modului în executabilul HOI4. Nu a fost rulată o campanie în joc.

Backupul fișierelor originale este indicat de `tools/spain_rework_backup_path.txt`.
Manifestul implementării este în `docs/spain-nationalist-rework-manifest.json`.

## Corecția încărcării din 16 octombrie

Motorul HOI4 a respins comparațiile compacte `>=` și `<=` generate în
recompense. Prima eroare a întrerupt încărcarea arborelui la D09 și a produs
apoi erori în cascadă pentru focusuri și AI. Comparațiile folosesc acum forma
nativă explicită `var`, `value`, `compare`. Testul de regresie verifică această
limitare separat de parserul generic al testelor.

Au fost eliminate și 32 de blocuri de reguli fără nicio regulă efectivă,
rămase în 19 fișiere după eliminarea permisiunilor vechi de voluntari.
Recompensele utile ale acelor focusuri și evenimente au fost păstrate.
Generatorul de cleanup elimină acum astfel de blocuri la sursă.

Logul unei porniri noi confirmă dispariția erorilor de focusuri și a celor
32 de blocuri goale. Rămân mesajele vechi de DLC/checksum, cinci referințe
grafice pentru tancuri și avertizarea de localizare duplicată. După această
verificare au fost aplicate integrarea completă a recuperării pozitive și
redenumirea alegerilor; acestea sunt verificate prin teste automate și se
încarcă la următoarea pornire. Evidența exactă este în `spain-load-fix.json`.

## Prezentarea compactă verificată live

Arborele refăcut are 109 iconițe distincte pentru 115 focusuri. Coordonatele
sunt definite individual în plan, cu niveluri consecutive și ramificații locale;
nu se mai calculează dintr-o matrice pe secțiuni. Alegerea permanentă între
economie și armată urmează modernizării comune. Prerequisitele tranzitive sunt
eliminate, iar condițiile curente rămân doar unde starea se poate schimba.

Aviația are cinci focusuri: comandament, industrie aeronautică, lecții
operaționale, pregătirea piloților și rețeaua de aerodromuri. Cele trei
fabrici militare rămân în buget; nu se reintroduc bonusurile aeriene
fragmentate ale primei versiuni.

Recompensele procentuale folosesc convenția Mongoliei: antetul modificatorului
și `add_to_variable` cu `tooltip = ..._tt`. Compensarea recompenselor din
salvările vechi rămâne ascunsă și este verificată separat. Profilele de
recuperare și avantajele condiționale folosesc aceeași formatare nativă în
`effect_tooltip`, fără a acorda bonusuri suplimentare prin previzualizare.

Offsetul spaniol al arborelui comun AXIS este 56; extremitatea sa stângă
începe la coloana 65, după marina națională care se termină la 61.
Reîncărcarea live în modul debug și inspecția vizuală au fost folosite pentru
verificare; avertismentele vechi de DLC/grafică sunt distincte de aceste schimbări.

## Reconstrucție comună și afișarea construcțiilor

National Reconstruction Commission este centrat la (31, 2), sub alegerile
Arsenal of the Axis și Our Place in the New Order, cu prerequisite OR.
Restore Civil Administration și Demobilisation and Reemployment sunt simetrice
la (29, 3) și (33, 3). Economia continuă din administrație, armata din
demobilizare, iar aviația și marina din comandamentul comun. Traseele Portugaliei
sunt în exteriorul liniilor reconstrucției. German Military Mission urmează
comisiei comune; condițiile curente privind Germania rămân.

Arborele naționalist ocupă coloanele 17–61 și nivelurile 0–18. Între armata
comună și aviație, respectiv aviație și marină, rămân trei coloane: două pentru
spațierea obișnuită și una suplimentară pentru separarea vizuală a ramurilor.
Alegerea specializării este la (28, 10) și (32, 10). Generatorul notifică și
arborele principal al Spaniei după modificarea focusurilor comune, pentru ca
instanța deja deschisă în debug să preia noua poziționare.

Focusurile cu fabrici, rafinării și șantiere afișează efectele native de
stat, sloturi și construcție, fără text custom de recompensă. Destinațiile
sunt definite explicit în `buildingStates`: de exemplu E02 acordă două
fabrici civile în Asturias, N02 trei șantiere în Galicia, iar N12 câte
trei în Asturias și Sevilla. Evidența internă plasează clădirile în aceleași
state și așteaptă dacă sunt ocupate ori pline. Nu redirecționează recompensa
în alt stat. Cozile generice ale versiunii precedente rămân procesate pentru
salvările care aveau deja recompense în așteptare. Compensarea fabricilor
obținute prin focusurile vechi se păstrează.

## Decizii, evenimente și variația recompenselor

Sunt păstrate cererea de aderare, acceptarea/refuzul, reluarea cererii și
evenimentul transferului industrial portughez. Nu sunt duplicate deciziile
moștenite de exploatare a resurselor și nu sunt reactivate rutele alternative.

Au fost adăugate șase decizii legate de focusuri:

| Focus | Decizie | Cost și durată | Rezultat |
| --- | --- | --- | --- |
| Restore Transport Links | Rebuild Asturias | 35 PP, 45 zile | +1 infrastructură și +1 slot în Asturias |
| Restore Transport Links | Reconnect Western Aragon | 35 PP, 45 zile | +1 infrastructură și +1 slot în Western Aragon |
| Restore Transport Links | Restore Andalusian Infrastructure | 35 PP, 45 zile | +1 infrastructură și +1 slot în Sevilla |
| Factory Technical Schools | Standardise Industrial Subcontractors | 75 PP, 60 zile | +5% retenție de eficiență la schimbarea producției, în Spanish Economy |
| The Staff Academy | Conduct Motor Pool Trials | 75 PP, 60 zile | −2.5% consum de combustibil al armatei, în Spanish Armed Forces |
| Organise National Service | Promote National Service | 35 PP, 120 zile între utilizări | +5% war support și −2% stabilitate |

Primele cinci sunt proiecte unice, cu flag permanent la finalizare. Cele
regionale restituie PP la pierderea controlului și pot fi reluate ulterior.
Campania cere stabilitate peste 30% și war support sub 90%. Bonusurile
proiectelor se acordă la finalizare, nu la activare.

National Labour Accords declanșează evenimentul TFR_spain_rework.5:
reconciliere (+5% stabilitate) sau mobilizare (+10% war support, −2.5%
stabilitate). Prima opțiune păstrează recompensa politică anterioară;
bonusul nu se mai acordă și direct de focus. Recuperarea economică și
celelalte efecte dinamice sunt identice pentru ambele opțiuni.

Recompensele vecine au fost diferențiate fără schimbarea totalului de
fabrici: E02/E05/E10 acordă 2/1/3 civile, E06/E07 acordă 3/1 militare,
iar E15/E16 acordă 3/1 civile. E05 primește cercetare pentru construcții;
cercetarea industrială se mută de la E10 la E12. E07 primește 2.5%
eficiență maximă din bonusul anterior de 5% al E12; E12 păstrează 2.5%.
E16 adaugă infrastructură în Ciudad Real. Testele verifică separat
recompensele complete ale focusurilor apropiate.

Validare: 63 de teste automate, inclusiv costuri/durate, condiții de
deblocare, anulare, recompense unice și cele două alegeri ale evenimentului.
Debug a reîncărcat deciziile și evenimentele fără erori; o a doua
reîncărcare a focusurilor a rezolvat referințele temporar necunoscute din
prima reîncărcare, când focusurile fuseseră citite înaintea noilor decizii.

## Aviație extinsă moderat și auditul cumulului

Pilot Training and Maintenance (21 zile) reduce accidentele cu 10%.
Forward Airfield Network (28 zile) reduce consumul de combustibil aerian
cu 5% și adaugă două niveluri de aerodrom în Valencia și Sevilla, până la
plafonul local. Cele două continuări sunt așezate direct sub A02/A03.
Bonusurile existente de misiune, agilitate și CAS și cele trei fabrici
militare sunt păstrate.

Bugetele complete ale celor opt trasee includ ambele moduri, specializările
mutual exclusive și doctrinele navale. Sunt executate și proiectele
opționale eligibile. Exemple de totaluri naționale permanente:

| Indicator | Înainte | După |
| --- | --- | --- |
| Organizare, specializare militară și război comun cu Germania | +20% | +12.5% |
| Recuperare, aceeași rută | +20% | +12.5% |
| Factory output, specializare economică și război comun | +30% | +25% |
| Construcție generală, specializare economică | +15% | +10% |
| Research speed, specializare economică | +12.5% | +10% |
| Dockyard output, toate rutele | +20% | +12.5% |
| Breakthrough, specializare militară | +10% | +5% |
| Atac/apărare globală, specializare militară | +5% fiecare | +2.5% fiecare |

An Iberian Naval Power acordă acum +2.5% dockyard output, An Iberian
Economic Powerhouse +2.5% factory output, iar A Professional Spanish Army
+2.5% atac și apărare globală. Sunt păstrate durata, porțile de calendar
și alegerile permanente. Nu sunt reduse fabricile și nici avantajul de
patru fabrici militare acordat participării directe la război.

Salvările existente sunt ajustate o singură dată: variabilele recompenselor
vechi sunt reduse cu diferențele de buget înaintea următoarei recompense
sau la actualizarea zilnică. Bonusurile importate din ideile vechi sunt
protejate; creditul eliberat este reutilizat la focusurile viitoare.
Componentele și datele programelor de recuperare rămân intacte.

Cele 67 de teste verifică inclusiv migrarea repetată, recompensele noi
aplicate după migrare, plafonul aerodromurilor și limitele tuturor celor
opt trasee. Aceste limite sunt criterii de testare, nu clamp-uri arbitrare
în joc. Ele acoperă rework-ul național și proiectele sale; legile,
consilierii și bonusurile comune ale facțiunii sunt sisteme separate.
Rezultatele executate sunt în `spain-air-balance.json`.
