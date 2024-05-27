/*
Command provides the interpret() function that will:
1. Parse the input command line:
   - Read a first keyword,
   - depending on the first keyword, read the requested parameters,
   - pack into an Action.
2. Use Transaction to handle the Action.
*/

#ifndef COMMAND_H
#define COMMAND_H

#include "config.h"

const char *interpret(char *input, const Config &config);

// https://stackoverflow.com/a/46711735
constexpr unsigned int hash(const char *s, int off = 0) {
  return !s[off] ? 5381 : (hash(s, off + 1) * 33) ^ (s[off] | 0x20);
}

#endif  // COMMAND_H