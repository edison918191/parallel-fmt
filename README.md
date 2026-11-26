# Stage 1: GNU fmt paragraph candidate inspector

This project currently **does not format text** and **does not use Pthreads**.
It scans blank-line-separated candidate chunks and records file byte offsets.
These boundaries are not guaranteed to match GNU fmt semantics for indentation, tabs, tagged or prefixed paragraphs.

Compile and run **inside the Ubuntu 22.04 container**:

    make
    ./inspect_paragraphs tests/input.txt
    fmt -w 40 tests/input.txt > tests/reference.txt

Expected number of candidate tasks: 3.

The next step is to test and refine the safe boundary rules against GNU fmt 8.32.
