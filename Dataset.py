import os
import re
import sqlite3
from pathlib import Path
import pandas as pd

CSV_PATH = Path("transactions_data.csv")      # <- your file
DB_PATH  = Path("kaggle_transactions.sqlite")
TABLE    = "transactions"                    # change if you like
CHUNKSIZE = 200_000                          # lower if memory is tight

def clean_columns(cols):
    out = []
    for c in cols:
        c = str(c).strip().lower()
        c = re.sub(r"[^\w]+", "_", c)        # spaces, punctuation -> _
        c = re.sub(r"_+", "_", c).strip("_")
        if not c: c = "col"
        out.append(c)
    return out

def likely_datetime(name: str) -> bool:
    k = name.lower()
    return any(t in k for t in ["date","time","timestamp","created","dt"])

def likely_numeric(name: str) -> bool:
    k = name.lower()
    return any(t in k for t in ["amount","value","balance","qty","count","fee","price"])

def create_helpful_indexes(conn, table, cols):
    cur = conn.cursor()
    candidates = [
        ("transaction_id", f"idx_{table}_transaction_id"),
        ("customer_id",    f"idx_{table}_customer_id"),
        ("user_id",        f"idx_{table}_user_id"),
        ("merchant_id",    f"idx_{table}_merchant_id"),
        ("amount",         f"idx_{table}_amount"),
    ]
    for col, idx in candidates:
        if col in cols:
            cur.execute(f'CREATE INDEX IF NOT EXISTS {idx} ON "{table}"("{col}");')

    # index first datetime-like column, if any
    dt_cols = [c for c in cols if likely_datetime(c)]
    if dt_cols:
        cur.execute(f'CREATE INDEX IF NOT EXISTS idx_{table}_{dt_cols[0]} ON "{table}"("{dt_cols[0]}");')

    conn.commit()

def main():
    assert CSV_PATH.exists(), f"CSV not found: {CSV_PATH}"

    # Sample first to detect columns & choose parsers
    sample = pd.read_csv(CSV_PATH, nrows=5000)
    sample.columns = clean_columns(sample.columns)

    parse_dates = [c for c in sample.columns if likely_datetime(c)]
    # read in chunks with lightweight coercion
    first = True
    total = 0

    conn = sqlite3.connect(DB_PATH)

    # Speed up bulk load
    conn.execute("PRAGMA journal_mode = OFF;")
    conn.execute("PRAGMA synchronous = OFF;")
    conn.execute("PRAGMA temp_store = MEMORY;")
    conn.execute("PRAGMA locking_mode = EXCLUSIVE;")

    for chunk in pd.read_csv(
        CSV_PATH,
        chunksize=CHUNKSIZE,
        parse_dates=[c for c in parse_dates if c in sample.columns],
        dtype_backend="pyarrow"  # keeps memory in check & good types
    ):
        # column cleanup
        chunk.columns = clean_columns(chunk.columns)

        # strip string columns, turn blanks into None
        for c in chunk.select_dtypes(include="string").columns:
            chunk[c] = chunk[c].str.strip()
            chunk[c] = chunk[c].replace({"": None})

        # numeric coercion for amount-like fields
        for c in chunk.columns:

            if likely_numeric(c):
        # Make sure we're working with strings
                chunk[c] = chunk[c].astype("string")

        # Remove currency symbols, commas, spaces, etc.
                chunk[c] = chunk[c].str.replace(r"[^\d\.\-]", "", regex=True)

        # Convert to actual numbers; invalid ones become NaN
                chunk[c] = pd.to_numeric(chunk[c], errors="coerce")


        # dump to sqlite
        chunk.to_sql(TABLE, conn, if_exists="replace" if first else "append", index=False)
        total += len(chunk)
        first = False
        print(f"Loaded {total:,} rows...", end="\r")

    print(f"\n✅ Done. Wrote {total:,} rows to {DB_PATH} (table '{TABLE}').")

    # Helpful indexes
    cols = sample.columns.tolist()
    create_helpful_indexes(conn, TABLE, cols)

    # Analyze DB for query planner
    conn.execute("ANALYZE;")
    conn.commit()
    conn.close()
    print("✅ Indexes created and ANALYZE run.")

if __name__ == "__main__":
    main()
