#!/usr/bin/env python3
"""List active Claude sessions for the current user with their state.

As a CLI, prints one tab-separated line per session: "<name>\t<id>\t<state>".

As a module, provides:
  - ClaudeState:          enum of possible session states
  - ClaudeSession:        dataclass describing one live session
  - get_sessions():       list[ClaudeSession] for all live claude processes
"""

import json
import os
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

SESSIONS_DIR = Path.home() / ".claude" / "sessions"
PROJECTS_DIR = Path.home() / ".claude" / "projects"

SAMPLE_SECONDS = 1.5
# CPU ticks accumulated by the claude process during the sample window that
# we treat as "this process is actively doing work". Node.js idle background
# activity (GC, timers) can produce 1–3 ticks in 1.5s; 20 (~13% CPU) clears it.
CPU_TICK_THRESHOLD = 20
# If the session's JSONL was touched within this many seconds, assume the
# process is still mid-operation even if our brief sample caught a lull.
RECENT_WRITE_SECONDS = 3.0
TAIL_BYTES = 64 * 1024


# =============================================================================
# Claude states and session
# =============================================================================


class ClaudeState(Enum):
    BUSY = "busy"
    ASKING = "asking"  # Awaiting user answer to menu
    IDLE = "idle"  # Awaiting prompt

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class ClaudeSession:
    path: str  # absolute project home (cwd of the claude process)
    name: str  # last component of path
    id: str  # session id (stem of the active JSONL file), "" if unknown
    state: ClaudeState


# =============================================================================
# ANSI colors
# =============================================================================

# --- Step 1: ANSI palette ------------------------------------------------
# Named SGR codes. Only the basic 16-color codes are used here because `watch`
# (and some other viewers) silently drop 256-color sequences like 48;5;208.

_ANSI_RESET = "\x1b[0m"

# Foregrounds
_FG_BLACK = "\x1b[30m"
_FG_WHITE = "\x1b[97m"
_FG_GREY = "\x1b[90m"  # "bright black" foreground = mid-dark grey

# Backgrounds
_BG_BLACK = "\x1b[40m"
_BG_RED = "\x1b[41m"
_BG_GREEN = "\x1b[42m"
_BG_YELLOW = "\x1b[43m"
_BG_BLUE = "\x1b[44m"
_BG_GREY = "\x1b[100m"  # "bright black" = mid-dark grey, standard 16-color

# Effects (ANSI blink applies to the foreground only)
_FX_BLINK = "\x1b[5m"
_FX_BOLD = "\x1b[1m"

# --- Step 2: per-state style ---------------------------------------------
# Each entry is the concatenated SGR prefix applied before the text. Tweak
# here to re-skin a state — e.g. `ClaudeState.AWAITING_PROMPT: _FG_WHITE + _BG_RED`.
_STATE_STYLE: dict[ClaudeState, str] = {
    ClaudeState.BUSY: _FG_BLACK + _BG_RED,
    ClaudeState.ASKING: _FG_BLACK + _BG_YELLOW + _FX_BLINK,
    ClaudeState.IDLE: _FG_BLACK + _BG_GREEN,
}


def _colorize(text: str, state: ClaudeState, doit: bool = True) -> str:
    """Wrap `text` in the ANSI style defined for `state`."""
    if not doit:
        return f"{_BG_BLACK}{_FG_GREY}{text}{_ANSI_RESET}"
    else:
        return f"{_STATE_STYLE[state]}{text}{_ANSI_RESET}"


# =============================================================================
# Probing
# =============================================================================


@dataclass(frozen=True)
class _FileSnap:
    size: int
    mtime: float


@dataclass(frozen=True)
class _LastJsonlEntry:
    kind: str  # "user" or "assistant"
    stop_reason: str | None
    has_tool_use: bool


@dataclass
class _SessionProbe:
    pid: int
    cwd: str
    jsonl: Path | None = None
    cpu0: int | None = None
    cpu1: int | None = None
    file0: _FileSnap | None = None
    file1: _FileSnap | None = None


def _is_process_claude(pid: int) -> bool:
    try:
        comm = Path(f"/proc/{pid}/comm").read_text().strip()
        if comm != "claude":
            return False
        return os.stat(f"/proc/{pid}").st_uid == os.getuid()
    except (FileNotFoundError, PermissionError, ProcessLookupError, OSError):
        return False


def _get_proc_stat_fields(pid_or_tid: str | int) -> list[str] | None:
    try:
        raw = Path(f"/proc/{pid_or_tid}/stat").read_text()
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return None
    rparen = raw.rfind(")")
    if rparen < 0:
        return None
    return raw[rparen + 2 :].split()


def _read_cpu_ticks(pid: int) -> int | None:
    """utime+stime+cutime+cstime — total CPU ticks incl. reaped children."""
    fields = _get_proc_stat_fields(pid)
    if fields is None:
        return None
    try:
        return int(fields[11]) + int(fields[12]) + int(fields[13]) + int(fields[14])
    except (IndexError, ValueError):
        return None


def _has_process_live_child(pid: int) -> bool:
    """True if `pid` has a non-zombie child process (not counting threads)."""
    try:
        entries = os.listdir("/proc")
    except OSError:
        return False
    for entry in entries:
        if not entry.isdigit():
            continue
        fields = _get_proc_stat_fields(entry)
        if fields is None:
            continue
        try:
            state = fields[0]
            ppid = int(fields[1])
        except (IndexError, ValueError):
            continue
        if ppid == pid and state != "Z":
            return True
    return False


def _find_active_jsonl(cwd: str) -> Path | None:
    """Most recently modified .jsonl in the cwd's project dir.

    Claude Code can rotate session IDs (e.g. on /clear) within a single
    process, so the sessionId recorded in ~/.claude/sessions/<pid>.json can
    go stale. The newest jsonl in the project dir is the live one.
    """
    encoded = cwd.replace("/", "-")
    project_dir = PROJECTS_DIR / encoded
    if not project_dir.is_dir():
        return None
    best: Path | None = None
    best_mtime = -1.0
    for p in project_dir.glob("*.jsonl"):
        try:
            mt = p.stat().st_mtime
        except OSError:
            continue
        if mt > best_mtime:
            best_mtime = mt
            best = p
    return best


def _get_stat_snapshot(path: Path | None) -> _FileSnap | None:
    if path is None:
        return None
    try:
        st = path.stat()
    except OSError:
        return None
    return _FileSnap(size=st.st_size, mtime=st.st_mtime)


def _get_last_jsonl_entry(path: Path | None) -> _LastJsonlEntry | None:
    if path is None:
        return None
    try:
        size = path.stat().st_size
        with path.open("rb") as f:
            if size > TAIL_BYTES:
                f.seek(-TAIL_BYTES, os.SEEK_END)
                f.readline()  # drop possibly-partial first line
            chunk = f.read()
    except OSError:
        return None
    for raw in reversed([ln for ln in chunk.splitlines() if ln.strip()]):
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            continue
        kind = obj.get("type")
        if kind not in ("user", "assistant"):
            continue
        msg = obj.get("message") or {}
        content = msg.get("content") or []
        has_tool_use = any(
            isinstance(c, dict) and c.get("type") == "tool_use" for c in content
        )
        return _LastJsonlEntry(
            kind=kind,
            stop_reason=msg.get("stop_reason"),
            has_tool_use=has_tool_use,
        )
    return None


def _is_busy(p: _SessionProbe, now: float) -> bool:
    if p.file0 is not None and p.file1 is not None and p.file0 != p.file1:
        return True
    if p.file1 is not None and now - p.file1.mtime < RECENT_WRITE_SECONDS:
        return True
    if _has_process_live_child(p.pid):
        return True
    if (
        p.cpu0 is not None
        and p.cpu1 is not None
        and p.cpu1 - p.cpu0 > CPU_TICK_THRESHOLD
    ):
        return True
    return False


def _classify(p: _SessionProbe, now: float) -> ClaudeState:
    if _is_busy(p, now):
        return ClaudeState.BUSY
    entry = _get_last_jsonl_entry(p.jsonl)
    if entry is None:
        return ClaudeState.IDLE
    if entry.kind == "assistant":
        if entry.has_tool_use:
            return ClaudeState.ASKING
        return ClaudeState.IDLE
    # Last entry is a user message (prompt or tool_result) and the process is
    # not busy. Claude Code buffers the next assistant tool_use until a pending
    # permission prompt is resolved, so this state = awaiting answer.
    return ClaudeState.ASKING


def _load_session_probes() -> list[_SessionProbe]:
    if not SESSIONS_DIR.is_dir():
        return []
    probes: list[_SessionProbe] = []
    seen: set[str] = set()
    for entry in sorted(SESSIONS_DIR.glob("*.json")):
        try:
            data = json.loads(entry.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        pid = data.get("pid")
        cwd = data.get("cwd")
        if not (isinstance(pid, int) and isinstance(cwd, str)):
            continue
        if cwd in seen or not _is_process_claude(pid):
            continue
        seen.add(cwd)
        probes.append(_SessionProbe(pid=pid, cwd=cwd))
    return probes


# =============================================================================
# Public API
# =============================================================================


def get_sessions() -> list[ClaudeSession]:
    """Return live Claude sessions for the current user, with state.

    Blocks for ~SAMPLE_SECONDS while it samples CPU and file activity.
    """
    probes = _load_session_probes()
    if not probes:
        return []

    for p in probes:
        p.jsonl = _find_active_jsonl(p.cwd)
        p.cpu0 = _read_cpu_ticks(p.pid)
        p.file0 = _get_stat_snapshot(p.jsonl)

    time.sleep(SAMPLE_SECONDS)
    now = time.time()

    sessions: list[ClaudeSession] = []
    for p in probes:
        p.cpu1 = _read_cpu_ticks(p.pid)
        p.file1 = _get_stat_snapshot(p.jsonl)
        sessions.append(
            ClaudeSession(
                path=p.cwd,
                name=os.path.basename(p.cwd.rstrip("/")),
                id=p.jsonl.stem if p.jsonl is not None else "",
                state=_classify(p, now),
            )
        )
    return sessions


def get_state_counts(
    sessions: list[ClaudeSession] | None = None,
) -> dict[ClaudeState, int]:
    """Count live sessions by state. All ClaudeState keys are present."""
    counts = {state: 0 for state in ClaudeState}
    for s in sessions or get_sessions():
        counts[s.state] += 1
    return counts


def main() -> int:
    sessions = get_sessions()
    state_counts = get_state_counts(sessions)

    print(
        " ".join(
            [
                _colorize(f" {n} {state} ", state, n > 0)
                for state, n in state_counts.items()
            ]
        )
    )
    print()
    for s in sessions:
        state_colored = _colorize(f" {s.state:^6} ", s.state)
        print(f"{s.id[-6:]} {state_colored} {s.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
