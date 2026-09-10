import csv
import re
import sqlite3
from datetime import date
from pathlib import Path

FUNDS = {
    "Whitestone", "Wallington", "Catalysm", "Belaware", "Gohen",
    "Applebead", "Magnum", "Trustmind", "Leeder", "Virtous"
}

DATE_PATTERNS = [
    re.compile(r"(?P<y>\d{4})[-_](?P<m>\d{2})[-_](?P<d>\d{2})"),
    re.compile(r"(?P<y>\d{4})[-_]?(?P<m>\d{2})(?P<d>\d{2})"),
    re.compile(r"(?P<a>\d{1,2})[-_](?P<b>\d{1,2})[-_](?P<y>\d{4})"),
]


def parse_eom_date(filename):
    for idx, pattern in enumerate(DATE_PATTERNS):
        match = pattern.search(filename)
        if not match:
            continue
        if idx < 2:
            y = int(match.group("y"))
            m = int(match.group("m"))
            d = int(match.group("d"))
        else:
            a = int(match.group("a"))
            b = int(match.group("b"))
            y = int(match.group("y"))
            if a > 12 and b <= 12:
                d, m = a, b
            elif b > 12 and a <= 12:
                m, d = a, b
            else:
                m, d = a, b
        return date(y, m, d).isoformat()
    raise ValueError(f"Could not find EOM date in {filename}")


def infer_fund(filename):
    name = filename.lower()
    for fund in FUNDS:
        if fund.lower() in name:
            return fund
    raise ValueError(f"Could not find fund name in {filename}")


def text(value):
    value = "" if value is None else str(value).strip()
    return value or None


def number(value):
    value = text(value)
    return None if value is None else float(value.replace(",", ""))


def reference_date(raw):
    raw = text(raw)
    if not raw:
        return None
    if re.fullmatch(r"\d{4}-\d{1,2}-\d{1,2}", raw):
        y, m, d = map(int, raw.split("-"))
        return f"{y:04d}-{m:02d}-{d:02d}"
    m, d, y = map(int, raw.split("/"))
    return f"{y:04d}-{m:02d}-{d:02d}"


def setup_database(conn, master_sql):
    # Load the supplied reference schema and normalize reference dates.
    conn.executescript(master_sql.read_text(encoding="utf-8"))

    conn.create_function("reference_date", 1, reference_date)
    conn.executescript(
        """
        DROP TABLE IF EXISTS equity_prices_norm;
        CREATE TABLE equity_prices_norm AS
        SELECT SYMBOL, PRICE, reference_date(DATETIME) AS price_date
        FROM equity_prices;

        DROP TABLE IF EXISTS bond_prices_norm;
        CREATE TABLE bond_prices_norm AS
        SELECT ISIN, PRICE, reference_date(DATETIME) AS price_date
        FROM bond_prices;

        CREATE INDEX idx_equity_price ON equity_prices_norm(SYMBOL, price_date);
        CREATE INDEX idx_bond_price ON bond_prices_norm(ISIN, price_date);
        CREATE INDEX idx_bond_ref_sedol ON bond_reference(SEDOL);
        CREATE INDEX idx_bond_ref_isin ON bond_reference(ISIN);
        """
    )

    conn.executescript(
        """
        DROP TABLE IF EXISTS fund_positions;
        CREATE TABLE fund_positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fund TEXT NOT NULL,
            eom_date TEXT NOT NULL,
            source_file TEXT NOT NULL,
            financial_type TEXT NOT NULL,
            symbol TEXT,
            security_name TEXT,
            sedol TEXT,
            isin TEXT,
            price REAL,
            quantity REAL,
            realised_pl REAL,
            market_value REAL
        );
        CREATE INDEX idx_positions_fund_date ON fund_positions(fund, eom_date);
        CREATE INDEX idx_positions_symbol ON fund_positions(symbol);
        CREATE INDEX idx_positions_isin ON fund_positions(isin);
        CREATE INDEX idx_positions_sedol ON fund_positions(sedol);
        """
    )


def load_fund_files(conn, external_dir):
    insert_sql = """
        INSERT INTO fund_positions
        (fund, eom_date, source_file, financial_type, symbol, security_name,
         sedol, isin, price, quantity, realised_pl, market_value)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    total = 0
    files = sorted(external_dir.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No CSV files found in {external_dir}")

    # Different funds use slightly different file layouts, so map them into one table.
    with conn:
        for path in files:
            fund = infer_fund(path.name)
            eom = parse_eom_date(path.name)
            with path.open("r", encoding="utf-8-sig", newline="") as fh:
                reader = csv.DictReader(fh)
                required = {"FINANCIAL TYPE", "PRICE", "QUANTITY", "MARKET VALUE", "REALISED P/L"}
                missing = required - set(reader.fieldnames or [])
                if missing:
                    raise ValueError(f"Missing columns in {path.name}: {sorted(missing)}")

                rows = []
                for row in reader:
                    rows.append(
                        (
                            fund,
                            eom,
                            path.name,
                            text(row.get("FINANCIAL TYPE")) or "UNKNOWN",
                            text(row.get("SYMBOL")),
                            text(row.get("SECURITY NAME")),
                            text(row.get("SEDOL")),
                            text(row.get("ISIN")),
                            number(row.get("PRICE")),
                            number(row.get("QUANTITY")),
                            number(row.get("REALISED P/L")),
                            number(row.get("MARKET VALUE")),
                        )
                    )
                conn.executemany(insert_sql, rows)
                total += len(rows)
    return total


def create_position_view(conn):
    conn.executescript(
        """
        DROP VIEW IF EXISTS positions;
        CREATE VIEW positions AS
        SELECT
            p.*,
            CASE
                WHEN p.financial_type = 'Equities' THEN p.symbol
                WHEN p.financial_type = 'Government Bond' THEN COALESCE(p.isin, b.ISIN)
                ELSE NULL
            END AS instrument_key
        FROM fund_positions p
        LEFT JOIN bond_reference b
          ON p.financial_type = 'Government Bond'
         AND p.sedol = b.SEDOL;
        """
    )


def write_csv(conn, sql, output_path):
    cur = conn.execute(sql)
    headers = [col[0] for col in cur.description]
    rows = cur.fetchall()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(headers)
        writer.writerows(rows)
    return len(rows)


def write_price_reconciliation(conn, output_path):
    # Pick the EOM price first; otherwise use the most recent earlier reference price.
    sql = """
    WITH candidates AS (
        SELECT
            p.id, p.fund, p.eom_date, p.source_file, p.financial_type,
            p.symbol, p.security_name, p.sedol, p.isin,
            p.instrument_key, p.price AS fund_price,
            ep.price_date AS ref_date, ep.PRICE AS ref_price
        FROM positions p
        LEFT JOIN equity_prices_norm ep
          ON p.financial_type = 'Equities'
         AND ep.SYMBOL = p.instrument_key
         AND ep.price_date <= p.eom_date
        WHERE p.financial_type = 'Equities'

        UNION ALL

        SELECT
            p.id, p.fund, p.eom_date, p.source_file, p.financial_type,
            p.symbol, p.security_name, p.sedol, p.isin,
            p.instrument_key, p.price AS fund_price,
            bp.price_date AS ref_date, bp.PRICE AS ref_price
        FROM positions p
        LEFT JOIN bond_prices_norm bp
          ON p.financial_type = 'Government Bond'
         AND bp.ISIN = p.instrument_key
         AND bp.price_date <= p.eom_date
        WHERE p.financial_type = 'Government Bond'
    ), ranked AS (
        SELECT *,
               ROW_NUMBER() OVER (
                   PARTITION BY id
                   ORDER BY ref_date DESC
               ) AS rn
        FROM candidates
    )
    SELECT
        fund,
        eom_date,
        source_file,
        financial_type,
        instrument_key,
        symbol,
        security_name,
        sedol,
        isin,
        fund_price,
        ref_date AS reference_price_date,
        ref_price AS reference_price,
        ROUND(fund_price - ref_price, 10) AS price_difference,
        CASE
            WHEN ref_price IS NULL THEN 'MISSING_REFERENCE_PRICE'
            WHEN ref_date = eom_date THEN 'MATCHED_EOM'
            ELSE 'FALLBACK_LAST_AVAILABLE'
        END AS reconciliation_status
    FROM ranked
    WHERE rn = 1
    ORDER BY eom_date, fund, financial_type, instrument_key;
    """
    return write_csv(conn, sql, output_path)


def write_best_fund(conn, output_path):
    # Use the previous month-end MV as the starting value for each fund.
    sql = """
    WITH monthly AS (
        SELECT
            fund,
            eom_date,
            SUM(COALESCE(market_value, 0)) AS fund_mv_end,
            SUM(COALESCE(realised_pl, 0)) AS realised_pl
        FROM fund_positions
        GROUP BY fund, eom_date
    ), periods AS (
        SELECT
            fund,
            eom_date,
            fund_mv_end,
            realised_pl,
            LAG(fund_mv_end) OVER (
                PARTITION BY fund
                ORDER BY eom_date
            ) AS fund_mv_start
        FROM monthly
    ), returns AS (
        SELECT
            fund,
            eom_date,
            fund_mv_start,
            fund_mv_end,
            realised_pl,
            CASE
                WHEN fund_mv_start IS NULL OR fund_mv_start = 0 THEN NULL
                ELSE (fund_mv_end - fund_mv_start + realised_pl) / fund_mv_start
            END AS rate_of_return
        FROM periods
        WHERE fund_mv_start IS NOT NULL
    ), ranked AS (
        SELECT *,
               RANK() OVER (
                   PARTITION BY eom_date
                   ORDER BY rate_of_return DESC
               ) AS month_rank
        FROM returns
        WHERE rate_of_return IS NOT NULL
    )
    SELECT
        strftime('%Y-%m', eom_date) AS month,
        fund,
        ROUND(fund_mv_start, 6) AS fund_mv_start,
        ROUND(fund_mv_end, 6) AS fund_mv_end,
        ROUND(realised_pl, 6) AS realised_pl,
        ROUND(rate_of_return, 10) AS rate_of_return,
        month_rank
    FROM ranked
    WHERE month_rank = 1
    ORDER BY month;
    """
    return write_csv(conn, sql, output_path)


def run(input_dir, db_path, output_dir):
    input_dir = input_dir.resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not (input_dir / "master-reference-sql.sql").exists():
        raise FileNotFoundError(f"Missing master-reference-sql.sql in {input_dir}")

    conn = sqlite3.connect(db_path)
    try:
        setup_database(conn, input_dir / "master-reference-sql.sql")
        rows = load_fund_files(conn, input_dir / "external-funds")
        create_position_view(conn)
        reconciliation_rows = write_price_reconciliation(
            conn, output_dir / "price_reconciliation.csv"
        )
        best_fund_rows = write_best_fund(
            conn, output_dir / "best_fund_by_month.csv"
        )
        return rows, reconciliation_rows, best_fund_rows
    finally:
        conn.close()


def main():
    project_dir = Path(__file__).resolve().parents[1]
    input_dir = project_dir / "data" / "Send_data"
    db_path = project_dir / "data" / "analytics.db"
    output_dir = project_dir / "output"

    loaded, reconciliation, best_fund = run(input_dir, db_path, output_dir)
    print(f"Loaded position rows : {loaded}")
    print(f"Reconciliation rows  : {reconciliation}")
    print(f"Best-fund rows       : {best_fund}")
    print(f"Output directory     : {output_dir.resolve()}")


if __name__ == "__main__":
    main()
