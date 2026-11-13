# Rutina nativa de rezolvare a atacului terestru

Analiza statica din 2026-11-09 identifica o rutina care combina soft attack si
hard attack pentru o tinta, produce numarul de atacuri, rezolva loviturile si
apeleaza aplicarea daunelor asupra unitatii. Nu este doar codul de afisare.
Nu a fost modificata sau executata aceasta rutina in cadrul investigatiei.

Continuarea investigatiei a recuperat apelantii, dispatch-ul virtual nativ,
constructorii participantilor si o parte din pregatirea factorilor:
[traseul calculului atacului](attack-callpath.md). Nu a rezultat un callback
de script demonstrat pentru inlocuirea formulei.

## Executabil si adrese

Target: `hoi4.exe`, Operation Postern v1.19.4.2.2da5, x64.
SHA-256: `bccc62909b6a1ec2c1d5a46ef18608e4d0c7cdc89ad341b7402a23c40f7a8037`.
Image base preferat: `0x140000000`.

| Rol dedus din cod | VA statica | RVA |
| --- | --- | --- |
| Rezolvarea atacului unei unitati asupra unei tinte | `0x141343100` | `0x01343100` |
| Apelant care itereaza unitatile si selecteaza/distribuie tintele | `0x1413480e0` | `0x013480e0` |
| Rezolvarea loviturilor si acumularea celor doua componente de daune | `0x141349aa0` | `0x01349aa0` |
| Factor de ofensiva folosit si de interfata | `0x140c51a00` | `0x00c51a00` |
| Metoda CArmy care scade efectiv valorile tintei | `0x140cec2e0` | `0x00cec2e0` |

Acestea sunt etichete descriptive, nu numele C++ originale recuperate.
`FUN_141343100` este numele automat al decompilatorului. Adresa dintr-un proces
este baza modulului incarcat + RVA; VA statica nu este o adresa runtime masurata.
Adresele si structurile sunt specifice executabilului cu hash-ul de mai sus.

## Legatura dintre statistici si calcul

Punctul de pornire a fost codul de actualizare a panoului de lupta,
`0x141675bc0`. El scrie in controalele numite explicit `soft_attack` si
`hard_attack` si permite asocierea urmatoarelor campuri:

```text
stats = *(unit + 0x138)
soft_attack_raw = *(stats + 0xc0)
hard_attack_raw = *(stats + 0xc8)
```

Rutina `0x141343100..0x1413438f2` citeste aceleasi campuri de la unitatea care
loveste. Foloseste si campul `*(target.stats + 0xb8)` ca pondere intre cele doua
tipuri de atac, cu ponderi complementare. Interpretarea ponderii ca hardness
este o inferenta din formula; nu a fost ancorata independent intr-un getter
cu nume recuperat.

O transcriere a portiunii de calcul, cu variabile denumite pentru lizibilitate:

```text
S = 100000                         # scala fixed-point
sa = trunc(soft_attack_raw * 10000 / S)
ha = trunc(hard_attack_raw * 10000 / S)
h = *(target.stats + 0xb8)
mixed = trunc((S-h)*sa/S) + trunc(ha*h/S)
offence = trunc(*(unit+0x198) * *(unit+0x188) / S)
factor = trunc(trunc((S+bonus1+bonus2)*offence/S) * allocation/S)
attacks_raw = trunc(mixed*factor/S)
```

`bonus1` si `bonus2` sunt bonusuri conditionale native; semantica lor completa
nu a fost recuperata. `allocation` vine de la apelantul care selecteaza tintele.
Scala este 100000, iar `10000/S` introduce aici factorul 0.1. Rutina transforma
apoi `attacks_raw/S` intr-un numar intreg prin rotunjire probabilistica: partea
fractionara este comparata cu un rezultat RNG modulo 100, la precizie de procent.

Acesta este calculul pentru o tinta din etapa de rezolvare a luptei. Nu include
recuperarea integrala a tuturor calculelor care au construit anterior cache-ul
statisticilor sau factorii unitatii.

## De ce apartine rezolvarii luptei

- Apelantul `0x1413480e0` parcurge unitatile, selecteaza tinte si apeleaza
  `0x141343100` la `0x1413483b0`, `0x1413486b0` si `0x1413488c2`.
- `0x141343100` calculeaza rapoarte intre alte statistici ale celor doua unitati,
  alege intrari din tabele si apeleaza `0x141349aa0` la `0x1413435f9`.
- `0x141349aa0` itereaza numarul de atacuri, verifica fiecare lovitura prin
  `0x140c4f4f0` si acumuleaza doua componente de daune cu RNG.
- Rezultatul este scalat si transmis metodei virtuale a tintei la slotul `+0xc0`.
  Vtable-ul principal asociat prin RTTI clasei `CArmy`, la `0x1429d6d98`, contine
  la acest slot adresa `0x140cec2e0`.
- Aceasta metoda aplica modificatori, scade valorile de la `unit+0x420` si
  `unit+0x428` si le limiteaza inferior la zero. Getter-ele de la sloturile
  `+0xf8` si `+0x120` citesc exact aceste campuri; rutina apelanta compara
  valorile inainte si dupa aplicare si acumuleaza diferentele in starea luptei.

Legatura pana la scaderea starii unitatii sustine identificarea unei cai de
rezolvare a atacului, fara a o confunda cu estimarea sau afisarea UI. Aceasta
este evidenta statica, nu observarea executiei intr-o lupta reala.

## Limitele rezultatului

Nu este o demonstratie de inlocuire a functiei printr-un mod Workshop. Nu a fost
gasita aici o interfata de script care sa accepte implementarea alternativa a
acestui calcul si nu a fost construit sau testat un patch x10. Identificarea
codului nativ si posibilitatea de a-l redirectiona din mod sunt rezultate
distincte.

Au fost folosite copia privata a executabilului, parsarea PE/.pdata/RTTI,
Capstone si decompilarea selectiva Ghidra. REA nu a furnizat o decompilare pentru
acest rezultat; analiza sa completa esuase anterior prin timeout.

Probe locale principale, in
`C:\Users\mihai\.codex\analysis\hoi4-workshop-engine-20261109\attack-calculation`:

- `stat-string-refs.json`: legatura cu numele controalelor UI;
- `attack-function-0x14166db30_0x14166eebe.c`: constructorul si actualizarea UI;
- `attack-function-0x141343100_0x1413438f2.c`: calculul per tinta si factorul;
- `combat-chain.json`: apelantii, fragmentele unwind si asocierea RTTI/vtable;
- `attack-function-0x1413480e0_0x141348d28.c`: distribuirea tintelor,
  rezolvarea loviturilor, aplicarea daunelor si getter-ele;
- `AttackCalcFocused.java`: scriptul de analiza selectiva offline.
