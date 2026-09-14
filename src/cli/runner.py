"""
CLI Runner
E2E test runner without API dependency
Tests core business logic directly
"""

import json
from pathlib import Path
from decimal import Decimal
from datetime import datetime
from typing import List, Dict, Optional

from src.core import (
    ReconciliationEngine,
    AnalyticsEngine,
    CSVProcessor,
    Position,
    PricePoint,
    PriceSnapshot
)


class CLIRunner:
    """
    CLI Runner
    Executes fund reconciliation end-to-end without API
    """
    
    def __init__(self, 
                 data_dir: Path = Path("data"),
                 output_dir: Path = Path("output")):
        """
        Initialize CLI runner
        
        Args:
            data_dir: Directory containing CSV and reference files
            output_dir: Directory for output files
        """
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.data_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize engines
        self.reconciliation_engine = ReconciliationEngine()
        self.analytics_engine = AnalyticsEngine()
        self.csv_processor = CSVProcessor()
        
        # Data holders
        self.positions: List[Position] = []
        self.reference_prices: List[PricePoint] = []
        self.reconciliation_results = []
        self.monthly_returns = []
    
    def run_full_workflow(self, verbose: bool = True) -> Dict[str, any]:
        """
        Run full reconciliation workflow
        
        1. Load CSVs
        2. Load reference prices
        3. Reconcile positions
        4. Calculate analytics
        5. Generate reports
        
        Args:
            verbose: Print progress
            
        Returns:
            Summary of results
        """
        
        if verbose:
            print("🚀 Starting Fund Reconciliation E2E Workflow\n")
        
        # Step 1: Load CSV data
        if verbose:
            print("📂 Step 1: Loading CSV files...")
        self._load_csv_files(verbose)
        if verbose:
            print(f"   ✅ Loaded {len(self.positions)} positions\n")
        
        # Step 2: Load reference prices
        if verbose:
            print("📋 Step 2: Loading reference prices...")
        self._load_reference_prices(verbose)
        if verbose:
            print(f"   ✅ Loaded {len(self.reference_prices)} reference prices\n")
        
        if not self.positions or not self.reference_prices:
            if verbose:
                print("⚠️  Skipping reconciliation - no data loaded")
            return {"status": "no_data"}
        
        # Step 3: Reconcile
        if verbose:
            print("🔄 Step 3: Reconciling positions...")
        self._reconcile(verbose)
        if verbose:
            print(f"   ✅ Reconciled {len(self.reconciliation_results)} positions\n")
        
        # Step 4: Calculate analytics
        if verbose:
            print("📊 Step 4: Calculating analytics...")
        self._calculate_analytics(verbose)
        if verbose:
            print(f"   ✅ Calculated {len(self.monthly_returns)} monthly returns\n")
        
        # Step 5: Generate reports
        if verbose:
            print("📄 Step 5: Generating reports...")
        self._generate_reports(verbose)
        if verbose:
            print("   ✅ Reports generated\n")
        
        # Summary
        summary = self._get_summary()
        if verbose:
            self._print_summary(summary)
        
        return summary
    
    def _load_csv_files(self, verbose: bool = False) -> None:
        """Load CSV files from data/Send_data directory"""
        
        csv_dir = self.data_dir / "Send_data"
        
        if not csv_dir.exists():
            if verbose:
                print(f"   ⚠️  Directory not found: {csv_dir}")
            return
        
        csv_files = list(csv_dir.glob("*.csv"))
        
        if verbose:
            print(f"   Found {len(csv_files)} CSV files")
        
        for csv_file in csv_files:
            try:
                if verbose:
                    print(f"   Processing: {csv_file.name}")
                
                parsed_funds = self.csv_processor.process_file(csv_file)
                
                for pf in parsed_funds:
                    position = Position(
                        fund_id=pf.fund_id,
                        date=pf.date,
                        price=pf.price,
                        quantity=pf.quantity,
                        value=pf.value
                    )
                    self.positions.append(position)
                
                if verbose:
                    print(f"     → {len(parsed_funds)} positions loaded")
                
            except Exception as e:
                if verbose:
                    print(f"     ❌ Error: {e}")
    
    def _load_reference_prices(self, verbose: bool = False) -> None:
        """Load reference prices from data/reference_prices.sql"""
        
        ref_file = self.data_dir / "reference_prices.sql"
        
        if not ref_file.exists():
            if verbose:
                print(f"   ⚠️  Reference file not found: {ref_file}")
            return
        
        try:
            with open(ref_file, 'r') as f:
                content = f.read()
            
            # Parse SQL INSERT statements
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line.startswith("INSERT"):
                    continue
                
                # Extract VALUES from INSERT statement
                # Format: INSERT INTO reference_prices (fund_id, price_date, price) VALUES ('FUND_A', '2024-01-31', 100.50);
                
                try:
                    # Simple extraction
                    if "VALUES" not in line:
                        continue
                    
                    values_part = line.split("VALUES")[1].strip()
                    # Remove trailing semicolon and parentheses
                    values_part = values_part.rstrip(';').strip()
                    values_part = values_part.strip("()")
                    
                    # Parse quoted values
                    parts = []
                    current = ""
                    in_quotes = False
                    
                    for char in values_part:
                        if char == "'":
                            in_quotes = not in_quotes
                        elif char == "," and not in_quotes:
                            parts.append(current.strip())
                            current = ""
                            continue
                        current += char
                    
                    if current:
                        parts.append(current.strip())
                    
                    if len(parts) >= 3:
                        fund_id = parts[0].strip("'")
                        price_date_str = parts[1].strip("'")
                        price_str = parts[2].strip("'")
                        
                        try:
                            price_date = datetime.fromisoformat(price_date_str)
                            price = Decimal(price_str)
                            
                            ref = PricePoint(
                                fund_id=fund_id,
                                date=price_date,
                                price=price,
                                source="reference"
                            )
                            self.reference_prices.append(ref)
                        except:
                            pass
                
                except:
                    pass
            
            if verbose and self.reference_prices:
                print(f"   Loaded {len(self.reference_prices)} reference prices from SQL")
        
        except Exception as e:
            if verbose:
                print(f"   ❌ Error loading reference prices: {e}")
    
    def _reconcile(self, verbose: bool = False) -> None:
        """Perform price reconciliation"""
        
        self.reconciliation_results = self.reconciliation_engine.reconcile_positions(
            self.positions,
            self.reference_prices
        )
        
        if verbose:
            # Show summary stats
            exact = sum(1 for r in self.reconciliation_results if r.status == "EXACT_MATCH")
            variance = sum(1 for r in self.reconciliation_results if "VARIANCE" in r.status)
            no_ref = sum(1 for r in self.reconciliation_results if r.status == "NO_REFERENCE_DATA")
            
            print(f"   Exact matches: {exact}")
            print(f"   Variance matches: {variance}")
            print(f"   No reference data: {no_ref}")
    
    def _calculate_analytics(self, verbose: bool = False) -> None:
        """Calculate analytics and monthly returns"""
        
        # Group positions by fund
        fund_prices: Dict[str, tuple] = {}
        
        for position in self.positions:
            if position.fund_id not in fund_prices:
                fund_prices[position.fund_id] = ("Fund_" + position.fund_id, [])
            
            snapshot = PriceSnapshot(
                fund_id=position.fund_id,
                date=position.date,
                price=position.price
            )
            fund_prices[position.fund_id][1].append(snapshot)
        
        # Calculate returns
        self.monthly_returns = self.analytics_engine.calculate_all_returns(fund_prices)
        
        if verbose:
            best_performers = sum(1 for r in self.monthly_returns if r.is_best_performer)
            print(f"   Total monthly returns: {len(self.monthly_returns)}")
            print(f"   Best performers identified: {best_performers}")
    
    def _generate_reports(self, verbose: bool = False) -> None:
        """Generate output reports"""
        
        # Reconciliation report
        self._generate_reconciliation_report()
        
        # Best performers report
        self._generate_best_performers_report()
        
        # Summary JSON
        self._generate_summary_json()
    
    def _generate_reconciliation_report(self) -> None:
        """Generate reconciliation report CSV"""
        
        output_file = self.output_dir / "reconciliation_report.json"
        
        data = []
        for result in self.reconciliation_results:
            data.append({
                "fund_id": result.fund_id,
                "position_date": result.position_date.isoformat(),
                "position_price": str(result.position_price),
                "reference_price": str(result.reference_price) if result.reference_price else None,
                "variance_pct": result.variance_pct,
                "status": result.status,
                "is_flagged": result.is_flagged
            })
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _generate_best_performers_report(self) -> None:
        """Generate best performers report JSON"""
        
        output_file = self.output_dir / "best_performers_report.json"
        
        best = [r for r in self.monthly_returns if r.is_best_performer]
        
        data = []
        for perf in best:
            data.append({
                "year": perf.year,
                "month": perf.month,
                "fund_id": perf.fund_id,
                "fund_name": perf.fund_name,
                "monthly_return_pct": perf.monthly_return_pct,
                "opening_price": str(perf.opening_price),
                "closing_price": str(perf.closing_price)
            })
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _generate_summary_json(self) -> None:
        """Generate overall summary JSON"""
        
        summary = self._get_summary()
        output_file = self.output_dir / "summary.json"
        
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
    
    def _get_summary(self) -> Dict[str, any]:
        """Get execution summary"""
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "data_loaded": {
                "positions": len(self.positions),
                "reference_prices": len(self.reference_prices)
            },
            "reconciliation": {
                "total": len(self.reconciliation_results),
                "exact_matches": sum(1 for r in self.reconciliation_results if r.status == "EXACT_MATCH"),
                "variance_matches": sum(1 for r in self.reconciliation_results if "VARIANCE" in r.status),
                "no_reference": sum(1 for r in self.reconciliation_results if r.status == "NO_REFERENCE_DATA"),
                "flagged": sum(1 for r in self.reconciliation_results if r.is_flagged)
            },
            "analytics": {
                "monthly_returns": len(self.monthly_returns),
                "best_performers": sum(1 for r in self.monthly_returns if r.is_best_performer)
            },
            "output_dir": str(self.output_dir)
        }
    
    def _print_summary(self, summary: Dict[str, any]) -> None:
        """Print summary to console"""
        
        print("=" * 60)
        print("RECONCILIATION SUMMARY")
        print("=" * 60)
        
        if "data_loaded" in summary:
            print(f"\n📂 Data Loaded:")
            print(f"   Positions: {summary['data_loaded']['positions']}")
            print(f"   Reference Prices: {summary['data_loaded']['reference_prices']}")
        
        if "reconciliation" in summary:
            recon = summary['reconciliation']
            print(f"\n🔄 Reconciliation Results:")
            print(f"   Total: {recon['total']}")
            print(f"   Exact Matches: {recon['exact_matches']}")
            print(f"   Variance Matches: {recon['variance_matches']}")
            print(f"   No Reference Data: {recon['no_reference']}")
            print(f"   Flagged: {recon['flagged']}")
        
        if "analytics" in summary:
            analytics = summary['analytics']
            print(f"\n📊 Analytics:")
            print(f"   Monthly Returns: {analytics['monthly_returns']}")
            print(f"   Best Performers: {analytics['best_performers']}")
        
        print(f"\n📄 Output Directory: {summary.get('output_dir', 'N/A')}")
        print("\n✅ Workflow completed successfully!")
        print("=" * 60)
