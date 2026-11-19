"""
monitoring.py - drop-in monitoring for your MCP server tools.

Usage in server.py / server_v2.py:
    from monitoring import monitored, stats_snapshot

    @mcp.tool()
    @monitored            # <- goes directly under @mcp.tool()
    def current_time() -> str: ...

    @mcp.tool()
    def server_stats() -> str:
        \"\"\"Call counts, errors and average latency since the server started.\"\"\"
        return stats_snapshot()

Every call is appended to mcp_audit.jsonl. Summarise it any time with:
    python monitoring.py report
"""
import functools
import inspect
import json
import logging
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone

AUDIT_FILE = "mcp_audit.jsonl"
SECRET_WORDS = ("token", "password", "secret", "key", "authorization")

# Log to stderr only: with the stdio transport, anything on stdout breaks the protocol.
logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("mcp")

_stats = defaultdict(lambda: {"calls": 0, "errors": 0, "denied": 0, "total_ms": 0.0, "max_ms": 0.0})


def _redact(args):
    return {k: ("***" if any(w in k.lower() for w in SECRET_WORDS) else str(v)[:200])
            for k, v in args.items()}


def _record(tool, args, started, status, result_chars):
    ms = (time.perf_counter() - started) * 1000
    s = _stats[tool]
    s["calls"] += 1
    s["total_ms"] += ms
    s["max_ms"] = max(s["max_ms"], ms)
    if status == "error":
        s["errors"] += 1
    if status == "denied":
        s["denied"] += 1
    entry = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "tool": tool,
             "args": _redact(args), "status": status, "ms": round(ms, 1), "result_chars": result_chars}
    with open(AUDIT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    log.info("tool_call tool=%s status=%s ms=%.0f", tool, status, ms)


def monitored(fn):
    """Wrap a tool: time it, count it, log it, and never log secrets."""
    sig = inspect.signature(fn)

    @functools.wraps(fn)          # keeps the name, docstring and signature MCP needs
    def wrapper(*args, **kwargs):
        bound = sig.bind_partial(*args, **kwargs)
        started = time.perf_counter()
        try:
            result = fn(*args, **kwargs)
        except Exception:
            _record(fn.__name__, bound.arguments, started, "error", 0)
            raise
        text = result if isinstance(result, str) else json.dumps(result, default=str)
        status = "denied" if text.startswith("Access denied") else "ok"
        _record(fn.__name__, bound.arguments, started, status, len(text))
        return result

    return wrapper


def stats_snapshot():
    if not _stats:
        return "No tool calls yet."
    lines = [f"{t}: {s['calls']} calls, {s['errors']} errors, {s['denied']} denied, "
             f"avg {s['total_ms'] / s['calls']:.0f} ms, max {s['max_ms']:.0f} ms" for t, s in _stats.items()]
    return "\n".join(lines)


def report():
    """Summarise mcp_audit.jsonl: calls, errors, denials and slowest calls per tool."""
    try:
        rows = [json.loads(line) for line in open(AUDIT_FILE, encoding="utf-8")]
    except FileNotFoundError:
        return "No audit file yet."
    by_tool = defaultdict(list)
    for r in rows:
        by_tool[r["tool"]].append(r)
    out = [f"{len(rows)} calls between {rows[0]['ts']} and {rows[-1]['ts']}"] if rows else ["No calls recorded."]
    for tool, rs in sorted(by_tool.items()):
        ms = sorted(r["ms"] for r in rs)
        p95 = ms[min(len(ms) - 1, int(len(ms) * 0.95))]
        bad = sum(r["status"] == "error" for r in rs)
        denied = sum(r["status"] == "denied" for r in rs)
        out.append(f"{tool:22} calls={len(rs):4} errors={bad:3} denied={denied:3} p95={p95:.0f}ms")
    return "\n".join(out)


if __name__ == "__main__":
    print(report())
