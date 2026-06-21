# Sea-Of-Sorrow

# PSZ Projekat 2025/2026 — Pronalaženje skrivenog znanja

Projektni zadatak iz predmeta *Pronalaženje skrivenog znanja*. Tema:
prikupljanje, analiza, vizuelizacija i mašinsko učenje nad podacima o
proizvodima bele tehnike sa srpskih onlajn prodavnica.

**Izvor podataka:** [Tehnomanija](https://www.tehnomanija.rs)
**Baza:** PostgreSQL · **Jezik:** Python 3.10+ · **GUI:** Tkinter

---

## Sadržaj zadataka

| # | Zadatak | Poeni | Status |
|---|---------|:-----:|:------:|
| 1 | Prikupljanje podataka (veb indekser + parser) | 10 | ✅ 8.065 zapisa, 3 izvora, paralelni scrape |
| 2 | Analiza i preprocesiranje (clean baza ≥7000) | 10 | ✅ 7.356 prečišćenih, IQR outlieri, Excel izvoz |
| 3 | Vizuelizacija (matplotlib, PNG grafici) | 5 | ✅ radi |
| 4 | Linearna regresija od nule (gradijentni spust) | 12 | ✅ R² ≈ 0.55 na realnim podacima |
| 5 | K-means klasterovanje od nule | 11 | ✅ silhouette ≈ 0.48 |
| 6 | Content-based recommender od nule | 12 | ✅ radi |
| | **Ukupno** | **60** | |

**Izvori podataka (paralelni scrape):**
| Sajt | Tehnologija | Zapisa |
|---|---|---|
| gigatron.rs | Next.js RSC payload | ~4.400 |
| tehnomanija.rs | statički Magento HTML | ~2.750 |
| metalac.rs | statički HTML + spec strane | ~940 |

> Zadaci 4, 5 i 6 implementiraju algoritme **ručno** (bez gotovih ML
> biblioteka za trening); `scikit-learn` se koristi isključivo za
> verifikaciju tačnosti.

---

## Preduslov: PostgreSQL

Postavka zahteva PostgreSQL (ili MySQL). Instaliraj PostgreSQL za Windows sa
<https://www.postgresql.org/download/windows/> i zapamti lozinku `postgres`
korisnika. Setup skripta sama kreira bazu i tabele — nije potreban `createdb`.

## Brzo pokretanje (Windows)

```powershell
# 1. Setup: pronalazi Python 3.10+, pravi .venv, instalira zavisnosti,
#    kreira .env i inicijalizuje PostgreSQL bazu (upisi DB_PASSWORD u .env)
.\setup.ps1

# 2. Pokretanje komandi — interaktivni meni:
.\run.ps1

#    ili direktno:
.\run.ps1 crawl        # paralelni scrape sa sva 3 izvora u bazu
.\run.ps1 analiza      # ciscenje + izvoz SQL upita u Excel
.\run.ps1 viz          # generisi grafike (PNG)
.\run.ps1 app          # GUI aplikacija (zadaci 4, 5, 6)
.\run.ps1 test         # automatski testovi
.\run.ps1 db-dump      # izvoz baza u baza\*_dump.sql (za predaju)
.\run.ps1 debug        # provera okruzenja
```

Crawl bira izvore: `.\run.ps1 crawl -Izvori gigatron,metalac` (default: sva tri).

**Prikupljanje (Zadatak 1)** radi preko orchestratora `kod/01_crawler/scrape.py`
koji svaki izvor pokreće u **zasebnom thread-u (paralelno)** — pošto su to
različiti serveri, ne povećava opterećenje ni jednom (nema dodatnog rizika od
bana), a ukupno vreme ≈ najsporiji sajt. **Watchdog** automatski prekida izvor
bez napretka 240s, pa scrape ne može da visi. Dodavanje novog sajta = novi
modul (`run(upsert_fn, log, stop_event)`) + jedan red u `IZVORI`.

> Na Linux/Mac postoji i `Makefile` sa istim ciljevima (`make setup`, `make crawl`, `make db-dump`, ...).

---

## Struktura projekta

```
Sea-Of-Sorrow/
├── kod/
│   ├── zajednicko/          # deljeni moduli
│   │   ├── db.py            # konekcija na PostgreSQL (čita .env)
│   │   └── util.py          # energetske klase, export, skaliranje
│   ├── 01_crawler/          # Zadatak 1: veb indekser + parser
│   │   ├── config.py        # kategorije, throttling, CSS selektori
│   │   ├── fetcher.py       # HTTP sloj (curl_cffi — Chrome TLS fingerprint)
│   │   ├── parser.py        # ekstrakcija atributa (BeautifulSoup)
│   │   ├── db.py            # upis u primarnu bazu (upsert)
│   │   └── crawler.py       # orchestrator (--discover/--test/--run)
│   ├── 02_analiza/          # Zadatak 2: čišćenje + SQL upiti
│   ├── 03_vizuelizacija/    # Zadatak 3: grafici
│   ├── 04_regresija/        # Zadatak 4: linearna regresija
│   ├── 05_klasterovanje/    # Zadatak 5: K-means
│   ├── 06_preporuke/        # Zadatak 6: recommender
│   ├── aplikacija/          # Tkinter GUI (objedinjuje 4, 5, 6)
│   ├── db_init.py           # kreira PostgreSQL bazu + tabele
│   └── debug.py             # rich debug provera okruženja
├── baza/                    # SQL šeme (PostgreSQL sintaksa)
│   ├── 01_schema_primarna.sql
│   └── 02_schema_revidirana.sql
├── izvestaj/                # Excel izvozi + grafici/ (PNG)
├── podaci/                  # sirovi podaci / HTML (gitignored)
├── tests/                   # 122 pytest testa (rade bez baze/interneta)
├── setup.ps1 · run.ps1      # Windows skripte
├── Makefile                 # prečice (Linux/Mac)
├── requirements.txt
└── pyproject.toml           # Python >= 3.10, pytest config
```

---

## Aplikacija (zadaci 4, 5, 6)

GUI je u NERV/terminal stilu, sa tri taba:

- **Regresija cene** — uneseš karakteristike uređaja → model predviđa cenu.
  Klikabilni primeri + grafovi konvergencije troška i predviđeno-vs-stvarno.
- **Klasterovanje** — biraš promenljive i težine (zbir 100%) i K → K-means grupiše
  proizvode. Preseti + 2D scatter klastera sa centroidima.
- **Preporuke** — uneseš ID proizvoda → top 5 najsličnijih (ista kategorija).
  Tabela se sortira klikom na zaglavlje.

---

## Napomene o korektnom ponašanju (web scraping)

Crawler poštuje izvorni sajt:

- nasumična pauza **1.5–3.5 s** između zahteva (bez DoS opterećenja),
- eksponencijalni *backoff* pri greškama (uključ. 403/429),
- rotacija `User-Agent` zaglavlja, ograničen broj paralelnih workera,
- prikupljaju se **isključivo javno dostupni** podaci o proizvodima.

---

## Testovi

```powershell
.\run.ps1 test        # ili: python -m pytest
```

122 testa pokrivaju parser, čišćenje, sve tri ML implementacije (regresija,
K-means, recommender) i vizuelizaciju — bez konekcije na bazu i bez interneta.
