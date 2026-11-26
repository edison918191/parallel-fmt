#!/usr/bin/env python3
"""Check Task tab history. Not a GNU fmt output-equivalence test."""
import pathlib
import re
import subprocess
import tempfile


def check(blob, expected):
    with tempfile.TemporaryDirectory() as tmp:
        path = pathlib.Path(tmp) / 'input.txt'
        path.write_bytes(blob)
        out = subprocess.check_output(['./inspect_paragraphs', str(path)], text=True)
    observed = re.findall(r'Context Task \d+: tabs_before=(true|false)', out)
    assert observed == expected, f'Expected {expected}, got {observed}:\n{out}'


check(b'alpha beta\n\ngamma delta\n', ['false', 'false'])
check(b'word\tone\n\n        First second third\n', ['false', 'true'])
check(b'alpha\nbeta\tword\n\nnext\n\nlast\n', ['false', 'true', 'true'])
print('PASS: Task tabs_before snapshots (3 tests)')
