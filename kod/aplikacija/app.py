"""
Glavna GUI aplikacija (Tkinter) — objedinjuje zadatke 4 (regresija),
5 (K-means klasterovanje) i 6 (preporuke proizvoda).

Pokretanje:
    cd kod/aplikacija
    python app.py
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
from zajednicko.util import normalizuj, standardizuj  # noqa: E402

sys.path.append(str(Path(__file__).resolve().parents[1] / "04_regresija"))
sys.path.append(str(Path(__file__).resolve().parents[1] / "05_klasterovanje"))
sys.path.append(str(Path(__file__).resolve().parents[1] / "06_preporuke"))

from regresija import LinearnaRegresijaGD, pripremi_podatke, podeli_train_test, r2_skor, rmse  # noqa: E402
from kmeans import KMeans, silhouette_score_rucno, interpretiraj_klaster  # noqa: E402
from recommender import ContentBasedRecommender  # noqa: E402


def ucitaj_revidiranu() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM proizvodi_revidirana;", conn)
    conn.close()
    return df


class Aplikacija(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PSZ Projekat — Bela tehnika")
        self.geometry("900x650")

        self.df = ucitaj_revidiranu()

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        self.tab_regresija = TabRegresija(notebook, self.df)
        self.tab_klasterovanje = TabKlasterovanje(notebook, self.df)
        self.tab_preporuke = TabPreporuke(notebook, self.df)

        notebook.add(self.tab_regresija, text="Zadatak 4 — Regresija cene")
        notebook.add(self.tab_klasterovanje, text="Zadatak 5 — Klasterovanje")
        notebook.add(self.tab_preporuke, text="Zadatak 6 — Preporuke")


class TabRegresija(ttk.Frame):
    """Korisnik unosi karakteristike uređaja -> model predviđa cenu."""

    def __init__(self, master, df: pd.DataFrame):
        super().__init__(master)
        self.df = df
        self.model: LinearnaRegresijaGD | None = None
        self.kolone: list[str] = []

        ttk.Button(self, text="Obuči model", command=self._obuci).pack(pady=10)
        self.lbl_metrike = ttk.Label(self, text="(model nije obučen)")
        self.lbl_metrike.pack(pady=5)

        unos_frame = ttk.LabelFrame(self, text="Karakteristike uređaja")
        unos_frame.pack(fill="x", padx=20, pady=10)

        self.polja: dict[str, tk.Entry] = {}
        for i, naziv in enumerate(["kategorija", "brend", "dijagonala_inch", "kapacitet_kg",
                                    "zapremina_l", "snaga_w", "energetska_klasa_num"]):
            ttk.Label(unos_frame, text=naziv).grid(row=i, column=0, sticky="w", padx=5, pady=2)
            entry = ttk.Entry(unos_frame)
            entry.grid(row=i, column=1, sticky="ew", padx=5, pady=2)
            self.polja[naziv] = entry
        unos_frame.columnconfigure(1, weight=1)

        ttk.Button(self, text="Predvidi cenu", command=self._predvidi).pack(pady=10)
        self.lbl_rezultat = ttk.Label(self, text="", font=("", 12, "bold"))
        self.lbl_rezultat.pack(pady=5)

    def _obuci(self):
        X, y, kolone = pripremi_podatke(self.df)
        self.kolone = kolone
        X_train, X_test, y_train, y_test = podeli_train_test(X, y)

        self.model = LinearnaRegresijaGD(stopa_ucenja=0.05, broj_iteracija=2000)
        self.model.fit(X_train, y_train)

        y_pred = self.model.predict(X_test)
        self.lbl_metrike.config(
            text=f"R² = {r2_skor(y_test, y_pred):.3f}   RMSE = {rmse(y_test, y_pred):,.0f} RSD"
        )

    def _predvidi(self):
        if self.model is None:
            messagebox.showwarning("Pažnja", "Prvo obuči model.")
            return
        # napravi jednorednu tabelu istog formata kao trening skup
        red = {k: v.get() for k, v in self.polja.items()}
        df_red = pd.DataFrame([{**red, "cena": np.nan}])
        df_kombinovano = pd.concat([self.df, df_red], ignore_index=True)

        for kol in ["dijagonala_inch", "kapacitet_kg", "zapremina_l", "snaga_w", "energetska_klasa_num"]:
            df_kombinovano[kol] = pd.to_numeric(df_kombinovano[kol], errors="coerce")

        X_sve, _, kolone = pripremi_podatke(df_kombinovano.fillna({"cena": 0}))
        x_novi = X_sve[-1].reshape(1, -1)

        # uskladi kolone sa onima na kojima je model treniran
        if list(kolone) != self.kolone:
            messagebox.showerror("Greška", "Kombinacija kategorija/brend nije viđena pri treningu.")
            return

        predikcija = self.model.predict(x_novi)[0]
        self.lbl_rezultat.config(text=f"Predviđena cena: {predikcija:,.0f} RSD")


class TabKlasterovanje(ttk.Frame):
    """Korisnik bira promenljive, težine i K -> rezultati klasterovanja."""

    NUMERICKE_OPCIJE = ["cena", "energetska_klasa_num", "dijagonala_inch",
                         "kapacitet_kg", "zapremina_l", "snaga_w"]

    def __init__(self, master, df: pd.DataFrame):
        super().__init__(master)
        self.df = df

        izbor_frame = ttk.LabelFrame(self, text="Promenljive i težine (zbir = 100%)")
        izbor_frame.pack(fill="x", padx=20, pady=10)

        self.checkboxi: dict[str, tk.BooleanVar] = {}
        self.tezine: dict[str, tk.Entry] = {}
        for i, kol in enumerate(self.NUMERICKE_OPCIJE):
            var = tk.BooleanVar(value=True)
            ttk.Checkbutton(izbor_frame, text=kol, variable=var).grid(row=i, column=0, sticky="w")
            entry = ttk.Entry(izbor_frame, width=6)
            entry.insert(0, str(round(100 / len(self.NUMERICKE_OPCIJE))))
            entry.grid(row=i, column=1, padx=5)
            self.checkboxi[kol] = var
            self.tezine[kol] = entry

        kontrole_frame = ttk.Frame(self)
        kontrole_frame.pack(fill="x", padx=20, pady=5)
        ttk.Label(kontrole_frame, text="Broj klastera (K):").pack(side="left")
        self.k_entry = ttk.Entry(kontrole_frame, width=5)
        self.k_entry.insert(0, "4")
        self.k_entry.pack(side="left", padx=5)
        ttk.Button(kontrole_frame, text="Pokreni klasterovanje", command=self._pokreni).pack(side="left", padx=10)

        self.tekst_rezultat = tk.Text(self, height=20)
        self.tekst_rezultat.pack(fill="both", expand=True, padx=20, pady=10)

    def _pokreni(self):
        izabrane = [k for k, v in self.checkboxi.items() if v.get()]
        if not izabrane:
            messagebox.showwarning("Pažnja", "Izaberi bar jednu promenljivu.")
            return

        tezine_str = [self.tezine[k].get() for k in izabrane]
        try:
            tezine = np.array([float(t) for t in tezine_str])
        except ValueError:
            messagebox.showerror("Greška", "Težine moraju biti brojevi.")
            return
        if abs(tezine.sum() - 100) > 0.01:
            messagebox.showerror("Greška", f"Zbir težina mora biti 100% (trenutno {tezine.sum()}%).")
            return

        k = int(self.k_entry.get())

        df = self.df.dropna(subset=izabrane).copy()
        X = np.column_stack([normalizuj(df[kol]) * (tezine[i] / 100) for i, kol in enumerate(izabrane)])

        model = KMeans(k=k)
        model.fit(X)
        df["klaster"] = model.labele

        skor = silhouette_score_rucno(X, model.labele)

        self.tekst_rezultat.delete("1.0", tk.END)
        self.tekst_rezultat.insert(tk.END, f"Silhouette score: {skor:.3f}\n\n")
        for klaster_id in sorted(df["klaster"].unique()):
            df_k = df[df["klaster"] == klaster_id]
            opis = interpretiraj_klaster(df_k, izabrane)
            self.tekst_rezultat.insert(
                tk.END,
                f"Klaster {klaster_id}: {len(df_k)} proizvoda — {opis}\n",
            )


class TabPreporuke(ttk.Frame):
    """Korisnik bira proizvod -> sistem prikazuje top 5 najsličnijih."""

    def __init__(self, master, df: pd.DataFrame):
        super().__init__(master)
        self.df = df
        self.recommender = ContentBasedRecommender(df)

        unos_frame = ttk.Frame(self)
        unos_frame.pack(fill="x", padx=20, pady=10)
        ttk.Label(unos_frame, text="ID proizvoda:").pack(side="left")
        self.id_entry = ttk.Entry(unos_frame, width=10)
        self.id_entry.pack(side="left", padx=5)
        ttk.Button(unos_frame, text="Preporuči slične proizvode", command=self._preporuci).pack(side="left", padx=10)

        kolone = ("id", "naziv", "brend", "cena", "slicnost")
        self.tabela = ttk.Treeview(self, columns=kolone, show="headings")
        for kol in kolone:
            self.tabela.heading(kol, text=kol)
        self.tabela.pack(fill="both", expand=True, padx=20, pady=10)

    def _preporuci(self):
        try:
            proizvod_id = int(self.id_entry.get())
        except ValueError:
            messagebox.showerror("Greška", "ID proizvoda mora biti broj.")
            return

        try:
            rezultat = self.recommender.preporuci(proizvod_id, top_n=5)
        except ValueError as e:
            messagebox.showerror("Greška", str(e))
            return

        for red in self.tabela.get_children():
            self.tabela.delete(red)
        for _, red in rezultat.iterrows():
            self.tabela.insert("", tk.END, values=(
                red["id"], red["naziv"], red["brend"], f"{red['cena']:,.0f}", f"{red['slicnost']:.3f}"
            ))


if __name__ == "__main__":
    Aplikacija().mainloop()
