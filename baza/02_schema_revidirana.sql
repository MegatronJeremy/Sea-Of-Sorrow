-- Revidirana (prečišćena) baza podataka (Zadatak 2)
-- Popunjava se iz proizvodi_primarna nakon preprocesiranja (kod/02_analiza/cisti_podatke.py).
-- Sadrži samo zapise sa adekvatnim brojem popunjenih atributa (min. 7000 zapisa).

CREATE TABLE IF NOT EXISTS proizvodi_revidirana (
    id                  SERIAL PRIMARY KEY,
    primarni_id         INTEGER REFERENCES proizvodi_primarna (id),

    izvor               TEXT        NOT NULL,
    naziv               TEXT        NOT NULL,
    brend               TEXT        NOT NULL,
    kategorija          TEXT        NOT NULL,

    cena                NUMERIC(12, 2) NOT NULL,
    na_lageru           BOOLEAN,

    energetska_klasa    TEXT,
    energetska_klasa_num SMALLINT,           -- numerička kodifikacija: G=1 ... A+++=10 (util.py)
    dijagonala_inch      NUMERIC(6, 2),
    kapacitet_kg          NUMERIC(6, 2),
    zapremina_l           NUMERIC(8, 2),
    snaga_w               NUMERIC(8, 2),

    sve_karakteristike    JSONB,

    datum_preuzimanja     TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_revid_kategorija ON proizvodi_revidirana (kategorija);
CREATE INDEX IF NOT EXISTS idx_revid_brend       ON proizvodi_revidirana (brend);
CREATE INDEX IF NOT EXISTS idx_revid_cena        ON proizvodi_revidirana (cena);
CREATE INDEX IF NOT EXISTS idx_revid_energklasa  ON proizvodi_revidirana (energetska_klasa_num);
