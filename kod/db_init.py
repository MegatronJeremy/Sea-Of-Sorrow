import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from zajednicko.db import run_sql_file

_ROOT = Path(__file__).resolve().parent.parent
run_sql_file(str(_ROOT / "baza" / "01_schema_primarna.sql"))
print("OK baza: podaci/psz.db")
