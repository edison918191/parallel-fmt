#include "parser.h"
#include <stdio.h>

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s input.txt\n", argv[0]);
        return 1;
    }
    FILE *file = fopen(argv[1], "rb");
    if (!file) {
        perror("fopen");
        return 1;
    }
    TaskList tasks = {0};
    if (parse_file(file, &tasks) != 0) {
        fprintf(stderr, "Failed to parse input\n");
        fclose(file);
        return 1;
    }
    fclose(file);
    printf("Candidate tasks: %zu\n", tasks.count);
    for (size_t i = 0; i < tasks.count; i++) {
        Task t = tasks.items[i];
        /* Keep this line unchanged for existing verify_chunks.py. */
        printf("Task %zu: bytes [%lld, %lld), length %lld\n", t.id,
               (long long)t.start, (long long)t.end,
               (long long)(t.end - t.start));
        printf("Context Task %zu: tabs_before=%s\n", t.id,
               t.tabs_before ? "true" : "false");
    }
    free_tasks(&tasks);
    return 0;
}
