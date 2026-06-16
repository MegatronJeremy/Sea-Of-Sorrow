# Sea-Of-Sorrow

# PSZ Projekat 2025/2026 — Pronalaženje skrivenog znanja

Projektni zadatak iz predmeta *Pronalaženje skrivenog znanja*. Tema:
prikupljanje, analiza, vizuelizacija i mašinsko učenje nad podacima o
proizvodima bele tehnike sa srpskih onlajn prodavnica.

**Izvor podataka:** [Tehnomanija](https://www.tehnomanija.rs)
**Baza:** PostgreSQL · **Jezik:** Python · **GUI:** Tkinter

Zvanična postavka zadatka: `../PSZ_Projekat_2026.pdf` (u roditeljskom PSZ folderu,
van ovog repoa — videti i [`izvestaj/IZVESTAJ.md`](izvestaj/IZVESTAJ.md) za šablon izveštaja).

---

## Sadržaj zadataka

| # | Zadatak | Poeni | Status |
|---|---------|:-----:|:------:|
| 1 | Prikupljanje podataka (veb indekser + parser) | 10 | 🔧 skelet gotov, selektori potvrđeni na primeru frižidera — treba `--discover` za sve kategorije i pun `--run` |
| 2 | Analiza i preprocesiranje (clean baza ≥ 7000) | 10 | 🔧 skelet gotov, čeka podatke iz zadatka 1 |
| 3 | Vizuelizacija (matplotlib, PNG grafici) | 5 | 🔧 skelet gotov, čeka prečišćenu bazu |
| 4 | Linearna regresija od nule (gradijentni spust) | 12 | 🔧 implementirano, treba evaluacija/tjuning na realnim podacima |
| 5 | K-means klasterovanje od nule | 11 | 🔧 implementirano, treba evaluacija/tjuning na realnim podacima |
| 6 | Content-based recommender od nule | 12 | 🔧 implementirano, treba provera na realnim podacima |
| | **Ukupno** | **60** | |

> **Sledeći korak:** pokrenuti `python crawler.py --discover` da se potvrde/isprave
> slugovi kategorija u `config.py` (televizori i klima uređaji nisu pod
> `bela-tehnika/...` putanjom — videti komentar u `config.KATEGORIJE`), zatim
> `--test --kat <naziv>` za svaku kategoriju pre punog `--run`.

> Obavezno je uraditi bar jedan zadatak iz skupa {4, 5} za prolaz.
> Zadaci 4, 5 i 6 implementiraju algoritme **ručno** (bez gotovih ML
> biblioteka za trening); `scikit-learn` se koristi isključivo za
> verifikaciju tačnosti.

---

## Struktura projekta

```
PSZ_Projekat/
├── kod/
│   ├── zajednicko/          # deljeni moduli (db konekcija, util)
│   │   ├── db.py            # konekcija na PostgreSQL (čita .env)
│   │   └── util.py          # energetske klase, export, skaliranje
│   ├── 01_crawler/          # Zadatak 1: veb indekser + parser
│   │   ├── config.py        # kategorije, throttling, URL obrasci
│   │   ├── fetcher.py       # HTTP sloj (cloudscraper/requests/Selenium)
│   │   ├── parser.py        # ekstrakcija atributa (regex + BS4)
│   │   ├── db.py            # upis u primarnu bazu (upsert)
│   │   └── crawler.py       # orchestrator (--discover/--test/--run)
│   ├── 02_analiza/          # Zadatak 2: čišćenje + SQL upiti
│   ├── 03_vizuelizacija/    # Zadatak 3: grafici
│   ├── 04_regresija/        # Zadatak 4: linearna regresija
│   ├── 05_klasterovanje/    # Zadatak 5: K-means
│   ├── 06_preporuke/        # Zadatak 6: recommender
│   └── aplikacija/          # Tkinter GUI (objedinjuje 4, 5, 6)
├── baza/                    # SQL šeme i izvezeni dump-ovi
│   └── 01_schema_primarna.sql
├── izvestaj/                # finalni izveštaj + Excel izvozi
│   └── grafici/             # PNG grafikoni (zadatak 3)
├── podaci/                  # sample podaci / sirovi HTML (gitignored)
├── alati/                   # pomoćne skripte (pakovanje ZIP-a)
├── requirements.txt
├── .env.example             # šablon za konfiguraciju baze
└── Makefile                 # prečice za česte komande
```

---

## Brzo pokretanje

### 1. Zavisnosti

```bash
pip install -r requirements.txt
# Linux: tkinter se instalira posebno
sudo apt install python3-tk      # (samo ako nije već prisutan)
```

### 2. Konfiguracija baze

```bash
cp .env.example .env
# otvori .env i upiši svoju PostgreSQL lozinku
```

### 3. Inicijalizacija baze

```bash
createdb psz_primarna
psql -d psz_primarna -f baza/01_schema_primarna.sql
# ili: make db-init
```

### 4. Prikupljanje podataka (Zadatak 1)

```bash
cd kod/01_crawler

# KORAK A: proveri koje kategorije/paginacija rade na sajtu (bez upisa)
python crawler.py --discover

# KORAK B: test jedne kategorije — ispiše par proizvoda (bez upisa)
python crawler.py --test --kat televizor

# KORAK C: pun crawl sa upisom u bazu (može satima — radi throttling)
python crawler.py --run
```

> **Bitno:** pre punog `--run`, proveri `--test` izlaz. Ako su nazivi
> ili cene prazni, treba podesiti CSS selektore u `parser.py`
> (sve je izdvojeno u `SELECTORS` rečnik na vrhu fajla).

### Ostali zadaci

```bash
make analiza     # Zadatak 2: čišćenje + SQL izveštaji
make viz         # Zadatak 3: grafici u izvestaj/grafici/
make app         # Pokreni GUI (zadaci 4, 5, 6)
```

---

## Napomene o korektnom ponašanju (web scraping)

Crawler poštuje izvorni sajt:

- nasumična pauza **1.5–3.5 s** između zahteva (bez DoS opterećenja),
- eksponencijalni *backoff* pri greškama,
- rotacija `User-Agent` zaglavlja,
- prikupljaju se **isključivo javno dostupni** podaci o proizvodima
  (ne lični podaci).

---

## Pakovanje za predaju

```bash
bash alati/spakuj.sh <Indeks> <Ime> <Prezime>
# npr: bash alati/spakuj.sh 2023_0123 Vuk Prezime
# -> /tmp/2023_0123_Vuk_Prezime.zip  (sa folderima /kod /baza /izveštaj)
```