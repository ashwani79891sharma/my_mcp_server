"""
mcp_report.py - monitor your MCP server from its audit log (mcp_audit.jsonl).

    python mcp_report.py                    summary of all calls
    python mcp_report.py --minutes 60       only the last 60 minutes
    python mcp_report.py --watch            live view, refreshes every 5 seconds (Ctrl+C to stop)

Run it from the folder that contains mcp_audit.jsonl (your server folder).
"""
import argparse
import json
import os
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone

AUDIT_FILE = "mcp_audit.jsonl"
ALERT_DENIED = 3        # warn when a tool has at least this many denied calls
ALERT_P95_MS = 2000     # warn when the slowest 5% of calls take longer than this


def load(minutes=None):
    if not os.path.exists(AUDIT_FILE):
        return []
    rows = []
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes) if minutes else None
    with open(AUDIT_FILE, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
                r["_t"] = datetime.fromisoformat(r["ts"])
            except Exception:
                continue                       # skip any damaged line
            if cutoff is None or r["_t"] >= cutoff:
                rows.append(r)
    return rows


def build_report(rows):
    if not rows:
        return "No tool calls recorded yet.\n(Is @monitored under @mcp.tool(), and have you used a tool since restarting?)"
    by_tool = defaultdict(list)
    for r in rows:
        by_tool[r["tool"]].append(r)

    out = [f"{len(rows)} calls | first {rows[0]['ts']} | last {rows[-1]['ts']}", "",
           f"{'tool':24}{'calls':>6}{'errors':>8}{'denied':>8}{'avg ms':>8}{'p95 ms':>8}"]
    alerts = []
    for tool, rs in sorted(by_tool.items()):
        ms = sorted(r["ms"] for r in rs)
        p95 = ms[min(len(ms) - 1, int(len(ms) * 0.95))]
        errors = sum(r["status"] == "error" for r in rs)
        denied = sum(r["status"] == "denied" for r in rs)
        out.append(f"{tool:24}{len(rs):>6}{errors:>8}{denied:>8}{sum(ms) / len(ms):>8.0f}{p95:>8.0f}")
        if errors:
            alerts.append(f"{tool}: {errors} failed call(s). Check the server terminal for the error.")
        if denied >= ALERT_DENIED:
            alerts.append(f"{tool}: {denied} denied calls. Something keeps asking for what it should not have.")
        if p95 > ALERT_P95_MS:
            alerts.append(f"{tool}: slow (p95 {p95:.0f} ms).")

    recent = [r for r in rows if r["status"] != "ok"][-5:]
    if recent:
        out += ["", "Latest problems:"] + [f"  {r['ts']}  {r['tool']}  {r['status']}  {r['args']}" for r in recent]
    out += ["", "ALERTS:" if alerts else "No alerts."] + [f"  ! {a}" for a in alerts]
    return "\n".join(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=int, help="only include the last N minutes")
    ap.add_argument("--watch", action="store_true", help="refresh every 5 seconds")
    a = ap.parse_args()
    if a.watch:
        try:
            while True:
                os.system("cls" if os.name == "nt" else "clear")
                print(f"MCP monitor - {datetime.now():%H:%M:%S} (Ctrl+C to stop)\n")
                print(build_report(load(a.minutes)))
                time.sleep(5)
        except KeyboardInterrupt:
            pass
    else:
        print(build_report(load(a.minutes)))
