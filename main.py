#!/usr/bin/env python3
"""
Enterprise Fund Reconciliation v2.0
Main entry point - Choose between CLI (E2E) or API mode
"""

import argparse
import asyncio
from pathlib import Path

from src.cli import CLIRunner


def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(
        description="Fund Reconciliation System v2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run E2E without API (default)
  python main.py
  
  # Run E2E with verbose output
  python main.py -v
  
  # Run REST API server
  python main.py --api
  
  # Run API with custom port
  python main.py --api --port 9000
"""
    )
    
    parser.add_argument(
        '--mode',
        choices=['e2e', 'api'],
        default='e2e',
        help='Run mode: e2e (default) or api'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    parser.add_argument(
        '--data-dir',
        type=Path,
        default=Path('data'),
        help='Data directory (default: data)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('output'),
        help='Output directory (default: output)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='API port (default: 8000)'
    )
    
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='API host (default: 0.0.0.0)'
    )
    
    args = parser.parse_args()
    
    if args.mode == 'e2e':
        run_e2e(args)
    else:
        run_api(args)


def run_e2e(args):
    """Run E2E workflow without API"""
    
    print(f"""
╔════════════════════════════════════════════════════════════════╗
║   Enterprise Fund Reconciliation v2.0 - E2E Mode              ║
║   (No API - Direct Testing of Core Logic)                     ║
╚════════════════════════════════════════════════════════════════╝
""")
    
    # Create and run CLI runner
    runner = CLIRunner(
        data_dir=args.data_dir,
        output_dir=args.output_dir
    )
    
    summary = runner.run_full_workflow(verbose=args.verbose)
    
    print(f"\n✅ E2E Workflow completed!")
    print(f"📄 Reports saved to: {args.output_dir}/")
    
    return summary


def run_api(args):
    """Run REST API server"""
    
    print(f"""
╔════════════════════════════════════════════════════════════════╗
║   Enterprise Fund Reconciliation v2.0 - API Mode              ║
║   FastAPI REST Server with Swagger Documentation             ║
╚════════════════════════════════════════════════════════════════╝
""")
    
    try:
        import uvicorn
        from src.api import app
        
        print(f"🚀 Starting API server...")
        print(f"📍 Server: http://{args.host}:{args.port}")
        print(f"📚 Docs: http://{args.host}:{args.port}/docs")
        print(f"❤️  Health: http://{args.host}:{args.port}/api/v1/health")
        print("\nPress Ctrl+C to stop server\n")
        
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            reload=True,
            log_level="info"
        )
    
    except ImportError:
        print("❌ Error: FastAPI/Uvicorn not installed")
        print("   Install with: pip install fastapi uvicorn")
        exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
