# Fund Position Reconciliation

A Python + SQLite solution for reconciling fund positions against reference prices, calculating monthly returns, and identifying best-performing funds.

## Overview

This project provides a complete fund reconciliation pipeline:

1. **Loads Reference Data** - Imports reference fund prices from SQL
2. **Processes Fund Reports** - Reads and normalizes CSV files in multiple formats
3. **Reconciles Prices** - Matches fund positions against reference prices (exact match or fallback)
4. **Calculates Returns** - Computes monthly fund returns and performance
5. **Identifies Winners** - Finds best-performing fund for each month
6. **Generates Reports** - Creates CSV outputs for reconciliation and analysis

## Features

- ✅ **Multi-format CSV Support** - Handles Format A, B, C, and generic formats
- ✅ **Flexible Date Parsing** - Supports multiple date formats (YYYY-MM-DD, DD-MM-YYYY, DD/MM/YYYY, etc.)
- ✅ **Smart Price Matching** - Exact EOM date match with intelligent fallback to latest available price
- ✅ **Variance Analysis** - Calculates price variance between position and reference prices
- ✅ **Monthly Analytics** - Computes monthly returns and identifies top performers
- ✅ **Reconciliation Status** - Detailed status indicators (EXACT_MATCH, FALLBACK_*, HIGH_VARIANCE, etc.)

## Requirements

- Python 3.10+
- SQLite3 (included with Python)

## Project Structure

```
fund-reconciliation/
├── src/
│   ├── main.py                 # Entry point
│   ├── database.py             # SQLite database operations
│   ├── csv_processor.py        # CSV reading and normalization
│   ├── reconciler.py           # Price reconciliation logic
│   ├── analytics.py            # Monthly returns and performance
│   └── output_generator.py     # CSV report generation
├── data/
│   ├── reference_prices.sql    # Reference price data
│   ├── Send_data/              # Input CSV files
│   │   ├── fund_positions_format_a.csv
│   │   ├── fund_positions_format_b.csv
│   │   └── fund_positions_format_c.csv
│   └── analytics.db            # SQLite database (created on run)
├── output/                      # Generated reports
│   ├── price_reconciliation.csv
│   └── best_fund_by_month.csv
└── README.md
```

## Installation

1. **Clone or download the project**

2. **Ensure Python 3.10+ is installed**
   ```bash
   python --version
   ```

3. **No external dependencies required** - Uses only Python standard library

## Usage

### Basic Run

From the project root directory:

```bash
python src/main.py
```

This will:
1. Initialize SQLite database
2. Load reference prices from `data/reference_prices.sql`
3. Process all CSV files from `data/Send_data/`
4. Reconcile prices and calculate returns
5. Generate output files in `output/`

### Sample Output

```
Starting Fund Position Reconciliation...
Project root: /path/to/fund-reconciliation

[1/5] Initializing database...
  Database schema initialized

[2/5] Processing fund CSV reports...
  Found 3 CSV files in /path/to/data/Send_data
  Processing: fund_positions_format_a.csv
    Detected format: format_a
  Processing: fund_positions_format_b.csv
    Detected format: format_b
  Processing: fund_positions_format_c.csv
    Detected format: format_c

[3/5] Reconciling fund prices...
  Reconciled 42 fund records

[4/5] Calculating monthly returns and best performers...
  Calculated returns for 12 entries
  Identified 6 monthly winners

[5/5] Generating output files...
  ✓ Created /path/to/output/price_reconciliation.csv
  ✓ Created /path/to/output/best_fund_by_month.csv
  ✓ Database saved to /path/to/data/analytics.db

✅ Fund Position Reconciliation completed successfully!
```

## Input Data Format

### CSV Formats Supported

#### Format A (Standard)
```
Fund_ID,Fund_Name,Date,Price,Quantity,Value
FUND_A,Growth Fund A,2024-01-15,100.25,1000,100250
```
- Standard column names expected
- Includes quantity and value fields

#### Format B (Alternative)
```
FundCode,FundName,TradeDate,Value
FUND_B,Income Fund B,2024-01-15,50.10
```
- Alternative naming convention
- NAV provided as "Value"

#### Format C (Extended)
```
ISIN,FundName,Date_EOM,NAV
IE00B4L5Y983,Balanced Fund C,2024-01-31,149.80
```
- ISIN-based identification
- Explicit NAV field

#### Generic Format
Processor attempts to match columns flexibly:
- Fund identifier: columns containing "id" or "code"
- Date: columns containing "date"
- Price: columns containing "price", "nav", or "value"

### Reference Price Format (SQL)

```sql
INSERT INTO reference_prices (fund_id, price_date, price) VALUES
('FUND_A', '2024-01-31', 100.50),
('FUND_A', '2024-02-29', 102.30);
```

## Output Files

### price_reconciliation.csv

Shows how each fund position's price compares to reference data:

| Fund_ID | Position_Date | Position_Price | Reference_Price | Reference_Date | Price_Variance | Variance_Pct | Reconciliation_Status |
|---------|--------------|-----------------|-----------------|-----------------|----------------|--------------|----------------------|
| FUND_A | 2024-01-15 | 100.25 | 100.50 | 2024-01-31 | -0.25 | -0.25 | FALLBACK_WITHIN_WEEK |
| FUND_A | 2024-01-31 | 100.50 | 100.50 | 2024-01-31 | 0.00 | 0.00 | EXACT_MATCH |

**Reconciliation Status Values:**
- `EXACT_MATCH` - Position date matches reference date, variance < 0.01%
- `MATCHED_MINOR_VARIANCE` - Exact date match, variance < 0.1%
- `MATCHED_ACCEPTABLE_VARIANCE` - Exact date match, variance < 1%
- `MATCHED_HIGH_VARIANCE` - Exact date match, variance > 1%
- `FALLBACK_SAME_DAY` - Using latest reference within same day
- `FALLBACK_WITHIN_WEEK` - Using latest reference within 7 days
- `FALLBACK_WITHIN_MONTH` - Using latest reference within 31 days
- `FALLBACK_STALE_DATA` - Using reference older than 1 month
- `NO_REFERENCE_DATA` - No reference price available

### best_fund_by_month.csv

Shows the best-performing fund for each month:

| Year | Month | Month_Label | Fund_ID | Fund_Name | Opening_Price | Closing_Price | Monthly_Return | Monthly_Return_Pct |
|------|-------|------------|---------|-----------|---------------|--------------|-----------------|--------------------|
| 2024 | 1 | January 2024 | FUND_A | Growth Fund A | 100.25 | 100.50 | 0.25 | 0.2498 |
| 2024 | 2 | February 2024 | FUND_A | Growth Fund A | 101.80 | 102.30 | 0.50 | 0.4910 |

## Database Schema

### reference_prices
```sql
CREATE TABLE reference_prices (
    id INTEGER PRIMARY KEY,
    fund_id TEXT NOT NULL,
    price_date DATE NOT NULL,
    price REAL NOT NULL,
    UNIQUE(fund_id, price_date)
);
```

### fund_positions
```sql
CREATE TABLE fund_positions (
    id INTEGER PRIMARY KEY,
    fund_id TEXT NOT NULL,
    fund_name TEXT,
    position_date DATE NOT NULL,
    position_price REAL NOT NULL,
    quantity REAL,
    value REAL,
    source TEXT,
    UNIQUE(fund_id, position_date, source)
);
```

### reconciled_prices
```sql
CREATE TABLE reconciled_prices (
    id INTEGER PRIMARY KEY,
    fund_id TEXT NOT NULL,
    position_date DATE NOT NULL,
    position_price REAL NOT NULL,
    reference_price REAL,
    reference_date DATE,
    price_variance REAL,
    variance_pct REAL,
    reconciliation_status TEXT
);
```

### monthly_returns
```sql
CREATE TABLE monthly_returns (
    id INTEGER PRIMARY KEY,
    fund_id TEXT NOT NULL,
    fund_name TEXT,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    opening_price REAL,
    closing_price REAL,
    monthly_return REAL,
    monthly_return_pct REAL
);
```

## Configuration

### Custom Data Paths

Modify `main.py` to use custom paths:

```python
data_dir = Path('/custom/data/path')
send_data_dir = Path('/custom/csv/path')
output_dir = Path('/custom/output/path')
```

### Price Variance Thresholds

Adjust variance thresholds in `reconciler.py`:

```python
def _determine_status(self, position_date, reference_date, variance_pct):
    if abs(variance_pct) < 0.01:      # Modify these thresholds
        return 'EXACT_MATCH'
    elif abs(variance_pct) < 0.1:
        return 'MATCHED_MINOR_VARIANCE'
```

## Troubleshooting

### No CSV files found
- Ensure CSV files are in `data/Send_data/` directory
- Check file extensions are `.csv`

### Date parsing errors
- Check date format in CSV files
- Supported formats: YYYY-MM-DD, DD-MM-YYYY, MM-DD-YYYY, YYYY/MM/DD, DD/MM/YYYY, etc.
- Add new formats to `csv_processor.py` if needed

### No reference prices
- Create/update `data/reference_prices.sql` with reference data
- Ensure fund IDs in reference data match position data

### Database locked
- Delete `data/analytics.db` and run again
- Database recreates on each run

## Adding New Data

### Add CSV Files
Place CSV files in `data/Send_data/` and re-run the application. The processor will automatically detect the format.

### Add Reference Prices
Update or create `data/reference_prices.sql`:

```sql
INSERT INTO reference_prices (fund_id, price_date, price) VALUES
('NEW_FUND', '2024-01-31', 100.00);
```

## Performance

- **Typical execution**: < 5 seconds for 1,000+ fund positions
- **Database**: SQLite file-based (no server required)
- **Memory**: Minimal - processes in batches

## License

Use as needed for your fund reconciliation requirements.

## Support

For issues or enhancements:
1. Check troubleshooting section above
2. Verify input data format
3. Check database file permissions
