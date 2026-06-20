"""
Glavna GUI aplikacija (Tkinter) — objedinjuje zadatke 4 (regresija),
5 (K-means klasterovanje) i 6 (preporuke proizvoda).

Pokretanje:
    python kod/aplikacija/app.py
"""
from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

sys.path.append(str(Path(__file__).resolve().parents[1]))
from zajednicko.db import get_connection  # noqa: E402
from zajednicko.util import normalizuj     # noqa: E402

sys.path.append(str(Path(__file__).resolve().parents[1] / "04_regresija"))
sys.path.append(str(Path(__file__).resolve().parents[1] / "05_klasterovanje"))
sys.path.append(str(Path(__file__).resolve().parents[1] / "06_preporuke"))

from regresija import LinearnaRegresijaGD, pripremi_podatke, podeli_train_test, r2_skor, rmse  # noqa: E402
from kmeans import KMeans, silhouette_score_rucno, interpretiraj_klaster                        # noqa: E402
from recommender import ContentBasedRecommender                                                  # noqa: E402

# ── Paleta boja (NERV / MAGI terminal estetika) ───────────────────────────────
BG       = "#020403"   # skoro crna pozadina
BG2      = "#0a0f0c"   # karte / frejmovi (tamno zelenkasta)
BORDER   = "#1f3d2b"   # prigusene zelene ivice
ACCENT   = "#00ff41"   # neon matrix zelena (naglasak)
GREEN    = "#00ff41"   # uspeh
AMBER    = "#ff9f1c"   # NERV amber (sekundarni naglasak)
RED      = "#ff003c"   # alarm crvena
TEXT     = "#b6ffcb"   # glavni tekst (svetlo zelena)
MUTED    = "#4f8c6a"   # sekundarni tekst (prigusena zelena)
FONT     = ("Consolas", 10)
FONT_SM  = ("Consolas", 9)
FONT_LG  = ("Consolas", 13, "bold")
FONT_HDR = ("Consolas", 11, "bold")

# Paleta boja za klastere (vivid na crnom)
KLASTER_BOJE = ["#00ff41", "#ff9f1c", "#00d4ff", "#ff003c",
                "#c77dff", "#ffe600", "#ff6ec7", "#7CFC00"]


def dark_osu(ax, poruka: str = ""):
    """Primeni dark (NERV) stil na matplotlib osu."""
    ax.clear()
    ax.set_facecolor(BG)
    for strana in ax.spines.values():
        strana.set_color(BORDER)
    ax.tick_params(colors=MUTED, labelsize=7)
    ax.xaxis.label.set_color(TEXT)
    ax.yaxis.label.set_color(TEXT)
    ax.title.set_color(ACCENT)
    if poruka:
        ax.text(0.5, 0.5, poruka, ha="center", va="center",
                color=MUTED, fontsize=9, transform=ax.transAxes)
        ax.set_xticks([]); ax.set_yticks([])


def ucitaj_revidiranu() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM proizvodi_revidirana;", conn)
    conn.close()
    return df


def stil_btn(btn: tk.Button, tip: str = "primary"):
    boja = ACCENT if tip == "primary" else AMBER
    btn.config(
        bg=BG, fg=boja, font=("Consolas", 10, "bold"), relief="flat", bd=0,
        activebackground=boja, activeforeground=BG,
        highlightthickness=1, highlightbackground=boja, highlightcolor=boja,
        cursor="hand2", padx=14, pady=6
    )


def kartica(roditelj, tekst: str = "", **kw) -> tk.LabelFrame:
    f = tk.LabelFrame(roditelj, text=f"  {tekst}  " if tekst else "",
                      bg=BG2, fg=MUTED, font=FONT_SM,
                      relief="flat", bd=1, highlightthickness=1,
                      highlightbackground=BORDER, **kw)
    return f


def lbl(roditelj, tekst: str, fg=TEXT, font=FONT, **kw) -> tk.Label:
    return tk.Label(roditelj, text=tekst, bg=roditelj["bg"] if hasattr(roditelj, "__getitem__") else BG2,
                    fg=fg, font=font, **kw)


def entry(roditelj, sirina: int = 20, placeholder: str = "") -> tk.Entry:
    e = tk.Entry(roditelj, width=sirina, bg=BG, fg=TEXT, font=FONT,
                 insertbackground=ACCENT, relief="flat", bd=1,
                 highlightthickness=1, highlightbackground=BORDER,
                 highlightcolor=ACCENT)
    if placeholder:
        e.insert(0, placeholder)
        e.config(fg=MUTED)

        def _on_focus_in(ev):
            if e.get() == placeholder:
                e.delete(0, tk.END)
                e.config(fg=TEXT)

        def _on_focus_out(ev):
            if not e.get():
                e.insert(0, placeholder)
                e.config(fg=MUTED)

        e.bind("<FocusIn>", _on_focus_in)
        e.bind("<FocusOut>", _on_focus_out)
    return e


# ── Aplikacija ────────────────────────────────────────────────────────────────

class Aplikacija(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PSZ — Sea of Sorrow")
        self.geometry("1000x700")
        self.configure(bg=BG)
        self.resizable(True, True)

        # Stilizuj ttk notebook
        stil = ttk.Style(self)
        stil.theme_use("clam")
        stil.configure("TNotebook", background=BG, borderwidth=0)
        stil.configure("TNotebook.Tab", background=BG2, foreground=MUTED,
                       font=FONT, padding=[14, 6], borderwidth=0)
        stil.map("TNotebook.Tab",
                 background=[("selected", BG)],
                 foreground=[("selected", ACCENT)])
        stil.configure("Treeview", background=BG2, foreground=TEXT,
                       fieldbackground=BG2, font=FONT_SM, rowheight=22)
        stil.configure("Treeview.Heading", background=BG, foreground=MUTED,
                       font=FONT_SM, relief="flat")
        stil.map("Treeview", background=[("selected", BORDER)])

        # Header (NERV/MAGI stil)
        hdr = tk.Frame(self, bg=BG2, height=58)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        levo_hdr = tk.Frame(hdr, bg=BG2)
        levo_hdr.pack(side="left", padx=20, pady=8)
        tk.Label(levo_hdr, text="◤ P S Z ◢", bg=BG2, fg=ACCENT,
                 font=("Consolas", 14, "bold")).pack(anchor="w")
        tk.Label(levo_hdr, text="S E A   O F   S O R R O W",
                 bg=BG2, fg=MUTED, font=("Consolas", 8)).pack(anchor="w")

        self.df = self._ucitaj_sa_promptom()
        n = len(self.df)
        desno_hdr = tk.Frame(hdr, bg=BG2)
        desno_hdr.pack(side="right", padx=20, pady=8)
        tk.Label(desno_hdr, text="● ONLINE", bg=BG2, fg=GREEN,
                 font=("Consolas", 9, "bold")).pack(anchor="e")
        tk.Label(desno_hdr, text=f"DB: {n} ZAPISA", bg=BG2, fg=AMBER,
                 font=("Consolas", 9)).pack(anchor="e")

        # tanka razdelna linija (scanline)
        tk.Frame(self, bg=ACCENT, height=1).pack(fill="x")

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=0, pady=0)

        self.tab_pregled       = TabPregledBaze(notebook, self.df)
        self.tab_regresija     = TabRegresija(notebook, self.df)
        self.tab_klasterovanje = TabKlasterovanje(notebook, self.df)
        self.tab_preporuke     = TabPreporuke(notebook, self.df)

        notebook.add(self.tab_pregled,       text="  Pregled baze  ")
        notebook.add(self.tab_regresija,     text="  Regresija cene  ")
        notebook.add(self.tab_klasterovanje, text="  Klasterovanje  ")
        notebook.add(self.tab_preporuke,     text="  Preporuke  ")

    def _ucitaj_sa_promptom(self):
        """Učita revidiranu bazu; na pogrešnu lozinku traži je dijalogom (do 3 puta)."""
        import zajednicko.db as db
        from tkinter import simpledialog
        for _ in range(3):
            try:
                return ucitaj_revidiranu()
            except Exception as e:
                if not db.je_auth_greska(e):
                    raise
                pwd = simpledialog.askstring(
                    "PostgreSQL lozinka",
                    f"Pogrešna ili nedostajuća lozinka za korisnika '{db.DB_USER}'.\n"
                    "Unesi lozinku:",
                    show="*", parent=self)
                if not pwd:
                    raise
                db.postavi_lozinku(pwd)  # čuva u .env za ubuduće
        return ucitaj_revidiranu()


# ── Tab 0: Pregled baze ───────────────────────────────────────────────────────

class TabPregledBaze(tk.Frame):
    """Read-only pregled revidirane baze: statistika, broj po kategoriji, tabela."""

    def __init__(self, master, df: pd.DataFrame):
        super().__init__(master, bg=BG)
        self.df = df

        # — Gornji panel: sažeta statistika —
        stat = kartica(self, "Statistika baze")
        stat.pack(fill="x", padx=20, pady=(20, 10))

        ukupno = len(df)
        br_kat = df["kategorija"].nunique()
        br_brendova = df["brend"].nunique()
        cmin, cmax = df["cena"].min(), df["cena"].max()
        pct_energ = 100 * df["energetska_klasa_num"].notna().mean() if ukupno else 0

        redovi_stat = [
            ("Ukupno zapisa", f"{ukupno:,}"),
            ("Kategorija", str(br_kat)),
            ("Brendova", str(br_brendova)),
            ("Raspon cena", f"{cmin:,.0f} – {cmax:,.0f} RSD"),
            ("Sa energ. klasom", f"{pct_energ:.0f}%"),
        ]
        red_frame = tk.Frame(stat, bg=BG2)
        red_frame.pack(fill="x", padx=10, pady=8)
        for i, (naziv, vred) in enumerate(redovi_stat):
            celija = tk.Frame(red_frame, bg=BG2)
            celija.grid(row=0, column=i, padx=14, sticky="w")
            tk.Label(celija, text=vred, bg=BG2, fg=ACCENT,
                     font=("Consolas", 14, "bold")).pack(anchor="w")
            tk.Label(celija, text=naziv, bg=BG2, fg=MUTED, font=FONT_SM).pack(anchor="w")

        # — Srednji panel: graf broja po kategoriji —
        graf = kartica(self, "Broj proizvoda po kategoriji")
        graf.pack(fill="x", padx=20, pady=10)
        self.fig = Figure(figsize=(7, 2.8), dpi=100, facecolor=BG2)
        self.ax = self.fig.add_subplot(111)
        self._nacrtaj_kategorije()
        canvas = FigureCanvasTkAgg(self.fig, master=graf)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=4, pady=4)

        # — Donji panel: filter + tabela proizvoda —
        donji = kartica(self, "Proizvodi")
        donji.pack(fill="both", expand=True, padx=20, pady=(10, 20))

        filter_frame = tk.Frame(donji, bg=BG2)
        filter_frame.pack(fill="x", padx=8, pady=(8, 4))
        tk.Label(filter_frame, text="Kategorija:", bg=BG2, fg=MUTED, font=FONT_SM).pack(side="left")
        self.kat_var = tk.StringVar(value="(sve)")
        kategorije = ["(sve)"] + sorted(df["kategorija"].dropna().unique().tolist())
        self.kat_menu = ttk.Combobox(filter_frame, textvariable=self.kat_var,
                                     values=kategorije, state="readonly", width=22)
        self.kat_menu.pack(side="left", padx=8)
        self.kat_menu.bind("<<ComboboxSelected>>", lambda e: self._popuni_tabelu())
        self.lbl_broj = tk.Label(filter_frame, text="", bg=BG2, fg=AMBER, font=FONT_SM)
        self.lbl_broj.pack(side="left", padx=12)

        kolone = ("id", "naziv", "brend", "kategorija", "cena")
        sirine  = (50, 360, 110, 130, 100)
        self._num_kolone = {"id", "cena"}
        self._sort_obrnuto: dict[str, bool] = {}
        self.tabela = ttk.Treeview(donji, columns=kolone, show="headings", height=10)
        for kol, sir in zip(kolone, sirine):
            self.tabela.heading(kol, text=kol, command=lambda k=kol: self._sortiraj(k))
            self.tabela.column(kol, width=sir, anchor="w")
        self.tabela.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self._popuni_tabelu()

    def _nacrtaj_kategorije(self):
        brojevi = self.df["kategorija"].value_counts()
        dark_osu(self.ax)
        boje = [KLASTER_BOJE[i % len(KLASTER_BOJE)] for i in range(len(brojevi))]
        self.ax.bar(range(len(brojevi)), brojevi.values, color=boje)
        self.ax.set_xticks(range(len(brojevi)))
        self.ax.set_xticklabels(brojevi.index, rotation=45, ha="right", fontsize=6)
        self.ax.set_ylabel("broj")
        self.fig.tight_layout()

    def _popuni_tabelu(self):
        kat = self.kat_var.get()
        podaci = self.df if kat == "(sve)" else self.df[self.df["kategorija"] == kat]
        podaci = podaci.sort_values("cena", ascending=False)
        for r in self.tabela.get_children():
            self.tabela.delete(r)
        for _, red in podaci.head(500).iterrows():
            self.tabela.insert("", tk.END, values=(
                int(red["id"]), str(red["naziv"])[:50], red["brend"],
                red["kategorija"], f"{red['cena']:,.0f} RSD"
            ))
        self.lbl_broj.config(text=f"{len(podaci):,} zapisa" +
                             ("  (prikazano prvih 500)" if len(podaci) > 500 else ""))

    def _sortiraj(self, kol: str):
        obrnuto = self._sort_obrnuto.get(kol, False)
        redovi = [(self.tabela.set(r, kol), r) for r in self.tabela.get_children()]
        if kol in self._num_kolone:
            def kljuc(par):
                c = par[0].replace(",", "").replace("RSD", "").strip()
                try:
                    return float(c)
                except ValueError:
                    return float("-inf")
        else:
            def kljuc(par):
                return par[0].lower()
        redovi.sort(key=kljuc, reverse=obrnuto)
        for i, (_, r) in enumerate(redovi):
            self.tabela.move(r, "", i)
        for k in self.tabela["columns"]:
            self.tabela.heading(k, text=k)
        self.tabela.heading(kol, text=kol + (" ▼" if obrnuto else " ▲"))
        self._sort_obrnuto[kol] = not obrnuto


# ── Tab 1: Regresija ──────────────────────────────────────────────────────────

class TabRegresija(tk.Frame):
    PRIMERI = [
        {"kategorija": "frizider",  "brend": "Samsung", "dijagonala_inch": "",  "kapacitet_kg": "",   "zapremina_l": "300", "snaga_w": "",    "energetska_klasa_num": "7"},
        {"kategorija": "televizor", "brend": "LG",      "dijagonala_inch": "55","kapacitet_kg": "",   "zapremina_l": "",    "snaga_w": "120", "energetska_klasa_num": "5"},
        {"kategorija": "ves_masina","brend": "Bosch",   "dijagonala_inch": "",  "kapacitet_kg": "8",  "zapremina_l": "",    "snaga_w": "2000","energetska_klasa_num": "8"},
    ]
    KOLONE = ["kategorija", "brend", "dijagonala_inch", "kapacitet_kg", "zapremina_l", "snaga_w", "energetska_klasa_num"]
    OPISI  = ["kategorija", "brend", "dijagonala (inch)", "kapacitet (kg)", "zapremina (l)", "snaga (W)", "energ. klasa (1-10)"]

    def __init__(self, master, df: pd.DataFrame):
        super().__init__(master, bg=BG)
        self.df = df
        self.model: LinearnaRegresijaGD | None = None
        self.kolone: list[str] = []

        # Leva kolona — unos
        levo = tk.Frame(self, bg=BG)
        levo.pack(side="left", fill="both", expand=True, padx=20, pady=20)

        # Desna kolona — info
        desno = tk.Frame(self, bg=BG, width=280)
        desno.pack(side="right", fill="y", padx=(0, 20), pady=20)
        desno.pack_propagate(False)

        # -- Unos
        k_unos = kartica(levo, "Karakteristike uredjaja")
        k_unos.pack(fill="x", pady=(0, 12))

        self.polja: dict[str, tk.Entry] = {}
        for i, (naziv, opis) in enumerate(zip(self.KOLONE, self.OPISI)):
            tk.Label(k_unos, text=opis, bg=BG2, fg=MUTED, font=FONT_SM,
                     width=20, anchor="w").grid(row=i, column=0, padx=10, pady=4, sticky="w")
            e = entry(k_unos, sirina=22)
            e.grid(row=i, column=1, padx=10, pady=4, sticky="ew")
            self.polja[naziv] = e
        k_unos.columnconfigure(1, weight=1)

        # -- Dugmici
        btn_frame = tk.Frame(levo, bg=BG)
        btn_frame.pack(fill="x", pady=8)

        btn_obuci = tk.Button(btn_frame, text="▶  Obuci model", command=self._obuci)
        stil_btn(btn_obuci)
        btn_obuci.pack(side="left", padx=(0, 8))

        btn_predvidi = tk.Button(btn_frame, text="◈  Predvidi cenu", command=self._predvidi)
        stil_btn(btn_predvidi, "success")
        btn_predvidi.pack(side="left")

        self.lbl_rezultat = tk.Label(levo, text="", bg=BG, fg=GREEN, font=FONT_LG)
        self.lbl_rezultat.pack(pady=8)

        self.lbl_metrike = tk.Label(levo, text="model nije obucen", bg=BG, fg=MUTED, font=FONT_SM)
        self.lbl_metrike.pack()

        # -- Graf (konvergencija + predvidjeno vs stvarno)
        k_graf = kartica(levo, "Dijagnostika treninga")
        k_graf.pack(fill="both", expand=True, pady=(12, 0))
        self.fig = Figure(figsize=(5, 2.6), dpi=100, facecolor=BG2)
        self.ax_trosak = self.fig.add_subplot(121)
        self.ax_pred = self.fig.add_subplot(122)
        dark_osu(self.ax_trosak, "Obuci model za prikaz")
        dark_osu(self.ax_pred, "")
        self.canvas = FigureCanvasTkAgg(self.fig, master=k_graf)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=4, pady=4)

        # -- Primeri (desna kolona)
        k_primeri = kartica(desno, "Primeri unosa")
        k_primeri.pack(fill="x")

        tk.Label(k_primeri, text="Klikni primer da popunis polja:", bg=BG2,
                 fg=MUTED, font=FONT_SM, wraplength=220, justify="left").pack(padx=10, pady=(8, 4))

        for p in self.PRIMERI:
            tekst = f"{p['kategorija']} / {p['brend']}"
            btn = tk.Button(k_primeri, text=tekst, bg=BG, fg=ACCENT, font=FONT_SM,
                            relief="flat", bd=0, cursor="hand2", anchor="w",
                            activebackground=BG2, activeforeground=TEXT,
                            command=lambda pr=p: self._popuni_primer(pr))
            btn.pack(fill="x", padx=10, pady=2)

        # -- Objasnjenje
        k_info = kartica(desno, "Energetska klasa")
        k_info.pack(fill="x", pady=(12, 0))
        mapa = "G=1  F=2  E=3  D=4  C=5\nB=6  A=7  A+=8  A++=9  A+++=10"
        tk.Label(k_info, text=mapa, bg=BG2, fg=MUTED, font=FONT_SM,
                 justify="left").pack(padx=10, pady=8)

    def _popuni_primer(self, primer: dict):
        for naziv, val in primer.items():
            e = self.polja[naziv]
            e.delete(0, tk.END)
            e.insert(0, val)
            e.config(fg=TEXT)

    def _obuci(self):
        self.lbl_metrike.config(text="Obucavanje...", fg=MUTED)
        self.update()
        X, y, kolone = pripremi_podatke(self.df)
        self.kolone = kolone
        X_tr, X_te, y_tr, y_te = podeli_train_test(X, y)
        self.model = LinearnaRegresijaGD(stopa_ucenja=0.05, broj_iteracija=2000).fit(X_tr, y_tr)
        y_pred = self.model.predict(X_te)
        r2 = r2_skor(y_te, y_pred)
        rm = rmse(y_te, y_pred)
        self.lbl_metrike.config(
            text=f"R² = {r2:.3f}   |   RMSE = {rm:,.0f} RSD",
            fg=GREEN if r2 > 0.5 else RED
        )
        self._nacrtaj_dijagnostiku(y_te, y_pred)

    def _nacrtaj_dijagnostiku(self, y_te, y_pred):
        # 1) konvergencija troska
        dark_osu(self.ax_trosak)
        self.ax_trosak.plot(self.model.istorija_troska, color=ACCENT, linewidth=1.2)
        self.ax_trosak.set_yscale("log")
        self.ax_trosak.set_title("Trosak (MSE)", fontsize=8)
        self.ax_trosak.set_xlabel("iteracija")

        # 2) predvidjeno vs stvarno
        dark_osu(self.ax_pred)
        self.ax_pred.scatter(y_te, y_pred, s=12, alpha=0.5, color=GREEN, edgecolors="none")
        lo = float(min(y_te.min(), y_pred.min()))
        hi = float(max(y_te.max(), y_pred.max()))
        self.ax_pred.plot([lo, hi], [lo, hi], color=AMBER, linewidth=1, linestyle="--")
        self.ax_pred.set_title("Predvidjeno vs stvarno", fontsize=8)
        self.ax_pred.set_xlabel("stvarno")
        self.ax_pred.set_ylabel("predvidjeno")

        self.fig.tight_layout()
        self.canvas.draw()

    def _predvidi(self):
        if self.model is None:
            messagebox.showwarning("Paznja", "Prvo obuci model.")
            return
        red = {k: v.get() for k, v in self.polja.items()}
        df_red = pd.DataFrame([{**red, "cena": np.nan}])
        df_kom = pd.concat([self.df, df_red], ignore_index=True)
        for kol in ["dijagonala_inch", "kapacitet_kg", "zapremina_l", "snaga_w", "energetska_klasa_num"]:
            df_kom[kol] = pd.to_numeric(df_kom[kol], errors="coerce")
        X_sve, _, kolone = pripremi_podatke(df_kom.fillna({"cena": 0}))
        x_novi = X_sve[-1].reshape(1, -1)
        if list(kolone) != self.kolone:
            messagebox.showerror("Greska", "Kombinacija kategorija/brend nije vidjena pri treningu.")
            return
        predikcija = self.model.predict(x_novi)[0]
        self.lbl_rezultat.config(text=f"≈  {predikcija:,.0f} RSD")


# ── Tab 2: Klasterovanje ──────────────────────────────────────────────────────

class TabKlasterovanje(tk.Frame):
    NUMERICKE = ["cena", "energetska_klasa_num", "dijagonala_inch",
                 "kapacitet_kg", "zapremina_l", "snaga_w"]

    # (naziv, K, {kolona: tezina}) — zbir tezina = 100
    # Vazno: izabrane kolone moraju ko-egzistirati (proizvod mora imati SVE
    # popunjene) — npr. dijagonala (TV) i zapremina (frizider) se iskljucuju.
    PRIMERI = [
        ("Cena vs efikasnost", 3, {"cena": 60, "energetska_klasa_num": 40}),
        ("Cena i zapremina",   4, {"cena": 50, "zapremina_l": 30, "energetska_klasa_num": 20}),
        ("Cena i snaga",       3, {"cena": 60, "snaga_w": 40}),
    ]

    def __init__(self, master, df: pd.DataFrame):
        super().__init__(master, bg=BG)
        self.df = df

        # Levo — kontrole
        levo = tk.Frame(self, bg=BG)
        levo.pack(side="left", fill="y", padx=20, pady=20)

        k_var = kartica(levo, "Promenljive i tezine (%)")
        k_var.pack(fill="x")

        self.checkboxi: dict[str, tk.BooleanVar] = {}
        self.tezine: dict[str, tk.Entry] = {}
        podrazumevane = {"cena": "50", "energetska_klasa_num": "30", "zapremina_l": "20"}

        for i, kol in enumerate(self.NUMERICKE):
            var = tk.BooleanVar(value=kol in podrazumevane)
            cb = tk.Checkbutton(k_var, text=kol, variable=var, bg=BG2,
                                fg=TEXT, selectcolor=BG, activebackground=BG2,
                                activeforeground=ACCENT, font=FONT_SM)
            cb.grid(row=i, column=0, sticky="w", padx=10, pady=3)
            e = entry(k_var, sirina=6, placeholder=podrazumevane.get(kol, "0"))
            e.grid(row=i, column=1, padx=8, pady=3)
            self.checkboxi[kol] = var
            self.tezine[kol] = e

        k_k = kartica(levo, "Broj klastera")
        k_k.pack(fill="x", pady=(12, 0))
        k_frame = tk.Frame(k_k, bg=BG2)
        k_frame.pack(padx=10, pady=8)
        tk.Label(k_frame, text="K =", bg=BG2, fg=MUTED, font=FONT).pack(side="left")
        self.k_entry = entry(k_frame, sirina=4, placeholder="4")
        self.k_entry.pack(side="left", padx=6)

        # Primeri (preseti)
        k_primeri = kartica(levo, "Primeri")
        k_primeri.pack(fill="x", pady=(12, 0))
        tk.Label(k_primeri, text="Klikni da popunis postavke:", bg=BG2,
                 fg=MUTED, font=FONT_SM).pack(anchor="w", padx=10, pady=(8, 2))
        for naziv, k, tezine in self.PRIMERI:
            tk.Button(k_primeri, text=f"▪ {naziv}  (K={k})", bg=BG, fg=ACCENT,
                      font=FONT_SM, relief="flat", bd=0, cursor="hand2", anchor="w",
                      activebackground=BG2, activeforeground=TEXT,
                      command=lambda k=k, t=tezine: self._popuni_primer(k, t)
                      ).pack(fill="x", padx=10, pady=2)

        btn = tk.Button(levo, text="▶  Pokreni klasterovanje", command=self._pokreni)
        stil_btn(btn)
        btn.pack(fill="x", pady=12)

        # Desno — vizuelizacija (gore) + rezultati (dole)
        desno = tk.Frame(self, bg=BG)
        desno.pack(side="right", fill="both", expand=True, padx=(0, 20), pady=20)

        k_graf = kartica(desno, "Vizuelizacija klastera")
        k_graf.pack(fill="both", expand=True)

        self.fig = Figure(figsize=(5, 3.6), dpi=100, facecolor=BG2)
        self.ax = self.fig.add_subplot(111)
        self._stilizuj_osu("Pokreni klasterovanje za prikaz")
        self.canvas = FigureCanvasTkAgg(self.fig, master=k_graf)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=4, pady=4)

        k_rez = kartica(desno, "Rezultati")
        k_rez.pack(fill="x", pady=(12, 0))

        self.tekst = tk.Text(k_rez, bg=BG, fg=TEXT, font=FONT_SM, height=8,
                             relief="flat", bd=0, padx=12, pady=8,
                             insertbackground=ACCENT, wrap="word")
        self.tekst.pack(fill="both", expand=True)
        self.tekst.config(state="disabled")
        self._upisi("Izaberi promenljive, podesi tezine (zbir = 100%) i klikni Pokreni.\n\n"
                    "Primer: cena=50%, energ.klasa=30%, zapremina=20%, K=4\n")

    def _popuni_primer(self, k: int, tezine: dict[str, float]):
        for kol in self.NUMERICKE:
            ukljuci = kol in tezine
            self.checkboxi[kol].set(ukljuci)
            e = self.tezine[kol]
            e.delete(0, tk.END)
            e.insert(0, str(tezine.get(kol, 0)))
            e.config(fg=TEXT if ukljuci else MUTED)
        self.k_entry.delete(0, tk.END)
        self.k_entry.insert(0, str(k))
        self.k_entry.config(fg=TEXT)

    def _upisi(self, tekst: str, boja: str = MUTED):
        self.tekst.config(state="normal")
        self.tekst.delete("1.0", tk.END)
        self.tekst.insert(tk.END, tekst)
        self.tekst.config(state="disabled", fg=boja)

    def _stilizuj_osu(self, poruka: str = ""):
        """Postavi dark stil na matplotlib osu (poziva se pri svakom crtanju)."""
        self.ax.clear()
        self.ax.set_facecolor(BG)
        for strana in self.ax.spines.values():
            strana.set_color(BORDER)
        self.ax.tick_params(colors=MUTED, labelsize=8)
        self.ax.xaxis.label.set_color(TEXT)
        self.ax.yaxis.label.set_color(TEXT)
        self.ax.title.set_color(ACCENT)
        if poruka:
            self.ax.text(0.5, 0.5, poruka, ha="center", va="center",
                         color=MUTED, fontsize=10, transform=self.ax.transAxes)
            self.ax.set_xticks([]); self.ax.set_yticks([])

    def _nacrtaj(self, df: pd.DataFrame, izabrane: list[str]):
        self._stilizuj_osu()

        if len(izabrane) == 1:
            # 1D: histogram po klasteru
            kol = izabrane[0]
            for kid in sorted(df["klaster"].unique()):
                vals = df[df["klaster"] == kid][kol]
                self.ax.hist(vals, bins=20, alpha=0.6,
                             color=KLASTER_BOJE[kid % len(KLASTER_BOJE)],
                             label=f"K{kid}")
            self.ax.set_xlabel(kol)
            self.ax.set_ylabel("broj proizvoda")
        else:
            # 2D: scatter prve dve izabrane promenljive (u izvornim jedinicama)
            xk, yk = izabrane[0], izabrane[1]
            for kid in sorted(df["klaster"].unique()):
                grupa = df[df["klaster"] == kid]
                boja = KLASTER_BOJE[kid % len(KLASTER_BOJE)]
                self.ax.scatter(grupa[xk], grupa[yk], s=18, alpha=0.7,
                                color=boja, edgecolors="none", label=f"K{kid}")
                # centroid (prosek u izvornim jedinicama)
                self.ax.scatter(grupa[xk].mean(), grupa[yk].mean(),
                                s=180, marker="X", color=boja,
                                edgecolors=BG, linewidths=1.5, zorder=5)
            self.ax.set_xlabel(xk)
            self.ax.set_ylabel(yk)

        leg = self.ax.legend(fontsize=7, facecolor=BG2, edgecolor=BORDER,
                             labelcolor=TEXT, loc="best")
        if leg:
            leg.get_frame().set_alpha(0.9)
        self.fig.tight_layout()
        self.canvas.draw()

    def _pokreni(self):
        izabrane = [k for k, v in self.checkboxi.items() if v.get()]
        if not izabrane:
            messagebox.showwarning("Paznja", "Izaberi bar jednu promenljivu.")
            return
        try:
            tezine = np.array([float(self.tezine[k].get()) for k in izabrane])
        except ValueError:
            messagebox.showerror("Greska", "Tezine moraju biti brojevi.")
            return
        if abs(tezine.sum() - 100) > 0.1:
            messagebox.showerror("Greska", f"Zbir tezina mora biti 100% (trenutno {tezine.sum():.0f}%).")
            return
        k = int(self.k_entry.get() or 4)
        df = self.df.dropna(subset=izabrane).copy()
        if len(df) < k:
            messagebox.showwarning(
                "Premalo podataka",
                f"Samo {len(df)} proizvoda ima sve izabrane atribute popunjene "
                f"(potrebno bar K={k}).\n\nNeki atributi se iskljucuju — npr. "
                f"dijagonala (TV) i zapremina (frizider) ne postoje na istom proizvodu. "
                f"Izaberi atribute koji se javljaju zajedno."
            )
            return
        X = np.column_stack([normalizuj(df[kol]) * (tezine[i] / 100) for i, kol in enumerate(izabrane)])
        model = KMeans(k=k).fit(X)
        df["klaster"] = model.labele
        skor = silhouette_score_rucno(X, model.labele)

        linije = [f"Silhouette score: {skor:.3f}  {'(dobar)' if skor > 0.5 else '(osrednji)' if skor > 0.25 else '(los)'}\n",
                  f"Promenljive: {', '.join(izabrane)}\n\n"]
        for kid in sorted(df["klaster"].unique()):
            df_k = df[df["klaster"] == kid]
            opis = interpretiraj_klaster(df_k, izabrane)
            linije.append(f"  Klaster {kid}  [{len(df_k):>3} proizvoda]  {opis}\n")
        self._upisi("".join(linije), TEXT)

        self._nacrtaj(df, izabrane)


# ── Tab 3: Preporuke ──────────────────────────────────────────────────────────

class TabPreporuke(tk.Frame):
    def __init__(self, master, df: pd.DataFrame):
        super().__init__(master, bg=BG)
        self.df = df
        self.recommender = ContentBasedRecommender(df)

        # Gornji panel — unos
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=20, pady=16)

        tk.Label(top, text="ID proizvoda:", bg=BG, fg=MUTED, font=FONT).pack(side="left")
        self.id_entry = entry(top, sirina=8)
        self.id_entry.pack(side="left", padx=8)

        btn = tk.Button(top, text="◈  Preporuci slicne", command=self._preporuci)
        stil_btn(btn)
        btn.pack(side="left")

        self.lbl_odabran = tk.Label(top, text="", bg=BG, fg=MUTED, font=FONT_SM)
        self.lbl_odabran.pack(side="left", padx=16)

        # Tabela sa primerima ID-jeva
        sredina = tk.Frame(self, bg=BG)
        sredina.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        # Levo — preporuke
        levo = tk.Frame(sredina, bg=BG)
        levo.pack(side="left", fill="both", expand=True)

        k_rez = kartica(levo, "Top 5 preporuka")
        k_rez.pack(fill="both", expand=True)

        kolone = ("id", "naziv", "brend", "cena", "slicnost")
        sirine  = (50, 380, 100, 90, 80)
        # kolone sa numerickim sortiranjem (ostale idu leksikografski)
        self._num_kolone = {"id", "cena", "slicnost"}
        self._sort_obrnuto: dict[str, bool] = {}
        self.tabela = ttk.Treeview(k_rez, columns=kolone, show="headings", height=8)
        for kol, sir in zip(kolone, sirine):
            self.tabela.heading(kol, text=kol,
                                command=lambda k=kol: self._sortiraj(k))
            self.tabela.column(kol, width=sir, anchor="w")
        self.tabela.pack(fill="both", expand=True, padx=4, pady=4)

        # Desno — primeri
        desno = tk.Frame(sredina, bg=BG, width=220)
        desno.pack(side="right", fill="y", padx=(16, 0))
        desno.pack_propagate(False)

        k_pr = kartica(desno, "Primeri ID-jeva")
        k_pr.pack(fill="both", expand=True)

        tk.Label(k_pr, text="(iz baze — klikni da uneseses)",
                 bg=BG2, fg=MUTED, font=FONT_SM, wraplength=180).pack(padx=8, pady=(8, 4))

        primeri = df.dropna(subset=["cena"]).groupby("kategorija").first().reset_index()
        for _, red in primeri.iterrows():
            tekst = f"[{int(red['id'])}]  {red['kategorija']}"
            tk.Button(k_pr, text=tekst, bg=BG, fg=ACCENT, font=FONT_SM,
                      relief="flat", bd=0, cursor="hand2", anchor="w",
                      activebackground=BG2, activeforeground=TEXT,
                      command=lambda pid=int(red["id"]): self._unesi_id(pid)
                      ).pack(fill="x", padx=8, pady=2)

    def _unesi_id(self, pid: int):
        self.id_entry.delete(0, tk.END)
        self.id_entry.insert(0, str(pid))
        self.id_entry.config(fg=TEXT)
        self._preporuci()

    def _sortiraj(self, kol: str):
        obrnuto = self._sort_obrnuto.get(kol, False)
        redovi = [(self.tabela.set(r, kol), r) for r in self.tabela.get_children()]

        if kol in self._num_kolone:
            def kljuc(par):
                # izvuci broj iz npr. "75,000 RSD" ili "0.526"
                ciscen = par[0].replace(",", "").replace("RSD", "").strip()
                try:
                    return float(ciscen)
                except ValueError:
                    return float("-inf")
        else:
            def kljuc(par):
                return par[0].lower()

        redovi.sort(key=kljuc, reverse=obrnuto)
        for indeks, (_, r) in enumerate(redovi):
            self.tabela.move(r, "", indeks)

        # strelica u zaglavlju + obrni smer za sledeci klik
        for k in self.tabela["columns"]:
            self.tabela.heading(k, text=k)
        strelica = " ▼" if obrnuto else " ▲"
        self.tabela.heading(kol, text=kol + strelica)
        self._sort_obrnuto[kol] = not obrnuto

    def _preporuci(self):
        try:
            pid = int(self.id_entry.get())
        except ValueError:
            messagebox.showerror("Greska", "ID mora biti broj.")
            return
        try:
            rezultat = self.recommender.preporuci(pid, top_n=5)
        except ValueError as e:
            messagebox.showerror("Greska", str(e))
            return

        red_orig = self.df[self.df["id"] == pid]
        if not red_orig.empty:
            naziv = red_orig.iloc[0]["naziv"]
            self.lbl_odabran.config(text=f"→  {naziv[:55]}", fg=MUTED)

        for r in self.tabela.get_children():
            self.tabela.delete(r)
        for _, red in rezultat.iterrows():
            self.tabela.insert("", tk.END, values=(
                int(red["id"]), red["naziv"][:50], red["brend"],
                f"{red['cena']:,.0f} RSD", f"{red['slicnost']:.3f}"
            ))


if __name__ == "__main__":
    try:
        Aplikacija().mainloop()
    except Exception as e:
        import tkinter.messagebox as mb
        mb.showerror(
            "Greška pri pokretanju",
            f"Ne mogu da se povežem na bazu:\n\n{e}\n\n"
            "Proveri da je PostgreSQL pokrenut i da je baza inicijalizovana "
            "(.\\run.ps1 setup).",
        )
