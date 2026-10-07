# Adaptive retrieval certificates

A standalone standard-library Python artifact for finite shared-world trace
refinement and exact-evidence retry cutoffs. It includes written mathematical
proofs, certificate producers, separately implemented consumers, direct finite
operational oracles, exact generators, retained cases/certificates and raw results.
No model, retriever, external API, GPU, private corpus or deployed service is used.

## Meaning of the result

Each module key denotes one static nonempty set of outcomes, shared by source
and target. Calls choose afresh from that set. Exact observations are the public
word, declared terminal label, and returned evidence. Both trace directions need
a matching observation with componentwise no-more-expensive target cost.
This is not deterministic memoization, probability preservation, or a strategy
that must choose its witness before observing a complete trace.

The general language consists of explicit forward DAGs. The retry fragment has
a fixed retrieval key, evidence union, nonempty evidence-indexed feedback and a
positive binary source horizon. Adaptive enclosing contexts need the full exit
interface and a separate certificate for each reachable entry contract. Written
retry theorems apply to finite join-semilattices; executable inputs use Boolean
masks. No proof assistant has certified the general mathematical arguments.

## Requirements and quick start

Use Python 3.10 or later from this directory. There are no third-party Python
dependencies and no network access is needed. POSIX resource limits are required
only for the bounded campaign runner. Run these commands sequentially:

```sh
python -m unittest discover -s tests -v
python -O -m unittest discover -s tests -v
python check.py retry inputs/examples/ordered.json --cutoff 1 --output scratch/ordered.json
python check.py retry inputs/examples/ordered.json --cutoff 1 --certificate scratch/ordered.json
python check.py retry inputs/examples/distance.json --cutoff 2 --output scratch/distance.json
python check.py retry inputs/examples/distance.json --cutoff 2 --certificate scratch/distance.json
python check.py retry inputs/examples/sharp.json --cutoff 2 --output scratch/sharp.json
python check.py retry inputs/examples/sharp.json --cutoff 2 --certificate scratch/sharp.json
python check.py graph inputs/examples/graph.json --output scratch/graph.json
python check.py graph inputs/examples/graph.json --certificate scratch/graph.json
python check.py least inputs/examples/distance.json --output scratch/least.json
python check.py least inputs/examples/distance.json --certificate scratch/least.json
python audit.py
```

The current 111-test suite passes locally in both interpreter modes, including
five observation-index regression groups with literal finite references. These
groups run in the existing discovery commands and scientific workflow. The
retained reference logs record the earlier 100-test suite; six additional runner
regressions check that timeout and nonzero-exit output survives while the fail
gate remains active. Their synthetic subprocess results are not campaign
measurements. The ordered, distance and
graph examples report `valid`; the sharp example reports `invalid`. The least
example reports `least-valid` and cutoff 2. Its bundle proves validity at 2 and
invalidity at 1; the rank upper bound alone would be 3.

**Exit code 0 means that the certificate was successfully checked, including
when it proves the rewrite invalid.** Read the JSON `status`; only `valid`
licenses a retry/graph rewrite. `least-valid` identifies the certified minimum.
Exit code 2 means malformed input/certificate or an I/O error; 3 means UNKNOWN
at an explicit enumeration limit. Argument errors also use 2. UNKNOWN is neither
validity nor invalidity. Proof generation always includes separate replay.
The `--cutoff` argument is required for both production and replay of retry
certificates. Output parent directories are created automatically.

## Full reproduction

This one command reruns all four groups (12 child commands) and compares both
semantic summaries and retained raw CSV/case/certificate files:

```sh
python reproduce.py --group all --out scratch/reproduction
```

Alternatively the same groups can be resumed in order:

```sh
python reproduce.py --group core --out scratch/reproduction
python reproduce.py --group relational --out scratch/reproduction
python reproduce.py --group cutoff --out scratch/reproduction
python reproduce.py --group graphs --out scratch/reproduction
```

These are alternative executions, not extra independent experiments. The cutoff
group creates missing grid files by running the relational group first. Do not
run groups concurrently. One child runs at a time, with 3500 MiB address-space
and 2700 CPU-second limits. The runner also imposes a 2700-second child wall
limit and disables core dumps. It records per-command CPU/wall times and the
cumulative maximum child RSS; task JSON records the task's own RSS. Resource
measurements vary between executions and are excluded from exact comparison.
On a child timeout, captured output and a failed execution record (exit 124)
are saved before the runner stops; the failed task is not retried or accepted.
Existing retained results are not overwritten by these documented commands.

The input generator and selection in `inputs/campaign.json` define the study.
`results/current/` contains the source-backed reference run. `results/reproduction.json`
records the later clean-extraction replay. Reproduction checks supplied raw
outputs, not only the final count of passing commands. Exact finite results are
not measurements of production speed, retrieval accuracy or workload coverage.

The prepared `.github/workflows/scientific-checks.yml` runs the material check,
retained-evidence audit and complete serial reproduction from this standalone
repository root on Ubuntu 24.04, for pushes to `main` or manual dispatch. It
keeps nonzero and semantic-mismatch gates, bounds the complete checking command
to 1,200 wall seconds (with a 15-second termination grace), retains the existing
per-child resource limits, and always attempts to upload raw output. Preparing
this workflow does not establish a successful remote run.

## Evidence and size

The two-bit grid has 82,620 declarations and 413,100 operational executions,
with 826,200 packet/cost comparisons. The graph family has 202 trees, all 40,804
ordered program pairs, and nine worlds per program. A separate support-family
census has 1,048,576 comparisons, of which 4,128 also exercise actual cover-tree
construction. The 816 fixed-seed larger declarations give 67,744 world
comparisons. These families overlap; adding counts does not create independent
workloads. Full results distinguish direct executions from downward-closure
comparisons and checks of already generated objects.

`results/current/encoding-scaling.csv` compares serialized input and certificate
sizes for horizons 1 through 12. `binary-horizons.json` records formula-derived
compact cases up to 2**60 without unfolding the source. The separate
`worst-cost-branches.json` enumerates terminal traces for all three branches of
the exact worst-vector formula, and `observation-erasure.json` executes the
three-atom exhaustion-projection boundary. This is a representation and finite
semantic comparison, not a lower bound for all proof systems. The specialized witness can still require
exponentially many worlds or evidence states.

## Input conventions

Retry masks have `bits` in 0..12, `initial`, positive `horizon`, and 1..64 outcomes
with distinct nonempty `id`, an `add` mask, and `failure` either null or a label.
`feedback` has exactly 2**bits entries: 1 means go, 2 stop, 3 both. Alternatively
`predicate` is a nonnegative integer whose bit e means stop at evidence e.
`query_cost` and `feedback_cost` are same-length nonnegative integer vectors,
defaulting to [1,0] and [0,1]. A Boolean is not an integer in the input schema.
The fixed-key/world and complete-evidence assumptions are semantic requirements,
not facts inferred about any real retrieval implementation.

Graph inputs declare `resources`, nominal evidence `tokens`, `initial`, terminal
`labels`, `modules`, `source`, and `target`. A token's list position is its nominal
identity; origin annotations may repeat. Modules have a distinct `key`, fixed
`requires` mask, outcome `adds`, and fixed `cost`. Nodes are `call`, `choose`,
`emit`, or `stop`. Calls have one successor per outcome; all successors point
forward. Stops specify a declared `label` and an owned `returned` evidence mask.
The example input and retained generated `graph-inputs.json` are complete cases.

Retry distance production/replay stops above 200,000 canonical worlds or
2,000,000 distance cells. General production/replay stops above 100,000 paths
per program and 200,000 cover nodes per challenge tree. These are structural
limits, not a bound on the total byte size of hostile JSON: loading precedes
admission, and strings/cost dimensions are not a hardened network protocol.
Use ordinary trusted local research inputs, not a public certificate service.
The uncapped mathematical completeness claim does not imply completeness under
these executable limits. Huge source horizons are handled only by retry modes;
the explicit adapter is intentionally restricted to horizon at most 12. It also
returns UNKNOWN before construction when the exact expansion would exceed the
graph schema's 32 nominal modules, 32 outcomes for one module, or 1000 nodes per
program; it never merges feedback keys or drops outcomes to fit those limits. A
non-integer or Boolean target horizon is malformed rather than resource-limited.

## Source map and trusted boundary

`src/schema.py` admits inputs. `graph_producer.py` constructs structural censuses
and cover forests; `graph_replay.py` independently reconstructs paths and checks
coverage. `retry_producer.py` constructs collapse/rank/distance witnesses;
`retry_replay.py` checks local parents, inequalities and counterexamples without
importing search. `cutoff_search.py` locates the least valid cutoff;
`cutoff_replay.py` checks its two ordinary proof components. `adapter.py` unfolds
only small capsules. `tests/oracle.py` implements direct operational semantics
and imports neither producer nor consumer. `experiments/campaign.py` selects,
executes and records finite comparisons.

The general producer and consumer each construct a call-local index by the full
public word, terminal label and returned evidence. It retains every canonical
census index and repeated route; each candidate still needs one whole-vector
cost witness and its own support checks. The consumer still reconstructs both
complete censuses and checks every positive obligation or the complete negative
opposite packet bucket. Nonstandard Python stop-label objects retain the scan.
`tests/test_observation_index.py` supplies independent literal route/tree and
nonempty-product-world references, admission/corruption/cap checks, and mutation
between calls. No route/world/cardinality is reduced, and no speedup or new
full-campaign result is claimed. A single-packet census still adds index storage.

The proof notes are `finite-programs.md`, `retry-theorems.md`,
`cutoff-certificates.md`, `least-cutoff.md`, and `boundaries.md`. Their general
proofs are written, not mechanized. `claim_evidence_ledger.csv` maps claims to
proofs, implementations, tests and raw results. `literature/` records the source
selection, read editions and precise comparison boundaries.

Producer, consumer and oracle are separate algorithms from the same substantive
AI-assisted workflow, not independent authors or blind reviewers. Admission,
Python's runtime, ordinary integer semantics and the correspondence between
written mathematics and code remain trusted. Successful replay does not prove
the absence of all common-mode errors.

## Attribution and status

Original artifact code, generated evidence and documentation use `LICENSE`
(MIT). Cited publications are not redistributed or relicensed. There are no
integrated external solver/model/benchmark internals. `external_resources.csv`
identifies scholarly and official sources and the integration mode.

AI contributed substantively to question design, proofs, code, test and
experiment design, execution orchestration, analysis, literature comparison and
writing. This is internal research, not an external submission. Human adoption,
intellectual contribution, accountability and applicable disclosure policies
remain external-use conditions. No public repository URL has been invented.
