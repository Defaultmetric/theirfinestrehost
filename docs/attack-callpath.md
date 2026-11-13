# Traseul nativ al calculului atacului

## Rezultat

Analiza statica din 2026-11-09 a recuperat traseul de la actualizarea
`CLandCombat` pana la rezolvarea atacului per tinta si aplicarea daunelor.
Exista dispatch virtual C++ intre obiectele native ale luptei, urmat de
apeluri directe catre calculul atacului. Nu a fost identificata pe acest
traseu o inregistrare din script sau un callback care sa furnizeze o
implementare alternativa a formulei.

Targetul este acelasi `hoi4.exe` 1.19.4.2.2da5, SHA-256
`bccc62909b6a1ec2c1d5a46ef18608e4d0c7cdc89ad341b7402a23c40f7a8037`.
Toate adresele sunt VA statice, cu image base preferat `0x140000000`;
RVA se obtine scazand aceasta baza. Analiza nu a executat jocul sau rutinele.

## Traseul recuperat

```text
CLandCombat: metoda virtuala +0x78
  0x141347fd0
    -> salt direct la 0x14147e600, implementarea comuna CCombat
       -> pentru fiecare dintre cele doua parti ale luptei:
          vtable +0xb0 -> 0x14133f5b0: pregatirea factorilor
          vtable +0x98 -> 0x1413480e0: selectia tintelor / atacuri
                            -> CALL direct 0x141343100
                               -> combina soft/hard attack si factorii
                               -> CALL direct 0x141349aa0: lovituri / daune
                               -> tinta.vtable +0xc0
                                  CArmy: 0x140cec2e0, scaderea starii tintei
```

`0x14147e600` citeste participantii din `combat+0x28` si `combat+0x30`.
Executa mai intai `+0xb0` pentru ambii, apoi `+0x98` pentru ambii. Urmeaza
si alte faze la sloturile `+0x70` si `+0x100`; acestea nu au fost recuperate
integral in aceasta etapa. Etichetele de rol din diagrama sunt descriptive,
nu simbolurile C++ originale.

Instructiunile de la `0x1413483b0`, `0x1413486b0` si `0x1413488c2` sunt
apeluri relative directe catre `0x141343100`. Adresa acestei rutine nu este
citita dintr-un nume de functie furnizat de mod sau dintr-o tabela de
callback-uri in aceste trei locuri. Inventarul anterior si scanarea
referintelor nu au identificat alti apelanti directi sau un pointer literal
catre aceasta rutina; acoperirea scanarilor este limitata, nu exhaustiva.

## De unde vine metoda virtuala

RTTI asociaza vtable-ul `0x142a236a0` clasei `CLandCombatant`:

| Slot | Destinatie nativa |
| --- | --- |
| `+0x98` | `0x1413480e0`, distribuirea si rezolvarea atacurilor |
| `+0xb0` | `0x14133f5b0`, pregatirea factorilor |
| `+0xb8` | `0x14147d860`, obtinerea unei contributii numerice |
| `+0xc0` | `0x1413428b0`, contributii numerice prin `0x141346a00` |

Constructorul `0x14133a1c0` scrie in obiect adresa constanta a acestui
vtable. Metoda `CLandCombat` de la `0x14133e5e0` aloca doua obiecte,
apeleaza direct constructorul si le stocheaza la `combat+0x28/+0x30`.

A fost gasita si o implementare derivata, `CLandBorderWarCombatant`:
vtable `0x142a372e8`, slot `+0x98` -> `0x141489810`. Constructorul
`0x141487570` instaleaza tot o adresa constanta din executabil. Aceasta
implementare extinde gestionarea participantilor si apeleaza apoi direct
`0x1413480e0` la `0x14148a2b8`.

Prin urmare, aceasta este o extensie nativa prin clase C++ compilate in joc.
Nu a fost gasita o legatura care sa permita scripturilor unui mod sa
construiasca o noua implementare a acestor metode sau sa o inregistreze in
locul lor. Existenta apelului virtual, singura, nu demonstreaza acea capacitate.

## Urmarirea factorilor numerici

Calculul per tinta obtine factorul de ofensiva prin `0x140c51a00`:

```text
factor_raw = trunc(unit[+0x198] * unit[+0x188] / 100000)
```

Au fost recuperate doua legaturi cu pregatirea anterioara atacului:

1. `0x14133f5b0` calculeaza valori numerice din starea unitatii, contributii
   ale modificatorilor si parametri globali. La `0x14133f817` apeleaza
   `0x140c59f80`, care contine doar stocarea valorii in `unit+0x198` si returul.
   Valoarea folosita aici deriva dintr-o pondere limitata la intervalul
   `0..100000`, interpolata intre doi parametri globali.
2. Aceeasi etapa apeleaza repetat `0x140c4f240`, care retine contributiile si
   actualizeaza numeric `unit+0x188` si `unit+0x190`. In functie de un parametru
   global existent, agregarea este aditiva sau multiplicativa. La final,
   `0x140c514f0` aplica limita inferioara prevazuta de cod.

Apelurile virtuale `+0xb8/+0xc0` din pregatire au fost rezolvate pentru
vtable-urile de mai sus. Prima metoda citeste contributii din statistici;
a doua aduna contributii numerice prin `0x141346a00`, care citeste campuri
de modificatori si starea unitatii. Nu a fost observat aici un argument
care sa reprezinte o implementare de functie din mod.

Aceste legaturi explica modul in care datele pot influenta factorii
formulei existente. Ele nu reprezinta inlocuirea formulei. Originea tuturor
modificatorilor, construirea integrala a cache-ului de soft/hard attack si
fiecare apel tranzitiv al pregatirii nu au fost urmarite exhaustiv.

## Implicatia pentru Workshop

Nu avem inca un mecanism demonstrat pentru a furniza o formula alternativa
doar prin abonare Workshop + Play. Pe traseul recuperat, selectia metodei
este fixata de constructori nativi, iar nucleul formulei este apelat direct.
Nu a fost demonstrata o delegare catre script comparabila cu override-ul
explicit verificat anterior pentru garantii.

Concluzia este limitata la aceste rutine, clase si referinte. Nu constituie
o demonstratie ca toate extensiile posibile ale motorului au fost excluse.
Nu s-a realizat un patch, o injectare sau un test x10.

## Probe si verificare

Director privat:
`C:\Users\mihai\.codex\analysis\hoi4-workshop-engine-20261109\attack-calculation`.

- `callpath-verified.json`: hash-urile originalului si copiei, instructiunile
  si destinatiile selectate din vtable-uri, reverificate cu Capstone/PE;
- `callpath-initial.json`, `callpath-upstream.json`, `callpath-dispatch.json`,
  `callpath-selected-slots.json`: referintele si clasificarea apelantilor;
- `attack-function-0x14147e600_0x14147e6af.c`: actualizarea comuna,
  constructorii si implementarea derivata a constructorului;
- `attack-function-0x141489810_0x14148a314.c`: varianta border war si
  pregatirea tintelor;
- `attack-function-0x14133f5b0_0x1413428af.c`: pregatirea factorilor si
  alocarea participantilor;
- `attack-function-0x140c4f240_0x140c4f4bf.c`: agregarea si metodele de
  contributii numerice;
- `attack-function-0x141346a00_0x141347140.c`: agregarea contributiilor;
- `callpath-factor-callers.json`, `callpath-factor-store-candidates.json`:
  probe auxiliare limitate pentru stocarile numerice. Candidatii de stocare
  nu sunt toti atribuiti aceleiasi clase doar pe baza offsetului.

Analiza este Ghidra selectiva + parsare PE/RTTI + Capstone. Nu este un rezultat
REA de decompilare; timeout-ul anterior al analizei complete REA nu a fost
repetat. Hash-ul executabilului original a ramas identic cu cel al copiei.
Decompilerul poate integra un tail-call in pseudocod; saltul real de la
`0x1413480d0` la `0x14147e600` a fost verificat separat in instructiuni.
