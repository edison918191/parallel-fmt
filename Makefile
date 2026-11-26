CC = gcc
CFLAGS = -std=c11 -D_POSIX_C_SOURCE=200809L -O2 -Wall -Wextra -Wpedantic

all: inspect_paragraphs

inspect_paragraphs: inspect_paragraphs.c parser.c parser.h
	$(CC) $(CFLAGS) inspect_paragraphs.c parser.c -o inspect_paragraphs

clean:
	rm -f inspect_paragraphs
