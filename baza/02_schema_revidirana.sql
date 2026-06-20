-- Revidirana (prečišćena) baza podataka (Zadatak 2) — SQLite sintaksa
-- Popunjava se iz proizvodi_primarna nakon preprocesiranja (kod/02_analiza/cisti_podatke.py).

CREATE TABLE IF NOT EXISTS proizvodi_revidirana (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    primarni_id          INTEGER REFERENCES proizvodi_primarna (id),

    izvor                TEXT    NOT NULL,
    naziv                TEXT    NOT NULL,
    brend                TEXT    NOT NULL,
    kategorija           TEXT    NOT NULL,

    cena                 REAL    NOT NULL,
    na_lageru            INTEGER,                -- 0/1

    energetska_klasa     TEXT,
    energetska_klasa_num INTEGER,               -- G=1 ... A+++=10 (util.py)
    dijagonala_inch      REAL,
    kapacitet_kg         REAL,
    zapremina_l          REAL,
    snaga_w              REAL,

    sve_karakteristike   TEXT,                  -- JSON string

    datum_preuzimanja    TEXT
);

CREATE INDEX IF NOT EXISTS idx_revid_kategorija ON proizvodi_revidirana (kategorija);
CREATE INDEX IF NOT EXISTS idx_revid_brend       ON proizvodi_revidirana (brend);
CREATE INDEX IF NOT EXISTS idx_revid_cena        ON proizvodi_revidirana (cena);
CREATE INDEX IF NOT EXISTS idx_revid_energklasa  ON proizvodi_revidirana (energetska_klasa_num);
