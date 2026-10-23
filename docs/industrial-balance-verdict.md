# Evaluare industrială TFR — 23 octombrie 2026

Evaluare statică pentru 1 ianuarie 1936, presupunând toate DLC-urile și un lobby
complet, cu SUA și Japonia jucate. Nu este rezultatul unei simulări sau al unor
meciuri. Nu au fost schimbate valori de gameplay în cadrul acestui audit.

## Verdict

Japonia și China (FCH) sunt cei mai clari candidați pentru verificare în meciuri.
Australia este un sprijin economic foarte puternic pentru Aliați. Nu există
suficiente date pentru a declara o țară sigur OP sau pentru un nerf numeric precis.

### Japonia: cel mai evident avantaj inițial față de baza teritorială

- 37 fabrici civile, 25 militare, 15 șantiere.
- Pe aceleași state, fișierele jocului de bază însumează 30 civile, 20 militare și
  15 șantiere: +7 civile (+23,3%) și +5 militare (+25%). Acesta este un reper
  pentru modificările modului, nu o țintă obligatorie de balans.
- 45 petrol brut, față de 13 în aceleași state din baza instalată. Oțel 105,
  aluminiu 16, tungsten 40, cauciuc 0: petrolul suplimentar ajută, dar nu oferă
  autonomie completă pentru aviație sau armată.
- Contraponderi: stabilitate inițială 20%, variabilă dinamică de bunuri de consum
  +30%, cercetare industrială penalizată și penalizarea de construcție civilă din
  militarism. Unele idei de facțiuni interne au efecte condiționale pe care tabelul
  static nu le însumează.
- Prima verificare recomandată: producția cumulată și fabricile active în 1937
  și la intrarea în război, înainte de a reduce bonusurile de cap.

### China: salt industrial și cercetare foarte puternice

- 38 civile, 22 militare, 2 șantiere, înainte de bonusurile din focusuri.
- Lanțul `FCH_unified_industrial_planning` → `FCH_rural_reconstruction_movement`
  → `FCH_mining_commission` → ambele arsenale → `FCH_start_the_war_machine`
  oferă 11 civile și 6 militare, apoi elimină `CHI_inefficient_war_econonmy`.
- Cele șase focusuri costă în total 60 de puncte: nominal 420 zile, dacă sunt
  prioritizate și condițiile de control teritorial sunt îndeplinite. Nu includ
  construcția normală sau pierderile teritoriale.
- Ideea eliminată penalizează outputul cu 30%, capul cu 7 puncte procentuale,
  creșterea eficienței cu 10% și retenția cu 10%. Eliminarea ei produce un salt
  mare fără a construi fabrici suplimentare în acel moment.
- Primul focus oferă și cinci bonusuri de cercetare industrială de +200%.
- Contraponderi: stabilitate 20%, free trade cu 80% export minim și variabile
  militare inițiale de -50% atac/apărare și -40% organizație. Acestea împiedică
  echivalarea automată a unei industrii puternice cu o armată OP.
- Candidatul principal de ajustare, dacă testele confirmă problema, este pachetul
  de cercetare și momentul eliminării penalizării; nu un nerf general al tuturor
  fabricilor.

### Australia: sprijin logistic puternic, economie penalizată

- 21 civile, 9 militare, 3 șantiere; include teritoriile indoneziene deținute de AST.
- 310 cauciuc și 140 petrol brut, plus 53 oțel și 47 tungsten. Sunt depozite
  teritoriale, înainte de infrastructură, export, modificatoare locale și rute.
- Nu trebuie comparată numai cu Australia continentală: o parte importantă din
  fabrici și resurse provine din imperiul deja repartizat la începutul modului.
- Marea Criză adaugă +40% la factorul de bunuri de consum și -15% la outputul
  fabricilor și șantierelor; economia civilă penalizează separat construcția.
- Pare foarte valoroasă pentru economia echipei, fără dovezi că producția proprie
  de început ar fi excesivă. Merită urmărite veniturile din comerț și efectul
  pierderii insulelor în fața Japoniei.

### Celelalte țări

- SUA: cea mai mare bază civilă și de petrol, dar numai 11 militare la început;
  izolarea și Marea Criză blochează mult potențial. Riscul este momentul mobilizării,
  nu simplul total de fabrici civile. Petrol brut 680, dintre care +223 față de
  aceleași state din baza instalată.
- URSS: 46 civile și 33 militare, resurse foarte bune; planul cincinal începe cu
  -15% creștere a eficienței și +10% factor de bunuri de consum. Puternică, fără
  un indiciu suficient de anomalie la început. Configurația Finlanda/Mongolia
  modifică substanțial totalurile prin scriptul de pornire.
- Germania: 35 civile și 28 militare; numai 2 petrol și 3 tungsten brut.
  Avantajele de construcție militară și MEFO se contrabalansează cu importurile,
  creșterea bunurilor de consum și obligația de expansiune. Trebuie inclusă
  industria țărilor înlocuitoare pe care le anexează ulterior.
- Marea Britanie: resurse diverse și 20 șantiere, dar numai 18 militare. O parte
  din resurse este colonială; protecția comerțului și transferurile de la supuși
  nu sunt reflectate într-un simplu total de state.
- Franța: -20% output din spiritul industrial inițial, multe resurse, numai 9
  militare. Bonusurile mari din focusuri merită urmărite în timpul campaniei.
  Suspiciunea de dublare între `FRA_reforming_economy` și `FRA_an_economy_unbound`
  este respinsă pentru progresia normală: primul depinde de `FRA_la_double_strategie`,
  al doilea de `FRA_le_pari_continental`, iar strategiile se exclud reciproc.
- Italia: 21 civile, 20 militare, 15 șantiere, dar fără petrol intern în statele
  inițiale; spiritul industriei militare penalizează capul, outputul și creșterea
  eficienței. Nu este un candidat evident pentru nerf industrial la început.
- România: 11 civile, 7 militare, 44 petrol brut și numai 11 oțel. Bonusurile din
  focusuri sunt bune, dar baza industrială și lipsa unor resurse o limitează.
- Ungaria: aluminiu 100, însă doar 9 civile și 7 militare, cu restricții militare
  și economice. Nu apare OP numai din datele de început.
- Bulgaria, Canada, Africa de Sud, India, Brazilia, Finlanda, Siam, Mexic și
  Irlanda nu prezintă un avantaj industrial inițial evident care să justifice
  un nerf automat. Unele au resurse specializate sau penalizări severe.
- Mongolia: bonusurile individuale de cap și construcție sunt mari, dar pleacă
  de la 8 civile, 3 militare, -20% output, -20% construcție și -7 puncte de cap
  în spiritul industrial. Ramurile economice se exclud parțial și bonusurile
  trebuie însumate cu penalizările inițiale. Nu rezultă că este OP la început.
- Malaya: furnizor important (542 cauciuc și 170 tungsten brut), cu numai 2 civile,
  1 militară și 1 șantier. Puterea comercială a echipei este mai relevantă decât
  producția militară proprie.

## Omisiune identificată în nerful anterior al capului

În `common/national_focus/australia_taog.txt`, liniile 4239, 4313, 7127 și 7605,
bonusurile variabilelor australiene au rămas 0.05/0.10. Sunt folosite de
modificatoare definite în fișierul `TAOG_dynamic_modifiers.txt` al jocului de bază,
care nu era inclus în descoperirea variabilelor la nerful precedent. Prin urmare,
afirmația anterioară că acoperirea era completă a fost prea largă. Acest audit
înregistrează problema fără a modifica valorile.

## Metodă și limite

Fișierele modului sunt suprapuse peste jocul de bază instalat. Sunt numărate toate
cele 42 de țări care dețin state, inclusiv țările înlocuitoare și ADT. Resursele
sunt depozite brute, nu disponibilul afișat în joc. Tabelul însumează modificatoare
directe din idei, legi implicite, variabile dinamice inițiale și tehnologii.
Nu aplică trăsături de lider, condiții complexe, efecte locale, infrastructură,
energie, ocupație, consum militar, comerț sau transferuri de fabrici între supuși
și stăpâni. Procentele nu reprezintă un calcul complet al producției efective.

`DynamicCountries.txt` schimbă anexările, statele și resursele la pornire pentru
majors only / fără Asia și în funcție de prezența jucătorilor pe Finlanda/Mongolia.
Tabelul de bază este anterior acestor redistribuiri. Țările înlocuitoare primesc
fabrici lunar prin `TFR_apply_logged_fake_industry_growth`; industria pe care o
câștigă Germania/Italia prin cuceriri depinde de momentul anexării.

Date complete: `industrial-balance-audit.md` și `industrial-balance-audit.json`.
Script de refacere: `python tools/industrial_balance_audit.py`.
