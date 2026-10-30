"""Build, analyze, render, and test the portfolio from committed raw extracts."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from floodfolio.pipeline import main as build


if __name__ == "__main__":
    build()
    from floodfolio.analysis import main as analyze
    from floodfolio.reporting import main as report
    analyze()
    report()
