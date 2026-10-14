# Required availability in a finite retry contract

The original contract permits every nonempty retrieval restriction. Some owned
finite modules instead guarantee that a documented fallback outcome is always
available. This extension accepts an explicit stronger premise, not an inferred
property of a deployed retriever. No failure probability or fairness is assumed.

The input is an object with exactly three fields: `protocol` must be
`required-outcomes-v1`, `required_outcomes` is a sorted distinct list of integer
outcome indices, and `capsule` is the original retry declaration. Empty required
sets are permitted and recover the original semantics. The separate entry
prevents legacy admission from silently discarding the stronger premise.

`python required_check.py produce input.json 1` writes a certificate to stdout.
`python required_check.py verify input.json 1 --certificate proof.json` replays
one. Exit 0 means successful construction/replay, including a checked INVALID
rewrite; only status `valid` licenses rewriting. This entry uses exit 2 for
UNKNOWN and exit 3 for MALFORMED (unlike the legacy CLI); argument errors use 2.
Its finite parser is not a hostile network service. There is no installation,
deployment mutation, service access or compiler transformation in this CLI.

The mathematical argument is `proofs/required-outcomes.md`. It replaces the
old already-selected representative by an enabled representative. Mandatory
successes can fill missing singleton joins. Mandatory failures can represent
accumulated failure evidence only with the same label. A negative collapse
world contains all required outcomes plus at most two optional outcomes. For
cutoff K the bound is K+1 optional outcomes, not K+1 total outcomes. The bound
is about support, not records, bytes or universal modal-system complexity.
Positive rows retain all required indices and feedback fields. Identity/rank
paths, local distance checks and UNKNOWN ceilings remain explicit.

## Reproducible finite selection and total costs

`experiments/required_campaign.py` fully enumerates the declared one-bit and
two-bit-join families and uses fixed seed 49049 for 512 higher-dimensional
inputs. The exact family definitions are code, not a claim of natural workloads.
Every selected input, certificate and contract verdict is in `cases.jsonl`;
`world-checks.csv` retains each world/cutoff comparison. `summary.json` binds the
original generated files; `summarize_required.py` consumes and verifies those
bindings, decision/phase accounting and paired cohorts before writing analysis.

The 872 newly valid one-attempt cases compare *different contracts* (required
versus unrestricted). This is semantic expressiveness, not a fair runtime
baseline or a fix to the old theorem. The cost comparator instead uses exactly
the same required contract, complete observations, charges and cutoff. It gets
the deterministic small-world theorem and common identity/rank shortcuts too.
It computes ordinary adjacent packet/cost reachability and recomputes after a
serialized status receipt. Both arms give the same mathematical decision
guarantee; ordinary recomputation is not a separate certified implementation.
Certificate construction, JSON, replay and admission are included, not hidden.

A fixed modular selection of 31 seeded inputs supplies 93 input/cutoff pairs;
five alternating-order repetitions per arm give 930 rows. All 31 collapse,
15 distance and 47 rank pairs are retained. Certificate/ordinary median ratios
are 0.3722, 0.5227 and 1.1260 by mode, but 8 collapse, 1 distance and all 47
rank pairs are slower. No exact timing ties occur. CPU per tiny arm often
quantizes to zero under GetProcessTimes: raw zeros are preserved and are not
speed or energy measurements. Total study CPU is measured separately. There
are no confidence intervals or representative-workload success rates.

## Complete compiled operational cross-check

`native/OwnedRetry.cs` is a separately written full bounded interpreter:
it enumerates every admitted R and nonempty feedback restriction, executes
horizon seven and each requested K with fresh choices, preserves evidence,
labels and whole cost vectors, and compares both trace directions. It does not
decide using the representative predicate. This cross-check shares the input
specification and developer; it is not independent peer review or verified code.
The owned campaign ceilings are four bits, six outcomes and horizon seven.
Its JSON reader is for these generated benign inputs, not adversarial admission.

On Windows with the installed .NET Framework compiler:

```
csc /nologo /optimize+ /r:System.Web.Extensions.dll /out:OwnedRetry.exe native\OwnedRetry.cs
OwnedRetry.exe results\required\cases.jsonl managed-world-decisions.jsonl
```

Use Windows backslashes: the legacy C# compiler interprets some slash-separated
paths as compiler options.
The executable is compiled managed code, CLR 4.0.30319.42000/JIT, not native AOT.
The reported `decisions` in its raw summary counts world/cutoff decisions
(350,141), while 17,232 is the contract-level count. It processed all 16,208
inputs and 294,447 worlds with zero mismatch. The 2.295-second wall,
2.250-second CPU and 35,692,544-byte peak working set include parsing, runtime
and JIT. Parent launch-to-exit was 2.328 seconds; successful compilation took
0.101 seconds separately. Python and C# timings are not an apples-to-apples
performance comparison. No third-party implementation, retriever, service,
LLVM/AOT pipeline, storage engine, or native production system was validated.

The aggregate-output run verifies final conjunctions and world counts. A separate
untimed pointwise run in `results/managed-pointwise/` compares every world/cutoff
coordinate, both packet counts and all 350,141 relations to the Python records.
It also compares all 17,232 final verdicts. The historical process timings above
do not include this additional world-stream serialization.

```sh
python -B native/check_managed_worlds.py results/managed-pointwise/worlds.csv results/managed-pointwise/decisions.jsonl
```

## Environment and scientific limits

Actual environment: Intel Core i7-12700KF, 12 cores/20 logical processors,
Windows 11 Pro 10.0.28000 64-bit, CPython 3.12.14 and linked SQLite 3.53.1.
SQLite is only runtime inventory; no database was exercised. Python wall clock
is QueryPerformanceCounter, CPU clock GetProcessTimes, each reporting 1e-7 s
resolution. Per-arm process-tree CPU/RSS and background load isolation are not
measured. The portable Windows full-task replay uses only parent timeouts;
the historical POSIX caps/RSS numbers retain their separate provenance.

May/must availability, thorough refinement, trace relations, BFS and local
distance certificates overlap standard mechanisms. Primary-source comparison
supports the stated distinctions, not a firstness/fulltext-completeness claim.
No proof assistant checks the new law. Independent proof review, broader
nearest-specialization search, a real admissible module contract, production
integration and current official venue-policy verification remain necessary.
