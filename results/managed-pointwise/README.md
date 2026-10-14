# Pointwise managed conformance

A fresh installed-.NET-Framework build of `native/OwnedRetry.cs` evaluates the
16,208 frozen required-availability inputs. `worlds.csv` stores every complete
input/cutoff/retrieval-mask/feedback key, both terminal-packet counts and the
relation verdict. `decisions.jsonl` stores final conjunctions and world counts.
All 350,141 relation/count pairs and 17,232 final verdicts match the independent
Python operational records. This is a functional run; its output protocol is
separate from the aggregate-output process-cost observations.

```sh
python -B native/check_managed_worlds.py results/managed-pointwise/worlds.csv results/managed-pointwise/decisions.jsonl
python -B -O native/check_managed_worlds.py results/managed-pointwise/worlds.csv results/managed-pointwise/decisions.jsonl
```

`execution.json` retains actual compile/run exits, commands and source/input
identities captured before and after execution. `interpreter.bin` is a
byte-identical data copy of the produced executable. File binding can additionally
be checked with `--source-binding-receipt results/managed-pointwise/file-bindings.json
--managed-executable results/managed-pointwise/interpreter.bin`; the checker
hashes but never executes that data. `tests/` retains the 142-test normal and
optimized runs, including all 23 pointwise comparison regressions. One control
flips a world verdict while the contract remains invalid and must be rejected.
