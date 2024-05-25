#ifndef TRANSACTION_H
#define TRANSACTION_H

#include <string.h>

#include <cstdint>

#include "config.h"

typedef intptr_t any;

class Action {
 public:
  unsigned int hash;
  any args[8];
  char str[BUFFER_LENGTH];

  void set(int h) { hash = h; }

  void set(int h, char* text) {
    hash = h;
    strncpy(str, text, sizeof(str));
  }

  void set(int h, int a) {
    hash = h;
    str[0] = 0;
    args[0] = (any)a;
  }

  void set(int h, int a, int b) {
    hash = h;
    str[0] = 0;
    args[0] = (any)a;
    args[1] = (any)b;
  }

  void set(int h, int a, int b, int c) {
    hash = h;
    str[0] = 0;
    args[0] = (any)a;
    args[1] = (any)b;
    args[2] = (any)c;
  }

  void set(int h, int a, int b, int c, int d) {
    hash = h;
    str[0] = 0;
    args[0] = (any)a;
    args[1] = (any)b;
    args[2] = (any)c;
    args[3] = (any)d;
  }

  void set(int h, int a, int b, int c, int d, int e) {
    hash = h;
    str[0] = 0;
    args[0] = (any)a;
    args[1] = (any)b;
    args[2] = (any)c;
    args[3] = (any)d;
    args[4] = (any)e;
  }

  void set(int h, int a, int b, int c, int d, int e, int f) {
    hash = h;
    str[0] = 0;
    args[0] = (any)a;
    args[1] = (any)b;
    args[2] = (any)c;
    args[3] = (any)d;
    args[4] = (any)e;
    args[5] = (any)f;
  }

  void set(int h, int a, int b, int c, int d, int e, int f, int g) {
    hash = h;
    str[0] = 0;
    args[0] = (any)a;
    args[1] = (any)b;
    args[2] = (any)c;
    args[3] = (any)d;
    args[4] = (any)e;
    args[5] = (any)f;
    args[6] = (any)g;
  }

  void set(int hh, int a, int b, int c, int d, int e, int f, int g, int h) {
    hash = hh;
    str[0] = 0;
    args[0] = (any)a;
    args[1] = (any)b;
    args[2] = (any)c;
    args[3] = (any)d;
    args[4] = (any)e;
    args[5] = (any)f;
    args[6] = (any)g;
    args[7] = (any)h;
  }
};

class Transaction {
 public:
  Action actions[1000];  // FIFO
  int next;
  bool enabled;

  Transaction() {
    next = 0;
    enabled = true;
  };

  void clear() { next = 0; }
  void enable(bool en) { enabled = en; }
  Action* action() { return &actions[next]; }
  void add();
  void commit();

 private:
  void do_action(Action*);
};

#endif  // TRANSACTION_H