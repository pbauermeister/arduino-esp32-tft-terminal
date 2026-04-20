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
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

SESSIONS_DIR = Path.home() / ".claude" / "sessions"
PROJECTS_DIR = Path.home() / ".claude" / "projects"
TAIL_BYTES = 64 * 1024

_CLK_TCK = os.sysconf("SC_CLK_TCK")


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

_ANSI_RESET = "\x1b[0m"

# Foregrounds
_FG_BLACK = "\x1b[30m"
_FG_WHITE = "\x1b[97m"
_FG_GREY = "\x1b[90m"

# Backgrounds
_BG_BLACK = "\x1b[40m"
_BG_RED = "\x1b[41m"
_BG_GREEN = "\x1b[42m"
_BG_YELLOW = "\x1b[43m"
_BG_BLUE = "\x1b[44m"
_BG_GREY = "\x1b[100m"

# Effects (ANSI blink applies to the foreground only)
_FX_BLINK = "\x1b[5m"
_FX_BOLD = "\x1b[1m"

_STATE_STYLE: dict[ClaudeState, str] = {
    ClaudeState.BUSY: _FG_BLACK + _BG_RED,
    ClaudeState.ASKING: _FG_BLACK + _BG_YELLOW + _FX_BLINK,
    ClaudeState.IDLE: _FG_BLACK + _BG_GREEN,
}


def _colorize(text: str, state: ClaudeState, doit: bool = True) -> str:
    """Wrap `text` in the ANSI style defined for `state`."""
    if not doit:
        return f"{_BG_BLACK}{_FG_GREY}{text}{_ANSI_RESET}"
    return f"{_STATE_STYLE[state]}{text}{_ANSI_RESET}"


# =============================================================================
# Probing
# =============================================================================
#
# -----------------------------------------------------------------------------
# STRATEGY — how we find ACTIVE sessions
# -----------------------------------------------------------------------------
# Two filesystem sources + /proc:
#
#   1. ~/.claude/sessions/<pid>.json
#        Each live `claude` process drops { pid, cwd, sessionId, ... } here.
#        ENUMERATION source. See `_load_session_probes`.
#
#   2. /proc/<pid>  (Linux only)
#        Verifies the candidate PID is still alive, has comm == "claude",
#        and is owned by the current UID. See `_is_process_claude`.
#
#   3. ~/.claude/projects/<encoded-cwd>/*.jsonl
#        The transcript. Resolved per-probe by `_find_active_jsonl`:
#          - solo probe for the cwd → newest jsonl (immune to /clear id
#            rotation that leaves sessions/<pid>.json stale);
#          - multiple concurrent probes for the same cwd → each uses its
#            own sessionId to pick its own jsonl (only way to keep them
#            distinct when they share a project_dir).
#
# -----------------------------------------------------------------------------
# STRATEGY — how we classify BUSY / ASKING / IDLE
# -----------------------------------------------------------------------------
# Single authoritative observable: the tail of the JSONL transcript.
#
#   last entry                                | state
#   ------------------------------------------|--------
#   none (fresh session)                      | IDLE
#   `user` (prompt submitted or tool_result)  | BUSY
#   `assistant` with `tool_use` content       | ASKING*
#   `assistant` without `tool_use`            | IDLE
#
#   * Refinement: "ASKING" is ambiguous between (a) permission modal waiting
#     for the user, and (b) tool was approved and is now executing. We
#     disambiguate by checking the start time of claude's children:
#       - any child spawned AFTER the tool_use entry's timestamp
#         → tool is running → BUSY;
#       - no such child → ASKING stays.
#     This uses /proc/<cpid>/stat field 22 (`starttime` in clock ticks
#     since boot) plus /proc/stat `btime` (boot epoch). Persistent helpers
#     (socat from /sandbox, editors from Ctrl-G) predate the tool_use and
#     are correctly ignored.
#
# We do not sample over time — no CPU ticks, no mtime deltas, no grace
# windows. Transitions appear with whatever latency the JSONL and /proc
# themselves exhibit, which is the minimum achievable by a passive monitor.
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class _LastEntry:
    kind: str  # "user" or "assistant"
    has_tool_use: bool
    timestamp: float | None  # epoch seconds, None if missing/unparseable


@dataclass
class _SessionProbe:
    pid: int
    cwd: str
    session_id_hint: str | None = None
    jsonl: Path | None = None


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


def _boot_time() -> float:
    """System boot as epoch seconds, from /proc/stat `btime`."""
    try:
        for line in Path("/proc/stat").read_text().splitlines():
            if line.startswith("btime "):
                return float(line.split()[1])
    except OSError:
        pass
    return 0.0


def _child_start_times(pid: int) -> list[float]:
    """Epoch start times of non-zombie direct children of `pid`."""
    btime = _boot_time()
    if btime == 0.0:
        return []
    try:
        entries = os.listdir("/proc")
    except OSError:
        return []
    starts: list[float] = []
    for entry in entries:
        if not entry.isdigit():
            continue
        fields = _get_proc_stat_fields(entry)
        if fields is None:
            continue
        try:
            state = fields[0]
            ppid = int(fields[1])
            # fields[19] = 22nd stat field (starttime in clock ticks since boot)
            starttime_ticks = int(fields[19])
        except (IndexError, ValueError):
            continue
        if ppid != pid or state == "Z":
            continue
        starts.append(btime + starttime_ticks / _CLK_TCK)
    return starts


def _newest_jsonl(project_dir: Path) -> Path | None:
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


def _find_active_jsonl(cwd: str, session_id_hint: str | None, solo: bool) -> Path | None:
    """Resolve a probe's live JSONL transcript.

    - solo probe for the cwd → newest jsonl in the project_dir. This is
      robust against /clear-driven sessionId rotation where
      sessions/<pid>.json may not reflect the new id.
    - multiple probes share the cwd → each probe's sessionId hint is the
      only way to distinguish them. We do NOT fall back to newest, which
      would cause all same-cwd probes to collide on the same file.
    """
    encoded = cwd.replace("/", "-")
    project_dir = PROJECTS_DIR / encoded
    if not project_dir.is_dir():
        return None
    if solo:
        return _newest_jsonl(project_dir)
    if session_id_hint:
        candidate = project_dir / f"{session_id_hint}.jsonl"
        if candidate.is_file():
            return candidate
    return None


def _parse_timestamp(s: str | None) -> float | None:
    if not isinstance(s, str) or not s:
        return None
    # Claude writes ISO 8601 like "2026-04-19T21:46:27.752Z".
    try:
        normalized = s.replace("Z", "+00:00") if s.endswith("Z") else s
        return datetime.fromisoformat(normalized).timestamp()
    except ValueError:
        return None


# Slash-command audit markers: Claude Code writes these as type="user"
# entries, but they are *not* user prompts — they are internal records of
# commands like /clear, /compact, etc. Including them in the tail scan
# would misclassify a freshly /clear'd session as BUSY.
_INTERNAL_USER_PREFIXES = (
    "<command-name>",
    "<local-command-caveat>",
    "<local-command-stdout>",
    "<local-command-stderr>",
)


def _is_internal_user_content(content) -> bool:
    if not isinstance(content, str):
        return False
    stripped = content.lstrip()
    return any(stripped.startswith(p) for p in _INTERNAL_USER_PREFIXES)


def _get_last_entry(path: Path | None) -> _LastEntry | None:
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
        if kind == "user" and _is_internal_user_content(content):
            continue
        has_tool_use = any(
            isinstance(c, dict) and c.get("type") == "tool_use" for c in content
        )
        return _LastEntry(
            kind=kind,
            has_tool_use=has_tool_use,
            timestamp=_parse_timestamp(obj.get("timestamp")),
        )
    return None


def _classify(pid: int, entry: _LastEntry | None) -> ClaudeState:
    if entry is None:
        return ClaudeState.IDLE
    if entry.kind == "user":
        return ClaudeState.BUSY
    # entry.kind == "assistant"
    if not entry.has_tool_use:
        return ClaudeState.IDLE
    # tool_use present: disambiguate "permission pending" vs "tool running".
    if entry.timestamp is not None:
        for start in _child_start_times(pid):
            if start > entry.timestamp:
                return ClaudeState.BUSY
    return ClaudeState.ASKING


def _load_session_probes() -> list[_SessionProbe]:
    if not SESSIONS_DIR.is_dir():
        return []
    probes: list[_SessionProbe] = []
    for entry in sorted(SESSIONS_DIR.glob("*.json")):
        try:
            data = json.loads(entry.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        pid = data.get("pid")
        cwd = data.get("cwd")
        session_id = data.get("sessionId")
        if not (isinstance(pid, int) and isinstance(cwd, str)):
            continue
        if not _is_process_claude(pid):
            continue
        probes.append(
            _SessionProbe(
                pid=pid,
                cwd=cwd,
                session_id_hint=session_id if isinstance(session_id, str) else None,
            )
        )
    return probes


# =============================================================================
# Public API
# =============================================================================


def get_sessions() -> list[ClaudeSession]:
    """Return live Claude sessions for the current user, with state.

    Non-blocking: single /proc + filesystem pass, no sampling window.
    """
    probes = _load_session_probes()
    if not probes:
        return []

    cwd_counts: dict[str, int] = {}
    for p in probes:
        cwd_counts[p.cwd] = cwd_counts.get(p.cwd, 0) + 1

    sessions: list[ClaudeSession] = []
    for p in probes:
        solo = cwd_counts[p.cwd] == 1
        p.jsonl = _find_active_jsonl(p.cwd, p.session_id_hint, solo)
        entry = _get_last_entry(p.jsonl)
        sessions.append(
            ClaudeSession(
                path=p.cwd,
                name=os.path.basename(p.cwd.rstrip("/")),
                id=p.jsonl.stem if p.jsonl is not None else "",
                state=_classify(p.pid, entry),
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
        # print(f"{s.id} {state_colored} {s.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
