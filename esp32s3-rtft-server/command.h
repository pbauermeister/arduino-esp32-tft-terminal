#ifndef COMMAND_H
#define COMMAND_H

#include "config.h"

const char *interpret(char *input, const Config &config);

// https://stackoverflow.com/a/46711735
constexpr unsigned int hash(const char *s, int off = 0) {
  return !s[off] ? 5381 : (hash(s, off + 1) * 33) ^ (s[off] | 0x20);
}

#endif  // COMMAND_H