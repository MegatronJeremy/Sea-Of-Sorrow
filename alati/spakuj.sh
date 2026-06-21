#!/usr/bin/env bash
# Pakuje projekat za predaju u formatu Indeks_Ime_Prezime.zip,
# sa folderima /kod /baza /izveštaj (kako zahteva postavka).
#
# Upotreba: bash alati/spakuj.sh <Indeks> <Ime> <Prezime>
# Primer:   bash alati/spakuj.sh 2023_0123 Vuk Prezime

set -euo pipefail

if [ "$#" -ne 3 ]; then
    echo "Upotreba: $0 <Indeks> <Ime> <Prezime>"
    exit 1
fi

INDEKS="$1"
IME="$2"
PREZIME="$3"
NAZIV="${INDEKS}_${IME}_${PREZIME}"
IZLAZ_DIR="/tmp/${NAZIV}"
ZIP_PUTANJA="/tmp/${NAZIV}.zip"

cd "$(dirname "$0")/.."  # koren projekta

# Generiši SQL dump-ove baze (primarna + revidirana) pre pakovanja, da /baza
# sadrži PODATKE, ne samo šeme. Koristi venv python ako postoji.
PY=".venv/Scripts/python.exe"
[ -x "$PY" ] || PY=".venv/bin/python"
[ -x "$PY" ] || PY="python"
echo "Generišem SQL dump-ove baze..."
"$PY" kod/db_dump.py || {
    echo "UPOZORENJE: db_dump nije uspeo (PostgreSQL pokrenut?). /baza će imati samo šeme."
}

rm -rf "$IZLAZ_DIR" "$ZIP_PUTANJA"
mkdir -p "$IZLAZ_DIR"

cp -r kod "$IZLAZ_DIR/kod"
cp -r baza "$IZLAZ_DIR/baza"
cp -r izvestaj "$IZLAZ_DIR/izveštaj"

# izbaci .env, __pycache__, scratch logove i node_modules iz arhive
find "$IZLAZ_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "$IZLAZ_DIR" -name "*.pyc" -delete 2>/dev/null || true
rm -f "$IZLAZ_DIR/kod"/**/.env

cd /tmp
zip -r "$ZIP_PUTANJA" "$NAZIV" > /dev/null

echo "Spakovano: $ZIP_PUTANJA"
