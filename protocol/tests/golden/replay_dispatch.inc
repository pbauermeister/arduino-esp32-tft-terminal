// AUTO-GENERATED from protocol/protocol.yaml — DO NOT EDIT.
// Regenerate with: make protocol-gen

case hash("bufNoArgs"): {
    replay_bufNoArgs();
    break;
}

case hash("bufAllTypes"): {
    replay_bufAllTypes((int16_t)action->args[0], (unsigned char)action->args[1], (bool)action->args[2], (int8_t)action->args[3], (int)action->args[4]);
    break;
}

case hash("bufOptional"): {
    replay_bufOptional((int)action->args[0], (int)action->args[1]);
    break;
}

case hash("bufText"): {
    replay_bufText(action->str);
    break;
}
