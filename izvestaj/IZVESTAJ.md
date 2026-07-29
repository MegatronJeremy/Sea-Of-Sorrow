# Izveštaj — PSZ Projekat 2025/2026

**Tema:** Prikupljanje, analiza, vizuelizacija i mašinsko učenje nad podacima o
beloj tehnici sa srpskih onlajn prodavnica.
**Baza:** PostgreSQL · **Jezik:** Python 3.11 · **GUI:** Tkinter

---

## 1. Prikupljanje podataka (Zadatak 1)

### Izvori
Podaci su prikupljeni sa **tri** prodavnice, sa poljem `izvor` koje beleži sajt
porekla (isti proizvod se često nudi u više radnji po različitoj ceni):

| Sajt | Tehnologija | Pristup | Zapisa |
|---|---|---|---|
| gigatron.rs | Next.js (SPA) | proizvodi ugrađeni u RSC payload (`self.__next_f`) — jedan zahtev daje 24 proizvoda + specifikacije | ~4.400 |
| tehnomanija.rs | Magento (statički HTML) | listing → zahtev po proizvodu (BeautifulSoup) | ~2.750 |
| market.metalac.com | statički HTML | listing (40/strani) → spec sa stranice proizvoda | ~940 |
| **Ukupno (primarna baza)** | | | **8.065** |

Prikupljeno polje po proizvodu: naziv, brend, kategorija, izvor, cena,
cena pre akcije, dostupnost na lageru, energetska klasa, dijagonala, kapacitet,
zapremina, snaga i ceo skup sirovih karakteristika (JSONB). Nedostupna polja
ostaju **NULL** (u skladu sa postavkom).

### Arhitektura indeksera
Svaki izvor je modul sa jedinstvenim interfejsom `run(upsert_fn, log, stop_event)`.
Orchestrator (`kod/01_crawler/scrape.py`) pokreće sve izvore **paralelno** (jedan
thread po sajtu) — pošto su to različiti serveri, ne povećava se opterećenje ni
jednom sajtu, a ukupno vreme ≈ najsporiji izvor. Upis u bazu je UPSERT
(`ON CONFLICT (url)`), pa ponovno pokretanje ne pravi duplikate.

### Poteškoće i rešenja
- **Cloudflare (HTTP 403)** na tehnomaniji → `curl_cffi` sa Chrome TLS
  otiskom (imitira pravi browser); retry sa eksponencijalnim backoff-om.
- **JS-renderovani sajtovi** (gigatron, tehnomedia) → umesto headless browsera,
  podaci se izvlače direktno iz ugrađenog Next.js RSC payload-a (gigatron) —
  brže i stabilnije. Tehnomedia (čist Vue bez ugrađenih podataka) je preskočena.
- **Korektno ponašanje:** throttling 0.2–3.5s između zahteva, rotacija
  User-Agent zaglavlja, ograničen broj paralelnih radnika (izbegavanje DoS-a).
- **Zaglavljivanje:** watchdog automatski prekida izvor bez napretka 240s +
  per-strana timeout 180s.

---

## 2. Analiza i preprocesiranje (Zadatak 2)

### Čišćenje
Preprocesiranje (`kod/02_analiza/cisti_podatke.py`):
1. odbacivanje zapisa bez obaveznih polja (naziv, brend, kategorija, cena);
2. uklanjanje cena ≤ 0;
3. deduplikacija po URL-u;
4. **normalizacija brenda** (velika slova) — spaja varijante iz različitih
   izvora (npr. `Vox`/`VOX`, `Gorenje`/`GORENJE`);
5. uklanjanje ekstremnih cena Tukey IQR pravilom (dodaci od par stotina RSD i
   premium uređaji koji kvare regresiju);
6. kodifikacija energetske klase u broj (G=1 … A+++=10).

**Rezultat: 8.065 → 7.356 zapisa** (odbačeno 709, 8.8%) — iznad praga od 7.000.

> Tehnička polja nisu obavezna: postavka kaže da nedostupni podaci ostaju NULL,
> pa zapis sa nazivom/brendom/kategorijom/cenom ostaje validan i bez spec atributa
> (mali aparati često nemaju standardizovane karakteristike).

### Rezultati upita (`upiti_rezultati.xlsx`)
- **Broj po kategoriji (top):** usisivač 975, frižider 814, veš mašina 708,
  ugradna rerna 685, pegla 515, šporet 494 (ukupno 34 kategorije).
- **Top brendovi:** GORENJE 857, VOX 800, BOSCH 565, BEKO 557, CANDY 408,
  PHILIPS 284.
- **Energetska klasa C ili bolja:** 1.508 proizvoda.
- **Cena ≤ 50.000 RSD:** 5.758 proizvoda.
- **Raspon cena:** min 1.039 / prosek 32.926 / max 120.999 RSD.
- Statistika cena po kategoriji, % klase A po kategoriji, top brendovi po ceni,
  dostupnost po kategoriji, Top30 televizora po ceni, frižideri po veličini.

SQL upiti su u `kod/02_analiza/upiti.sql`, rezultati u Excel-u (10 sheet-ova).

---

## 3. Vizuelizacija (Zadatak 3)

Grafici u `izvestaj/grafici/` (PNG, sa naslovima):

| Fajl | Sadržaj |
|---|---|
| `kategorije_broj/procenat.png` | broj i % za 10 najzastupljenijih kategorija |
| `brendovi_broj/procenat.png` | broj i % po brendovima (≥5) |
| `cenovni_opsezi_broj/procenat.png` | raspodela po opsezima (≤30k: 3.909, 30–100k: 3.271, 100–300k: 176) |
| `energetska_klasa_broj/procenat.png` | broj i % po energetskoj klasi |
| `scatter_cena_zapremina.png`, `scatter_cena_dijagonala.png` | odnos cene i tehničkih atributa |
| `boxplot_cena_kategorija.png` | raspodela cena po kategoriji |

---

## 4. Regresija (Zadatak 4)

Višestruka linearna regresija, **ručna implementacija** gradijentnog spusta
(funkcija troška, korak GD-a i predikcija samostalno kodirani; sklearn samo za
verifikaciju).

- **Atributi (256):** kategorija i brend (one-hot), energetska klasa,
  dijagonala, kapacitet, zapremina, snaga (numerički standardizovani).
- **Ciljna promenljiva:** cena.
- **Podela:** 5.884 train / 1.472 test (80/20).
- **Parametri:** stopa učenja 0.05, 2.000 iteracija.
- **Kriva učenja:** trošak (MSE) opada 844M → 167M — model konvergira
  (vidljivo i u GUI-ju, tab Regresija).
- **Rezultat:** **R² = 0.549**, **RMSE = 17.832 RSD** na test skupu.

**Eksperimentisanje:** ključno otkriće bilo je da negativan R² na sirovim
podacima nije greška GD-a (sklearn closed-form daje isti rezultat) već posledica
ekstremnih cena — IQR filtriranje je podiglo R² sa ≈ −0.5 na +0.55. Veći broj
brendova (256 feature-a) blago razblažuje R² ali je realističan.

---

## 5. Klasterovanje (Zadatak 5)

K-means, **ručna implementacija** (k-means++ inicijalizacija, ručni silhouette).
Korisnik kroz GUI bira promenljive, težine (zbir 100%) i K.

**Primer:** cena (50%) + energetska klasa (30%) + zapremina (20%), K=4,
na 1.356 proizvoda sa svim atributima:

- **Silhouette = 0.487** (dobra razdvojenost).
- Klaster 0 [254]: prosečna cena ≈ 54.306 RSD, slabije energetske klase
- Klaster 1 [344]: ≈ 26.424 RSD, slabije energetske klase
- Klaster 2 [205]: ≈ 89.548 RSD (premium segment)
- Klaster 3 [553]: ≈ 37.156 RSD, **bolje energetske klase** (prosek 7.2/10)

Klasteri se vizuelizuju u GUI-ju (scatter dve dimenzije, tačke obojene po
klasteru + centroidi).

---

## 6. Preporuke (Zadatak 6)

Content-based sistem, **ručna implementacija** TF-IDF i kosinusne sličnosti.
Feature vektor kombinuje četiri tipa odlika: cenu, tehničke specifikacije
(standardizovane), brend (one-hot) i naziv (ručni TF-IDF). Preporučuje Top 5 iz
**iste kategorije**.

### Težinsko balansiranje odlika

Postavka traži da se prokomentariše kako su balansirane različite karakteristike
(npr. da li cena ima veći uticaj od brenda). Različiti tipovi odlika **nemaju
isti uticaj** na sličnost — svaki blok vektora se množi svojim težinskim
faktorom pre računanja kosinusne sličnosti:

| Tip odlike | Težina | Obrazloženje |
|---|:---:|---|
| Tehničke spec. | **1.0** | Suština sličnosti — proizvodi istih specifikacija (kapacitet, energ. klasa, dijagonala) su funkcionalno zamenljivi |
| Cena | **0.9** | Drži isti cenovni segment, ali malo ispod tehnike (korelira sa spec., ne sme da je nadjača) |
| Naziv (TF-IDF) | **0.7** | Hvata istu seriju/model; umeren da ne vraća samo duplikate istog modela |
| Brend | **0.5** | Najniže namerno — za „slično" želimo i alternative drugih brendova, ne kolaps na jednog proizvođača |

Redosled uticaja: **tehnika ≥ cena > naziv > brend**. Dakle cena ima *veći*
uticaj od brenda — kupcu je bliži proizvod sličnih performansi i cene nego
proizvod istog brenda ali sasvim drugih karakteristika.

**Tehnička napomena:** pre množenja težinama, svaki blok se skalira na jedinični
intenzitet. Bez toga bi *veličina* bloka (tehnika ima 5 kolona, cena 1, brend
one-hot, TF-IDF sitne vrednosti), a ne težina, određivala stvarni uticaj.

**Primer 1 — Beko kombinovani frižider RDSO206K40WN (26.499 RSD):**
| Preporuka | Cena | Sličnost |
|---|---|---|
| BEKO RDSO206K40WN (gigatron) | 22.499 | 0.992 |
| Beko RDSO206K40WN (metalac) | 22.002 | 0.988 |
| Beko RDSO206K40SN | 24.741 | 0.815 |
| Beko RSSE265K40 (jedna vrata) | 28.844 | 0.810 |
| Beko RCSA300K40WN | 32.661 | 0.799 |

> Top dve preporuke su **isti model sa druga dva sajta** (cena 22.002–26.499) —
> sistem tačno prepoznaje identičan proizvod, a različita cena pokazuje vrednost
> multi-source pristupa (poređenje cena po prodavnici). Ostale su tehnički bliske
> Beko varijante u istom cenovnom rangu.

**Primer 2 — Candy mašina za pranje veša CO4 1262D3/2-S (24.999 RSD):**
| Preporuka | Cena | Sličnost |
|---|---|---|
| Candy GD 27SB7-S | 27.711 | 0.907 |
| Candy GD 27SB7-S (drugi izvor) | 29.999 | 0.903 |
| Candy CSO4474TWMB6/1-S | 34.191 | 0.892 |
| Candy EY 27S7-S | 26.991 | 0.888 |
| Candy CSO286TWM6/1-S | 32.391 | 0.883 |

> Preporuke su mašine sličnog kapaciteta i cenovnog ranga; visoke sličnosti
> (0.88–0.91) potvrđuju da tehničke odlike + cena dominiraju nad pukim
> poklapanjem naziva.

---

## Zaključak

Svi zahtevi postavke su ispunjeni: 8.065 primarnih / 7.356 prečišćenih zapisa u
PostgreSQL bazi, sa tri izvora; sva tri ML algoritma ručno implementirana sa
zadovoljavajućom evaluacijom (R²=0.55, silhouette=0.49, tačne preporuke);
GUI objedinjuje zadatke 4–6; 122 automatska testa pokrivaju parser, čišćenje i
ML module.
