# Part 1: Paragraph Parser regression tests

This package only **adds** a regression script. It does **not** replace your current `parser.c`, `parser.h`, `inspect_paragraphs.c`, `Makefile`, or `tests/input.txt`.

## Install (Mac Terminal)

1. Move the downloaded ZIP to `~/final_project` using Finder.
2. Run:

```sh
cd ~/final_project
unzip -n fmt_part1_regression.zip
```

## Run (Ubuntu Docker `/workspace`)

```sh
cd /workspace
make
python3 tests/test_part1_regression.py
```

Checks:
- `Task` ranges are contiguous, non-overlapping and cover all bytes.
- IDs are in ascending order and `tabs_before` matches the previously scanned input bytes.
- 15 deterministic fixtures (empty input, normal paragraphs, indent variations, no final newline, blank lines, punctuation, short paragraphs, long paragraphs).
- 30 deterministic mixed-length ASCII test cases, with random seed `20261126`.
- For each of the 45 non-Tab fixtures, compares complete-file `fmt` output against concatenated independently formatted candidate tasks, at width 40, 80 and 120.
- Separately prints the known Tab-context limitation. A mismatch here is **expected** and not counted as a successful compatibility case.

**Scope and limits**: This validates *candidate boundaries* only, under default GNU `fmt` behavior with ASCII examples. It does not mean that the full GNU `fmt` specification is supported, and it does not exercise a worker pool. Passing the corpus does not prove general output equivalence. `-c`, `-t`, `-p`, Unicode and full internal-state restoration are out of scope for these tests. Your actual Linux GNU `fmt` version (8.32) is printed and should be recorded for the final report. This script does not alter anything in your existing source tree except temporary test files outside it.

## After tests: inspect the exact GNU `fmt` 8.32 source

```sh
cd /workspace
mkdir -p third_party
curl -fL -o third_party/coreutils-8.32.tar.xz \
  https://ftp.gnu.org/gnu/coreutils/coreutils-8.32.tar.xz
tar -xf third_party/coreutils-8.32.tar.xz -C third_party

grep -nE 'get_paragraph|fmt_paragraph|put_paragraph|same_para|other_indent|tabs' \
  third_party/coreutils-8.32/src/fmt.c | head -50
```

The next implementation decision should be made after comparing `get_paragraph()` and `same_para()` with the candidate boundary heuristic. GNU Coreutils is GPL-licensed; if adapting its source into this project, retain the appropriate licensing notices and comply with its terms.
