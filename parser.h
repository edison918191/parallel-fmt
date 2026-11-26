#ifndef PARSER_H
#define PARSER_H

#include <stdbool.h>
#include <stddef.h>
#include <stdio.h>
#include <sys/types.h>

typedef struct {
    size_t id;
    off_t start;
    off_t end;
    /* Whether earlier input bytes contain a TAB character.
       This is a raw-input snapshot, not a full GNU fmt state snapshot. */
    bool tabs_before;
} Task;

typedef struct {
    Task *items;
    size_t count;
    size_t capacity;
} TaskList;

int parse_file(FILE *file, TaskList *tasks);
void free_tasks(TaskList *tasks);

#endif
