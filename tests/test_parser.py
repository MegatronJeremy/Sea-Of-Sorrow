"""
Testovi za kod/01_crawler/parser.py

Svi testovi koriste lokalne HTML fixture fajlove — nema HTTP zahteva.
sys.path za 01_crawler se postavlja u conftest.py.
"""
from __future__ import annotations

import pytest

# conftest.py dodaje kod/01_crawler na sys.path
import parser as _parser  # modul iz 01_crawler/

parsiraj_listing = _parser.parsiraj_listing
parsiraj_proizvod = _parser.parsiraj_proizvod
apsolutni_url = _parser.apsolutni_url


# ── parsiraj_listing ─────────────────────────────────────────────────────────

class TestParsirajListing:
    def test_vraca_listu_linkova(self, listing_html):
        linkovi, _ = parsiraj_listing(listing_html)
        assert len(linkovi) == 3

    def test_linkovi_su_apsolutni_url(self, listing_html):
        linkovi, _ = parsiraj_listing(listing_html)
        for link in linkovi:
            assert link.startswith("http"), f"Očekivan apsolutni URL, dobijeno: {link}"

    def test_vraca_sledecu_stranicu(self, listing_html):
        _, sledeca = parsiraj_listing(listing_html)
        assert sledeca is not None
        assert "p=2" in sledeca

    def test_prazan_html_nema_linkova(self, prazan_html):
        linkovi, sledeca = parsiraj_listing(prazan_html)
        assert linkovi == []
        assert sledeca is None

    def test_nema_duplikata(self, listing_html):
        linkovi, _ = parsiraj_listing(listing_html)
        assert len(linkovi) == len(set(linkovi))


# ── parsiraj_proizvod ─────────────────────────────────────────────────────────

class TestParsirajProizvod:
    URL1 = "https://www.tehnomanija.rs/samsung-frizider-123456/"
    URL2 = "https://www.tehnomanija.rs/lg-frizider-789012/"

    def test_vraca_recnik(self, proizvod_html):
        podaci = parsiraj_proizvod(proizvod_html, self.URL1, "frizider")
        assert isinstance(podaci, dict)

    def test_naziv_parsiran(self, proizvod_html):
        podaci = parsiraj_proizvod(proizvod_html, self.URL1, "frizider")
        assert "Samsung" in podaci["naziv"]

    def test_cena_parsirana(self, proizvod_html):
        podaci = parsiraj_proizvod(proizvod_html, self.URL1, "frizider")
        assert podaci["cena"] == pytest.approx(89999.00)

    def test_dostupnost_na_lageru(self, proizvod_html):
        podaci = parsiraj_proizvod(proizvod_html, self.URL1, "frizider")
        assert podaci["na_lageru"] is True

    def test_dostupnost_nije_na_lageru(self, proizvod_nedostupan_html):
        podaci = parsiraj_proizvod(proizvod_nedostupan_html, self.URL2, "frizider")
        assert podaci["na_lageru"] is False

    def test_energetska_klasa_parsirana(self, proizvod_html):
        podaci = parsiraj_proizvod(proizvod_html, self.URL1, "frizider")
        assert podaci["energetska_klasa"] == "D"

    def test_zapremina_parsirana(self, proizvod_html):
        podaci = parsiraj_proizvod(proizvod_html, self.URL1, "frizider")
        assert podaci["zapremina_l"] == pytest.approx(652.0)

    def test_import_specifikacija_ignorisana(self, proizvod_html):
        podaci = parsiraj_proizvod(proizvod_html, self.URL1, "frizider")
        # "import specifikacija" red mora biti isfiltriran
        assert "import specifikacija" not in podaci["sve_karakteristike"]

    def test_sve_karakteristike_recnik(self, proizvod_html):
        podaci = parsiraj_proizvod(proizvod_html, self.URL1, "frizider")
        assert isinstance(podaci["sve_karakteristike"], dict)
        assert len(podaci["sve_karakteristike"]) >= 2

    def test_prazan_html_vraca_none(self, prazan_html):
        podaci = parsiraj_proizvod(prazan_html, self.URL1, "frizider")
        assert podaci is None

    def test_kategorija_sacuvana(self, proizvod_html):
        podaci = parsiraj_proizvod(proizvod_html, self.URL1, "frizider")
        assert podaci["kategorija"] == "frizider"

    def test_url_sacuvan(self, proizvod_html):
        podaci = parsiraj_proizvod(proizvod_html, self.URL1, "frizider")
        assert podaci["url"] == self.URL1

    def test_alternativni_selektor_tabele(self, proizvod_nedostupan_html):
        # fixture koristi "data table additional-attributes" (alternativni CSS selektor)
        podaci = parsiraj_proizvod(proizvod_nedostupan_html, self.URL2, "frizider")
        assert podaci is not None
        assert podaci["energetska_klasa"] == "C"

    def test_energetska_klasa_nedostupnog(self, proizvod_nedostupan_html):
        podaci = parsiraj_proizvod(proizvod_nedostupan_html, self.URL2, "frizider")
        assert podaci["zapremina_l"] == pytest.approx(387.0)


# ── apsolutni_url ─────────────────────────────────────────────────────────────

class TestApsolutniUrl:
    def test_vec_apsolutan(self):
        url = "https://www.tehnomanija.rs/proizvod/123/"
        assert apsolutni_url(url) == url

    def test_relativan_sa_slash(self):
        result = apsolutni_url("/bela-tehnika/frizideri/")
        assert result.startswith("https://")
        assert "/bela-tehnika/frizideri/" in result

    def test_relativan_bez_slash(self):
        result = apsolutni_url("bela-tehnika/frizideri/")
        assert result.startswith("https://")
        assert "bela-tehnika/frizideri/" in result
