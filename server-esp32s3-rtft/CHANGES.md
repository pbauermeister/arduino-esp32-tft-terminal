# Changes

## Version 0.2.0:

- Add the `getPrintMaxLength` command (usable print-text length per buffered action, `\0` reserved).
- Fix the action-FIFO full handling: auto-commit then queue the new action (previously the triggering action was dropped); the delayed response back-pressures the client.

## Version 0.1.0:

- First versioned firmware release; adds the `version` command.
