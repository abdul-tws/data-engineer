# 🗄️ Database Setup with Alembic

## Overview

This project uses **Alembic** for database migrations and **SQLAlchemy** for ORM. 

### Supported Databases

- ✅ **SQLite** (default, zero-config)
- ✅ **PostgreSQL** (production recommended)
- ✅ **MySQL/MariaDB** (supported)

---

## Quick Start

### Step 1: Install Dependencies
```bash
pip install -r requirements-local.txt
```

### Step 2: Run Database Setup
```bash
./setup_database.sh
```

Or manually:
```bash
# Apply migrations
alembic upgrade head
```

### Step 3: Verify Installation
```bash
# Check database file was created
ls -la *.db

# Run database tests
pytest tests/test_database.py -v
```

---

## Database Architecture

### SQLAlchemy Models

Located in `src/database/models.py`:

```python
# Core models
Fund                 # Master fund data
ReferencePrice       # Benchmark prices
FundPosition         # Positions from CSVs
ReconciledPrice      # Reconciliation results
MonthlyReturn        # Monthly performance
```

### Schema Diagram

```
funds (master data)
├── fund_id (PK, unique)
├── fund_name
├── currency
└── timestamps

reference_prices
├── fund_id (FK → funds)
├── price_date
└── price

fund_positions
├── fund_id (FK → funds)
├── position_date
├── position_price
├── quantity
└── value

reconciled_prices
├── fund_id (FK → funds)
├── position_date
├── position_price
├── reference_price
├── variance_pct
└── status

monthly_returns
├── fund_id (FK → funds)
├── year
├── month
├── opening_price
├── closing_price
└── monthly_return_pct
```

---

## Alembic Configuration

### File Structure

```
alembic/
├── env.py                 # Migration environment
├── script.py.mako         # Migration template
└── versions/
    └── 001_initial_schema.py    # Initial migration
```

### Key Files

**alembic.ini**
- Alembic configuration
- Database URL settings
- Logging configuration

**alembic/env.py**
- Migration execution logic
- Database connection setup
- Target metadata definition

**alembic/versions/001_initial_schema.py**
- Creates all 5 tables
- Defines indexes
- Sets up foreign keys

---

## Migration Commands

### Create New Migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add new column"

# Or manually create migration
alembic revision -m "Custom migration"
```

### Apply Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific number of migrations
alembic upgrade +2

# Downgrade all
alembic downgrade base
```

### View Migration History

```bash
# Show current revision
alembic current

# Show migration history
alembic history --verbose
```

---

## Database Configuration

### SQLite (Default)

**Automatic:**
```bash
./setup_database.sh
# Creates fund_reconciliation.db
```

**Manual:**
```bash
export DATABASE_URL="sqlite:///./fund_reconciliation.db"
alembic upgrade head
```

### PostgreSQL (Production)

```bash
# Install PostgreSQL driver
pip install psycopg2-binary

# Set connection string
export DATABASE_URL="postgresql://user:password@localhost:5432/fund_reconciliation"

# Apply migrations
alembic upgrade head
```

### MySQL

```bash
# Install MySQL driver
pip install mysql-connector-python

# Set connection string
export DATABASE_URL="mysql+pymysql://user:password@localhost:3306/fund_reconciliation"

# Apply migrations
alembic upgrade head
```

---

## Database Tables

### 1. funds
Master fund registry

```sql
CREATE TABLE funds (
  id INTEGER PRIMARY KEY,
  fund_id VARCHAR(50) UNIQUE NOT NULL,
  fund_name VARCHAR(255) NOT NULL,
  currency VARCHAR(3) DEFAULT 'USD',
  is_active BOOLEAN DEFAULT 1,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes:** fund_id

### 2. reference_prices
Benchmark prices for funds

```sql
CREATE TABLE reference_prices (
  id INTEGER PRIMARY KEY,
  fund_id VARCHAR(50) NOT NULL,
  price_date DATETIME NOT NULL,
  price DECIMAL(18,6) NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (fund_id) REFERENCES funds(fund_id)
);
```

**Indexes:** (fund_id, price_date)

### 3. fund_positions
Positions loaded from CSV files

```sql
CREATE TABLE fund_positions (
  id INTEGER PRIMARY KEY,
  fund_id VARCHAR(50) NOT NULL,
  position_date DATETIME NOT NULL,
  position_price DECIMAL(18,6) NOT NULL,
  quantity DECIMAL(18,6),
  value DECIMAL(18,6),
  source VARCHAR(50) DEFAULT 'csv',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (fund_id) REFERENCES funds(fund_id)
);
```

**Indexes:** (fund_id, position_date)

### 4. reconciled_prices
Reconciliation results

```sql
CREATE TABLE reconciled_prices (
  id INTEGER PRIMARY KEY,
  fund_id VARCHAR(50) NOT NULL,
  position_date DATETIME NOT NULL,
  position_price DECIMAL(18,6) NOT NULL,
  reference_price DECIMAL(18,6),
  variance DECIMAL(18,6),
  variance_pct DECIMAL(10,4),
  status VARCHAR(50) NOT NULL,
  is_flagged BOOLEAN DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (fund_id) REFERENCES funds(fund_id)
);
```

**Indexes:** (fund_id, status)

### 5. monthly_returns
Monthly performance metrics

```sql
CREATE TABLE monthly_returns (
  id INTEGER PRIMARY KEY,
  fund_id VARCHAR(50) NOT NULL,
  year INTEGER NOT NULL,
  month INTEGER NOT NULL,
  opening_price DECIMAL(18,6) NOT NULL,
  closing_price DECIMAL(18,6) NOT NULL,
  monthly_return DECIMAL(18,6) NOT NULL,
  monthly_return_pct DECIMAL(10,4) NOT NULL,
  is_best_performer BOOLEAN DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (fund_id) REFERENCES funds(fund_id)
);
```

**Indexes:** (fund_id, year, month)

---

## Testing

### Run All Database Tests

```bash
pytest tests/test_database.py -v
```

### Test Coverage

Tests include:

**Model Tests (25+ tests)**
- ✅ Fund creation and constraints
- ✅ Reference price creation
- ✅ Position creation with optional fields
- ✅ Reconciliation records
- ✅ Monthly returns calculation

**Integration Tests (8+ tests)**
- ✅ Full reconciliation workflow
- ✅ Multiple funds workflow
- ✅ Cross-table relationships

**Query Tests (7+ tests)**
- ✅ Query by fund and date
- ✅ Query flagged records
- ✅ Aggregation queries

**Total: 40+ database tests**

---

## Using Database in Code

### Session Management

```python
from src.database import get_session, Fund

# Get session
session = get_session()

# Create
fund = Fund(fund_id="FUND_A", fund_name="Growth Fund")
session.add(fund)
session.commit()

# Read
fund = session.query(Fund).filter(Fund.fund_id == "FUND_A").first()

# Update
fund.fund_name = "Updated Name"
session.commit()

# Delete
session.delete(fund)
session.commit()
```

### Querying Examples

```python
from src.database import Fund, FundPosition, ReferencePrice
from datetime import datetime

session = get_session()

# Get all funds
all_funds = session.query(Fund).all()

# Get specific fund
fund = session.query(Fund).filter(Fund.fund_id == "FUND_A").first()

# Get positions for date range
positions = session.query(FundPosition).filter(
    FundPosition.fund_id == "FUND_A",
    FundPosition.position_date >= datetime(2024, 1, 1)
).all()

# Get flagged reconciliations
flagged = session.query(ReconciledPrice).filter(
    ReconciledPrice.is_flagged == True
).all()

# Get best performers
best = session.query(MonthlyReturn).filter(
    MonthlyReturn.is_best_performer == True
).all()
```

---

## Production Deployment

### PostgreSQL Setup

```bash
# 1. Create database
createdb fund_reconciliation

# 2. Set connection
export DATABASE_URL="postgresql://user:password@localhost/fund_reconciliation"

# 3. Run migrations
alembic upgrade head

# 4. Verify
psql -c "SELECT * FROM funds;" fund_reconciliation
```

### Docker Setup

```dockerfile
FROM python:3.11

WORKDIR /app

COPY requirements-local.txt .
RUN pip install -r requirements-local.txt

COPY . .

# Run migrations on startup
CMD alembic upgrade head && \
    uvicorn src.api:app --host 0.0.0.0 --port 8000
```

---

## Troubleshooting

### Database file not created

```bash
# Ensure directory exists
mkdir -p fund_reconciliation_data

# Set database path
export DATABASE_URL="sqlite:///./fund_reconciliation_data/app.db"

# Run migrations
alembic upgrade head
```

### Migration conflicts

```bash
# Check current version
alembic current

# Downgrade and retry
alembic downgrade -1
alembic upgrade head
```

### Foreign key errors

```bash
# Enable foreign keys in SQLite
# Add to alembic/env.py:
# 
# if config.get_main_option('sqlalchemy.url').startswith('sqlite'):
#     @event.listens_for(Engine, "connect")
#     def set_sqlite_pragma(dbapi_conn, connection_record):
#         cursor = dbapi_conn.cursor()
#         cursor.execute("PRAGMA foreign_keys=ON")
#         cursor.close()
```

---

## Best Practices

✅ **Always use migrations**
- Never manually modify schema
- Use `alembic revision` for changes

✅ **Test migrations**
- Run tests after migrations
- Keep database in clean state

✅ **Use transactions**
- Wrap changes in try/except
- Always commit or rollback

✅ **Index frequently queried columns**
- fund_id, position_date, status
- Improves query performance

✅ **Set database in environment**
- Use DATABASE_URL variable
- Don't hardcode in code

---

## Summary

✅ **Alembic Setup:** Complete with initial migration  
✅ **SQLAlchemy Models:** 5 tables, properly indexed  
✅ **Database Tests:** 40+ test cases  
✅ **Setup Script:** Automated setup with `setup_database.sh`  
✅ **Multiple DB Support:** SQLite, PostgreSQL, MySQL  
✅ **Production Ready:** Proper configuration and best practices  

Ready to use! Run `./setup_database.sh` to get started.

