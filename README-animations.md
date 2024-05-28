# Graphical animations

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

Complex graphics mean sending more primitives, adding up to the data transmission delay, and hence causing increasing flicker.

To mitigate this, a transactional mode can be activated by this command to the board (responses not shown):
```
autoDisplay 0
```
Then a frame is rendered as follows:
```
clearDisplay
... transmit all desired rendering commands...
display
```
All commands are buffered by the board, and effectively rendered all at once upon `display`.
So, during the whole transmission time, the previous frame is held visible.

## More speedup: redraw the last frame with background color

Since "effectively rendering all buffered commands at once" by the board is not instantaneous, some flicker may still be perceived, especially if many pixels are affected.

In this case, an additional strategy is used: the Python program does not call `clearDisplay`, but erases the effects of the last frame (for instance by re-drawing all, but in background color), before drawing the new frame.

Example app, Soap Bubbles:
```
cd client-py
./run.py --only bubbles-soap
```
The outer border is not flickering.

### Even more speedup: erase only the remains of the last frame

Instead of erasing the objects of the last frame, only the "remains" of the last frames (i.e. parts of the last frame that are not present in the new frame) are selectively erased (painted in background color). 

### Summary

These different techniques can be seen in the sequences of the Cube app:
```
cd client-py
./run.py --only cube
```
- _Wireframe_ and _Opaque_: Transactional speedup (no `clearDisplay`).
- _Shaded_: using `clearDisplay`, many pixels are drawn, much flicker.
- _No flicker_ and _Contour_: Transactional speedup, and selective erasure of remains of the previous frame.
