import os
import re
import sqlite3
from pathlib import Path
import pandas as pd

CSV_PATH = Path("transactions_data.csv")
DB_PATH  = Path("kaggle_transactions.sqlite")
TABLE    = "transactions"
CHUNKSIZE = 200_000
MAX_ROWS = 300_000  # ← Limit to 1 million rows

def clean_columns(cols):
    out = []
    for c in cols:
        c = str(c).strip().lower()
        c = re.sub(r"[^\w]+", "_", c)
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

    print(f"\n{'='*60}")
    print(f"📊 Creating database with most recent {MAX_ROWS:,} rows")
    print(f"{'='*60}\n")

    # Sample first to detect columns & choose parsers
    sample = pd.read_csv(CSV_PATH, nrows=5000)
    sample.columns = clean_columns(sample.columns)

    # Find date column for sorting
    parse_dates = [c for c in sample.columns if likely_datetime(c)]
    date_column = parse_dates[0] if parse_dates else None
    
    if date_column:
        print(f"📅 Found date column: {date_column}")
        print(f"🔄 Will sort by {date_column} DESC to get most recent data\n")
    else:
        print("⚠️  No date column found, will take first 1M rows\n")

    # Read entire CSV (sorted by date)
    print("📖 Reading CSV file...")
    df = pd.read_csv(
        CSV_PATH,
        parse_dates=parse_dates if parse_dates else None,
        dtype_backend="pyarrow"
    )
    
    # Clean column names
    df.columns = clean_columns(df.columns)
    
    print(f"✅ Total rows in CSV: {len(df):,}")
    
    # Sort by date (most recent first) if date column exists
    if date_column and date_column in df.columns:
        print(f"🔄 Sorting by {date_column} DESC...")
        df = df.sort_values(by=date_column, ascending=False)
    
    # Take only the most recent MAX_ROWS
    if len(df) > MAX_ROWS:
        print(f"✂️  Limiting to most recent {MAX_ROWS:,} rows...")
        df = df.head(MAX_ROWS)
    
    print(f"📊 Final dataset: {len(df):,} rows\n")
    
    # Data cleaning
    print("🧹 Cleaning data...")
    
    # Strip string columns, turn blanks into None
    for c in df.select_dtypes(include="string").columns:
        df[c] = df[c].str.strip()
        df[c] = df[c].replace({"": None})
    
    # Numeric coercion for amount-like fields
    for c in df.columns:
        if likely_numeric(c):
            df[c] = df[c].astype("string")
            df[c] = df[c].str.replace(r"[^\d\.\-]", "", regex=True)
            df[c] = pd.to_numeric(df[c], errors="coerce")
    
    # Create database
    print("💾 Writing to SQLite database...")
    conn = sqlite3.connect(DB_PATH)
    
    # Speed up bulk load
    conn.execute("PRAGMA journal_mode = OFF;")
    conn.execute("PRAGMA synchronous = OFF;")
    conn.execute("PRAGMA temp_store = MEMORY;")
    conn.execute("PRAGMA locking_mode = EXCLUSIVE;")
    
    # Write to database
    df.to_sql(TABLE, conn, if_exists="replace", index=False, chunksize=CHUNKSIZE)
    
    print(f"✅ Wrote {len(df):,} rows to {DB_PATH}")
    
    # Create indexes
    print("\n🔍 Creating indexes...")
    cols = df.columns.tolist()
    create_helpful_indexes(conn, TABLE, cols)
    
    # Analyze DB for query planner
    conn.execute("ANALYZE;")
    conn.commit()
    conn.close()
    
    # Show database size
    db_size_mb = os.path.getsize(DB_PATH) / (1024 * 1024)
    
    print("\n" + "="*60)
    print("✅ Database created successfully!")
    print("="*60)
    print(f"📁 Database file: {DB_PATH}")
    print(f"📊 Total rows: {len(df):,}")
    print(f"💾 Database size: {db_size_mb:.2f} MB")
    
    if date_column and date_column in df.columns:
        print(f"📅 Date range:")
        print(f"   Most recent: {df[date_column].max()}")
        print(f"   Oldest: {df[date_column].min()}")
    
    print("="*60)
    
    # Warning if still too big for GitHub
    if db_size_mb > 90:
        print("\n⚠️  WARNING: Database is still > 90 MB")
        print("   GitHub limit is 100 MB")
        print(f"   Consider reducing MAX_ROWS to ~{int(MAX_ROWS * 90 / db_size_mb):,}")

if __name__ == "__main__":
    main()