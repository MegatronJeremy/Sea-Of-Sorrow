-- Primarna baza podataka (Zadatak 1) — SQLite sintaksa
-- Sirovi podaci prikupljeni veb indekserom, pre čišćenja.

CREATE TABLE IF NOT EXISTS proizvodi_primarna (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,

    -- identifikacija proizvoda na izvornom sajtu
    izvor               TEXT        NOT NULL,
    izvorni_id          TEXT,
    url                 TEXT        NOT NULL UNIQUE,

    -- osnovni atributi
    naziv               TEXT        NOT NULL,
    brend               TEXT,
    kategorija          TEXT,
    podkategorija       TEXT,

    -- cena i dostupnost
    cena                REAL,
    cena_pre_akcije     REAL,
    na_lageru           INTEGER,    -- 0/1 umesto BOOLEAN

    -- najčešće tehničke karakteristike
    energetska_klasa    TEXT,
    dijagonala_inch     REAL,
    kapacitet_kg        REAL,
    zapremina_l         REAL,
    snaga_w             REAL,

    -- sve sirove tehničke karakteristike kao JSON string (umesto JSONB)
    sve_karakteristike  TEXT,

    -- metapodaci
    datum_preuzimanja   TEXT        NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_primarna_kategorija ON proizvodi_primarna (kategorija);
CREATE INDEX IF NOT EXISTS idx_primarna_brend       ON proizvodi_primarna (brend);
CREATE INDEX IF NOT EXISTS idx_primarna_cena        ON proizvodi_primarna (cena);
