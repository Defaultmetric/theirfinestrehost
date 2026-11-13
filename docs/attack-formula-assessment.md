# Cerinta: inlocuirea calculului nativ de atac

Utilizatorul a precizat ca testul cerut este schimbarea calculului folosit de
motor astfel incat o unitate care ataca sa primeasca exact10x atacul normal.
Schimbarea unui define, a echipamentului, tacticii sau a unui modificator nu
este acceptata drept demonstratie de inlocuire a formulei.

## Rezultat actual

Actualizare 2026-11-09: a fost identificata static o rutina nativa de rezolvare
a atacului per tinta, la `0x141343100` (RVA `0x01343100`), urmarita pana la
aplicarea daunelor asupra unitatii. Formula recuperata, adresele si limitele
sunt documentate in [attack-calculation-addresses.md](attack-calculation-addresses.md).
Acest rezultat nu demonstreaza inlocuirea rutinei prin Workshop.

Nu a fost identificat si demonstrat un callback care sa inlocuiasca formula
nativa de atac, analog celui verificat pentru eligibilitatea garantiilor.
Nu a fost modificata formula, nu s-a construit un patch nativ si nu s-a rulat
un test de lupta cu o formula nativa inlocuita. TFR si executabilul nu au primit
modificari de gameplay/cod din aceasta etapa.

Override-ul pentru garantii controleaza ramuri pe care motorul le deleaga
explicit unui trigger numit. El nu este o interfata pentru redirectionarea
oricarei functii C++ si nu a fost extins la calculul atacului.

## Verificari efectuate

- Documentatia si resursele livrate expun factori precum `army_attack_factor`,
  `offence`, date de echipament si campuri attacker/defender ale tacticilor.
  Acestea sunt intrari ale mecanicilor existente, nu inlocuiri demonstrate ale
  formulei native.
- `is_attacker` este documentat pentru scope-ul COMBATANT. RTTI identifica
  `CIsAttackerTrigger`; numele/clasa nu constituie un callback numeric pentru
  returnarea unei noi puteri de atac. Tabela virtuala si instructiunile scurte
  accesibile au fost retinute fara invocarea codului.
- `attacker_modifier` din dynamic_modifiers are comentariul ca extinde citirea
  modificatorului asupra participantilor care nu se afla in stat. Numele sau
  nu este tratat drept dovada ca poate inlocui calculul sau ca asigura singur
  conditia "doar cand unitatea ataca".
- Inventarul ASCII a gasit29 literale ce combina termeni attack/combat/damage
  cu script/callback/override/trigger/calculat. Rezultatele sunt etichete,
  predicate, RTTI si mesaje; nu a fost stabilit un endpoint de inlocuire a formulei.
- Initializatorul cunoscut al cache-ului de scripted triggers
  `0x140b086b0..0x140b09374` refera18 nume, pentru rezistenta, crypto si
  diplomatie. Nu a aparut aici un nume de override pentru formula atacului.
  Aceasta nu este o enumerare a tuturor mecanismelor sau cailor indirecte din motor.

Un bonus aditiv de +900% nu este folosit drept proba ca rezultatul final este
exact10x fata de formula normala in prezenta altor bonusuri. Nici multiplicarea
daunelor unei tactici nu este echivalata cu inlocuirea statisticilor soft/hard
attack sau cu schimbarea functiei native.

## Limita investigatiei

S-a recuperat calculul per tinta dintr-o rutina nativa de rezolvare a atacului,
dar nu integral toate calculele anterioare care produc statisticile si factorii.
Nu s-au exclus toate numele calculate, apelurile indirecte sau comportamentele nedocumentate.
Concluzia este absenta unui mecanism demonstrat in verificarile efectuate,
nu o demonstratie de imposibilitate universala.

Pentru a realiza cerinta ar fi necesar fie un punct de extensie al acelei
rutine care poate primi implementarea din mod, fie un mecanism de incarcare a
unui patch nativ. Primul nu a fost identificat pentru acest calcul; niciun
mecanism nativ verificat anterior nu respecta exclusiv abonare Workshop + Play.

Probe private:
`C:\Users\mihai\.codex\analysis\hoi4-workshop-engine-20261109\attack-native-callback-string-audit.json`,
`attack-callback-assessment.json`, `attack-callback/assess.py`, documentatia
livrata si inventarul anterior `native-script-callback-candidates.json`.
Targetul static este1.19.4.2, SHA-256
`bccc62909b6a1ec2c1d5a46ef18608e4d0c7cdc89ad341b7402a23c40f7a8037`.
