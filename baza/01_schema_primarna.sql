-- Primarna baza podataka (Zadatak 1)
-- Sirovi podaci prikupljeni veb indekserom, pre čišćenja.
-- Polja koja nisu pronađena u opisu proizvoda ostaju NULL.

CREATE TABLE IF NOT EXISTS proizvodi_primarna (
    id                  SERIAL PRIMARY KEY,

    -- identifikacija proizvoda na izvornom sajtu
    izvor               TEXT        NOT NULL,           -- npr. 'tehnomanija.rs'
    izvorni_id          TEXT,                            -- product-id / sku sa sajta
    url                 TEXT        NOT NULL UNIQUE,

    -- osnovni atributi
    naziv               TEXT        NOT NULL,
    brend               TEXT,
    kategorija          TEXT,                            -- npr. 'televizor', 'frizider'
    podkategorija       TEXT,                            -- slug podkategorije sa sajta

    -- cena i dostupnost
    cena                NUMERIC(12, 2),
    cena_pre_akcije     NUMERIC(12, 2),
    na_lageru           BOOLEAN,

    -- najčešće tehničke karakteristike (zajedničke za više kategorija)
    energetska_klasa    TEXT,                            -- npr. 'A+++', 'E'
    dijagonala_inch      NUMERIC(6, 2),                   -- televizori
    kapacitet_kg         NUMERIC(6, 2),                   -- mašine za pranje/sušenje/sudove
    zapremina_l          NUMERIC(8, 2),                   -- frižideri/zamrzivači/rerne
    snaga_w              NUMERIC(8, 2),                   -- klima uređaji, aspiratori, itd.

    -- sve sirove tehničke karakteristike sa stranice proizvoda, kao JSON
    -- (ključ = naziv atributa sa sajta, vrednost = tekstualna vrednost)
    sve_karakteristike   JSONB,

    -- metapodaci o prikupljanju
    datum_preuzimanja    TIMESTAMP   NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_primarna_kategorija ON proizvodi_primarna (kategorija);
CREATE INDEX IF NOT EXISTS idx_primarna_brend       ON proizvodi_primarna (brend);
CREATE INDEX IF NOT EXISTS idx_primarna_cena        ON proizvodi_primarna (cena);
