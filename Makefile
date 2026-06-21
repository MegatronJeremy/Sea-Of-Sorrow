.PHONY: install db-init discover test-crawl crawl analiza viz app test debug debug-db clean

# ── Setup ─────────────────────────────────────────────────────────────────────

## Automatski setup (pronalazi Python 3.10+, pravi venv, instalira, inicijalizuje bazu)
setup:
	powershell -ExecutionPolicy Bypass -File setup.ps1

## Instalacija Python zavisnosti (pretpostavlja aktivan venv)
install:
	pip install -r requirements.txt

## Inicijalizacija PostgreSQL baze (kreira bazu + tabele)
db-init:
	python kod/db_init.py

# ── Zadatak 1: Crawler ────────────────────────────────────────────────────────

## Proveri koje kategorije postoje na sajtu (bez upisa)
discover:
	cd kod/01_crawler && python crawler.py --discover

## Testiraj parsiranje jedne kategorije: make test-crawl KAT=frizider
test-crawl:
	cd kod/01_crawler && python crawler.py --test --kat $(KAT)

## Paralelni scrape sa svih izvora (gigatron + tehnomanija) u bazu
crawl:
	cd kod/01_crawler && python scrape.py

## Scrape samo izabranih izvora: make crawl-izvori IZVORI=gigatron
crawl-izvori:
	cd kod/01_crawler && python scrape.py --izvori $(IZVORI)

## Crawl samo jedne tehnomanija kategorije: make crawl-kat KAT=frizider
crawl-kat:
	cd kod/01_crawler && python crawler.py --run --kat $(KAT)

# ── Zadatak 2: Analiza ────────────────────────────────────────────────────────

## Čišćenje podataka + izvoz SQL upita u Excel
analiza:
	cd kod/02_analiza && python cisti_podatke.py && python izvezi_upite.py

# ── Zadatak 3: Vizuelizacija ──────────────────────────────────────────────────

## Generisanje grafika (PNG u izvestaj/grafici/)
viz:
	cd kod/03_vizuelizacija && python generisi_grafike.py

# ── Zadaci 4-6: GUI aplikacija ────────────────────────────────────────────────

## Pokreni GUI (regresija, klasterovanje, preporuke)
app:
	cd kod/aplikacija && python app.py

# ── Testovi i debug ───────────────────────────────────────────────────────────

## Automatski testovi (rade bez baze, ~10s)
test:
	python -m pytest

## Provera okruženja i parsera (bez baze)
debug:
	python kod/debug.py

## Provera okruženja + test konekcije na bazu
debug-db:
	python kod/debug.py --db --verbose

# ── Čišćenje ──────────────────────────────────────────────────────────────────

## Ukloni __pycache__ i .pyc fajlove
clean:
	find . -name "__pycache__" -type d -exec rm -rf {} +
	find . -name "*.pyc" -delete

# ── Help ──────────────────────────────────────────────────────────────────────

help:
	@echo ""
	@echo "Dostupne komande:"
	@echo "  make setup        -- instaliraj zavisnosti + inicijalizuj bazu"
	@echo "  make install      -- pip install -r requirements.txt"
	@echo "  make db-init      -- kreiraj PostgreSQL bazu + tabele"
	@echo ""
	@echo "  make discover     -- proveri kategorije na sajtu (bez upisa)"
	@echo "  make test-crawl KAT=frizider  -- testiraj parser za jednu kategoriju"
	@echo "  make crawl        -- pun crawl svih kategorija"
	@echo "  make crawl-kat KAT=frizider   -- crawl jedne kategorije"
	@echo ""
	@echo "  make analiza      -- cisti_podatke + izvezi_upite (Excel)"
	@echo "  make viz          -- generisi grafike (PNG)"
	@echo "  make app          -- pokreni GUI aplikaciju"
	@echo ""
	@echo "  make test         -- automatski testovi (bez baze)"
	@echo "  make debug        -- provera okoline i parsera"
	@echo "  make debug-db     -- provera okoline + baze"
	@echo "  make clean        -- ukloni pycache"
	@echo ""
