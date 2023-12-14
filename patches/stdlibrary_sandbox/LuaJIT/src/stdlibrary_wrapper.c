#include <stdio.h>
#include <stdlib.h>

size_t fwrite_sandbox(const void *buffer, size_t size, size_t count, FILE *stream) {
    if (stream == stdout || stream == stderr) {
        return fwrite(buffer, size, count, stream);
    }

    return NULL;
}

int system_sandbox(const char *command) {
    return 0;
}