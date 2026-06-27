# 0034 — Firmware builds on esp32 core 3.3.0

- GH issue: #34
- Branch: impl/0034-firmware-core33
- Opened: 2026-06-27
- Closed: 2026-06-27

Fast-path task. Follow-up to #32 (firmware-build surfaced the errors).

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

Make the firmware compile on esp32 core 3.3.0 (the locally-installed core). Two blockers found by `make firmware-build`.

### Acceptance criteria

1. Clean `arduino-cli compile` (exit 0) on core 3.3.0.
2. No behaviour change for implemented commands.

## 2. Execution plan

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

1. `command.cpp`: `int hh = hash(cmd)` → `unsigned int hh`. `hash()` returns `unsigned int`; with an `int` switch the `case hash("…")` labels (values > `INT_MAX`) narrow → `-Werror=narrowing`. Unsigned switch matches the labels.
2. `hardcopy` case (unimplemented, #4): `tft.begin()` is now `protected` in Adafruit_ST77xx and `return null;` uses an undeclared identifier. Replace the broken body with an honest stub: `return "ERROR hardcopy not implemented";` (matches the `ERROR …` protocol convention). `transaction.commit()` kept.

## 3. Closure

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

### 3.1 Verification

- `arduino-cli compile` (FQBN + arduino.json options) → exit 0, 498103 bytes (34% flash).
- Only two lines of real change; implemented commands untouched. `hardcopy` was already non-compiling (dead) code, so neutralising it is not a behaviour change for any working path.

### 3.2 Retrospective

| #   | Point                                                       | Agent | User |
| --- | ----------------------------------------------------------- | ----- | ---- |
| 1   | The #32 firmware-build target paid off immediately          | well  |      |
| 2   | Honest error stub over silent `ok()` (user steer)           | well  |      |

### 3.3 Verdict

Accept.

## Governance trace

| Source                     | Clause          | Action  | Note                                       |
| -------------------------- | --------------- | ------- | ------------------------------------------ |
| CLAUDE.md (Naming/honesty) | honest signals  | applied | unimplemented command returns an explicit error |
| CLAUDE.md (YAGNI)          | minimal change  | applied | two-line fix; no hardcopy feature added    |

## Resource consumption

| Phase | Tokens (approx) | Wall time |
| ----- | --------------- | --------- |
| Total | ~9k             | ~12 min   |

| Counter       | Value |
| ------------- | ----- |
| Files changed | 2 (command.cpp, devlog) |
