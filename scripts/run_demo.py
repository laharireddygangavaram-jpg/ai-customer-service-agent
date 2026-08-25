#!/usr/bin/env python3
"""
Demo script for the AI Customer Service Agent.
"""
import os
import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Add examples to path
sys.path.insert(0, str(Path(__file__).parent.parent / "examples"))

from customer_service_agent import CustomerServiceAgent, setup_logging
from basic_usage import main as basic_demo
from workflow_demo import main as workflow_demo
from performance_report import main as performance_demo

def main():
    """Run the demo based on command line arguments."""
    parser = argparse.ArgumentParser(description="AI Customer Service Agent Demo")
    parser.add_argument(
        "--demo-type",
        choices=["basic", "workflow", "performance", "all"],
        default="basic",
        help="Type of demo to run",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level",
    )
    parser.add_argument("--log-file", help="Log file path")

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level, args.log_file)

    print("🚀 AI Customer Service Agent Demo")
    print("=" * 60)

    demos = {
        "basic": basic_demo,
        "workflow": workflow_demo,
        "performance": performance_demo,
    }

    if args.demo_type == "all":
        for name, demo_func in demos.items():
            print(f"\n🎬 Running {name} demo...")
            print("=" * 60)
            demo_func()
    else:
        demos[args.demo_type]()

    print("\n✅ Demo completed successfully!")


if __name__ == "__main__":
    main()
