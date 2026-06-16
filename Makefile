.PHONY: db-init discover test-crawl crawl analiza viz app clean

# Zadatak 1
db-init:
	createdb $${DB_NAME:-psz_primarna}
	psql -d $${DB_NAME:-psz_primarna} -f baza/01_schema_primarna.sql

discover:
	cd kod/01_crawler && python crawler.py --discover

test-crawl:
	cd kod/01_crawler && python crawler.py --test --kat $(KAT)

crawl:
	cd kod/01_crawler && python crawler.py --run

# Zadatak 2
analiza:
	cd kod/02_analiza && python cisti_podatke.py && python izvezi_upite.py

# Zadatak 3
viz:
	cd kod/03_vizuelizacija && python generisi_grafike.py

# Zadaci 4-6 (GUI aplikacija)
app:
	cd kod/aplikacija && python app.py

clean:
	find . -name "__pycache__" -type d -exec rm -rf {} +
