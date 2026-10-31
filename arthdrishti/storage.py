import sqlite3, json
from pathlib import Path
import pandas as pd

DB = Path(__file__).resolve().parents[1] / "data" / "arthdrishti.db"

def init_db():
    DB.parent.mkdir(exist_ok=True)
    with sqlite3.connect(DB) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS simulations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            workspace TEXT NOT NULL,
            assumptions TEXT NOT NULL,
            baseline_end REAL NOT NULL,
            scenario_end REAL NOT NULL,
            runway REAL NOT NULL,
            first_negative INTEGER
        )""")

def save_simulation(workspace, assumptions, result):
    from datetime import datetime
    with sqlite3.connect(DB) as con:
        con.execute("""INSERT INTO simulations
        (created_at,workspace,assumptions,baseline_end,scenario_end,runway,first_negative)
        VALUES (?,?,?,?,?,?,?)""",
        (datetime.now().isoformat(timespec="seconds"),workspace,json.dumps(assumptions),
         result["baseline_end"],result["scenario_end"],result["runway"],result["first_negative"]))

def load_history():
    with sqlite3.connect(DB) as con:
        return pd.read_sql_query("SELECT id,created_at,workspace,assumptions,baseline_end,scenario_end,runway,first_negative FROM simulations ORDER BY id DESC",con)
