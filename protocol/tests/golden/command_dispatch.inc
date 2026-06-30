// AUTO-GENERATED from protocol/protocol.yaml — DO NOT EDIT.
// Regenerate with: make protocol-gen

case hash("bufNoArgs"): {
    no_arg(&rest, error);
    if (error.message) return error.message;
    transaction.action()->set(hh);
    transaction.add();
    return ok();
}

case hash("bufAllTypes"): {
    int x = read_int(&rest, error);
    int ch = read_int(&rest, error);
    int flag = read_int(&rest, error);
    int sz = read_int(&rest, error);
    int color = read_int(&rest, error);
    if (error.message) return error.message;
    transaction.action()->set(hh, x, ch, flag, sz, color);
    transaction.add();
    return ok();
}

case hash("bufOptional"): {
    int a = read_int(&rest, error);
    int b = read_int(&rest, error, true, -1);
    if (error.message) return error.message;
    transaction.action()->set(hh, a, b);
    transaction.add();
    return ok();
}

case hash("bufText"): {
    transaction.action()->set(hh, rest);
    transaction.add();
    return ok();
}

case hash("qBounds"): {
    int x = read_int(&rest, error);
    const char *s = read_last_str(&rest, error);
    if (error.message) return error.message;
    return handle_qBounds(x, s);
}

case hash("qValue"): {
    no_arg(&rest, error);
    if (error.message) return error.message;
    return handle_qValue();
}

case hash("ctlVoid"): {
    no_arg(&rest, error);
    if (error.message) return error.message;
    return handle_ctlVoid();
}

case hash("btnRead"): {
    int ms = read_int(&rest, error, true, 100);
    if (error.message) return error.message;
    return handle_btnRead(ms);
}
