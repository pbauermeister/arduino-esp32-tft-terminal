# Graphical animations

As mentioned in [Communication protocol](README-protocol.md), **commands** are sent by the computer to the board as plain text lines over USB, which the boards translates into embedded library calls (gfx **primitives**).

## Frames

For animations, the command `clearDisplay` is sent, and then desired primitives are send to render a frame.
Same process for the next frame.

Example app, Asteriods:
```
cd client-py
./run.py --only asteriods --app-asteriods-autoplay
```
On the top-left, one can notice that the score is slightly flickering.

## Transactional speedup

Complexer graphics mean sending more commands, adding up to the data transmission delay, and hence causing increasing flicker.

To mitigate this, a so-called "transactional mode" can be activated: All pixel changes are buffered by the board, and effectively rendered all at once upon `display`.
So, during the whole computation and transmission time, the previous frame is held visible and unchanged.
Some display boards provide, by design, transactions. (Like the [FeatherWing 128x64 OLED](https://www.adafruit.com/product/4650) -- no longer supported in this project.)

Unfortunately, the [ESP32-S3 Reverse TFT Feather](https://www.adafruit.com/product/5345) does not provide transactions, so it has been simulated by buffering the commands, eventually yielding the same effect, and allowing easy portability with boards supporting transactions.

The transactional mode (real or simulated) can be activated by sending this command to the board (response not shown):
```
autoDisplay 0
```
Then a frame can be rendered as follows:
```
clearDisplay
... transmit all desired commands...
display
```
All commands are buffered by the board, and effectively executed all at once upon `display`.

## More speedup: "undraw" the last frame with background color

Since "effectively rendering all buffered commands at once" by the board is not instantaneous, some flicker may still be perceived, especially if many pixels are affected (e.g. clearing the display).

In this case, an additional strategy is used: the Python program does not call `clearDisplay`, but erases the effects of the last frame (for instance by re-drawing all, but in background color), before drawing the new frame.

Example app, Soap Bubbles:
```
cd client-py
./run.py --only bubbles-soap
```
The outer border is not flickering.

## Even more speedup: erase only the remains of the last frame

Instead of erasing the objects of the last frame, only the "remains" of the last frames (i.e. parts of the last frame that are not present in the new frame) are selectively erased (painted in background color).

All these different techniques can be seen in the sequences of the Cube app:
```
cd client-py
./run.py --only cube
```
- _Wireframe_ and _Opaque_: Transactional speedup (no `clearDisplay`).
- _Shaded_: using `clearDisplay`, many pixels are drawn, much flicker.
- _No flicker_ and _Contour_: Transactional speedup, and selective erasure of remains of the previous frame.
