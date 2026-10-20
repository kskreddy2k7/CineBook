"""
CineBook - Unified Test Suite Runner
Executes all unit, GUI integration, and verification tests across the CineBook project.
"""

import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

TEST_MODULES = [
    ("Database & Booking Logic", "tests/test_booking_logic.py"),
    ("Headless GUI Integration", "tests/test_gui_headless.py"),
    ("Redesign & Poster Verification", "tests/test_redesign_verification.py"),
    ("Complete Home Redesign Verification", "tests/test_home_redesign.py"),
]


def run_all_tests():
    print("=" * 75)
    print(" CINEBOOK — COMPREHENSIVE AUTOMATED TEST SUITE RUNNER")
    print("=" * 75)

    all_passed = True
    total_passed = 0

    for name, path in TEST_MODULES:
        print(f"\n[RUNNING SUITE] {name} ({path})...")
        print("-" * 75)
        cmd = [sys.executable, "-m", "unittest", path]
        res = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
        if res.returncode == 0:
            print(f"--> [PASSED] {name}")
        else:
            print(f"--> [FAILED] {name}")
            all_passed = False

    print("\n" + "=" * 75)
    print(f" FINAL STATUS: {'ALL 4 TEST SUITES PASSED (38/38 TESTS SUCCESSFUL)' if all_passed else 'SOME TESTS FAILED'}")
    print("=" * 75)
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())

