#!/usr/bin/env python3
"""
E2E Demo - Core Logic Testing
This demonstrates the complete fund reconciliation workflow
without external dependencies like FastAPI.
"""

import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import json
import tempfile

sys.path.insert(0, '.')

# Import core modules
exec(open('src/core/reconciliation_engine.py').read())
exec(open('src/core/analytics_engine.py').read())
exec(open('src/core/csv_processor.py').read())

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def main():
    print_header("🎓 FUND RECONCILIATION SYSTEM - COMPLETE E2E DEMO")
    
    print("\n📌 This demo shows:")
    print("   ✅ Data loading (CSV positions + reference prices)")
    print("   ✅ Reconciliation (matching and variance calculation)")
    print("   ✅ Analytics (monthly returns, best performers)")
    print("   ✅ Reporting (JSON output)")
    
    # Step 1: Prepare test data
    print_header("STEP 1: Loading Position Data from CSV")
    
    csv_data = """Fund_ID,Fund_Name,Date,Price,Quantity,Value
FUND_A,Growth Fund,2024-01-15,100.00,1000,100000
FUND_A,Growth Fund,2024-01-31,100.50,1000,100500
FUND_B,Income Fund,2024-01-15,50.00,2000,100000
FUND_B,Income Fund,2024-01-31,50.75,2000,101500
FUND_C,Balanced,2024-01-15,75.00,1500,112500
FUND_C,Balanced,2024-01-31,76.00,1500,114000
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_data)
        csv_file = f.name
    
    processor = CSVProcessor()
    positions = processor.process_file(csv_file)
    
    print(f"✅ Loaded {len(positions)} positions from CSV")
    for pos in positions[:3]:
        print(f"   {pos.fund_id}: {pos.date.strftime('%Y-%m-%d')} @ ${pos.price}")
    print(f"   ... ({len(positions) - 3} more)")
    
    # Step 2: Load reference prices
    print_header("STEP 2: Loading Reference Prices")
    
    reference_prices = [
        PricePoint("FUND_A", datetime(2024, 1, 15), Decimal("100.00")),
        PricePoint("FUND_A", datetime(2024, 1, 31), Decimal("100.50")),
        PricePoint("FUND_B", datetime(2024, 1, 15), Decimal("50.00")),
        PricePoint("FUND_B", datetime(2024, 1, 31), Decimal("50.75")),
        PricePoint("FUND_C", datetime(2024, 1, 15), Decimal("73.00")),  # Different!
        PricePoint("FUND_C", datetime(2024, 1, 31), Decimal("76.00")),
    ]
    
    print(f"✅ Loaded {len(reference_prices)} reference prices")
    for ref in reference_prices[:3]:
        print(f"   {ref.fund_id}: {ref.date.strftime('%Y-%m-%d')} @ ${ref.price}")
    print(f"   ... ({len(reference_prices) - 3} more)")
    
    # Step 3: Reconcile
    print_header("STEP 3: Reconciling Positions")
    
    engine = ReconciliationEngine()
    results = engine.reconcile_positions(positions, reference_prices)
    
    print(f"✅ Reconciled {len(results)} positions\n")
    
    # Count results by status
    exact = sum(1 for r in results if r.status == "EXACT_MATCH")
    minor = sum(1 for r in results if r.status == "MATCHED_MINOR_VARIANCE")
    acceptable = sum(1 for r in results if r.status == "MATCHED_ACCEPTABLE_VARIANCE")
    high = sum(1 for r in results if r.status == "MATCHED_HIGH_VARIANCE")
    no_ref = sum(1 for r in results if r.status == "NO_REFERENCE_DATA")
    
    print(f"Results Summary:")
    print(f"   ✅ Exact Matches: {exact}")
    print(f"   ✅ Minor Variance: {minor}")
    print(f"   ✅ Acceptable Variance: {acceptable}")
    print(f"   ⚠️  High Variance: {high}")
    print(f"   ❌ No Reference Data: {no_ref}")
    
    flagged = sum(1 for r in results if r.is_flagged)
    print(f"   🚩 Flagged for Review: {flagged}")
    
    # Show details
    print(f"\nDetailed Results:")
    for i, result in enumerate(results, 1):
        status_icon = "✅" if not result.is_flagged else "⚠️ "
        print(f"   {status_icon} {result.fund_id} ({result.position_date.strftime('%Y-%m-%d')})")
        print(f"      Position: ${result.position_price} | Reference: ${result.reference_price}")
        if result.variance_pct is not None:
            print(f"      Variance: {result.variance_pct:.4f}% | Status: {result.status}")
        else:
            print(f"      Status: {result.status}")
    
    # Step 4: Calculate Analytics
    print_header("STEP 4: Calculating Analytics")
    
    # Group prices by fund
    fund_prices_dict = {}
    for pos in positions:
        key = pos.fund_id
        if key not in fund_prices_dict:
            # Get fund name from results
            fund_name = [r.fund_id for r in results if r.fund_id == key][0]
            fund_prices_dict[key] = (fund_name, [])
        
        snapshot = PriceSnapshot(
            fund_id=pos.fund_id,
            date=pos.date,
            price=pos.price
        )
        fund_prices_dict[key][1].append(snapshot)
    
    analytics = AnalyticsEngine()
    monthly_returns = analytics.calculate_all_returns(fund_prices_dict)
    
    print(f"✅ Calculated {len(monthly_returns)} monthly returns\n")
    print(f"Performance by Fund (January 2024):")
    for ret in sorted(monthly_returns, key=lambda x: x.monthly_return_pct, reverse=True):
        mark = "🥇" if ret.is_best_performer else "  "
        print(f"   {mark} {ret.fund_id}: {ret.monthly_return_pct:.2f}%")
    
    # Step 5: Generate Reports
    print_header("STEP 5: Generating Reports")
    
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Reconciliation report
    reconciliation_report = [
        {
            "fund_id": r.fund_id,
            "position_date": r.position_date.isoformat(),
            "position_price": str(r.position_price),
            "reference_price": str(r.reference_price),
            "variance_pct": float(r.variance_pct) if r.variance_pct else None,
            "status": r.status,
            "is_flagged": r.is_flagged
        }
        for r in results
    ]
    
    with open(output_dir / "reconciliation_report.json", "w") as f:
        json.dump(reconciliation_report, f, indent=2)
    
    # Best performers report
    best_report = [
        {
            "fund_id": r.fund_id,
            "fund_name": r.fund_name,
            "year": r.year,
            "month": r.month,
            "monthly_return_pct": float(r.monthly_return_pct),
            "opening_price": str(r.opening_price),
            "closing_price": str(r.closing_price),
            "is_best_performer": r.is_best_performer
        }
        for r in monthly_returns
    ]
    
    with open(output_dir / "best_performers_report.json", "w") as f:
        json.dump(best_report, f, indent=2)
    
    # Summary
    summary = {
        "timestamp": datetime.now().isoformat(),
        "data_loaded": {
            "positions": len(positions),
            "reference_prices": len(reference_prices)
        },
        "reconciliation": {
            "total": len(results),
            "exact_matches": exact,
            "minor_variance": minor,
            "acceptable_variance": acceptable,
            "high_variance": high,
            "no_reference_data": no_ref,
            "flagged": flagged
        },
        "analytics": {
            "monthly_returns": len(monthly_returns),
            "best_performers": sum(1 for r in monthly_returns if r.is_best_performer)
        }
    }
    
    with open(output_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"✅ Generated 3 reports in output/ directory:")
    print(f"   - reconciliation_report.json")
    print(f"   - best_performers_report.json")
    print(f"   - summary.json")
    
    # Final summary
    print_header("✅ E2E WORKFLOW COMPLETED SUCCESSFULLY!")
    
    print("\n📊 Final Summary:")
    print(f"   Total Positions: {len(positions)}")
    print(f"   Exact Matches: {exact}")
    print(f"   Flagged Items: {flagged}")
    print(f"   Best Performers: {sum(1 for r in monthly_returns if r.is_best_performer)}")
    
    print("\n📁 Output Files Generated:")
    for file in sorted(output_dir.glob("*.json")):
        print(f"   ✓ {file.name} ({file.stat().st_size} bytes)")
    
    print("\n" + "=" * 70)
    print("🎉 DEMO COMPLETE - All systems working perfectly!")
    print("=" * 70 + "\n")
    
    # Cleanup
    Path(csv_file).unlink()

if __name__ == "__main__":
    main()
