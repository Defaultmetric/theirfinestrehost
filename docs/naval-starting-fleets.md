# Flote inițiale compactate — 1936, Man the Guns

Țări cu minimum 1.000 IC în producția navală eliminată. Fiecare tip este compactat separat:
`număr inițial compactat = floor((IC deployed + IC investit în producție) / cost design standard 1936)`.

Resturile de IC sunt reunite pentru completări, fără eliminarea navelor deja bugetate.
Se păstrează minimum o navă din fiecare tip deja deployed. Costurile exclud reducerile de MIO/idei/tehnologii.

| Țară | Nave înainte | Nave după | IC deployed | IC producție | Buget total | IC flotă nouă | Rest IC |
|---|---:|---:|---:|---:|---:|---:|---:|
| ENG | 239 | 194 | 531,202.38 | 25,103.95 | 556,306.33 | 556,103.00 | 203.33 |
| FRA | 135 | 108 | 204,108.00 | 10,453.99 | 214,561.99 | 213,870.00 | 691.99 |
| GER | 38 | 34 | 70,658.00 | 28,755.19 | 99,413.19 | 99,093.25 | 319.94 |
| ITA | 154 | 123 | 204,458.50 | 25,161.66 | 229,620.16 | 229,382.63 | 237.54 |
| JAP | 194 | 154 | 393,638.65 | 21,912.50 | 415,551.15 | 415,009.63 | 541.52 |
| SOV | 85 | 72 | 91,215.25 | 4,313.03 | 95,528.28 | 95,464.88 | 63.40 |
| SPR | 31 | 31 | 55,465.50 | 4,785.96 | 60,251.46 | 59,942.63 | 308.84 |
| USA | 230 | 177 | 453,923.15 | 18,855.68 | 472,778.83 | 472,778.00 | 0.83 |

## Identificarea subtipurilor

Denumirile standard explicite și role_icon_index (LD=2, TD=8, ASW=3) au prioritate pentru destroyers.
Design-urile istorice fără aceste indicii sunt ASW dacă au cel puțin două module depth charge,
TD dacă au cel puțin două module torpedo, altfel LD. O singură torpilă/depth charge nu schimbă un DD mixt în TD/ASW.
LC/HC/BB/BC păstrează definition-ul istoric; submarinele crucișător rămân CS.
Producția folosește definition-ul aceluiași design în OOB-urile istorice, unde există.

Navele vechi și cele deja din 1936 sunt incluse împreună și înlocuite cu variantele standard.
Numele, experiența, flagship-ul, ofițerii și distribuția între task forces sunt păstrate unde numărul compactat permite.
Flotele 1939, țările sub prag și liniile de producție eliminate rămân neschimbate.

Snapshot-ul surselor originale și inventarul pe navă sunt în `naval-starting-fleets-original.json`.
Calculul pe tip, completările din resturi și navele păstrate/eliminate/adăugate sunt în `naval-starting-fleets.json`.

## ENG

| Tip | Înainte | Floor pe tip | După resturi comune | IC deployed | IC producție | Cost/navă 1936 | IC final |
|---|---:|---:|---:|---:|---:|---:|---:|
| LD | 76 | 65 | 65 | 81,922.50 | 0.00 | 1,259.25 | 81,851.25 |
| TD | 52 | 50 | 50 | 69,506.00 | 10,745.60 | 1,604.25 | 80,212.50 |
| LC | 31 | 21 | 22 | 104,638.50 | 13,026.13 | 5,478.88 | 120,535.25 |
| HC | 18 | 11 | 11 | 87,461.75 | 0.00 | 7,797.63 | 85,773.88 |
| BB | 12 | 6 | 7 | 102,997.75 | 0.00 | 15,842.25 | 110,895.75 |
| BC | 3 | 1 | 1 | 22,323.88 | 0.00 | 15,548.88 | 15,548.88 |
| CV | 5 | 4 | 4 | 38,988.00 | 777.83 | 9,105.75 | 36,423.00 |
| SS | 42 | 32 | 34 | 23,364.00 | 554.40 | 731.25 | 24,862.50 |

## FRA

| Tip | Înainte | Floor pe tip | După resturi comune | IC deployed | IC producție | Cost/navă 1936 | IC final |
|---|---:|---:|---:|---:|---:|---:|---:|
| TD | 52 | 41 | 42 | 62,675.50 | 3,882.20 | 1,604.25 | 67,378.50 |
| LC | 7 | 4 | 5 | 23,481.50 | 2,927.40 | 5,478.88 | 27,394.38 |
| HC | 7 | 4 | 5 | 31,428.75 | 0.00 | 7,797.63 | 38,988.13 |
| BB | 5 | 2 | 2 | 42,380.00 | 0.00 | 15,842.25 | 31,684.50 |
| BC | 0 | 0 | 0 | 0.00 | 2,757.33 | 15,548.88 | 0.00 |
| CV | 1 | 0 | 1 | 7,003.00 | 0.00 | 9,105.75 | 9,105.75 |
| SS | 62 | 50 | 51 | 36,059.25 | 887.06 | 731.25 | 37,293.75 |
| CS | 1 | 1 | 2 | 1,080.00 | 0.00 | 1,012.50 | 2,025.00 |

## GER

| Tip | Înainte | Floor pe tip | După resturi comune | IC deployed | IC producție | Cost/navă 1936 | IC final |
|---|---:|---:|---:|---:|---:|---:|---:|
| LD | 12 | 10 | 11 | 10,665.00 | 2,896.28 | 1,259.25 | 13,851.75 |
| LC | 8 | 4 | 5 | 25,879.00 | 0.00 | 5,478.88 | 27,394.38 |
| HC | 2 | 2 | 3 | 14,892.00 | 8,335.76 | 7,797.63 | 23,392.88 |
| BB | 2 | 1 | 1 | 11,830.00 | 5,366.40 | 15,842.25 | 15,842.25 |
| CV | 0 | 1 | 1 | 0.00 | 10,889.55 | 9,105.75 | 9,105.75 |
| SS | 14 | 11 | 13 | 7,392.00 | 1,267.20 | 731.25 | 9,506.25 |

## ITA

| Tip | Înainte | Floor pe tip | După resturi comune | IC deployed | IC producție | Cost/navă 1936 | IC final |
|---|---:|---:|---:|---:|---:|---:|---:|
| LD | 82 | 67 | 68 | 83,619.75 | 1,435.20 | 1,259.25 | 85,629.00 |
| LC | 11 | 8 | 8 | 37,686.50 | 7,368.91 | 5,478.88 | 43,831.00 |
| HC | 8 | 4 | 5 | 38,122.25 | 0.00 | 7,797.63 | 38,988.13 |
| BB | 2 | 2 | 2 | 16,848.00 | 16,022.05 | 15,842.25 | 31,684.50 |
| SS | 51 | 38 | 40 | 28,182.00 | 335.50 | 731.25 | 29,250.00 |

## JAP

| Tip | Înainte | Floor pe tip | După resturi comune | IC deployed | IC producție | Cost/navă 1936 | IC final |
|---|---:|---:|---:|---:|---:|---:|---:|
| LD | 35 | 26 | 26 | 32,067.75 | 1,386.00 | 1,259.25 | 32,740.50 |
| TD | 59 | 50 | 51 | 74,908.00 | 6,284.75 | 1,604.25 | 81,816.75 |
| LC | 21 | 12 | 12 | 66,524.75 | 2,211.45 | 5,478.88 | 65,746.50 |
| HC | 14 | 9 | 9 | 70,958.00 | 0.00 | 7,797.63 | 70,178.63 |
| BB | 6 | 3 | 4 | 61,029.50 | 0.00 | 15,842.25 | 63,369.00 |
| BC | 3 | 1 | 2 | 26,354.25 | 1,756.95 | 15,548.88 | 31,097.75 |
| CV | 4 | 4 | 4 | 30,259.40 | 8,106.35 | 9,105.75 | 36,423.00 |
| SS | 52 | 46 | 46 | 31,537.00 | 2,167.00 | 731.25 | 33,637.50 |

## SOV

| Tip | Înainte | Floor pe tip | După resturi comune | IC deployed | IC producție | Cost/navă 1936 | IC final |
|---|---:|---:|---:|---:|---:|---:|---:|
| LD | 1 | 1 | 4 | 747.50 | 1,629.55 | 1,259.25 | 5,037.00 |
| TD | 17 | 11 | 13 | 18,393.75 | 0.00 | 1,604.25 | 20,855.25 |
| LC | 5 | 2 | 3 | 14,651.00 | 0.00 | 5,478.88 | 16,436.63 |
| HC | 0 | 0 | 0 | 0.00 | 910.35 | 7,797.63 | 0.00 |
| BB | 3 | 1 | 1 | 24,258.00 | 0.00 | 15,842.25 | 15,842.25 |
| SS | 59 | 47 | 51 | 33,165.00 | 1,773.13 | 731.25 | 37,293.75 |

## SPR

| Tip | Înainte | Floor pe tip | După resturi comune | IC deployed | IC producție | Cost/navă 1936 | IC final |
|---|---:|---:|---:|---:|---:|---:|---:|
| LD | 12 | 13 | 15 | 14,211.00 | 2,504.70 | 1,259.25 | 18,888.75 |
| LC | 5 | 3 | 3 | 17,401.00 | 0.00 | 5,478.88 | 16,436.63 |
| HC | 0 | 0 | 0 | 0.00 | 2,281.26 | 7,797.63 | 0.00 |
| BB | 2 | 1 | 1 | 17,108.00 | 0.00 | 15,842.25 | 15,842.25 |
| SS | 12 | 9 | 12 | 6,745.50 | 0.00 | 731.25 | 8,775.00 |

## USA

| Tip | Înainte | Floor pe tip | După resturi comune | IC deployed | IC producție | Cost/navă 1936 | IC final |
|---|---:|---:|---:|---:|---:|---:|---:|
| TD | 113 | 90 | 92 | 140,517.50 | 5,422.25 | 1,604.25 | 147,591.00 |
| LC | 12 | 6 | 8 | 38,352.00 | 0.00 | 5,478.88 | 43,831.00 |
| HC | 15 | 9 | 10 | 71,164.50 | 6,015.63 | 7,797.63 | 77,976.25 |
| BB | 15 | 8 | 8 | 131,690.50 | 0.00 | 15,842.25 | 126,738.00 |
| CV | 4 | 4 | 4 | 34,010.90 | 7,000.43 | 9,105.75 | 36,423.00 |
| SS | 71 | 52 | 55 | 38,187.75 | 417.38 | 731.25 | 40,218.75 |
