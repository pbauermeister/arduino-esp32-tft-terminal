#ifndef CONFIG_H
#define CONFIG_H

struct Config {
    int display_width;
    int display_height;
};

#define BUFFER_LENGTH 200

// Per-buffered-action print text capacity. Kept well below BUFFER_LENGTH
// because it is paid 1000x (one per buffered Action) — the dominant DRAM user.
// A single print is at most one screen line (~37 chars); longer text truncates.
#define PRINT_LENGTH 128

#endif