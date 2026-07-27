#!/usr/bin/env python3
"""
Code Quality Audit for Refactoring Priorities
Run: python test.py
"""

import subprocess
import json
from pathlib import Path


def run_radon(cmd):
    """Run radon command and return parsed json output"""
    try:
        # radon supports json output for many commands, which is safer
        import shlex
        result = subprocess.run(  # noqa: S603
            shlex.split(cmd + " --json"), capture_output=True, text=True
        )
        return json.loads(result.stdout)
    except Exception:
        return None


def analyze_complexity():
    """Get all files with complexity issues"""
    print("\n" + "=" * 60)
    print("🔍 1. COMPLEXITY ANALYSIS (High Complexity = Refactor)")
    print("=" * 60)

    data = run_radon("radon cc . -s -e 'tests/*'")
    if not data:
        print("Could not run complexity analysis.")
        return

    high_complexity = []
    for file_path, items in data.items():
        for item in items:
            if item.get("rank") in ["B", "C", "D", "E", "F"]:
                high_complexity.append((file_path, item["name"], item["rank"]))

    if high_complexity:
        print(f"⚠️  Found {len(high_complexity)} high-complexity items:")
        for path, name, rank in high_complexity[:10]:
            print(f"  {path}:{name} - {rank}")
    else:
        print("✅ No high-complexity files found in production code!")


def analyze_maintainability():
    """Get all files with low maintainability"""
    print("\n" + "=" * 60)
    print("🔧 2. MAINTAINABILITY INDEX (Low Score = Refactor)")
    print("=" * 60)

    data = run_radon("radon mi . -s -e 'tests/*'")
    if not data:
        print("Could not run maintainability analysis.")
        return

    critical = []
    needs_work = []
    total_score = 0
    count = 0

    for file_path, info in data.items():
        score = info.get("mi", 0)
        total_score += score
        count += 1
        if score < 50:
            critical.append((file_path, score))
        elif score < 65:
            needs_work.append((file_path, score))

    print("\n🚨 CRITICAL (< 50): Must refactor NOW")
    for path, score in critical:
        print(f"  🔴 {path} ({score:.2f})")

    print("\n⚠️  NEEDS WORK (50-65): Should refactor")
    for path, score in needs_work:
        print(f"  🟡 {path} ({score:.2f})")

    if count > 0:
        print(f"\n📊 Overall Maintainability: {total_score / count:.2f}")


def analyze_file_sizes():
    """Find files that are too large"""
    print("\n" + "=" * 60)
    print("📏 3. FILE SIZE ANALYSIS (Large Files = Split)")
    print("=" * 60)

    python_files = Path(".").rglob("*.py")
    large_files = []

    for f in python_files:
        if "tests" in str(f) or "__pycache__" in str(f) or ".venv" in str(f):
            continue
        try:
            lines = len(f.read_text().splitlines())
            if lines > 300:
                large_files.append((str(f), lines))
        except Exception as e:
            # TODO: Log this properly
            print(f"Error checking file {f}: {e}")
            pass

    if large_files:
        large_files.sort(key=lambda x: x[1], reverse=True)
        print("⚠️  Files > 300 lines (consider splitting):")
        for file, lines in large_files[:10]:
            print(f"  {file} - {lines} lines")
    else:
        print("✅ All files under 300 lines!")


def analyze_test_coverage():
    """Check test coverage (optional)"""
    print("\n" + "=" * 60)
    print("🧪 5. TEST COVERAGE SUGGESTION")
    print("=" * 60)

    test_files = list(Path(".").glob("tests/test_*.py"))
    source_files = list(Path(".").rglob("*.py"))
    source_files = [
        f
        for f in source_files
        if "tests" not in str(f)
        and "__pycache__" not in str(f)
        and ".venv" not in str(f)
    ]

    print(f"📁 Source files: {len(source_files)}")
    print(f"📁 Test files: {len(test_files)}")

    # List untested modules
    source_names = {
        f.stem for f in source_files if f.stem not in ["__init__", "setup", "conftest"]
    }
    test_names = {f.stem.replace("test_", "") for f in test_files}
    untested = source_names - test_names

    if untested:
        print("\n⚠️  Modules without dedicated tests:")
        for name in sorted(untested)[:10]:
            print(f"  - {name}.py")


if __name__ == "__main__":
    print("\n🚀 STARTING COMPREHENSIVE REFACTORING AUDIT")
    print("Analyzing your codebase...\n")

    analyze_complexity()
    analyze_maintainability()
    analyze_file_sizes()
    analyze_test_coverage()
