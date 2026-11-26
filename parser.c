#include "parser.h"
#include <stdlib.h>
#include <string.h>

#define TAB_WIDTH 8

static int add_task(TaskList *tasks, off_t start, off_t end, bool tabs_before) {
    if (start >= end) return 0;
    if (tasks->count == tasks->capacity) {
        size_t next = tasks->capacity ? tasks->capacity * 2 : 8;
        Task *tmp = realloc(tasks->items, next * sizeof(*tmp));
        if (!tmp) return -1;
        tasks->items = tmp;
        tasks->capacity = next;
    }
    tasks->items[tasks->count] = (Task){
        .id = tasks->count,
        .start = start,
        .end = end,
        .tabs_before = tabs_before
    };
    tasks->count++;
    return 0;
}

void free_tasks(TaskList *tasks) {
    free(tasks->items);
    *tasks = (TaskList){0};
}

/* Candidate boundaries for the default GNU fmt mode only.
   Return visual indentation (TAB stop width 8). */
static size_t line_indent(const char *line, ssize_t length, int *is_blank) {
    size_t column = 0;
    *is_blank = 1;
    for (ssize_t i = 0; i < length; ++i) {
        if (line[i] == ' ') {
            ++column;
        } else if (line[i] == '\t') {
            column += TAB_WIDTH - (column % TAB_WIDTH);
        } else if (line[i] == '\r' || line[i] == '\n') {
            /* Whitespace-only lines are considered blank. */
        } else {
            *is_blank = 0;
            break;
        }
    }
    return column;
}

int parse_file(FILE *file, TaskList *tasks) {
    char *line = NULL;
    size_t capacity = 0;
    ssize_t nread;
    off_t pos = 0, start = 0;
    int have_text = 0;
    int saw_blank = 0;
    size_t previous_indent = 0;
    bool tabs_before = false;
    bool tabs_in_current_task = false;

    while ((nread = getline(&line, &capacity, file)) != -1) {
        int blank;
        size_t indent = line_indent(line, nread, &blank);
        if (blank) {
            saw_blank = 1;
        } else {
            /* At a candidate boundary, finalize the previous task.
               The current line belongs to the NEW task, so inspect its
               TABs only AFTER closing the previous task. */
            if (have_text && (saw_blank || indent != previous_indent)) {
                if (add_task(tasks, start, pos, tabs_before) != 0) goto error;
                tabs_before = tabs_before || tabs_in_current_task;
                tabs_in_current_task = false;
                start = pos;
            }
            have_text = 1;
            saw_blank = 0;
            previous_indent = indent;
        }
        /* getline gives a byte count; memchr also works with embedded NUL. */
        if (memchr(line, '\t', (size_t)nread) != NULL)
            tabs_in_current_task = true;
        pos += nread;
    }
    if (ferror(file) || add_task(tasks, start, pos, tabs_before) != 0)
        goto error;
    free(line);
    return 0;
error:
    free(line);
    free_tasks(tasks);
    return -1;
}
