"""
Rich debug mod za PSZ projekat — provera okoline, konfiguracije i parsera.

Pokretanje iz korena projekta:
    python kod/debug.py           # osnovna provera (bez baze)
    python kod/debug.py --db      # + test konekcije na bazu
    python kod/debug.py --verbose # + ispis svih karakteristika iz parsera
    python kod/debug.py --all     # sve gore navedeno

Izlaz je strukturiran u sekcije radi lakog skeniranja.
"""
from __future__ import annotations

import argparse
import importlib
import platform
import sys
import textwrap
from pathlib import Path

# --- setup sys.path ---
_ROOT = Path(__file__).resolve().parent.parent          # Sea-Of-Sorrow/
_KOD = _ROOT / "kod"
for _d in (_KOD, _KOD / "01_crawler", _KOD / "04_regresija",
           _KOD / "05_klasterovanje", _KOD / "06_preporuke"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

# ──────────────────────────────────────────────────────────────────────────────

SEPARATOR = "-" * 64
OK   = "[OK]    "
WARN = "[UPOZ]  "
ERR  = "[ERR]   "
INFO = "[INFO]  "


def naslov(tekst: str) -> None:
    print(f"\n{SEPARATOR}")
    print(f"  {tekst}")
    print(SEPARATOR)


def proveri_python() -> None:
    naslov("1. Python okruženje")
    v = sys.version_info
    print(f"{INFO}Python {v.major}.{v.minor}.{v.micro} — {platform.system()} {platform.machine()}")
    if (v.major, v.minor) < (3, 10):
        print(f"{WARN}Preporučen Python >= 3.10 (current: {v.major}.{v.minor})")
    else:
        print(f"{OK}Verzija Pythona je podržana")


def proveri_pakete() -> None:
    naslov("2. Python paketi (requirements.txt)")
    paketi = [
        ("requests",       "requests"),
        ("bs4",            "beautifulsoup4"),
        ("lxml",           "lxml"),
        ("dotenv",         "python-dotenv"),
        ("pandas",         "pandas"),
        ("numpy",          "numpy"),
        ("matplotlib",     "matplotlib"),
        ("xlsxwriter",     "xlsxwriter"),
        ("sklearn",        "scikit-learn"),
    ]
    sve_ok = True
    for modul, ime_paketa in paketi:
        try:
            m = importlib.import_module(modul)
            verzija = getattr(m, "__version__", "?")
            print(f"{OK}{ime_paketa:<22} verzija {verzija}")
        except ImportError:
            print(f"{ERR}{ime_paketa:<22} NIJE INSTALIRAN  →  pip install {ime_paketa}")
            sve_ok = False
    if sve_ok:
        print(f"\n{OK}Svi paketi su dostupni.")


def proveri_env() -> None:
    naslov("3. Konfiguracija (.env)")
    env_fajl = _ROOT / ".env"
    example = _ROOT / ".env.example"
    if not env_fajl.exists():
        print(f"{INFO}.env fajl ne postoji — koristi se podrazumevano: podaci/psz.db")
        print(f"      cp {example} {env_fajl}")
        return

    from dotenv import dotenv_values
    vrednosti = dotenv_values(str(env_fajl))
    for kljuc, vrednost in vrednosti.items():
        if vrednost:
            maskirana = vrednost[:2] + "*" * max(0, len(vrednost) - 2)
        else:
            maskirana = "(prazno)"
        print(f"{INFO}{kljuc:<20} = {maskirana}")
    print(f"{OK}.env učitan ({len(vrednosti)} ključeva)")


def proveri_bazu() -> None:
    naslov("4. Konekcija na bazu (PostgreSQL)")
    try:
        from zajednicko.db import get_connection
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT version();")
        ver = cur.fetchone()[0]
        conn.close()
        print(f"{OK}Konekcija uspela.")
        print(f"{INFO}{textwrap.shorten(ver, 60)}")
    except Exception as e:
        print(f"{ERR}Konekcija neuspela: {e}")
        print(f"      Proveri DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD u .env")
        return

    try:
        from zajednicko.db import cursor as db_cursor
        with db_cursor() as cur:
            cur.execute("""
                SELECT table_name, (SELECT count(*) FROM information_schema.columns
                    WHERE table_name = t.table_name) AS br_kolona
                FROM information_schema.tables t
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tabele = cur.fetchall()
        if tabele:
            print(f"\n{INFO}Tabele u bazi:")
            for naziv, br_kol in tabele:
                print(f"      {naziv:<35} ({br_kol} kolona)")
        else:
            print(f"{WARN}Baza je prazna (nema tabela u 'public' shemi). Pokreni:")
            print(f"      psql -d psz_primarna -f baza/01_schema_primarna.sql")
    except Exception as e:
        print(f"{WARN}Nije uspelo listanje tabela: {e}")


def proveri_parser(verbose: bool = False) -> None:
    naslov("5. Parser (lokalni HTML fixture)")
    fixtures = _ROOT / "tests" / "fixtures"
    if not fixtures.exists():
        print(f"{WARN}Nema tests/fixtures/ direktorijuma.")
        return

    import parser as _parser  # 01_crawler/parser.py

    # --- listing ---
    listing_fajl = fixtures / "listing.html"
    if listing_fajl.exists():
        html = listing_fajl.read_text(encoding="utf-8")
        linkovi, sledeca = _parser.parsiraj_listing(html)
        print(f"{OK}parsiraj_listing: {len(linkovi)} linkova, "
              f"sledeća strana: {'DA' if sledeca else 'NE'}")
        if verbose:
            for l in linkovi:
                print(f"       → {l}")
    else:
        print(f"{WARN}listing.html ne postoji u tests/fixtures/")

    # --- proizvod ---
    za_testirati = [
        ("proizvod.html",           "frizider", "na lageru"),
        ("proizvod_nedostupan.html", "frizider", "nije na lageru"),
    ]
    for ime_fajla, kategorija, opis in za_testirati:
        fajl = fixtures / ime_fajla
        if not fajl.exists():
            print(f"{WARN}{ime_fajla} ne postoji")
            continue
        html = fajl.read_text(encoding="utf-8")
        podaci = _parser.parsiraj_proizvod(html, f"https://www.tehnomanija.rs/{ime_fajla}", kategorija)
        if podaci is None:
            print(f"{ERR}{ime_fajla}: parsiraj_proizvod vratio None — proveri selektore!")
        else:
            print(f"{OK}{ime_fajla} ({opis}):")
            print(f"       naziv={podaci['naziv']!r}")
            print(f"       cena={podaci['cena']}  na_lageru={podaci['na_lageru']}")
            print(f"       energ.klasa={podaci['energetska_klasa']!r}  "
                  f"zapremina={podaci['zapremina_l']} l")
            print(f"       {len(podaci['sve_karakteristike'])} karakteristika pronađeno")
            if verbose and podaci["sve_karakteristike"]:
                for k, v in podaci["sve_karakteristike"].items():
                    print(f"         {k}: {v}")


def proveri_ml_module() -> None:
    naslov("6. ML moduli (smoke test bez baze)")
    import numpy as np

    # --- regresija ---
    try:
        from regresija import LinearnaRegresijaGD, r2_skor
        rng = np.random.default_rng(0)
        X = rng.normal(0, 1, (100, 2))
        y = 2 * X[:, 0] - X[:, 1] + rng.normal(0, 0.1, 100)
        model = LinearnaRegresijaGD(stopa_ucenja=0.1, broj_iteracija=500).fit(X, y)
        r2 = r2_skor(y, model.predict(X))
        print(f"{OK}Regresija: R²={r2:.3f} (očekivano > 0.90)")
    except Exception as e:
        print(f"{ERR}Regresija: {e}")

    # --- kmeans ---
    try:
        from kmeans import KMeans, silhouette_score_rucno
        rng = np.random.default_rng(1)
        X = np.vstack([rng.normal(c, 0.3, (40, 2)) for c in [[0, 0], [5, 0], [2.5, 4]]])
        model = KMeans(k=3, seed=1).fit(X)
        skor = silhouette_score_rucno(X, model.labele)
        print(f"{OK}KMeans (k=3): silhouette={skor:.3f} (očekivano > 0.70)")
    except Exception as e:
        print(f"{ERR}KMeans: {e}")

    # --- recommender ---
    try:
        import pandas as pd
        from recommender import ContentBasedRecommender, kosinusna_slicnost
        v1, v2 = np.array([1.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0])
        assert abs(kosinusna_slicnost(v1, v2)) < 1e-9, "ortogonalni vektori moraju dati 0"

        df_test = pd.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "naziv": ["Samsung frižider A", "LG frižider B", "Samsung veš mašina",
                      "LG veš mašina", "Bosch frižider C"],
            "brend": ["Samsung", "LG", "Samsung", "LG", "Bosch"],
            "kategorija": ["frizider", "frizider", "ves_masina", "ves_masina", "frizider"],
            "cena": [80000.0, 65000.0, 50000.0, 45000.0, 70000.0],
            "energetska_klasa_num": [7, 6, 5, 5, 8],
            "dijagonala_inch": [None, None, None, None, None],
            "kapacitet_kg": [None, None, 8.0, 7.0, None],
            "zapremina_l": [500.0, 400.0, None, None, 450.0],
            "snaga_w": [None, None, None, None, None],
        })
        rec = ContentBasedRecommender(df_test)
        preporuke = rec.preporuci(1, top_n=2)
        print(f"{OK}Recommender: {len(preporuke)} preporuka za id=1 (frizider)")
        for _, red in preporuke.iterrows():
            print(f"       → {red['naziv']}  sličnost={red['slicnost']:.3f}")
    except Exception as e:
        print(f"{ERR}Recommender: {e}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db",      action="store_true", help="testiraj konekciju na bazu")
    ap.add_argument("--verbose", action="store_true", help="ispiši više detalja")
    ap.add_argument("--all",     action="store_true", help="sve provere uključujući bazu")
    args = ap.parse_args()

    if args.all:
        args.db = True
        args.verbose = True

    proveri_python()
    proveri_pakete()
    proveri_env()

    if args.db:
        proveri_bazu()
    else:
        naslov("4. Konekcija na bazu")
        print(f"{INFO}Preskočeno (dodaj --db da testiraš konekciju)")

    proveri_parser(verbose=args.verbose)
    proveri_ml_module()

    print(f"\n{SEPARATOR}")
    print("  Debug provera završena.")
    print(SEPARATOR)


if __name__ == "__main__":
    main()
