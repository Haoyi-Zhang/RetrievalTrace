# Finite-program semantics, support covers, and contextual replacement

These are written mathematical proofs. Separate producer, replay, and operational-oracle implementations test finite instances; none is represented as a proof-assistant proof of the statements below.

## G0. Declarations and executions

Fix a finite set K of nominal module keys. Each key k has a finite nonempty outcome set O_k, a required evidence set U_k, a fixed nonnegative resource vector w_k, and an evidence addition d_(k,o) for each outcome. Token identities are immutable positions with declared origin labels. Two different identities may have the same origin label. The labels are annotations, not assertions that the cited origin is truthful or authentic.

A world rho chooses a nonempty R_k subset O_k independently for every k. The same rho interprets both programs. Every invocation chooses any outcome in its static R_k, afresh; earlier choices neither remove outcomes nor force later choices. Distinct keys remain distinct even when their declared outcome sets are isomorphic.

A program is a finite forward directed acyclic graph with one entry. Nodes are: call a key and branch on its outcome; internal finite nonempty choice; emit one observable symbol; or return a declared terminal label and a fixed evidence subset. Successors have larger indices. A call joins its outcome addition into the evidence set and adds w_k to the cost. Every call requires U_k to be owned; every return requires its returned evidence to be owned. The initial evidence is fixed by the entry contract. A structural route follows any declared branch, without yet selecting a world. It records all visited nodes and chosen edge indices, including repeated destinations reached by different edges.

A terminal trace observes (the complete emitted word, terminal label, returned evidence); it also records its nonnegative cost vector. Internal decisions are not public unless emitted. The general graph language need not return all owned evidence. The specialized retry interface does return all accumulated evidence on every terminal role.

All routes terminate because indices increase, choices and calls have nonempty branches, and only terminal nodes have no successor. Each structural route is realizable in the full world R_k=O_k. The structural set is finite, although its size can be exponential in the graph size.

## G1. Exact finite effects and evidence safety

At the entry put M=e0 and W=0. At each reachable node, take intersection of incoming guaranteed-token sets, and componentwise maxima of incoming resource vectors. Across a call outcome edge, map M to M union d_(k,o) and W to W+w_k. Other edges leave these two quantities unchanged. A structural path count is summed over edges, including parallel edges. Reject a call unless U_k subset M, and reject a return unless its returned evidence is a subset of M.

**Theorem G1.** This forward computation gives exactly the intersection of owned evidence over all structural prefixes at every reachable node, exactly the componentwise maximum prefix costs there, and exactly their multiplicity-sensitive structural path count. In an admitted graph, every enabled trace in every world respects required and returned evidence. At terminals, the union of reachable terminal labels is the exact uniform may-failure/terminal-label effect. The componentwise terminal maximum is an exact uniform vector bound, though its coordinates need not be attained on one trace.

**Proof.** Induct over node indices. Every prefix to a nonentry node has a unique final incoming edge, and its preceding prefix ends at the edge's smaller-index source. Intersection over a union of incoming prefix families is the intersection of their individual intersections. Adding one fixed set distributes over intersection: (intersection_i E_i) union d = intersection_i(E_i union d). Addition of one fixed vector preserves coordinatewise maxima. Counting sums the disjoint route-and-edge families, even when two outcome edges share a destination. These facts establish all three recurrences and their exactness. The admission conditions then hold on every structural prefix, hence every world-enabled prefix. Conversely every structural prefix is enabled in the full world, so no uniformly possible label or coordinatewise maximum is spurious. Coordinates can choose different maximizing prefixes, which explains the lack of joint attainment. QED.

This exactness uses fixed edge additions and charges, and the full world being allowed. It is not an exact analysis for arbitrary state-dependent transfer functions, mandatory-outcome contracts, or correlated restrictions across keys.

## G2. The two-sided resource-sensitive trace relation

Write match(p,q) when p and q have the same observation and cost(q)<=cost(p) componentwise. For programs P (source) and Q (target), P >= Q means, for every allowed world rho:

* target safety: every q in Tr_rho(Q) has some p in Tr_rho(P) with match(p,q);
* source coverage: every p in Tr_rho(P) has some q in Tr_rho(Q) with match(p,q).

The existential choices are per completed trace and per world; they need not agree between directions. They are not a causal matching strategy or a bijection. This relation combines no-new-observation with no-lost-observation and compares individual matching costs, rather than merely worst costs.

**Theorem G2.** The relation is a preorder. It preserves exact may reachability of observable packets, exact declared failure observations, and every componentwise source budget in the target.

**Proof.** Reflexivity chooses each trace itself. For transitivity P>=Q>=R, fix one world. For an R trace r, target safety of Q>=R gives q with the same observation and cost(r)<=cost(q); target safety of P>=Q gives p with cost(q)<=cost(p). This proves safety of P>=R. For a P trace, compose the two coverage witnesses in the same order, obtaining cost(r)<=cost(q)<=cost(p). Observations are equal by transitivity of equality. Thus coverage also holds. The two directions imply equality of observation sets. If every P trace has cost<=B, any R or Q trace obtains a dominating P trace from target safety and therefore obeys B. Nonnegative scalar prices applied to these matched vectors preserve their order. QED.

A comparison of worst cost alone would not prove the per-trace property. Nor does proving each scalar-price problem with a different witness prove that one componentwise-compatible witness exists. See the boundary examples.

## G3. Support and minimal enabling worlds

For a structural trace t define its support S_t(k) to be the set of outcomes actually used at key k. A key never called has empty support.

**Lemma G3.** A structural trace t is enabled in rho exactly when S_t(k) subset R_k for every k.

**Proof.** Each outcome choice in an enabled trace belongs to the corresponding R_k, proving necessity. Conversely every chosen outcome is available when its call is reached if the support is included. The graph's internal branches, evidence additions, and costs then replay exactly. Availability does not depend on earlier choices because the world is static. QED.

Define Min(t) as the worlds with R_k=S_t(k) whenever S_t(k) is nonempty, and R_k an arbitrary singleton whenever S_t(k) is empty. These are precisely the inclusion-minimal nonempty worlds enabling t. There are product_(k:S_t(k)=empty)|O_k| such worlds, with the empty product one.

**Theorem G3a (support-cover criterion).** For a challenged structural trace t and a finite family C of observation-and-cost-compatible opposite-program traces, every world enabling t enables at least one member of C if and only if every world in Min(t) enables at least one member of C.

**Proof.** The forward direction specializes to minimal worlds. For the reverse direction, take an arbitrary enabling world rho. At a used key keep exactly S_t(k); at an unused key choose any one element of nonempty R_k. This yields mu in Min(t) with mu subset rho. By hypothesis a candidate c is enabled in mu. Its support is included in mu by G3 and therefore in rho, so c is also enabled in rho. QED.

One candidate may work in one minimal world and a different candidate in another. The criterion is not equivalent to finding a single global candidate, nor to taking the union of candidates' supports. Keys unused by the challenge cannot simply be ignored because every world must give those keys some nonempty outcome set.

## G4. Positive and negative certificates

A census is the complete canonical list of structural traces, obtained by depth-first traversal in node/outcome order. A positive certificate carries both censuses and one obligation for every challenged trace in both directions. The compatible-candidate list is computed and checked from the observations and vector costs, not trusted as an unchecked premise.

Each obligation has a finite cover tree. Initially used keys are fixed to the challenged support and unused keys are unfixed. An internal node chooses a previously unfixed key and has exactly one child for every declared outcome, fixing that key to the corresponding singleton. A leaf names a compatible candidate whose entire support is included in the fixed components; its support must be empty at every still-unfixed key. The leaf therefore works under every remaining singleton completion.

**Theorem G4 (cover-tree exactness).** An accepted tree covers every member of Min(t). Conversely, whenever the support-cover criterion holds, such a finite tree exists.

**Proof.** Induct on the tree. A valid leaf's support is included in every completion of its partial assignment. At a split, the complete set of outcome children partitions the remaining singleton completions at the chosen key; the induction hypothesis covers each part. Thus the root covers all minimal worlds. Conversely split all unused keys in any fixed order. Each resulting leaf is a complete minimal world; choose a compatible enabled candidate there, whose existence follows from the criterion. This finite full tree satisfies all rules. Earlier leaves merely compress this full tree. QED.

A negative certificate names one challenged trace and one nonempty enabling world. Replay recomputes the complete opposite census and checks that no observation-and-cost-compatible trace has support included in that world.

**Theorem G4a (certificate soundness and finite completeness).** Without explicit resource limits, the producer and replay format decide P>=Q for the finite admitted graph language. Positive certificates prove the quantified relation, and negative certificates prove its failure.

**Proof.** Complete census replay establishes that no structural trace has been omitted or invented. Positive obligations, G4, G3a, and G3 then establish both quantified directions for all worlds. A negative world enables its challenged trace and no matching opposite trace, directly refuting one direction. For completeness, the structural censuses and minimal-world products are finite. If all obligations hold, full cover trees exist by G4. If an obligation fails, some minimal enabling world is uncovered by G3a and is a negative certificate. QED.

The implementation saturates path counts before enumeration and has explicit path/tree limits. Exceeding a limit reports UNKNOWN. Finite mathematical completeness does not imply that all accepted declarations fit those limits.

## G5. Complexity of the explicit support-cover subproblem

**Theorem G5.** Given explicit finite outcome alphabets, one support vector, and a list of candidate support vectors, deciding support cover is coNP-complete, already for binary outcome alphabets.

**Proof.** A failure is witnessed by one minimal enabling world, represented by a singleton choice at each unused key. Its size is polynomial in the explicit alphabet/support input, and testing that every candidate is disabled is polynomial. Thus the problem is in coNP.

For hardness reduce unsatisfiability of a CNF formula. Make one unused binary key per propositional variable and let the challenge have empty support everywhere. Its minimal worlds encode total truth assignments. For each non-tautological clause, add a candidate whose support requires exactly the unique falsifying value of each variable appearing in that clause and is empty elsewhere. A candidate is enabled exactly when the assignment falsifies that clause. Consequently the candidates cover every minimal world precisely when every assignment falsifies some clause, i.e. when the CNF formula is unsatisfiable. Tautological clauses can be removed; an empty clause is represented by an empty-support candidate, which covers all worlds. This is a polynomial reduction. QED.

This is a standard coverage/tautology reduction and an explicit baseline complexity fact, not the claimed new scientific principle. It does not establish a tight complexity classification in terms of succinct program graphs, whose trace census can itself be exponential.

## G6. Conditional witness minimization

The graph producer orders all challenges by (number of visited nodes, direction, canonical trace index). At the first uncovered challenge, it returns the first uncovered minimal enabling world in canonical unused-key outcome order. All earlier challenges have been proved covered during search.

**Proposition G6.** This producer selects a shortest structural challenged trace among all failures of the declared pair, using the stated tie breaks. Its returned world is inclusion-minimal among nonempty worlds enabling that fixed trace. These are conditional, ordered objectives, not simultaneous global minimization of world cardinality and trace length.

**Proof.** If any earlier challenge failed, the exhaustive finite cover search would have stopped there, by G3a and G4. The selected trace therefore has minimum length in that order. In its minimal world every used component equals its necessary support, and every unused component is a nonempty singleton; no component can shrink while preserving both nonemptiness and enablement. QED.

Negative replay verifies invalidity, not the producer's search history or minimality of the challenge. A consumer needing certified optimality must additionally replay positive covers for all earlier challenges. The delivered invalidity certificate deliberately does not claim that stronger property. The specialized collapse rule instead guarantees minimum retrieval-world cardinality two, and within that class has a separate length characterization. The two orders need not agree.

## G7. Finite contextual replacement

An exit interface contains its terminal/control tag and every evidence/state component the continuation may inspect. Public words emitted by a component are also compared. Assume a finite acyclic context whose next control point is a function only of that interface, whose module-world keys are interpreted in the same rho, and whose future availability does not depend on hidden component history. Costs combine additively. Every reachable component entry contract is verified, including its exact initial evidence. The context may invoke finitely many certified components and may select their keys from earlier public exits.

**Theorem G7.** Replacing each such component by a two-sided refining component preserves the enclosing finite program relation.

**Proof.** Fix a world and one complete context trace in either challenged direction. Decompose it at component entry and exit boundaries. Context-only segments are copied. At a component use the appropriate local trace witness in this same world and entry contract. It has the same emitted subword and the same full exit interface, so the context takes the same following control choice and starts the next segment in the same relevant state. Static relations make future choices available regardless of which hidden component path supplied that exit. Continue in topological order; there are finitely many invocations. Concatenating equal subwords and equal terminal interfaces yields equal global observations. Summing the componentwise cost inequalities and the identical context costs gives the required global inequality. Repeat in the other direction. QED.

A public projection alone is insufficient if the context can inspect hidden final evidence. The proof also fails for consumptive external streams, hidden time-dependent worlds, and a context that reads the replaced component's private iteration count. This theorem therefore justifies the fixed-key retry capsules inside an adaptive outer graph only at explicitly declared full interfaces; it does not justify arbitrary rewriting of an unrestricted adaptive query loop.


## G8. Renaming and observable projection

A consistent bijection on token identities, nominal keys, outcomes within each
key, terminal labels and public symbols transports every declaration field and
branch together. Map each world component and every step through these
bijections. Union, subset, branching, fixed charges and ownership commute with
that transport. Thus traces correspond bijectively with equal costs and renamed
observations; transporting matching witnesses proves and reflects refinement.
This is not permission to merge distinct keys or distinct evidence tokens.

For any fixed function h on complete observations, exact-observation refinement
implies refinement after projection through h, using the identical witnesses
and unchanged costs. Reflection fails: two distinct constant-return programs
at zero cost become equivalent when h maps their packets to one value. This
implication for a fixed pair is not a characterization theorem across horizons.

## G9. Bounded retry expansion correspondence

For a positive explicit horizon h, construct a retrieval node for each layer i
and entry evidence e reachable in the full declared capsule, with 0<=i<h.
All retrieval nodes call the same nominal key and charge q. A failure edge
returns its label and joined evidence immediately. A success edge enters a
feedback node indexed by that joined evidence; it calls the one shared feedback
key for that evidence, adds no evidence, and charges b. Stop returns success;
go enters layer i+1 or returns exhaustion when i+1=h. Return nodes may be shared
only when their full interfaces agree. Order retrieval then feedback nodes per
layer, and all terminals after the layers; all edges are forward.

Induct on the number of attempted retrievals. At each retrieval-node entry,
the expanded execution and capsule have equal evidence and the same accumulated
cost and attempt count. A retrieval choice is available in exactly the same
shared relation in both representations. Its failure edge agrees immediately;
its success edge joins the same addition and calls feedback at exactly the same
evidence. Feedback availability and its charge therefore agree. Stop and final
go have the same complete terminal packets, while a nonfinal go restores the
induction invariant at the next layer. Reversing these local steps maps every
expanded trace to a capsule execution; there are no extra exits or choices.
The constructed retrieval node needs only the fixed entry evidence, each
feedback node has the evidence encoded in its index on every incoming path,
and terminal returns disclose exactly their owned evidence. Hence admission
holds. Shared graph worlds and capsule worlds correspond componentwise,
including irrelevant unused feedback keys. Both directions of trace refinement
therefore agree between two expansions. This is the uncapped mathematical
construction. The delivered adapter first validates the target horizon as a
non-Boolean integer in 1..H and returns UNKNOWN if the source horizon exceeds
`max_horizon` (default 12), independently of reachable graph size. For example,
a zero-bit, horizon-13 capsule with one successful outcome and stop-only feedback
has a three-node expansion on either side, but exceeds the default horizon cap.
For horizons within the cap, the adapter preserves every nominal feedback key and
retrieval outcome, and returns UNKNOWN rather than a smaller graph if the exact expansion
would exceed the graph schema's module, outcome, or node ceilings. The node
ceiling is enforced while unique states are discovered. This is a written
correspondence proof, not an assertion that huge horizons are expanded or that
Python is verified.

## G10. Compatible-candidate reduction

Fix a challenge and compute cost/observation compatibility before reduction.
On used keys a candidate needs support included in the challenge's support.
On an unused key it needs at most a singleton support. A failed test means it
is enabled in no minimal enabling world and can be removed. A surviving
candidate defines the cylinder of singleton assignments meeting all its
coordinate constraints. If cylinder Z_c is contained in cylinder Z_d, removing
c leaves the union of cylinders unchanged. Thus cover validity is preserved.
The argument is local to that challenge and direction: changing either changes
compatibility, so this is not a global program-path deletion theorem. QED.
