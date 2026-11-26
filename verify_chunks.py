#!/usr/bin/env python3
"""Diagnostic only: compare whole-file GNU fmt to independently formatted candidate chunks."""
import re
import subprocess
import sys
from pathlib import Path

TASK = re.compile(r'^Task (\d+): bytes \[(\d+), (\d+)\), length (\d+)$')


def format_bytes(blob: bytes, width: int) -> bytes:
    return subprocess.run(["fmt", "-w", str(width)], input=blob,
                          stdout=subprocess.PIPE, check=True).stdout


def main():
    if len(sys.argv) not in (2, 3):
        print(f"Usage: python3 {sys.argv[0]} FILE [WIDTH]", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    width = int(sys.argv[2]) if len(sys.argv) == 3 else 40
    source = path.read_bytes()
    inspection = subprocess.run(["./inspect_paragraphs", str(path)],
                                capture_output=True, text=True, check=True).stdout
    tasks = []
    for line in inspection.splitlines():
        match = TASK.fullmatch(line)
        if match:
            task_id, start, end, length = map(int, match.groups())
            if end - start != length:
                raise RuntimeError(f"Inconsistent task length: {line}")
            tasks.append((task_id, start, end))
    if source and not tasks:
        raise RuntimeError("No tasks returned for nonempty file")
    cursor = 0
    chunks = []
    for expected_id, (task_id, start, end) in enumerate(tasks):
        if task_id != expected_id or start != cursor or end > len(source):
            raise RuntimeError("Tasks are not sequential and contiguous")
        chunks.append(source[start:end])
        cursor = end
    if cursor != len(source):
        raise RuntimeError("Task ranges do not cover entire file")
    reference = format_bytes(source, width)
    concatenated = b"".join(format_bytes(chunk, width) for chunk in chunks)
    print(f"File: {path} | candidate tasks: {len(chunks)} | width: {width}")
    if reference == concatenated:
        print("Result: MATCH (this test only)")
        return 0
    first = next((i for i, (a, b) in enumerate(zip(reference, concatenated)) if a != b),
                 min(len(reference), len(concatenated)))
    print(f"Result: DIFF | first differing output byte: {first}")
    print(f"  whole fmt: {reference[max(0, first-20):first+60]!r}")
    print(f"  per-task:  {concatenated[max(0, first-20):first+60]!r}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
