#ifndef FILESYSTEM_WRAPPER_H_
#define FILESYSTEM_WRAPPER_H_

#define fwrite fwrite_sandbox
#define system system_sandbox

#include <stdio.h>

size_t fwrite_sandbox(const void *buffer, size_t size, size_t count, FILE *stream);

int system_sandbox(const char *command);

#endif // FILESYSTEM_WRAPPER_H_