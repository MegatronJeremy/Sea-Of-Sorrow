-- Zadatak 2: SQL upiti nad revidiranom bazom (proizvodi_revidirana).
-- Rezultati ovih upita se izvoze u Excel pomoću izvezi_upite.py.

-- 1) Broj proizvoda po kategoriji
SELECT kategorija, count(*) AS broj_proizvoda
FROM proizvodi_revidirana
GROUP BY kategorija
ORDER BY broj_proizvoda DESC;

-- 2) Top 10 brendova po broju artikala
SELECT brend, count(*) AS broj_proizvoda
FROM proizvodi_revidirana
GROUP BY brend
ORDER BY broj_proizvoda DESC
LIMIT 10;

-- 3) Broj proizvoda sa energetskom klasom C (ili A+ po staroj klasifikaciji) ili boljom
--    (energetska_klasa_num: C=5, A+=8 -- videti zajednicko/util.py ENERGETSKE_KLASE)
SELECT count(*) AS broj_proizvoda
FROM proizvodi_revidirana
WHERE energetska_klasa_num >= 5;

-- 4) Broj proizvoda sa cenom do 50.000 dinara
SELECT count(*) AS broj_proizvoda
FROM proizvodi_revidirana
WHERE cena <= 50000;

-- 5) Top 30 televizora po najvećoj ceni
SELECT naziv, brend, cena, dijagonala_inch, energetska_klasa
FROM proizvodi_revidirana
WHERE kategorija = 'televizor'
ORDER BY cena DESC
LIMIT 30;

-- 6) Prosečna, minimalna i maksimalna cena po kategoriji
SELECT
    kategorija,
    count(*)                            AS broj_proizvoda,
    round(avg(cena), 2)                 AS prosecna_cena,
    min(cena)                           AS min_cena,
    max(cena)                           AS max_cena,
    round(stddev(cena), 2)              AS std_cena
FROM proizvodi_revidirana
GROUP BY kategorija
ORDER BY prosecna_cena DESC;

-- 7) Procenat proizvoda sa energetskom klasom A ili boljom, po kategoriji
SELECT
    kategorija,
    count(*)                                          AS ukupno,
    count(*) FILTER (WHERE energetska_klasa_num >= 7) AS klasa_A_ili_bolja,
    round(
        100.0 * count(*) FILTER (WHERE energetska_klasa_num >= 7) / count(*),
        1
    )                                                 AS procenat_klasa_A
FROM proizvodi_revidirana
WHERE energetska_klasa_num IS NOT NULL
GROUP BY kategorija
ORDER BY procenat_klasa_A DESC;

-- 8) Top 10 brendova po prosečnoj ceni (samo brendovi sa >= 20 proizvoda)
SELECT
    brend,
    count(*)                AS broj_proizvoda,
    round(avg(cena), 0)     AS prosecna_cena,
    round(min(cena), 0)     AS min_cena,
    round(max(cena), 0)     AS max_cena
FROM proizvodi_revidirana
GROUP BY brend
HAVING count(*) >= 20
ORDER BY prosecna_cena DESC
LIMIT 10;

-- 9) Dostupnost na lageru po kategoriji
SELECT
    kategorija,
    count(*)                                  AS ukupno,
    count(*) FILTER (WHERE na_lageru = true)  AS na_lageru,
    count(*) FILTER (WHERE na_lageru = false) AS nije_na_lageru,
    round(
        100.0 * count(*) FILTER (WHERE na_lageru = true) / count(*),
        1
    )                                         AS procenat_na_lageru
FROM proizvodi_revidirana
WHERE na_lageru IS NOT NULL
GROUP BY kategorija
ORDER BY procenat_na_lageru DESC;

-- 10) Frizideri grupisani po zapremini (mali/srednji/veliki)
SELECT
    CASE
        WHEN zapremina_l < 200  THEN 'mali (< 200 l)'
        WHEN zapremina_l <= 400 THEN 'srednji (200-400 l)'
        ELSE                         'veliki (> 400 l)'
    END                     AS velicina,
    count(*)                AS broj_proizvoda,
    round(avg(cena), 0)     AS prosecna_cena
FROM proizvodi_revidirana
WHERE kategorija = 'frizider' AND zapremina_l IS NOT NULL
GROUP BY velicina
ORDER BY min(zapremina_l);
