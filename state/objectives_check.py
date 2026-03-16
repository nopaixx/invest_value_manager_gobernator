#!/usr/bin/env python3
"""
Objectives checker — verifies measurable objectives from git data and files.
Outputs a CUMPLE/NO CUMPLE table.

Usage: python3 state/objectives_check.py
"""

import os
import sys
import json
import re
import subprocess
import glob as globmod
from datetime import datetime, timedelta
from pathlib import Path

# --- Config ---
SPECIALIST_REPO = "/home/angel/value_invest2"
GOBERNATOR_REPO = "/home/angel/invest_value_manager_gobernator"
PORTFOLIO_FILE = f"{SPECIALIST_REPO}/portfolio/current.yaml"
THESIS_ACTIVE = f"{SPECIALIST_REPO}/thesis/active"
THESIS_PIPELINE = f"{SPECIALIST_REPO}/thesis/research"
STRESS_TEST_DIR = f"{SPECIALIST_REPO}/reports/stress_test"
SMART_MONEY_DIR = f"{SPECIALIST_REPO}/reports/smart_money"
SECTOR_VIEWS_DIR = f"{SPECIALIST_REPO}/world/sectors"
TWEETS_DIR = f"{GOBERNATOR_REPO}/reports/tweets"
DAILY_REPORTS_DIR = f"{GOBERNATOR_REPO}/reports/daily"
CALENDAR_FILE = f"{GOBERNATOR_REPO}/state/calendar.jsonl"

TODAY = datetime.now().date()
YESTERDAY = TODAY - timedelta(days=1)
WEEK_START = TODAY - timedelta(days=TODAY.weekday())  # Monday


def use_colors():
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


COLORS = use_colors()
GREEN = "\033[92m" if COLORS else ""
RED = "\033[91m" if COLORS else ""
BOLD = "\033[1m" if COLORS else ""
RESET = "\033[0m" if COLORS else ""
DIM = "\033[2m" if COLORS else ""


def git_log_count(repo, since, patterns, until=None):
    """Count commits matching any of the patterns since a date."""
    cmd = ["git", "-C", repo, "log", "--oneline", f"--since={since}"]
    if until:
        cmd.append(f"--until={until}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        lines = [l for l in result.stdout.strip().split("\n") if l]
    except Exception as e:
        print(f"  WARN: git_log_count failed: {e}")
        return -1  # -1 signals error, not "zero results"
    count = 0
    for line in lines:
        lower = line.lower()
        if any(p.lower() in lower for p in patterns):
            count += 1
    return count


def git_log_new_dirs(repo, since, base_path):
    """Count new directories created under base_path via git log."""
    cmd = ["git", "-C", repo, "log", "--oneline", "--diff-filter=A",
           "--name-only", f"--since={since}", "--", base_path]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        dirs = set()
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if "/" in line and not line.startswith(" ") and len(line) > 5:
                # Extract first dir component under base_path
                rel = line.replace(base_path.lstrip("/"), "").lstrip("/")
                if "/" in rel:
                    dirs.add(rel.split("/")[0])
        return len(dirs)
    except Exception:
        return 0


def parse_yaml_positions(filepath):
    """Simple YAML parser for portfolio positions — extracts ticker, fair_value, last_review."""
    positions = []
    if not os.path.exists(filepath):
        return positions
    with open(filepath, "r") as f:
        lines = f.readlines()

    current = {}
    in_positions = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("positions:"):
            in_positions = True
            continue
        if not in_positions:
            continue
        # New position entry
        if stripped.startswith("- ticker:"):
            if current and "ticker" in current:
                positions.append(current)
            current = {"ticker": stripped.split(":", 1)[1].strip()}
        elif stripped.startswith("ticker:") and not stripped.startswith("- "):
            continue
        elif stripped.startswith("fair_value:") and current:
            current["fair_value"] = stripped.split(":", 1)[1].strip().strip('"\'')
        elif stripped.startswith("last_review:") and current:
            current["last_review"] = stripped.split(":", 1)[1].strip()
        # Comment lines with REMOVED — skip
        elif stripped.startswith("#") and "REMOVED" in stripped:
            if current and "ticker" in current:
                # Check if this is a removal comment for the current position
                pass
    if current and "ticker" in current:
        positions.append(current)
    return positions


def check_screening():
    """>=5 new companies/day: new dirs in thesis/research/ + files modified in research/."""
    # Method 1: new dirs created in thesis/research via git
    new_dirs = git_log_new_dirs(SPECIALIST_REPO, TODAY.isoformat(),
                                "thesis/research")
    # Method 2: count research files modified today via git
    cmd = ["git", "-C", SPECIALIST_REPO, "log", "--name-only", "--oneline",
           f"--since={TODAY.isoformat()}", "--", "thesis/research/*"]
    research_files = 0
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        dirs = set()
        for line in result.stdout.strip().split("\n"):
            if line.strip().startswith("thesis/research/") and "/" in line.strip()[len("thesis/research/"):]:
                dirs.add(line.strip().split("/")[2])
        research_files = len(dirs)
    except Exception:
        pass
    # Method 3: commit keywords as fallback
    commit_count = git_log_count(SPECIALIST_REPO, TODAY.isoformat(),
                                 ["R1 ", "screen", "rapid triage", "fallen angel"])
    commit_count = max(commit_count, 0)
    # Method 4: screening report files in reports/
    screening_reports = 0
    reports_dir = f"{SPECIALIST_REPO}/reports"
    if os.path.isdir(reports_dir):
        for f in os.listdir(reports_dir):
            if "screen" in f.lower() and TODAY.isoformat() in f:
                # Try to count candidates in the report
                fpath = os.path.join(reports_dir, f)
                try:
                    with open(fpath, "r") as fh:
                        content = fh.read()
                    # Count ticker-like patterns (e.g., lines with | that look like table rows)
                    table_rows = [l for l in content.split("\n")
                                  if "|" in l and not l.strip().startswith("---") and not l.strip().startswith("|--")]
                    screening_reports = max(screening_reports, len(table_rows) - 1)  # minus header
                except Exception:
                    screening_reports = max(screening_reports, 1)
    total = max(new_dirs, research_files, commit_count, screening_reports)
    return total, f"{total} found", total >= 25


def check_pipeline():
    """>=50 companies in R1-R4 pipeline."""
    if not os.path.isdir(THESIS_PIPELINE):
        return 0, "pipeline dir not found", False
    dirs = [d for d in os.listdir(THESIS_PIPELINE)
            if os.path.isdir(os.path.join(THESIS_PIPELINE, d)) and not d.startswith(".")]
    count = len(dirs)
    return count, str(count), count >= 50


def check_thesis_freshness():
    """0 positions with last_review >7 days."""
    positions = parse_yaml_positions(PORTFOLIO_FILE)
    if not positions:
        return 0, "no positions found", False
    stale = []
    for pos in positions:
        lr = pos.get("last_review", "")
        if not lr:
            stale.append(pos["ticker"] + " (no date)")
            continue
        try:
            lr_date = datetime.strptime(lr.strip(), "%Y-%m-%d").date()
            if (TODAY - lr_date).days > 7:
                stale.append(f"{pos['ticker']} ({lr})")
        except ValueError:
            stale.append(pos["ticker"] + " (bad date)")
    count = len(stale)
    detail = ", ".join(stale[:5]) if stale else "all fresh"
    return count, f"{count} stale: {detail}" if stale else "0 stale", count == 0


def check_sector_views():
    """0 sectors >3 days without update."""
    if not os.path.isdir(SECTOR_VIEWS_DIR):
        return -1, "sector_views dir not found", False
    stale = []
    threshold = TODAY - timedelta(days=3)
    for f in os.listdir(SECTOR_VIEWS_DIR):
        fpath = os.path.join(SECTOR_VIEWS_DIR, f)
        if os.path.isfile(fpath) and f.endswith(".md") and not f.startswith("_"):
            mtime = datetime.fromtimestamp(os.path.getmtime(fpath)).date()
            if mtime < threshold:
                stale.append(f.replace(".md", ""))
    total_sectors = len([f for f in os.listdir(SECTOR_VIEWS_DIR)
                         if f.endswith(".md") and not f.startswith("_")])
    count = len(stale)
    detail = ", ".join(stale[:5]) if stale else "all fresh"
    if count > 5:
        detail = f"{', '.join(stale[:5])}... +{count - 5} more"
    return count, f"{count}/{total_sectors} stale" + (f": {detail}" if stale else ""), count == 0


def check_stress_test():
    """Run this week: check for JSON file from this week."""
    if not os.path.isdir(STRESS_TEST_DIR):
        return 0, "dir not found", False
    found = 0
    for f in os.listdir(STRESS_TEST_DIR):
        if f.endswith(".json"):
            # Try to parse date from filename
            match = re.search(r"(\d{4}-\d{2}-\d{2})", f)
            if match:
                try:
                    fdate = datetime.strptime(match.group(1), "%Y-%m-%d").date()
                    if fdate >= WEEK_START:
                        found += 1
                except ValueError:
                    pass
    return found, f"{found} this week", found >= 1


def check_smart_money():
    """2 reports/week (legacy, kept for backward compat)."""
    if not os.path.isdir(SMART_MONEY_DIR):
        return 0, "dir not found", False
    found = 0
    for f in os.listdir(SMART_MONEY_DIR):
        match = re.search(r"(\d{4}-\d{2}-\d{2})", f)
        if match:
            try:
                fdate = datetime.strptime(match.group(1), "%Y-%m-%d").date()
                if fdate >= WEEK_START:
                    found += 1
            except ValueError:
                pass
    return found, f"{found} this week", found >= 2


def check_smart_money_daily():
    """>=1 report/day: smart money report today."""
    if not os.path.isdir(SMART_MONEY_DIR):
        return 0, "dir not found", False
    found = 0
    for f in os.listdir(SMART_MONEY_DIR):
        if TODAY.isoformat() in f:
            found += 1
    # Also check reports/ root for smart money files
    reports_dir = f"{SPECIALIST_REPO}/reports"
    if os.path.isdir(reports_dir):
        for f in os.listdir(reports_dir):
            if "smart" in f.lower() and TODAY.isoformat() in f:
                found += 1
    return found, str(found), found >= 1


def check_pipeline_velocity():
    """>=20 pipeline stage advances per week (R1->R2, R2->R3, R3->R4, new R4)."""
    # Count commits this week mentioning stage advances
    advances = git_log_count(SPECIALIST_REPO, WEEK_START.isoformat(),
                              ["R1", "R2", "R3", "R4", "triage", "DA ", "committee",
                               "pipeline", "advancement", "advanced"])
    advances = max(advances, 0)
    # Also count thesis files modified this week (proxy for pipeline work)
    cmd = ["git", "-C", SPECIALIST_REPO, "log", "--name-only", "--oneline",
           f"--since={WEEK_START.isoformat()}", "--", "thesis/research/*/thesis.md"]
    research_modified = 0
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        files = set(l.strip() for l in result.stdout.strip().split("\n")
                    if l.strip().endswith("thesis.md"))
        research_modified = len(files)
    except Exception:
        pass
    total = max(advances, research_modified)
    return total, f"{total} this week", total >= 20


def check_tweets():
    """5 published today: check if today's tweet file exists."""
    today_file = os.path.join(TWEETS_DIR, f"{TODAY.isoformat()}.md")
    exists = os.path.isfile(today_file)
    return 1 if exists else 0, "exists" if exists else "not found", exists


def check_daily_report():
    """Delivered yesterday."""
    yesterday_file = os.path.join(DAILY_REPORTS_DIR, f"{YESTERDAY.isoformat()}.md")
    exists = os.path.isfile(yesterday_file)
    return 1 if exists else 0, "exists" if exists else "not found", exists


def check_contrathesis():
    """>=10/day: contrathesis files modified today OR commits mentioning contrathesis."""
    # Method 1: check git for files with 'contra' in path modified today
    cmd = ["git", "-C", SPECIALIST_REPO, "log", "--oneline", "--name-only",
           f"--since={TODAY.isoformat()}", "--", "*/contra*", "*/contrathes*"]
    files_found = 0
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        files = [l for l in result.stdout.strip().split("\n")
                 if l.strip() and "contra" in l.lower() and not l[0].isalnum() is False]
        files_found = len([f for f in files if "/" in f])
    except Exception:
        pass
    # Method 2: commit messages
    commit_count = git_log_count(SPECIALIST_REPO, TODAY.isoformat(),
                                  ["contrathesis", "contra-thesis", "contratheses"])
    commit_count = max(commit_count, 0)
    # Method 3: check if any thesis file modified today contains contrathesis content
    thesis_contra = 0
    if os.path.isdir(THESIS_ACTIVE):
        for ticker_dir in os.listdir(THESIS_ACTIVE):
            contra_dir = os.path.join(THESIS_ACTIVE, ticker_dir)
            if not os.path.isdir(contra_dir):
                continue
            for fname in os.listdir(contra_dir):
                if "contra" in fname.lower():
                    fpath = os.path.join(contra_dir, fname)
                    mtime = datetime.fromtimestamp(os.path.getmtime(fpath)).date()
                    if mtime >= TODAY:
                        thesis_contra += 1
    total = max(files_found, commit_count, thesis_contra)
    return total, str(total), total >= 10


def check_r4_candidates():
    """>=15 new R4 approvals this week."""
    count = git_log_count(SPECIALIST_REPO, WEEK_START.isoformat(), ["R4"])
    return count, f"{count} this week", count >= 15


def check_kill_conditions():
    """Reviewed today: KC-related file changes OR commits with KC/kill OR kc_sweep report."""
    # Method 1: commit messages
    commit_count = git_log_count(SPECIALIST_REPO, TODAY.isoformat(),
                                  ["KC", "kill condition", "kill_cond", "kc_monitor", "kc sweep"])
    commit_count = max(commit_count, 0)
    # Method 2: check if thesis files with KCs were modified today via git
    cmd = ["git", "-C", SPECIALIST_REPO, "log", "--name-only", "--oneline",
           f"--since={TODAY.isoformat()}", "--", "thesis/active/*/thesis.md"]
    thesis_modified = 0
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        files = set(l.strip() for l in result.stdout.strip().split("\n")
                    if l.strip().endswith("thesis.md"))
        thesis_modified = len(files)
    except Exception:
        pass
    # Method 3: check for kc_sweep report file today
    kc_report = 0
    reports_dir = f"{SPECIALIST_REPO}/reports"
    if os.path.isdir(reports_dir):
        for f in os.listdir(reports_dir):
            if "kc" in f.lower() and TODAY.isoformat() in f:
                kc_report = 1
                break
    # If multiple thesis files were modified in same commit, likely a KC sweep
    total = max(commit_count, 1 if thesis_modified >= 3 else 0, kc_report)
    return total, str(total), total >= 1


def check_fv_consistency():
    """For each position with fair_value in current.yaml, check thesis exists and has matching FV."""
    positions = parse_yaml_positions(PORTFOLIO_FILE)
    if not positions:
        return 0, "no positions", False
    divergences = []
    for pos in positions:
        ticker = pos["ticker"]
        portfolio_fv = pos.get("fair_value", "")
        if not portfolio_fv:
            continue
        # Extract numeric FV from portfolio string (first number after currency symbol or start)
        pf_match = re.search(r"[\$€£]?\s*(\d+(?:\.\d+)?)", portfolio_fv)
        pf_num = pf_match.group(1) if pf_match else None

        thesis_path = os.path.join(THESIS_ACTIVE, ticker, "thesis.md")
        if not os.path.exists(thesis_path):
            divergences.append(f"{ticker} (no thesis)")
            continue

        with open(thesis_path, "r") as f:
            content = f.read(3000)  # Read header only

        # Look for Fair Value line in thesis
        fv_match = re.search(r"\*\*Fair Value:?\*\*\s*(.+)", content)
        if not fv_match:
            divergences.append(f"{ticker} (no FV in thesis)")
            continue

        thesis_fv = fv_match.group(1)
        tf_match = re.search(r"[\$€£]?\s*(\d+(?:\.\d+)?)", thesis_fv)
        tf_num = tf_match.group(1) if tf_match else None

        if pf_num and tf_num and pf_num != tf_num:
            divergences.append(f"{ticker} (yaml:{pf_num} vs thesis:{tf_num})")

    count = len(divergences)
    detail = ", ".join(divergences[:5]) if divergences else "consistent"
    return count, f"{count} divergences" + (f": {detail}" if divergences else ""), count == 0


def check_system_integration():
    """Verify all portfolio tickers are present in specialist tool mappings (SECTOR_MAP, COVID data)."""
    positions = parse_yaml_positions(PORTFOLIO_FILE)
    if not positions:
        return 0, "no positions", False
    tickers = [p["ticker"] for p in positions]

    # Also get short positions
    short_tickers = []
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, "r") as f:
            content = f.read()
        in_shorts = False
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped.startswith("short_positions:"):
                in_shorts = True
                continue
            if in_shorts and stripped.startswith("- ticker:"):
                short_tickers.append(stripped.split(":", 1)[1].strip())
            if in_shorts and stripped.startswith("transactions:"):
                break
    all_tickers = tickers + short_tickers

    missing = []
    # Check stress_test.py SECTOR_MAP
    stress_test_path = f"{SPECIALIST_REPO}/tools/stress_test.py"
    if os.path.exists(stress_test_path):
        with open(stress_test_path, "r") as f:
            st_content = f.read()
        for t in all_tickers:
            if f"'{t}'" not in st_content and f'"{t}"' not in st_content:
                missing.append(f"{t} (not in SECTOR_MAP)")
    else:
        missing.append("stress_test.py not found")

    # Check portfolio_stats.py can handle all tickers (no hardcoded ticker lists)
    # Check fx_defaults.py has needed currencies
    fx_path = f"{SPECIALIST_REPO}/tools/fx_defaults.py"
    if os.path.exists(fx_path):
        with open(fx_path, "r") as f:
            fx_content = f.read()
        needed_fx = set()
        for t in all_tickers:
            if t.endswith(".PA") or t.endswith(".MI") or t.endswith(".DE") or t.endswith(".AS"):
                needed_fx.add("EURUSD")
            elif t.endswith(".L"):
                needed_fx.add("GBPUSD")
            elif t.endswith(".SW"):
                needed_fx.add("CHFUSD")
        for fx in needed_fx:
            if fx not in fx_content:
                missing.append(f"{fx} missing from fx_defaults.py")

    count = len(missing)
    detail = ", ".join(missing[:5]) if missing else "all integrated"
    return count, f"{count} gaps" + (f": {detail}" if missing else "") if count else "all integrated", count == 0


def check_earnings_prep():
    """100% frameworks before earnings: check calendar for upcoming earnings, verify thesis has prep."""
    if not os.path.exists(CALENDAR_FILE):
        return 0, "calendar not found", False

    upcoming_earnings = []
    with open(CALENDAR_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            # Check if it's an upcoming earnings event (within next 14 days)
            edate_str = event.get("date", "")
            status = event.get("status", "")
            event_text = event.get("event", "").lower()
            if "earnings" not in event_text and "fy20" not in event_text and "q" not in event_text[:3]:
                continue
            if status == "done":
                continue
            try:
                edate = datetime.strptime(edate_str, "%Y-%m-%d").date()
                if TODAY <= edate <= TODAY + timedelta(days=14):
                    # Extract ticker from event text
                    ticker_match = re.match(r"(\S+)", event.get("event", ""))
                    if ticker_match:
                        upcoming_earnings.append((ticker_match.group(1), edate_str))
            except ValueError:
                pass

    if not upcoming_earnings:
        return 0, "no upcoming earnings", True  # Nothing to prepare for = pass

    missing = []
    for ticker, edate in upcoming_earnings:
        thesis_path = os.path.join(THESIS_ACTIVE, ticker, "thesis.md")
        if not os.path.exists(thesis_path):
            # Check without exchange suffix
            clean = ticker.split(".")[0]
            found = False
            if os.path.isdir(THESIS_ACTIVE):
                for d in os.listdir(THESIS_ACTIVE):
                    if d.startswith(clean):
                        thesis_path = os.path.join(THESIS_ACTIVE, d, "thesis.md")
                        found = os.path.exists(thesis_path)
                        break
            if not found:
                missing.append(f"{ticker} (no thesis)")
                continue

        with open(thesis_path, "r") as f:
            content = f.read()

        # Look for earnings-related sections
        has_prep = any(kw in content.lower() for kw in [
            "earnings", "pre-earnings", "earnings_framework",
            "earnings framework", "q1", "q2", "q3", "q4",
            "pre-q", "post-earnings"
        ])
        if not has_prep:
            missing.append(f"{ticker} (no earnings section)")

    count = len(missing)
    total = len(upcoming_earnings)
    prepped = total - count
    detail = ", ".join(missing[:3]) if missing else "all prepped"
    return count, f"{prepped}/{total} prepped" + (f", missing: {detail}" if missing else ""), count == 0


def check_file_hygiene():
    """Accountability and state files must stay compact. Max 50 lines each."""
    MAX_LINES = 50
    files_to_check = [
        ("gobernator_accountability", f"{GOBERNATOR_REPO}/state/gobernator_accountability.md"),
        ("specialist_accountability", f"{GOBERNATOR_REPO}/state/specialist_accountability.md"),
        ("push_tracker", f"{GOBERNATOR_REPO}/state/push_tracker.md"),
        ("angel_outbox", f"{GOBERNATOR_REPO}/state/angel_outbox.jsonl"),
    ]
    bloated = []
    for name, path in files_to_check:
        if os.path.exists(path):
            with open(path, "r") as f:
                lines = len(f.readlines())
            if lines > MAX_LINES:
                bloated.append(f"{name} ({lines} lines)")
    count = len(bloated)
    detail = ", ".join(bloated) if bloated else "all compact"
    return count, detail, count == 0


# --- Main ---

def main():
    objectives = [
        # Flow metrics (Phase 1 active)
        ("Screening", ">=25 new/day", check_screening),
        ("Contrathesis", ">=10/day", check_contrathesis),
        ("Smart money", ">=1/day", check_smart_money_daily),
        # Flow metrics (Phase 2 — week 2)
        ("R4 candidates", ">=15/week", check_r4_candidates),
        ("Pipeline velocity", ">=20 adv/week", check_pipeline_velocity),
        # Quality metrics
        ("Pipeline", ">=50 in R1-R4", check_pipeline),
        ("Thesis freshness", "0 stale (>7d)", check_thesis_freshness),
        ("Sector views", "0 stale (>3d)", check_sector_views),
        ("Stress test", ">=1 this week", check_stress_test),
        ("Kill conditions", "reviewed today", check_kill_conditions),
        ("FV consistency", "0 divergences", check_fv_consistency),
        ("System integration", "0 gaps", check_system_integration),
        ("File hygiene", "all <50 lines", check_file_hygiene),
        ("Earnings prep", "100% prepped", check_earnings_prep),
        # Growth metrics
        ("Tweets", "published today", check_tweets),
        ("Daily report", "yesterday done", check_daily_report),
    ]

    results = []
    for name, target, checker in objectives:
        try:
            _val, actual, passed = checker()
        except Exception as e:
            actual = f"ERROR: {e}"
            passed = False
        results.append((name, target, actual, passed))

    # Print table
    col_w = [20, 16, 50, 12]
    header = f"{'Objective':<{col_w[0]}} {'Target':<{col_w[1]}} {'Actual':<{col_w[2]}} {'Result':<{col_w[3]}}"
    separator = "-" * sum(col_w)

    print(f"\n{BOLD}Objectives Check — {TODAY.isoformat()}{RESET}\n")
    print(f"{BOLD}{header}{RESET}")
    print(separator)

    passed_count = 0
    for name, target, actual, passed in results:
        status = f"{GREEN}CUMPLE{RESET}" if passed else f"{RED}NO CUMPLE{RESET}"
        if passed:
            passed_count += 1
        # Truncate actual if too long
        if len(actual) > col_w[2]:
            actual = actual[:col_w[2] - 3] + "..."
        print(f"{name:<{col_w[0]}} {target:<{col_w[1]}} {actual:<{col_w[2]}} {status}")

    print(separator)
    total = len(results)
    pct = int(passed_count / total * 100) if total else 0
    color = GREEN if passed_count == total else RED
    print(f"\n{BOLD}Summary: {color}{passed_count}/{total} objectives met ({pct}%){RESET}\n")

    return 0 if passed_count == total else 1


if __name__ == "__main__":
    sys.exit(main())
