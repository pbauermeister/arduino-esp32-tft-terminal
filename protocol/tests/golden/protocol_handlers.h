// AUTO-GENERATED from protocol/protocol.yaml — DO NOT EDIT.
// Regenerate with: make protocol-gen

#ifndef PROTOCOL_HANDLERS_AUTOGEN_H
#define PROTOCOL_HANDLERS_AUTOGEN_H

#include <stdint.h>

// Buffered replay handlers — the TFT binding for each draw command.
// Hand-written in transaction.cpp; a missing one is a link error.
void replay_bufNoArgs();
void replay_bufAllTypes(int16_t x, unsigned char ch, bool flag, int8_t sz, int color);
void replay_bufOptional(int a, int b);
void replay_bufText(const char * text);

// Immediate command handlers — return the response string.
// Hand-written in command.cpp.
const char *handle_qBounds(int16_t x, const char * s);
const char *handle_qValue();
const char *handle_ctlVoid();
const char *handle_btnRead(int ms);

#endif  // PROTOCOL_HANDLERS_AUTOGEN_H
