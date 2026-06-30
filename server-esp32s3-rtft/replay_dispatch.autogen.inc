// AUTO-GENERATED from protocol/protocol.yaml — DO NOT EDIT.
// Regenerate with: make protocol-gen

case hash("print"): {
    replay_print(action->str);
    break;
}

case hash("clearDisplay"): {
    replay_clearDisplay();
    break;
}

case hash("clear"): {
    replay_clear();
    break;
}

case hash("home"): {
    replay_home();
    break;
}

case hash("setFgColor"): {
    replay_setFgColor((int)action->args[0], (int)action->args[1], (int)action->args[2]);
    break;
}

case hash("setBgColor"): {
    replay_setBgColor((int)action->args[0], (int)action->args[1], (int)action->args[2]);
    break;
}

case hash("drawPixel"): {
    replay_drawPixel((int16_t)action->args[0], (int16_t)action->args[1], (int16_t)action->args[2]);
    break;
}

case hash("setRotation"): {
    replay_setRotation((int)action->args[0]);
    break;
}

case hash("invertDisplay"): {
    replay_invertDisplay((bool)action->args[0]);
    break;
}

case hash("drawFastVLine"): {
    replay_drawFastVLine((int16_t)action->args[0], (int16_t)action->args[1], (int16_t)action->args[2], (int)action->args[3]);
    break;
}

case hash("drawFastHLine"): {
    replay_drawFastHLine((int16_t)action->args[0], (int16_t)action->args[1], (int16_t)action->args[2], (int)action->args[3]);
    break;
}

case hash("fillScreen"): {
    replay_fillScreen((int)action->args[0]);
    break;
}

case hash("drawLine"): {
    replay_drawLine((int16_t)action->args[0], (int16_t)action->args[1], (int16_t)action->args[2], (int16_t)action->args[3], (int)action->args[4]);
    break;
}

case hash("drawRect"): {
    replay_drawRect((int16_t)action->args[0], (int16_t)action->args[1], (int16_t)action->args[2], (int16_t)action->args[3], (int)action->args[4]);
    break;
}

case hash("fillRect"): {
    replay_fillRect((int16_t)action->args[0], (int16_t)action->args[1], (int16_t)action->args[2], (int16_t)action->args[3], (int)action->args[4]);
    break;
}

case hash("drawCircle"): {
    replay_drawCircle((int16_t)action->args[0], (int16_t)action->args[1], (int16_t)action->args[2], (int)action->args[3]);
    break;
}

case hash("fillCircle"): {
    replay_fillCircle((int16_t)action->args[0], (int16_t)action->args[1], (int16_t)action->args[2], (int)action->args[3]);
    break;
}

case hash("drawTriangle"): {
    replay_drawTriangle((int16_t)action->args[0], (int16_t)action->args[1], (int16_t)action->args[2], (int16_t)action->args[3], (int16_t)action->args[4], (int16_t)action->args[5], (int)action->args[6]);
    break;
}

case hash("fillTriangle"): {
    replay_fillTriangle((int16_t)action->args[0], (int16_t)action->args[1], (int16_t)action->args[2], (int16_t)action->args[3], (int16_t)action->args[4], (int16_t)action->args[5], (int)action->args[6]);
    break;
}

case hash("drawRoundRect"): {
    replay_drawRoundRect((int16_t)action->args[0], (int16_t)action->args[1], (int16_t)action->args[2], (int16_t)action->args[3], (int16_t)action->args[4], (int)action->args[5]);
    break;
}

case hash("fillRoundRect"): {
    replay_fillRoundRect((int16_t)action->args[0], (int16_t)action->args[1], (int16_t)action->args[2], (int16_t)action->args[3], (int16_t)action->args[4], (int)action->args[5]);
    break;
}

case hash("drawChar"): {
    replay_drawChar((int16_t)action->args[0], (int16_t)action->args[1], (unsigned char)action->args[2], (bool)action->args[3], (bool)action->args[4], (int8_t)action->args[5]);
    break;
}

case hash("setTextSize"): {
    replay_setTextSize((int)action->args[0], (int)action->args[1]);
    break;
}

case hash("setCursor"): {
    replay_setCursor((int16_t)action->args[0], (int16_t)action->args[1]);
    break;
}

case hash("setTextColor"): {
    replay_setTextColor((int)action->args[0], (int)action->args[1], (int)action->args[2]);
    break;
}

case hash("setTextWrap"): {
    replay_setTextWrap((bool)action->args[0]);
    break;
}
