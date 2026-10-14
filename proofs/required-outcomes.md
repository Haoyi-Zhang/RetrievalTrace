# Retry collapse with required availability

This is a written extension of the finite static contract, not a claim that
modal specifications, environment restrictions, BFS, or certifying algorithms
are new. The original unrestricted theorems and retained campaign remain valid.
The executable protocol is `required-outcomes-v1` with an explicit `capsule`
object and a sorted list `required_outcomes` of indices. A legacy capsule does
not carry this stronger premise. No adapter to an external retriever is proved.

## Assumptions and quantifiers

Use exactly the finite join-semilattice, initial evidence e0, persistent fresh
retrieval choice, nonempty feedback sets G(e), private internal events, exact
successful/exhausted/failure evidence, failure labels, and fixed nonnegative
retrieval/feedback cost vectors of retry-theorems.md. Let O be the finite
declared outcome set and M a declared subset. Admitted worlds satisfy
`empty != R subseteq O` and `M subseteq R`; feedback restrictions are unchanged.
An outcome in M must remain *available*, not be selected. Neither fairness,
independence, history dependence, probabilistic accuracy nor forced execution
is added. All trace matches may depend on the fixed world and challenged trace.
The two-sided relation retains the same whole-vector cost witness as before.

For each outcome o write A_o=e0 join d_o. S and F are success/failure indices;
lambda_f is the failure label. C consists of c in S with go in G(A_c).

## Exact required-representative law

For every H>=2, Retry_H refines Retry_1 in every admitted world iff BOTH hold:

1. For every c in C and s in S, A_c join A_s is in
   `{A_c,A_s} union {A_m: m in M intersect S}`.
2. For every c in C and f in F, there is a g in `{f} union (M intersect F)`
   with `lambda_g=lambda_f` and `A_g=A_c join A_f`.

The failure label equality is essential: an always-available failure with a
different label cannot represent the challenged packet. Required successes
cannot represent failures even with the same evidence. Outcome identities
remain distinct; equal values may be valid representatives without being equal
indices. When M is empty the two clauses are exactly the old comparability and
absorption conditions. Their failure is a real semantic counterexample, not an
input-admission failure.

### Sufficiency

Fix one admitted (R,B). After the first continuing successful retrieval the
current evidence equals A_c for some *enabled* success c. Inductively suppose
this holds with current evidence A_c and go in B(A_c), hence c in C. If the
next outcome is success s, clause 1 supplies an enabled representative of the
new evidence: c or s is enabled because it was selected, and every required
representative is enabled because M subseteq R. If execution continues, its
representative is again in C. Importantly, the representative need not have
been selected earlier; the original already-seen invariant would be too strong.

A successful terminal packet can therefore be produced by selecting its
representative directly and choosing the same stop feedback. An exhausted
packet has a representative with go available and is obtained after one
attempt. A failure after a continuing prefix uses clause 2 and its required
same-label representative; a first-attempt failure represents itself. Thus
every source packet has a target match. Direct success/exhaustion costs q+b
and direct failure costs q, componentwise no more than the source's fixed
nonnegative additive charges. Zero coordinates cause no exception.

For target safety, immediate success/failure is also an H-attempt source
execution. A one-attempt exhausted packet can be pumped to H by repeating
its enabled success and go at the same evidence, by join idempotence and
persistence. The target costs no more. This proves both quantifier directions.

### Necessity and counterworld

If clause 1 fails at (c,s), use R=M union {c,s} and full declared feedback G.
The first success c can continue. Choosing s next reaches J=A_c join A_s.
If stop belongs to G(J), stop after this second retrieval; otherwise repeat s
and go to exhaust at H. No success in R has singleton value J, exactly by the
failed clause; no direct failure can match the terminal tag. The one-attempt
target has no matching packet, regardless of its lower costs.

If clause 2 fails at (c,f), use R=M union {c,f}. Choose c/go then f; the
result is (fail:lambda_f,J). No enabled one-attempt failure has both that label
and that evidence. Success/exhaustion tags cannot match. This is a coverage
counterexample for every H>=2. A source exhaustion witness is stored as two
run-length pairs, not expanded to its binary-encoded horizon.

Each negative pair world adds at most two *optional* indices to M; its total
size is at most |M|+2. This is not a minimum-cardinality certificate and not
a lower bound on encodings, bytes, all modal models, or all policies. Required
indices cannot be discarded to claim a two-outcome total bound.

## Arbitrary cutoff

The pointwise adjacent-horizon proof in cutoff-certificates.md fixes one world,
so its exact K+1 versus K equivalence remains true under this restriction of
worlds. The rank upper bound is unchanged (not necessarily tight for a given M).
For a failing cutoff take an adjacent bad trace and deterministic feedback as
in that proof. Retain M as well as the retrieval support of this trace, removing
only other optional outcomes. Its bad packet still occurs. Removing optional
outcomes cannot create a new K-attempt target packet. Therefore a negative
world uses at most K+1 optional outcomes and at most |M|+K+1 total outcomes.
The determinization argument must retain the bad trace's consistent actions;
it does not mean that the original G was deterministic. No assumption that a
required outcome was executed is used.

For sharpness, take K+1 independent atoms with optional singleton successes,
and any finite number of distinct required successes adding no new evidence.
Use empty e0 and always-go feedback. With at most K optional indices every
nonempty reachable union is obtainable in at most K attempts and can be pumped;
the all-initial packet, if available, also needs only one. With all K+1 optional
indices their full union needs K+1 attempts. Thus K+1 optional indices are
necessary in this family; the required indices are additionally present in
every admitted world. This is a representation-independent bound on outcome
support in this specified semantic family, not a storage lower bound.

The complete positive deterministic census has
`2^a * sum_{j=lo..min(K+1,m-|M|)} choose(m-|M|,j)` rows, where a counts
ambiguous G entries, and lo=0 for nonempty M, otherwise lo=1. Each row uses the
original positive-length continuation distances, including the fresh root,
parent descent, reachability closure and terminal minima. All feedback fields,
even unreachable ones, remain quantified. Existing 200000-world/2000000-cell
ceilings return UNKNOWN, never a semantic verdict. The consumer implements its
census separately from producer enumeration and imports no producer/search.
Legacy distance-row replay is a shared, explicitly trusted consumer component.

## Source and execution boundary

May/must availability is standard modal specification; modal/thorough
refinement and label products already provide much broader theories. This
specialization does not replace those theories, prove a new general trace
relation, or establish priority over all related work. Its specific object is
the two finite representative clauses for this exact retry interface, and the
optional-support correction in a horizon-independent certificate. Written
arguments and exhaustive finite differential checks are not mechanization.
