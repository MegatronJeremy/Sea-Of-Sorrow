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
