"""
Database Manager - Handles SQLite connections and operations
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional


class DatabaseManager:
    """Manages SQLite database for fund reconciliation"""
    
    def __init__(self, db_path: Path):
        """Initialize database manager"""
        self.db_path = Path(db_path)
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """Connect to SQLite database"""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
    
    def initialize(self):
        """Initialize database schema"""
        self.connect()
        
        # Create tables if they don't exist
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS reference_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fund_id TEXT NOT NULL,
                price_date DATE NOT NULL,
                price REAL NOT NULL,
                UNIQUE(fund_id, price_date)
            )
        """)
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS fund_positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fund_id TEXT NOT NULL,
                fund_name TEXT,
                position_date DATE NOT NULL,
                position_price REAL NOT NULL,
                quantity REAL,
                value REAL,
                source TEXT,
                UNIQUE(fund_id, position_date, source)
            )
        """)
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS reconciled_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fund_id TEXT NOT NULL,
                position_date DATE NOT NULL,
                position_price REAL NOT NULL,
                reference_price REAL,
                reference_date DATE,
                price_variance REAL,
                variance_pct REAL,
                reconciliation_status TEXT
            )
        """)
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS monthly_returns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fund_id TEXT NOT NULL,
                fund_name TEXT,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                opening_price REAL,
                closing_price REAL,
                monthly_return REAL,
                monthly_return_pct REAL
            )
        """)
        
        self.connection.commit()
        print("  Database schema initialized")
    
    def load_sql_file(self, sql_file: Path):
        """Load and execute SQL from file"""
        try:
            with open(sql_file, 'r') as f:
                sql_content = f.read()
            
            # Split by semicolon and execute each statement
            statements = sql_content.split(';')
            for statement in statements:
                statement = statement.strip()
                if statement:
                    self.cursor.execute(statement)
            
            self.connection.commit()
            print(f"  Loaded reference SQL: {sql_file.name}")
        except Exception as e:
            print(f"  Error loading SQL file: {e}")
            self.connection.rollback()
    
    def insert_fund_position(self, fund_id: str, fund_name: str, position_date: str,
                            position_price: float, quantity: float = None, 
                            value: float = None, source: str = None):
        """Insert fund position record"""
        try:
            self.cursor.execute("""
                INSERT OR REPLACE INTO fund_positions
                (fund_id, fund_name, position_date, position_price, quantity, value, source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (fund_id, fund_name, position_date, position_price, quantity, value, source))
            self.connection.commit()
        except Exception as e:
            print(f"Error inserting fund position: {e}")
    
    def insert_reference_price(self, fund_id: str, price_date: str, price: float):
        """Insert reference price"""
        try:
            self.cursor.execute("""
                INSERT OR REPLACE INTO reference_prices (fund_id, price_date, price)
                VALUES (?, ?, ?)
            """, (fund_id, price_date, price))
            self.connection.commit()
        except Exception as e:
            print(f"Error inserting reference price: {e}")
    
    def insert_reconciled_price(self, fund_id: str, position_date: str, position_price: float,
                               reference_price: float, reference_date: str, 
                               price_variance: float, variance_pct: float, status: str):
        """Insert reconciled price record"""
        try:
            self.cursor.execute("""
                INSERT INTO reconciled_prices
                (fund_id, position_date, position_price, reference_price, reference_date,
                 price_variance, variance_pct, reconciliation_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (fund_id, position_date, position_price, reference_price, reference_date,
                  price_variance, variance_pct, status))
            self.connection.commit()
        except Exception as e:
            print(f"Error inserting reconciled price: {e}")
    
    def insert_monthly_return(self, fund_id: str, fund_name: str, year: int, month: int,
                            opening_price: float, closing_price: float, 
                            monthly_return: float, monthly_return_pct: float):
        """Insert monthly return record"""
        try:
            self.cursor.execute("""
                INSERT INTO monthly_returns
                (fund_id, fund_name, year, month, opening_price, closing_price,
                 monthly_return, monthly_return_pct)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (fund_id, fund_name, year, month, opening_price, closing_price,
                  monthly_return, monthly_return_pct))
            self.connection.commit()
        except Exception as e:
            print(f"Error inserting monthly return: {e}")
    
    def get_fund_positions(self) -> List[Dict[str, Any]]:
        """Get all fund positions"""
        self.cursor.execute("SELECT * FROM fund_positions ORDER BY fund_id, position_date")
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_reference_price(self, fund_id: str, price_date: str) -> Optional[tuple]:
        """Get reference price for fund on specific date or latest before date"""
        # Try exact date first
        self.cursor.execute("""
            SELECT price, price_date FROM reference_prices
            WHERE fund_id = ? AND price_date = ?
        """, (fund_id, price_date))
        result = self.cursor.fetchone()
        
        if result:
            return (result[0], result[1])
        
        # Get latest price before the date
        self.cursor.execute("""
            SELECT price, price_date FROM reference_prices
            WHERE fund_id = ? AND price_date <= ?
            ORDER BY price_date DESC
            LIMIT 1
        """, (fund_id, price_date))
        result = self.cursor.fetchone()
        
        return (result[0], result[1]) if result else None
    
    def get_monthly_returns(self) -> List[Dict[str, Any]]:
        """Get all monthly returns"""
        self.cursor.execute("""
            SELECT * FROM monthly_returns
            ORDER BY year, month, fund_id
        """)
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_reconciled_prices(self) -> List[Dict[str, Any]]:
        """Get all reconciled prices"""
        self.cursor.execute("""
            SELECT * FROM reconciled_prices
            ORDER BY fund_id, position_date
        """)
        return [dict(row) for row in self.cursor.fetchall()]
