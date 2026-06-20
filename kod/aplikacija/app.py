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

sys.path.append(str(Path(__file__).resolve().parents[1]))
from zajednicko.db import get_connection  # noqa: E402
from zajednicko.util import normalizuj     # noqa: E402

sys.path.append(str(Path(__file__).resolve().parents[1] / "04_regresija"))
sys.path.append(str(Path(__file__).resolve().parents[1] / "05_klasterovanje"))
sys.path.append(str(Path(__file__).resolve().parents[1] / "06_preporuke"))

from regresija import LinearnaRegresijaGD, pripremi_podatke, podeli_train_test, r2_skor, rmse  # noqa: E402
from kmeans import KMeans, silhouette_score_rucno, interpretiraj_klaster                        # noqa: E402
from recommender import ContentBasedRecommender                                                  # noqa: E402

# ── Paleta boja ───────────────────────────────────────────────────────────────
BG       = "#0d1117"   # pozadina (GitHub dark)
BG2      = "#161b22"   # karte / frejmovi
BORDER   = "#30363d"   # ivice
ACCENT   = "#58a6ff"   # plava (naglasak)
GREEN    = "#3fb950"   # uspeh
RED      = "#f85149"   # greška
TEXT     = "#e6edf3"   # glavni tekst
MUTED    = "#8b949e"   # sekundarni tekst
FONT     = ("Consolas", 10)
FONT_SM  = ("Consolas", 9)
FONT_LG  = ("Consolas", 13, "bold")
FONT_HDR = ("Consolas", 11, "bold")


def ucitaj_revidiranu() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM proizvodi_revidirana;", conn)
    conn.close()
    return df


def stil_btn(btn: tk.Button, tip: str = "primary"):
    boja = ACCENT if tip == "primary" else "#238636"
    btn.config(
        bg=boja, fg=BG, font=FONT, relief="flat", bd=0,
        activebackground=TEXT, activeforeground=BG,
        cursor="hand2", padx=12, pady=5
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
        self.title("PSZ — Bela tehnika | Tehnomanija.rs")
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

        # Header
        hdr = tk.Frame(self, bg=BG2, height=48)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="⬡  PSZ PROJEKAT", bg=BG2, fg=ACCENT,
                 font=("Consolas", 13, "bold")).pack(side="left", padx=20, pady=12)

        self.df = ucitaj_revidiranu()
        n = len(self.df)
        tk.Label(hdr, text=f"{n} proizvoda u bazi", bg=BG2, fg=MUTED,
                 font=FONT_SM).pack(side="right", padx=20)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=0, pady=0)

        self.tab_regresija     = TabRegresija(notebook, self.df)
        self.tab_klasterovanje = TabKlasterovanje(notebook, self.df)
        self.tab_preporuke     = TabPreporuke(notebook, self.df)

        notebook.add(self.tab_regresija,     text="  Regresija cene  ")
        notebook.add(self.tab_klasterovanje, text="  Klasterovanje  ")
        notebook.add(self.tab_preporuke,     text="  Preporuke  ")


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
        r2 = r2_skor(y_te, self.model.predict(X_te))
        rm = rmse(y_te, self.model.predict(X_te))
        self.lbl_metrike.config(
            text=f"R² = {r2:.3f}   |   RMSE = {rm:,.0f} RSD",
            fg=GREEN if r2 > 0.5 else RED
        )

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

        btn = tk.Button(levo, text="▶  Pokreni klasterovanje", command=self._pokreni)
        stil_btn(btn)
        btn.pack(fill="x", pady=12)

        # Desno — rezultati
        desno = tk.Frame(self, bg=BG)
        desno.pack(side="right", fill="both", expand=True, padx=(0, 20), pady=20)

        k_rez = kartica(desno, "Rezultati")
        k_rez.pack(fill="both", expand=True)

        self.tekst = tk.Text(k_rez, bg=BG, fg=TEXT, font=FONT_SM,
                             relief="flat", bd=0, padx=12, pady=8,
                             insertbackground=ACCENT, wrap="word")
        self.tekst.pack(fill="both", expand=True)
        self.tekst.config(state="disabled")
        self._upisi("Izaberi promenljive, podesi tezine (zbir = 100%) i klikni Pokreni.\n\n"
                    "Primer: cena=50%, energ.klasa=30%, zapremina=20%, K=4\n")

    def _upisi(self, tekst: str, boja: str = MUTED):
        self.tekst.config(state="normal")
        self.tekst.delete("1.0", tk.END)
        self.tekst.insert(tk.END, tekst)
        self.tekst.config(state="disabled", fg=boja)

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
        self.tabela = ttk.Treeview(k_rez, columns=kolone, show="headings", height=8)
        for kol, sir in zip(kolone, sirine):
            self.tabela.heading(kol, text=kol)
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
    Aplikacija().mainloop()
