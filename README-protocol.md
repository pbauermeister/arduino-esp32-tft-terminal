## Communication protocol between the PC and the board

The computer may send textual command lines over USB to the board (`cmd: ` below), to which the board responds (`ans: ` below):
```
cmd: width
ans: 240
cmd: height
ans: 135
cmd: reset
ans: OK
cmd: setTextSize 2 4
ans: OK
cmd: getTextBounds 0 0 HELLO WORLD
ans: 0 0 144 32
cmd: setCursor 48 52
ans: OK
cmd: print HELLO WORLD
ans: OK
```

Many of these commands are mapped to corresponding calls to graphical primitives of the TFT library.
