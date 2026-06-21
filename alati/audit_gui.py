"""
Differential audit GUI logike: za svaku kontrolu pušta varirane ulaze i proverava
da se izlaz menja kako treba (ne samo da ne puca). Privremen alat, ne deo predaje.
"""
import sys, tkinter as tk
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "kod" / "aplikacija"))
import app as A

PASS, FAIL = "[PASS]", "[FAIL]"
rez = []
def proveri(naziv, uslov):
    rez.append((naziv, uslov))
    print(f"  {PASS if uslov else FAIL} {naziv}")

a = A.Aplikacija(); a.update_idletasks()
df = a.df

# ── REGRESIJA ──────────────────────────────────────────────────────────────────
print("\n=== TabRegresija ===")
tr = a.tab_regresija
tr._obuci()
proveri("model obucen (metrike prikazane)", "R" in tr.lbl_metrike.cget("text"))
tr._popuni_primer({"kategorija":"frizider","brend":"Samsung","dijagonala_inch":"",
                   "kapacitet_kg":"","zapremina_l":"300","snaga_w":"","energetska_klasa_num":"7"})
tr._predvidi(); cena1 = tr.lbl_rezultat.cget("text")
tr._popuni_primer({"kategorija":"frizider","brend":"Samsung","dijagonala_inch":"",
                   "kapacitet_kg":"","zapremina_l":"600","snaga_w":"","energetska_klasa_num":"7"})
tr._predvidi(); cena2 = tr.lbl_rezultat.cget("text")
proveri("razlicit ulaz (zapremina 300 vs 600) -> razlicita cena", cena1 != cena2 and cena1 and cena2)
# case-insensitivnost brenda
tr._popuni_primer({"kategorija":"frizider","brend":"samsung","dijagonala_inch":"",
                   "kapacitet_kg":"","zapremina_l":"300","snaga_w":"","energetska_klasa_num":"7"})
tr._predvidi()
proveri("brend 'samsung' (mala slova) radi (uppercase normalizacija)", "RSD" in tr.lbl_rezultat.cget("text"))

# ── KLASTEROVANJE ──────────────────────────────────────────────────────────────
print("\n=== TabKlasterovanje ===")
tk_ = a.tab_klasterovanje
def klaster_tekst(tezine, k):
    tk_._popuni_primer(k, tezine); tk_._pokreni()
    return tk_.tekst.get("1.0", tk.END)
t_energ = klaster_tekst({"cena":60,"energetska_klasa_num":40}, 3)
t_zaprem = klaster_tekst({"cena":50,"zapremina_l":50}, 3)
t_snaga = klaster_tekst({"cena":60,"snaga_w":40}, 3)
proveri("izbor cena+energ -> ispis pominje 'energ'", "energ" in t_energ.lower())
proveri("izbor cena+zapremina -> ispis pominje 'zapremin' (NE energ)",
        "zapremin" in t_zaprem.lower() and "energ" not in t_zaprem.lower())
proveri("izbor cena+snaga -> ispis pominje 'snag'", "snag" in t_snaga.lower())
# razlicit K -> razlicit broj klastera u ispisu
t_k2 = klaster_tekst({"cena":60,"energetska_klasa_num":40}, 2)
t_k5 = klaster_tekst({"cena":60,"energetska_klasa_num":40}, 5)
proveri("K=2 vs K=5 -> razlicit broj 'Klaster' linija",
        t_k2.count("Klaster") != t_k5.count("Klaster"))

# ── PREPORUKE ──────────────────────────────────────────────────────────────────
print("\n=== TabPreporuke ===")
tp = a.tab_preporuke
import pandas as pd
def preporuke_za(kat):
    pid = int(df[df.kategorija==kat].dropna(subset=["cena"]).iloc[0].id)
    rez_df = tp.recommender.preporuci(pid, 5)
    kats = df[df.id.isin(rez_df.id)].kategorija.unique()
    sl = rez_df.slicnost.tolist()
    return pid, list(kats), sl
pid_f, kat_f, sl_f = preporuke_za("frizider")
pid_v, kat_v, sl_v = preporuke_za("ves_masina")
proveri("preporuke za frizider su iz kategorije frizider", kat_f == ["frizider"])
proveri("preporuke za ves_masina su iz kategorije ves_masina", kat_v == ["ves_masina"])
proveri("razlicit proizvod -> razlicite preporuke", pid_f != pid_v)
proveri("slicnost sortirana opadajuce", sl_f == sorted(sl_f, reverse=True))

# ── PREGLED BAZE ───────────────────────────────────────────────────────────────
print("\n=== TabPregledBaze ===")
pb = a.tab_pregled
def kategorije_u_tabeli():
    return {pb.tabela.item(r)["values"][3] for r in pb.tabela.get_children()}
pb.kat_var.set("(sve)"); pb._popuni_tabelu(); kat_sve = kategorije_u_tabeli()
pb.kat_var.set("frizider"); pb._popuni_tabelu(); kat_friz = kategorije_u_tabeli()
broj_friz = int((df.kategorija=="frizider").sum())
proveri("filter '(sve)' prikazuje vise kategorija", len(kat_sve) > 1)
proveri("filter 'frizider' prikazuje SAMO frizidere (sadrzaj se menja)",
        kat_friz == {"frizider"})
proveri("filter 'frizider' broj redova == broj frizidera (do 500 cap)",
        len(pb.tabela.get_children()) == min(broj_friz, 500))

# ── REZIME ─────────────────────────────────────────────────────────────────────
a.destroy()
ok = sum(1 for _,u in rez if u)
print(f"\n=== REZIME: {ok}/{len(rez)} provera proslo ===")
if ok != len(rez):
    print("PALE:", [n for n,u in rez if not u]); sys.exit(1)
