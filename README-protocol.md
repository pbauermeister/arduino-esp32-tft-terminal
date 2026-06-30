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

## Command reference

The table below is generated from the protocol meta-spec (`protocol/protocol.yaml`).
Argument notation: `name` positional, `[name]` optional (a default applies when omitted), `<name>` free text running to the end of the line.
Buffered commands are queued and rendered on `display`; the others act immediately.

<!-- BEGIN GENERATED COMMANDS (protocol.yaml) — do not edit; regenerate with: make protocol-gen -->

| Command             | Arguments               | Answer    | Category | Description                                                                                           |
| ------------------- | ----------------------- | --------- | -------- | ----------------------------------------------------------------------------------------------------- |
| `reboot`            | —                       | —         | control  | Reboot the board; sends no response, so the client must not wait.                                     |
| `reset`             | —                       | OK        | control  | Reset display state and clear the pending action buffer.                                              |
| `display`           | —                       | OK        | control  | Flush the buffered draw actions to the screen.                                                        |
| `autoDisplay`       | on                      | OK        | control  | If on=1 draw commands render immediately; if 0 they buffer until `display`.                           |
| `autoReadButtons`   | on                      | OK        | control  | If on=1, every OK response carries the current button-state suffix.                                   |
| `version`           | —                       | string    | query    | Firmware version string.                                                                              |
| `width`             | —                       | int       | query    | Display width in pixels.                                                                              |
| `height`            | —                       | int       | query    | Display height in pixels.                                                                             |
| `getPrintMaxLength` | —                       | int       | query    | Maximum unescaped text length storable by one buffered `print`.                                       |
| `getRotation`       | —                       | int       | query    | Current display rotation (0-3).                                                                       |
| `getCursorX`        | —                       | int       | query    | Current text-cursor X coordinate.                                                                     |
| `getCursorY`        | —                       | int       | query    | Current text-cursor Y coordinate.                                                                     |
| `getTextBounds`     | x y <text>              | x1 y1 w h | query    | Pixel bounding box (x1,y1,w,h) of `text` rendered at (x,y).                                           |
| `print`             | <text>                  | OK        | buffered | Print text at the cursor; supports \n, \t and \\ escapes.                                             |
| `clearDisplay`      | —                       | OK        | buffered | Clear the screen to the background colour.                                                            |
| `clear`             | —                       | OK        | buffered | Clear the screen to the background colour (alias of clearDisplay).                                    |
| `home`              | —                       | OK        | buffered | Move the text cursor to (0,0).                                                                        |
| `setFgColor`        | r g b                   | OK        | buffered | Set the foreground (palette index 1) colour from RGB 0-255.                                           |
| `setBgColor`        | r g b                   | OK        | buffered | Set the background (palette index 0) colour from RGB 0-255.                                           |
| `drawPixel`         | x y color               | OK        | buffered | Plot a pixel at (x,y) in palette `color`.                                                             |
| `setRotation`       | m                       | OK        | buffered | Set display rotation (0-3, in 90 degree steps).                                                       |
| `invertDisplay`     | [inv]                   | OK        | buffered | Invert display colours; inv defaults to 1 (on).                                                       |
| `drawFastVLine`     | x y h color             | OK        | buffered | Vertical line from (x,y), height h, in palette `color`.                                               |
| `drawFastHLine`     | x y w color             | OK        | buffered | Horizontal line from (x,y), width w, in palette `color`.                                              |
| `fillScreen`        | color                   | OK        | buffered | Fill the whole screen with palette `color`.                                                           |
| `drawLine`          | x0 y0 x1 y1 color       | OK        | buffered | Line from (x0,y0) to (x1,y1) in palette `color`.                                                      |
| `drawRect`          | x y w h color           | OK        | buffered | Outline rectangle at (x,y), size w x h, in palette `color`.                                           |
| `fillRect`          | x y w h color           | OK        | buffered | Filled rectangle at (x,y), size w x h, in palette `color`.                                            |
| `drawCircle`        | x y r color             | OK        | buffered | Outline circle centred (x,y), radius r, in palette `color`.                                           |
| `fillCircle`        | x y r color             | OK        | buffered | Filled circle centred (x,y), radius r, in palette `color`.                                            |
| `drawTriangle`      | x0 y0 x1 y1 x2 y2 color | OK        | buffered | Outline triangle through the three vertices, in palette `color`.                                      |
| `fillTriangle`      | x0 y0 x1 y1 x2 y2 color | OK        | buffered | Filled triangle through the three vertices, in palette `color`.                                       |
| `drawRoundRect`     | x y w h r color         | OK        | buffered | Outline rounded rectangle, corner radius r, in palette `color`.                                       |
| `fillRoundRect`     | x y w h r color         | OK        | buffered | Filled rounded rectangle, corner radius r, in palette `color`.                                        |
| `drawChar`          | x y c fg bg size        | OK        | buffered | Draw character code c at (x,y) with fg/bg flags and magnification `size`.                             |
| `setTextSize`       | sx [sy]                 | OK        | buffered | Set text magnification; omit sy (default -1) for square.                                              |
| `setCursor`         | x y                     | OK        | buffered | Move the text cursor to (x,y).                                                                        |
| `setTextColor`      | r g b                   | OK        | buffered | Set text colour from RGB 0-255.                                                                       |
| `setTextWrap`       | w                       | OK        | buffered | Enable (1) or disable (0) automatic text wrapping at the screen edge.                                 |
| `readButtons`       | —                       | string    | button   | Currently pressed buttons, e.g. "A", "AB", or "NONE".                                                 |
| `waitButton`        | during up               | string    | button   | Block up to `during` ms for a button event; up=1 waits for release, 0 for press.                      |
| `monitorButtons`    | during [interval]       | OK        | button   | Stream button states for `during` ms every `interval` ms (default 100), then OK.                      |
| `watchButtons`      | [during] [interval]     | —         | button   | Report button changes for `during` ms (0 = until reset) every `interval` ms; no terminating response. |
| `test`              | —                       | string    | misc     | Run the built-in display diagnostic.                                                                  |
| `hardcopy`          | —                       | string    | misc     | Screen capture (not implemented; returns an error).                                                   |

<!-- END GENERATED COMMANDS -->
