// AUTO-GENERATED from protocol/protocol.yaml — DO NOT EDIT.
// Regenerate with: make protocol-gen

case hash("reboot"): {
    no_arg(&rest, error);
    if (error.message) return error.message;
    return handle_reboot();
}

case hash("reset"): {
    no_arg(&rest, error);
    if (error.message) return error.message;
    return handle_reset();
}

case hash("display"): {
    no_arg(&rest, error);
    if (error.message) return error.message;
    return handle_display();
}

case hash("autoDisplay"): {
    int on = read_int(&rest, error);
    if (error.message) return error.message;
    return handle_autoDisplay(on);
}

case hash("autoReadButtons"): {
    int on = read_int(&rest, error);
    if (error.message) return error.message;
    return handle_autoReadButtons(on);
}

case hash("version"): {
    no_arg(&rest, error);
    if (error.message) return error.message;
    return handle_version();
}

case hash("width"): {
    no_arg(&rest, error);
    if (error.message) return error.message;
    return handle_width();
}

case hash("height"): {
    no_arg(&rest, error);
    if (error.message) return error.message;
    return handle_height();
}

case hash("getPrintMaxLength"): {
    no_arg(&rest, error);
    if (error.message) return error.message;
    return handle_getPrintMaxLength();
}

case hash("getRotation"): {
    no_arg(&rest, error);
    if (error.message) return error.message;
    return handle_getRotation();
}

case hash("getCursorX"): {
    no_arg(&rest, error);
    if (error.message) return error.message;
    return handle_getCursorX();
}

case hash("getCursorY"): {
    no_arg(&rest, error);
    if (error.message) return error.message;
    return handle_getCursorY();
}

case hash("getTextBounds"): {
    int x = read_int(&rest, error);
    int y = read_int(&rest, error);
    const char *text = read_last_str(&rest, error);
    if (error.message) return error.message;
    return handle_getTextBounds(x, y, text);
}

case hash("print"): {
    transaction.action()->set(hh, rest);
    transaction.add();
    return ok();
}

case hash("clearDisplay"): {
    no_arg(&rest, error);
    if (error.message) return error.message;
    transaction.action()->set(hh);
    transaction.add();
    return ok();
}

case hash("clear"): {
    no_arg(&rest, error);
    if (error.message) return error.message;
    transaction.action()->set(hh);
    transaction.add();
    return ok();
}

case hash("home"): {
    no_arg(&rest, error);
    if (error.message) return error.message;
    transaction.action()->set(hh);
    transaction.add();
    return ok();
}

case hash("setFgColor"): {
    int r = read_int(&rest, error);
    int g = read_int(&rest, error);
    int b = read_int(&rest, error);
    if (error.message) return error.message;
    transaction.action()->set(hh, r, g, b);
    transaction.add();
    return ok();
}

case hash("setBgColor"): {
    int r = read_int(&rest, error);
    int g = read_int(&rest, error);
    int b = read_int(&rest, error);
    if (error.message) return error.message;
    transaction.action()->set(hh, r, g, b);
    transaction.add();
    return ok();
}

case hash("drawPixel"): {
    int x = read_int(&rest, error);
    int y = read_int(&rest, error);
    int color = read_int(&rest, error);
    if (error.message) return error.message;
    transaction.action()->set(hh, x, y, color);
    transaction.add();
    return ok();
}

case hash("setRotation"): {
    int m = read_int(&rest, error);
    if (error.message) return error.message;
    transaction.action()->set(hh, m);
    transaction.add();
    return ok();
}

case hash("invertDisplay"): {
    int inv = read_int(&rest, error, true, 1);
    if (error.message) return error.message;
    transaction.action()->set(hh, inv);
    transaction.add();
    return ok();
}

case hash("drawFastVLine"): {
    int x = read_int(&rest, error);
    int y = read_int(&rest, error);
    int h = read_int(&rest, error);
    int color = read_int(&rest, error);
    if (error.message) return error.message;
    transaction.action()->set(hh, x, y, h, color);
    transaction.add();
    return ok();
}

case hash("drawFastHLine"): {
    int x = read_int(&rest, error);
    int y = read_int(&rest, error);
    int w = read_int(&rest, error);
    int color = read_int(&rest, error);
    if (error.message) return error.message;
    transaction.action()->set(hh, x, y, w, color);
    transaction.add();
    return ok();
}

case hash("fillScreen"): {
    int color = read_int(&rest, error);
    if (error.message) return error.message;
    transaction.action()->set(hh, color);
    transaction.add();
    return ok();
}

case hash("drawLine"): {
    int x0 = read_int(&rest, error);
    int y0 = read_int(&rest, error);
    int x1 = read_int(&rest, error);
    int y1 = read_int(&rest, error);
    int color = read_int(&rest, error);
    if (error.message) return error.message;
    transaction.action()->set(hh, x0, y0, x1, y1, color);
    transaction.add();
    return ok();
}

case hash("drawRect"): {
    int x = read_int(&rest, error);
    int y = read_int(&rest, error);
    int w = read_int(&rest, error);
    int h = read_int(&rest, error);
    int color = read_int(&rest, error);
    if (error.message) return error.message;
    transaction.action()->set(hh, x, y, w, h, color);
    transaction.add();
    return ok();
}

case hash("fillRect"): {
    int x = read_int(&rest, error);
    int y = read_int(&rest, error);
    int w = read_int(&rest, error);
    int h = read_int(&rest, error);
    int color = read_int(&rest, error);
    if (error.message) return error.message;
    transaction.action()->set(hh, x, y, w, h, color);
    transaction.add();
    return ok();
}

case hash("drawCircle"): {
    int x = read_int(&rest, error);
    int y = read_int(&rest, error);
    int r = read_int(&rest, error);
    int color = read_int(&rest, error);
    if (error.message) return error.message;
    transaction.action()->set(hh, x, y, r, color);
    transaction.add();
    return ok();
}

case hash("fillCircle"): {
    int x = read_int(&rest, error);
    int y = read_int(&rest, error);
    int r = read_int(&rest, error);
    int color = read_int(&rest, error);
    if (error.message) return error.message;
    transaction.action()->set(hh, x, y, r, color);
    transaction.add();
    return ok();
}

case hash("drawTriangle"): {
    int x0 = read_int(&rest, error);
    int y0 = read_int(&rest, error);
    int x1 = read_int(&rest, error);
    int y1 = read_int(&rest, error);
    int x2 = read_int(&rest, error);
    int y2 = read_int(&rest, error);
    int color = read_int(&rest, error);
    if (error.message) return error.message;
    transaction.action()->set(hh, x0, y0, x1, y1, x2, y2, color);
    transaction.add();
    return ok();
}

case hash("fillTriangle"): {
    int x0 = read_int(&rest, error);
    int y0 = read_int(&rest, error);
    int x1 = read_int(&rest, error);
    int y1 = read_int(&rest, error);
    int x2 = read_int(&rest, error);
    int y2 = read_int(&rest, error);
    int color = read_int(&rest, error);
    if (error.message) return error.message;
    transaction.action()->set(hh, x0, y0, x1, y1, x2, y2, color);
    transaction.add();
    return ok();
}

case hash("drawRoundRect"): {
    int x = read_int(&rest, error);
    int y = read_int(&rest, error);
    int w = read_int(&rest, error);
    int h = read_int(&rest, error);
    int r = read_int(&rest, error);
    int color = read_int(&rest, error);
    if (error.message) return error.message;
    transaction.action()->set(hh, x, y, w, h, r, color);
    transaction.add();
    return ok();
}

case hash("fillRoundRect"): {
    int x = read_int(&rest, error);
    int y = read_int(&rest, error);
    int w = read_int(&rest, error);
    int h = read_int(&rest, error);
    int r = read_int(&rest, error);
    int color = read_int(&rest, error);
    if (error.message) return error.message;
    transaction.action()->set(hh, x, y, w, h, r, color);
    transaction.add();
    return ok();
}

case hash("drawChar"): {
    int x = read_int(&rest, error);
    int y = read_int(&rest, error);
    int c = read_int(&rest, error);
    int fg = read_int(&rest, error);
    int bg = read_int(&rest, error);
    int size = read_int(&rest, error);
    if (error.message) return error.message;
    transaction.action()->set(hh, x, y, c, fg, bg, size);
    transaction.add();
    return ok();
}

case hash("setTextSize"): {
    int sx = read_int(&rest, error);
    int sy = read_int(&rest, error, true, -1);
    if (error.message) return error.message;
    transaction.action()->set(hh, sx, sy);
    transaction.add();
    return ok();
}

case hash("setCursor"): {
    int x = read_int(&rest, error);
    int y = read_int(&rest, error);
    if (error.message) return error.message;
    transaction.action()->set(hh, x, y);
    transaction.add();
    return ok();
}

case hash("setTextColor"): {
    int r = read_int(&rest, error);
    int g = read_int(&rest, error);
    int b = read_int(&rest, error);
    if (error.message) return error.message;
    transaction.action()->set(hh, r, g, b);
    transaction.add();
    return ok();
}

case hash("setTextWrap"): {
    int w = read_int(&rest, error);
    if (error.message) return error.message;
    transaction.action()->set(hh, w);
    transaction.add();
    return ok();
}

case hash("readButtons"): {
    no_arg(&rest, error);
    if (error.message) return error.message;
    return handle_readButtons();
}

case hash("waitButton"): {
    int during = read_int(&rest, error);
    int up = read_int(&rest, error);
    if (error.message) return error.message;
    return handle_waitButton(during, up);
}

case hash("monitorButtons"): {
    int during = read_int(&rest, error);
    int interval = read_int(&rest, error, true, 100);
    if (error.message) return error.message;
    return handle_monitorButtons(during, interval);
}

case hash("watchButtons"): {
    int during = read_int(&rest, error, true, 0);
    int interval = read_int(&rest, error, true, 100);
    if (error.message) return error.message;
    return handle_watchButtons(during, interval);
}

case hash("test"): {
    no_arg(&rest, error);
    if (error.message) return error.message;
    return handle_test();
}

case hash("hardcopy"): {
    no_arg(&rest, error);
    if (error.message) return error.message;
    return handle_hardcopy();
}
