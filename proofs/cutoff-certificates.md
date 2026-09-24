# Local certificates for horizon cutoffs

The macros are Boolean-evidence implementations of Theorems R1--R6. They do not implement arbitrary finite semilattices; the written theorems do not depend on distributivity.

## D1. The positive continuing graph

Fix one retrieval world R and one deterministic feedback refinement B. Add a fresh root r distinct from every evidence value. For each success s with B(A_s)=go, put an edge r -> A_s. For each evidence e and success s with B(e join d_s)=go, put an edge e -> e join d_s. Each edge has weight one. The shortest root-to-e distance is exactly the positive continuing distance m_go(e). The fresh root matters when e=e0: a positive continuing path of length one must not be confused with an empty execution of length zero.

A distance certificate assigns each evidence value either infinity or an integer from 1 through |L|. Every finite entry has a parent edge, either from the root with distance one or from an evidence predecessor with distance one smaller. In addition, every root edge reaches a finite value of distance at most one, and every edge from a finite value reaches a finite value with distance at most its predecessor's distance plus one.

**Theorem D1 (local exactness).** The distance labels satisfy these conditions if and only if they are exact shortest positive continuing distances, with suitable parent witnesses.

**Proof.** Following a parent strictly decreases a positive integer until it reaches a root parent. This constructs a legal path of exactly the assigned length, proving that true distance is at most the label. For any actual root path, the root condition makes its first label finite and at most one. Induction along the path using the edge inequalities makes its final label finite and no larger than its path length. Taking the shortest path proves label at most true distance. An infinity label is unreachable by the same induction. These directions give equality. Conversely choose shortest paths for all reachable evidence values and give each a predecessor on such a path. Their labels and parents satisfy all conditions. A shortest path does not repeat an evidence vertex, so its length is at most |L|. QED.

This is an ordinary shortest-path potential/parent certificate, specialized to a positive-length continuation graph. The local certificate structure, not BFS itself, is checked by the consumer.

## D2. Exact terminal distances

For each successful final outcome s whose joined evidence permits stop, a candidate ok distance is one from the root or m_go(e)+1 from each reachable continuing evidence e. For each failure f, the same candidates give its failure-label/evidence distance, without feedback on the last call. The minimum over candidates is the exact terminal-role distance.

**Proof.** Every such candidate is a continuing prefix (or the empty root prefix) followed by the stated final retrieval and terminal action, so it is feasible. Every finite terminal trace has exactly one final retrieval of this form; its earlier calls form a continuing prefix. Replacing that prefix by its minimum-distance path gives one of the candidates and cannot increase length. Taking minima gives equality. Failure labels may coincide: minima are grouped by the complete (label,evidence) packet, not by outcome identity. QED.

A world is stable at cutoff K exactly when every finite positive continuing distance and every finite terminal distance is at most K. One direction follows directly from R3. For the other, if some distance exceeds K then either a shortest missing role already has length K+1 or its first K+1 continuing steps give a missing exhausted packet, by R4. Therefore the adjacent pair is invalid. Fixed costs make packet stability equivalent to the full two-sided cost relation by R3a.

## D3. Complete finite certificate modes

Identity certificates require K=H. One-attempt certificates require K=1 and replay the exact R2 condition (or its concrete two-outcome witness). Rank certificates compute D=max(1,n-popcount(e0)+delta) and require K>=D. Neither rule unfolds H.

Otherwise enumerate, in canonical order, every nonempty retrieval subset of at most K+1 declared outcomes and every deterministic feedback refinement of the declared relation. An accepting certificate contains a locally checked D1 row for each such world and passes the terminal-distance condition D2 in every row. A rejected certificate contains one such world, a length-K+1 outcome path, and an exact packet absent from Retry_K. Rejection replay executes the supplied path and the complete bounded target state sets. R4 supplies the lifting to the original H: success/failure paths still stop at K+1, and an exhausted path repeats its final success/go H-K-1 additional times.

**Theorem D3 (soundness and finite completeness).** Without explicit implementation resource caps, the certificate modes decide uniform cutoff refinement for every admitted finite Boolean-evidence capsule and binary H,K.

**Proof.** Identity, collapse and rank modes are sound by their respective theorems. For universal rows, D1 and D2 establish stability of every enumerated small deterministic world. If the original uniform refinement were invalid, R5 would supply an invalid world among exactly these rows, a contradiction. Thus acceptance is sound. Rejection is sound because replay checks an actual adjacent counterworld and R4 lifts it. For completeness, identity/collapse/rank may conclude immediately. Otherwise the enumeration is finite. A valid contract has exact distance rows in every world by D1, all passing D2. An invalid contract has an enumerated bad world by R5; R4 provides an adjacent counterpacket with a length-K+1 witness. A breadth-first producer can construct that witness using exact distances. QED.

For m declared retrieval outcomes and a ambiguous feedback values, the universal row count is 2^a times sum_{i=1}^{min(K+1,m)} binomial(m,i). With n evidence bits a row has 2^n distance slots. These explicit dimensions are reported; binary encoding of H does not make either dimension polynomial. The implementation rejects oversized certificate counts before iterating the expected world product and reports resource exhaustion as UNKNOWN. The producer's shortest-path computation, independent consumer's local checks, and direct finite operational oracle are separate algorithms, but share the paper's semantic assumptions and the same authorship workflow.
