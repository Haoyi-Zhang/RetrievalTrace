# Retry collapse and observation-complete cutoffs

These are complete written mathematical arguments over the specified finite semantics. The implementation and exact small oracles exercise them; they are not a proof-assistant mechanization of the quantified theorems.

## R0. The capsule

Let (L, join, <=) be a finite join-semilattice and let e0 in L be its initial evidence. There is a nonempty finite retrieval outcome set O=S disjoint-union F of successes and failures. Each outcome o adds d_o; write A_o=e0 join d_o. A failure f has a declared tag lab(f). Different failure outcomes may share a tag. Every evidence e declares a nonempty feedback set G(e) subset {go,stop}. G need not be deterministic or monotone.

A world is a nonempty R subset O and independently chosen nonempty B(e) subset G(e) for every e. Both are static. Repeated calls choose afresh from the same relations. Retrieval costs q in N^r and successful feedback costs b in N^r are fixed across iterations and outcomes.

Retry_H, H>=1, starts with e0. An attempt chooses o in R and replaces e by e join d_o. If o is a failure, return (fail:lab(o),e) immediately, without feedback for this attempt. Otherwise choose an action in B(e). A stop returns (ok,e). A go continues unless this was attempt H, in which case it returns (exhausted,e). All returned evidence, including failure and exhaustion evidence, is observed exactly. There are no public emissions inside the capsule. Collapse is Retry_1, mapping its go to exhausted.

These are fixed-key retries. A surrounding finite adaptive program may select the capsule's key and entry evidence using earlier results, but the key is fixed during this capsule. Every reachable entry contract must satisfy the applicable certificate.

## R1. Target safety is automatic

**Lemma R1.** In every world and for all 1<=K<=H, every trace of Retry_K has an observation-identical trace of Retry_H with componentwise at least its cost.

**Proof.** Copy a target success or failure trace; it terminates in at most K attempts and therefore before the larger horizon expires. For a target exhaustion trace, let e be its final evidence and s its last successful retrieval outcome. Because d_s<=e, repeating s leaves e unchanged. The final target go proves go in B(e). Repeat s and go another H-K times. Static R keeps s available, idempotent join keeps e unchanged, and static B permits every repeated go. The source exhausts with the same packet. Every added retrieval/feedback has nonnegative cost. QED.

The hard requirement is source coverage, not this safety direction.

## R2. Exact one-attempt law

Define C={c in S : go in G(A_c)}. These are success outcomes that can continue on their own evidence, not all successes and not only outcomes that must continue.

**Theorem R2.** For H>=2, Retry_H uniformly refines Collapse with the two-sided cost relation if and only if:

(A) for every c in C and s in S, A_c and A_s are comparable;

(B) for every c in C and f in F, A_c<=A_f.

For H=1 the transformation is identity without these conditions.

**Sufficiency.** Fix an arbitrary world. Lemma R1 proves safety. For coverage maintain this invariant after every successful nonstopping prefix: the accumulated evidence equals A_c for some success c already retrieved on that prefix, and go belongs to the actual B(A_c). In particular c belongs to C.

For the first success followed by go, its own outcome witnesses the invariant. Suppose the invariant holds with evidence A_c and the next outcome is a success s. By (A), A_c join A_s equals A_c or A_s. Thus the new evidence is again the singleton value A_v of an outcome v already retrieved on this path. If feedback goes, the actual go at this value establishes the invariant with v. If it stops, Collapse can select v (which is in R) and then select this same stop at A_v. This gives exactly the source's (ok,A_v). Notice that v need not be the last retrieved outcome: nondeterministic feedback may previously have continued at its value.

A first-attempt failure is copied directly. A later failure f follows an invariant state A_c; (B) gives A_c join A_f=A_f, so Collapse selecting f returns the same failure tag and evidence. If the source exhausts, its final go and invariant representative v allow Collapse to select v and go, returning exactly (exhausted,A_v).

Each target match uses one retrieval and at most one feedback. A successful source terminal used at least one of each; a failing source used at least one retrieval and at least zero feedbacks. Componentwise cost domination follows from nonnegativity of q and b. The fixed world was arbitrary.

**Necessity of (A).** If c in C and s in S have incomparable values, choose R={c,s} and choose B(e)=G(e) everywhere. Retrieve c and choose go. Retrieve s next. Their join J=A_c join A_s differs from both A_c and A_s. If stop is allowed at J, stop at attempt two. Otherwise nonemptiness makes go allowed; repeat s and go until H and exhaust. In either case the source returns evidence J. Collapse in this two-outcome world returns only A_c or A_s, so no exact match exists.

**Necessity of (B).** If c in C and f in F violate absorption, use R={c,f} and full feedback G. Retrieve c/go and then f. The returned packet is (fail:lab(f),A_c join A_f), whose evidence differs from A_f. Collapse's failure choice f has the wrong evidence, while c has no failure tag. Coverage fails. QED.

**Corollary R2a (minimal retrieval-world cardinality).** Every invalid one-attempt collapse has a counterworld with two retrieval outcomes, and no singleton retrieval world is invalid.

**Proof.** The necessity constructions use two outcomes. In a singleton success world, every accumulation is A_s; all source terminal actions are available to Collapse and its go can be pumped by R1. A singleton failure world stops on its first attempt in both programs. Costs have the required order. QED.

This cardinality counts retrieval outcomes, not all the feedback-key outcome entries in a world. The two-outcome construction uses the full declared feedback relation.

Within two-outcome counterworlds the shortest mismatching source trace has two retrievals if some violated failure pair exists or some incomparable continuing pair has stop available at its union. Otherwise it has H retrievals and can be stored as two run-length segments. Comparable success pairs and absorbed failure pairs cannot fail by the sufficient direction applied to the restricted signature. An incomparable pair has no new evidence before its second retrieval; without stop at that union its first mismatching terminal is exhaustion at H. This proves the stated minimum among cardinality-two worlds, not global shortest trace length over larger worlds.

## R3. Positive continuation distances

Fix one world. A continuing path is a positive-length sequence of successful retrievals whose feedback actions are all go. It has an exact final evidence value. Define m_go(e) as its minimum positive retrieval length, or infinity if none exists. Similarly m_ok(e) is the minimum length of a trace stopping with (ok,e), and m_fail(f,e) is the minimum length of a trace failing with label f and evidence e. Here paths are considered without a horizon cutoff; every finite terminal path has its ordinary length.

**Lemma R3.** Retry_H has (ok,e) or (fail:f,e) exactly when the corresponding minimum is at most H. It has (exhausted,e) exactly when m_go(e)<=H.

**Proof.** The success/failure statements are the definition of bounded execution. An exhaustion trace is a continuing path of length H, so it bounds m_go. Conversely, take a shortest positive continuing path of length m<=H. Repeat its final success and go at its final evidence, as in R1, until its length is H. It then exhausts with the same evidence. QED.

**Lemma R3a (coverage versus observations).** For 1<=K<H, Retry_H refines Retry_K in a fixed world exactly when every source terminal packet occurs in the target.

**Proof.** Refinement implies coverage of packets. Conversely R1 gives safety. A source success/failure trace ending at j<=K is copied exactly. If j>K, any observation-identical target trace has length at most K, so fewer retrievals and no more feedbacks than the source (failure paths have one fewer feedback than retrievals). A source exhaustion has H retrievals and feedbacks, while its target match has K of each. Thus packet coverage supplies cost-compatible trace coverage. QED.

Fixed per-call nonnegative costs are used here; arbitrary outcome-dependent or state-dependent prices are outside this lemma.

## R4. The adjacent-horizon theorem

**Theorem R4 (adjacent horizon suffices).** Fix K>=1. For every world and every H>K,

    Retry_H >= Retry_K  iff  Retry_(K+1) >= Retry_K.

Consequently the same equivalence holds uniformly over all allowed worlds. Its direction is source-to-shorter-target refinement, not a cost equivalence between the two source horizons.

**Proof.** Suppose the adjacent pair is invalid. By R1 and R3a some packet is missing from Retry_K. If it is success/failure, its adjacent trace also exists at H. If it is exhaustion with evidence e, R3 gives K<m_go(e)<=K+1; pumping supplies it at H, but it is still absent at K. Thus the larger pair is invalid.

Conversely suppose the larger pair is invalid. Choose a missing packet and a minimum path realizing its role (success, failure, or positive continuation). Let its length be m. By R3, K<m<=H. If m=K+1, this role already gives a missing packet at the adjacent horizon. If m>K+1, take the first K+1 attempts of the minimum path. They are successful and all go because the terminal, if any, is later. Let their final evidence be e. There cannot be a positive continuing path of length at most K to e: substituting it for this prefix, then following the same suffix, would give a shorter path for the selected role, contradicting minimality. The suffix remains available because future behavior depends only on current evidence and the same static world. The existing prefix has length K+1, so m_go(e)=K+1. Therefore Retry_(K+1) exhausts at e while Retry_K cannot. The adjacent pair is invalid. Contraposition proves the desired direction. QED.

This is a semantic reachability stabilization argument made applicable by two interface facts: each continuing state can be pumped without changing evidence, and exhaustion exposes that exact evidence. It is not a general theorem for arbitrary loop bodies or coarsened exhausted observations.

## R5. Small counterworlds and deterministic feedback

**Theorem R5.** If a cutoff K is invalid at any H>K, there is an invalid world with at most K+1 distinct retrieval outcomes and singleton (deterministic) feedback at every evidence value. The K+1 bound is sharp.

**Proof of the upper bound.** By R4 choose a packet missing from the adjacent source/target pair and a shortest path for its role. Its minimum length is exactly K+1 by R3: a smaller one would already give a target match. Restrict retrieval to the support of this path, using at most K+1 outcomes.

Choose singleton feedback values retaining the path. For an exhausted path all actions are go, so repeated evidence states pose no conflict. The same is true for the successful prefix of a failure path. For an ok path, all earlier actions are go and the last is stop. Its final evidence cannot have occurred at an earlier feedback: stop was available at that same evidence in the original world, so stopping earlier would have produced the allegedly missing packet within K attempts. Thus the last stop does not conflict with any earlier go at its key. At unvisited evidence values choose any one originally allowed action, possible by nonemptiness. This gives a deterministic subworld preserving the bad path. Restricting relations cannot create a target path, so its packet remains missing. Pump an exhausted adjacent witness to H using its retained final outcome/go; success and failure witnesses simply terminate at K+1. The same restricted world is invalid at H.

**Proof of sharpness.** For any K>=1, take K+1 distinct evidence atoms, empty initial evidence, one successful outcome adding each atom, no failures, and feedback always go. In a world with at most K outcomes, any reachable evidence union can be obtained using at most K retrievals and then pumped to K or H. Hence every such world is valid. The world containing all K+1 outcomes lets Retry_H return their entire union at exhaustion, while Retry_K cannot collect all atoms in K calls. Therefore a minimum invalid retrieval world has exactly K+1 outcomes. QED.

The theorem does not say the full feedback relation is always the only world to check for K>1. It justifies exhaustive search over deterministic refinements and small retrieval subsets. Neither ordinary general DAGs nor hidden exhaustion evidence have this bound.

## R6. Rank cutoffs and optimal worst-case bounds

Let d be the largest number of strict increases in a chain starting at e0 in L. Let delta=1 if the declared retrieval signature has a failure outcome and delta=0 otherwise. Set D=max(1,d+delta).

**Theorem R6 (rank cutoff).** For every allowed world, every H>=K>=D satisfies Retry_H >= Retry_K. With n initially missing Boolean evidence atoms, d=n. The bounds n+1 with failures and max(1,n) without failures are worst-case sharp.

**Proof.** A continuing path that repeats the same evidence at consecutive attempts can have that attempt removed without changing the subsequent evidence or any later allowed action. For a positive continuing path ending strictly above e0, remove every non-increasing step; what remains is a chain of at most d strict increases. If it ends at e0, one of its outcomes/go steps alone suffices. Thus every finite m_go is at most max(1,d).

For an ok path, let e be the final evidence. If e=e0, its last retrieval and stop can be taken directly, yielding length one. Otherwise, consider the first retrieval on the path that reaches e. At e the original final stop is available in the same static feedback world. Stop at this first arrival instead, discard later attempts, and delete all earlier non-increasing steps. At most d strict increases remain. Thus every finite m_ok is at most max(1,d).

For a failure path, remove all non-increasing steps from its successful prefix. If the prefix never leaves e0, remove it entirely. Otherwise at most d strict increases remain; append the original final failure outcome. This gives a path of at most d+1 attempts with the same failure tag and evidence. This case is absent when delta=0.

Every finite minimum from R3 is therefore at most D. Since K>=D, any source packet present at H is already present at K; use R3a (or identity when H=K). All deletions only reduce successful retrieval/feedback counts and retain the original terminal role.

For sharpness without failures and n>=2, take n singleton-adding successes and always-go feedback. The union of all n atoms is an exhaustion packet reachable at n but not n-1. With failures, add an empty-payload failure to n such success outcomes. The failure packet retaining all n atoms first needs n successful retrievals followed by the failure, so cutoff n is invalid at n+1. For n=0 the positive-horizon lower bound is one; for n=1 without failure it is also one. QED.

**Corollary R6a (upper interval).** Valid uniform cutoffs form a nonempty upper interval of positive integers with its minimum at most D.

**Proof.** Nonemptiness follows from R6. If K is valid and L>K, a packet of a source H>L matches Retry_K. A success/failure match terminates within K and therefore in L too. An exhausted match can be pumped from K to L with identical evidence. R3a supplies the cost relation. This holds in every world. QED.

The generic finite certificate engine can therefore test an intermediate cutoff through the explicitly unfolded adjacent pair K+1 versus K. Large binary H never has to be unfolded for this reduction. The state/evidence and path spaces can still be exponential in other input parameters. A rank bound is not a claim that finite models are always cheap.

## R7. Exact symbolic worst costs

**Theorem R7.** In a fixed world, if some enabled successful outcome s has go in B(A_s), Retry_H has the attained worst vector H(q+b). If there is an enabled success but none with that property, its attained worst vector is q+b. If all enabled outcomes are failures, it is q. Replace H by any target K for that target's formula.

**Proof.** In the first case repeat s and go H times at its unchanged singleton value A_s. Every path has at most H retrievals and H feedbacks, so this attained vector bounds all others. In the second case no first successful retrieval can continue. Every successful trace has one retrieval/feedback, while a failure has one retrieval only and is dominated by q+b. In the third case every trace fails on its first retrieval and has cost q. QED.

Any nonnegative scalar price vector can be applied to these exact vectors. The general DAG's componentwise maximum need not be jointly attained, whereas this macro's worst vector is. Arithmetic in binary H is exact; the large-horizon tests check these formulas and certificates, not H actual iterations or deployed latency.
