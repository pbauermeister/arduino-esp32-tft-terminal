#include "command.h"

#include <Stream.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>

#include "config.h"
#include "esp32s3-display.h"
#include "protocol_handlers.autogen.h"
#include "transaction.h"
#include "version.h"  // generated: FW_VERSION

// constants
const char *ERR_EXTRA_ARG = "ERROR extra arg";
const char *ERR_MISSING_ARG = "ERROR missing arg";
const char *ERR_UNKNOWN_CMD = "ERROR unknown cmd";
const char *OK_MESSAGE = "OK";
const char *NONE_MESSAGE = "NONE";

// variables
bool auto_read_buttons = false;
char buffer[BUFFER_LENGTH];

Transaction transaction = Transaction();

// Board config, captured each interpret() call so the immediate handlers
// (width/height) can read it without threading it through every signature.
const Config *g_config = nullptr;

// forward declarations
const char *ok();
const char *int_response(int val);
void unescape_inplace(char *input);

class ErrorHolder {
   public:
    const char *message;
    ErrorHolder() { message = NULL; }
};

char *split(char *s) {
    char *rest;
    strtok_r(s, " ", &rest);
    return rest;
}

void no_arg(char **rest_p, ErrorHolder &error) {
    if (*rest_p != NULL)
        error.message = ERR_EXTRA_ARG;
    else
        error.message = NULL;
}

int read_int(char **rest_p, ErrorHolder &error, bool optional = false,
             int defval = -1) {
    char *v = *rest_p;
    *rest_p = split(*rest_p);

    if (v == NULL && optional) {
        return defval;
    }

    if (v == NULL)
        error.message = ERR_MISSING_ARG;
    else if (*rest_p != NULL)
        error.message = ERR_EXTRA_ARG;
    else
        error.message = NULL;

    return atoi(v);
}

const char *read_last_str(char **rest_p, ErrorHolder &error) {
    char *v = *rest_p;
    if (v == NULL)
        error.message = ERR_MISSING_ARG;
    else {
        error.message = NULL;
        *rest_p = NULL;
    }
    return v;
}

void (*rebootF)(void) = 0;  // declare reboot function @ address 0

const char *interpret(char *input, const Config &config) {
    g_config = &config;
    unescape_inplace(input);

    char buf[BUFFER_LENGTH];
    strncpy(buf, input, sizeof(buf));

    char *cmd = input;
    char *rest = split(input);
    ErrorHolder error = ErrorHolder();
    unsigned int hh = hash(cmd);

    switch (hh) {
#include "command_dispatch.autogen.inc"

        default:
            break;
    }

    Serial.printf("# %s: ", ERR_UNKNOWN_CMD);
    Serial.println(buf);
    return ERR_UNKNOWN_CMD;
}

const char *ok() {
    strcpy(buffer, OK_MESSAGE);
    if (auto_read_buttons) {
        strcat(buffer, " ");
        bool any = false;

        if (button0_pressed()) {
            strcat(buffer, "A");
            any = true;
        }
        if (button1_pressed()) {
            strcat(buffer, "B");
            any = true;
        }
        if (button2_pressed()) {
            strcat(buffer, "C");
            any = true;
        }
        if (!any) strcat(buffer, NONE_MESSAGE);
    }
    return buffer;
}

const char *int_response(int val) {
    snprintf(buffer, sizeof(buffer) - 1, "%d", val);
    return buffer;
}

void unescape_inplace(char *input) {
    for (char *from = input, *to = input;;) {
        if (*from != '\\') {
            *to = *from;
        } else {
            ++from;
            switch (*from) {
                case 'n':
                    *to = '\n';
                    break;
                case '\\':
                    *to = '\\';
                    break;
                case 't':
                    *to = '\t';
                    break;
                default:
                    *to = *from;
            }
        }
        if (*from == 0) break;
        ++from;
        ++to;
    }
}

// --- Immediate command handlers (declared in protocol_handlers.autogen.h) ---
// Bodies are hand-written; the generated dispatch calls them after parsing.

const char *handle_reboot() {
    rebootF();
    return ok();
}

const char *handle_reset() {
    display_reset();
    transaction.clear();
    return ok();
}

const char *handle_display() {
    transaction.commit();
    return ok();
}

const char *handle_autoDisplay(bool on) {
    transaction.enable(!on);
    return ok();
}

const char *handle_autoReadButtons(bool on) {
    auto_read_buttons = on;
    return ok();
}

const char *handle_version() { return FW_VERSION; }

const char *handle_width() { return int_response(g_config->display_width); }

const char *handle_height() { return int_response(g_config->display_height); }

const char *handle_getPrintMaxLength() {
    return int_response(PRINT_LENGTH - 1);
}

const char *handle_getRotation() {
    transaction.commit();
    return int_response(get_rotation());
}

const char *handle_getCursorX() {
    transaction.commit();
    return int_response(get_cursor_x());
}

const char *handle_getCursorY() {
    transaction.commit();
    return int_response(get_cursor_y());
}

const char *handle_getTextBounds(int16_t x, int16_t y, const char *text) {
    transaction.commit();

    int16_t x1;
    int16_t y1;
    uint16_t w;
    uint16_t h;
    get_text_bounds(text, x, y, &x1, &y1, &w, &h);
    snprintf(buffer, sizeof(buffer) - 1, "%d %d %d %d", x1, y1, w, h);
    return buffer;
}

const char *handle_readButtons() { return read_buttons(buffer); }

const char *handle_waitButton(int during, int up) {
    return wait_buttons(during, up);
}

const char *handle_monitorButtons(int during, int interval) {
    monitor_buttons(during, interval);
    return ok();
}

const char *handle_watchButtons(int during, int interval) {
    watch_buttons(during, interval);
    return "";
}

const char *handle_test() {
    display_test(buffer);
    return buffer;
}

const char *handle_hardcopy() {
    transaction.commit();
    return "ERROR hardcopy not implemented";
}
