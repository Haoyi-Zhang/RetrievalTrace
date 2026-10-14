# Aggregate-output managed execution

The successful compiler invocation records 0.10083849998773076 seconds of parent
wall time. The separate managed launch records 2.3283992999931797 seconds;
the in-Main clock records 2.2949362 seconds wall, 2.25 seconds process CPU and
35,692,544 bytes peak working set. `records/` and `logs/` retain command receipts
and original streams, including the unsuccessful compilation attempt. Only
machine-specific command/cwd prefixes are redacted in receipt views.

The output has 16,208 input rows and 17,232 final contract verdicts. It does not
store individual world verdicts. `results/managed-pointwise/` separately retains
the full per-world conformance stream; its additional serialization is outside
the timing protocol here.

`binary/interpreter.bin` contains the exact retained executable bytes as data.
The original input remains `../required/cases.jsonl`. The matching C# source
body is in `../portable-replay/historical-source/native/OwnedRetry.cs.snapshot.txt`.
Executable, input and source identities were captured in the frozen-after
inventory; the compiler/launch receipts have no pre-execution hashes. Host
inventory was observed at 2026-10-14T04:11:37.417001+00:00, after the build.
