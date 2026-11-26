#!/usr/bin/env python3
"""GNU fmt candidate-boundary regression checks (default mode only).

Runs GNU fmt on whole input and on each proposed task independently.
MATCH only demonstrates equivalence for the tested input + options.  The
known tab-context mismatch is reported separately, not silently counted as
correct.  This is NOT a test of parallel formatting or -c/-t/-p support.
"""
from __future__ import annotations

import os
import pathlib
import random
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
INSPECT = ROOT / 'inspect_paragraphs'
TASK_RE = re.compile(r'^Task (\d+): bytes \[(\d+), (\d+)\), length (\d+)$')
CONTEXT_RE = re.compile(r'^Context Task (\d+): tabs_before=(true|false)$')
WIDTHS = (40, 80, 120)
ENV = dict(os.environ, LC_ALL='C')


def run(cmd, **kwargs):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          env=ENV, check=True, **kwargs).stdout


def parse_tasks(path: pathlib.Path, data: bytes):
    text = run([str(INSPECT), str(path)]).decode('utf-8', 'replace')
    tasks, contexts = [], {}
    for line in text.splitlines():
        m = TASK_RE.fullmatch(line)
        if m:
            tid, start, end, length = map(int, m.groups())
            if end - start != length:
                raise AssertionError('Incorrect task length')
            tasks.append((tid, start, end))
        m = CONTEXT_RE.fullmatch(line)
        if m:
            contexts[int(m.group(1))] = m.group(2) == 'true'
    if bool(tasks) != bool(data):
        raise AssertionError('Expected task ranges for every nonempty file')
    cursor = 0
    for index, (tid, start, end) in enumerate(tasks):
        if tid != index or start != cursor or start >= end or end > len(data):
            raise AssertionError(f'Invalid/noncontiguous task: {tid}, {start}, {end}')
        if contexts.get(index) != (b'\t' in data[:start]):
            raise AssertionError(f'Incorrect tabs_before for task {index}')
        cursor = end
    if cursor != len(data):
        raise AssertionError('Task intervals do not cover source bytes')
    return tasks


def fmt(blob: bytes, width: int):
    return run(['fmt', '-w', str(width)], input=blob)


def first_diff(a: bytes, b: bytes):
    return next((i for i, (x, y) in enumerate(zip(a, b)) if x != y),
                min(len(a), len(b)))


def check_case(name: str, data: bytes, *, expect_match: bool,
               expected_tasks: int | None = None, widths=WIDTHS):
    with tempfile.TemporaryDirectory(prefix='fmt-part1-') as tmp:
        src = pathlib.Path(tmp) / 'input.txt'
        src.write_bytes(data)
        tasks = parse_tasks(src, data)
    if expected_tasks is not None and len(tasks) != expected_tasks:
        raise AssertionError(f'Expected {expected_tasks} tasks, got {len(tasks)}')
    mismatches = []
    for width in widths:
        reference = fmt(data, width)
        combined = b''.join(fmt(data[start:end], width) for _, start, end in tasks)
        if reference != combined:
            mismatches.append((width, first_diff(reference, combined)))
    if expect_match and mismatches:
        raise AssertionError(f'GNU fmt output differs (width, first byte): {mismatches}')
    status = 'PASS' if expect_match else ('KNOWN DIFF' if mismatches else 'MATCH (version dependent)')
    print(f'{status}: {name:29s} tasks={len(tasks):3d}' +
          (f'  mismatches={mismatches}' if mismatches else ''))
    return not mismatches


def ordinary_fixture():
    return (b'Parallel programming allows multiple tasks to run at the same time.\n'
            b'This paragraph has two input lines.\n\n'
            b'GNU fmt reformats paragraphs into lines of a given width.\n'
            b'This paragraph also has two lines.\n\n'
            b'The third paragraph is separate.\n')


def corpus():
    return [
        ('empty file', b'', 0),
        ('one line', b'alpha beta gamma delta\n', 1),
        ('one paragraph', b'alpha beta gamma delta\nepsilon zeta eta theta\n', 1),
        ('ordinary paragraphs', ordinary_fixture(), 3),
        ('indentation changes',
         b'Alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu.\n'
         b'  Indented one two three four five six seven eight nine ten eleven.\n'
         b'Normal indentation returns here with another sentence to wrap.\n', 3),
        ('multiple blank lines', b'one two three\n\n\n\nfour five six\n\nseven eight\n', 3),
        ('whitespace-only lines', b'one two three\n   \n\nfour five six\n', 2),
        ('no final newline', b'one two three\n\nfour five six', 2),
        ('leading blank lines', b'\n\nalpha beta gamma\n\ndelta epsilon\n', 2),
        ('trailing blank lines', b'alpha beta gamma\n\n', 1),
        ('blank-only file', b'\n\n \n', 1),
        ('spaces indentation', b'  One two three four\n  Five six seven eight\n'
         b'    Nine ten eleven twelve\n  Thirteen fourteen fifteen\n', 3),
        ('punctuation', b'Hello world.  This is one sentence!\n'
         b'Next phrase?  New lines will be reflowed.\n\n'
         b'The second paragraph goes here.\n', 2),
        ('many small paragraphs', b'\n\n'.join(
            f'paragraph {i} says hello world'.encode() for i in range(60)) + b'\n', 60),
        ('single long paragraph', b'word ' * 2000 + b'word\n', 1),
    ]


def fuzz_cases(seed=20261126, count=30):
    rng = random.Random(seed)
    vocabulary = ('parallel programming makes correct segmentation important '
                  'when worker threads format paragraphs independently').split()
    for i in range(count):
        parts = []
        for _ in range(rng.randrange(1, 8)):
            indent = b' ' * rng.choice((0, 0, 2, 4))
            lines = []
            for _ in range(rng.randrange(1, 5)):
                nwords = rng.randrange(3, 20)
                lines.append(indent + ' '.join(rng.choices(vocabulary, k=nwords)).encode())
            parts.append(b'\n'.join(lines))
        yield f'fuzz #{i+1:02d}', b'\n\n'.join(parts) + b'\n'


def main():
    if not INSPECT.is_file():
        print('ERROR: run `make` in /workspace first', file=sys.stderr)
        return 2
    print('Reference:', run(['fmt', '--version']).decode().splitlines()[0])
    print('Default-mode ASCII test widths:', WIDTHS)
    passed = failed = 0
    for name, data, count in corpus():
        try:
            check_case(name, data, expect_match=True, expected_tasks=count)
            passed += 1
        except (AssertionError, subprocess.CalledProcessError) as e:
            failed += 1
            print(f'FAIL: {name}: {e}')
    for name, data in fuzz_cases():
        try:
            check_case(name, data, expect_match=True)
            passed += 1
        except (AssertionError, subprocess.CalledProcessError) as e:
            failed += 1
            print(f'FAIL: {name}: {e}')
    # Diagnostic for the already observed cross-task tab effect.
    tab_data = (b'word\tone two three four five six seven eight nine ten\n\n'
                b'        First second third fourth fifth sixth seventh eighth ninth\n')
    try:
        check_case('tab context (known limitation)', tab_data,
                   expect_match=False, expected_tasks=2, widths=(40,))
    except (AssertionError, subprocess.CalledProcessError) as e:
        failed += 1
        print(f'FAIL: tab structural test: {e}')
    print(f'\nPart 1 tests: {passed} PASS, {failed} FAIL (plus tab diagnostic).')
    print('Reminder: PASS is evidence only for this corpus and default GNU fmt mode.')
    return 1 if failed else 0

if __name__ == '__main__':
    sys.exit(main())
