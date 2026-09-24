# Boundary counterexamples and non-claims

## B1. Erasing exhaustion evidence destroys adjacency and constant small worlds

For n>=3, use n singleton-adding successful outcomes, empty initial evidence, and deterministic feedback that stops exactly when all n atoms are present. Let the observable exhausted packet omit evidence, but keep successful evidence exact. At horizons one and two the only packet is this undistinguished exhaustion, so cutoff one passes the adjacent test. At horizon n, retrieving all n outcomes permits a success packet unavailable at horizon one. Thus Theorem R4 fails under this coarser observation.

Every proper retrieval subset still produces only undistinguished exhaustion at every horizon, so no world with fewer than n outcomes witnesses the failure. This refutes a constant retrieval-world bound under that observation. The missing exhausted evidence, not an increased processor budget, is the reason the earlier theorem no longer applies.

## B2. Cardinality and shortest source trace are different objectives

Use the same n-outcome threshold feedback but retain exact exhaustion evidence and let H>n. A two-outcome world is invalid: the source exhausts at H with the union of those two atoms, unavailable in one target retrieval. It has no successful terminal, so its first mismatching terminal is at H. In the full n-outcome world, the source can stop successfully after n calls, which is shorter. No successful path can stop before n, and no exhausted path stops before H. Thus global shortest mismatch length is n, while every cardinality-two witness needs H calls. Macro witnesses minimize retrieval-world cardinality before length; the general graph producer orders challenged trace length before conditional world minimization.

## B3. Hiding failure evidence removes an exact-law obligation

If a failure packet contains only its failure label, condition (B) of R2 is no longer necessary. Under (A), the same singleton-representative invariant matches success and exhaustion. Any source failure can be matched by choosing its final failure outcome directly, because its hidden accumulated evidence need not be matched. Necessity of (A) still follows from the incomparable-success world, which has no failure. Hence (A) alone is exact for this alternative interface. This is a distinct declared semantics, not permission for the checker to erase evidence silently.

In the original exact interface, if an enabled failure has no evidence beyond e0, (B) forces A_c=e0 for every continuing-capable c. Any continuation that accumulates genuinely new evidence may later reveal it in a failure packet. A cache transformation can then change observable audit information even if the failure label is unchanged.

## B4. Mandatory outcomes change the quantifier domain

Consider additions {a}, {b}, and {a,b}, with no failures and always-go feedback. Require the {a,b} outcome to be enabled in every world. A_c and A_s for the singleton outcomes are incomparable, so R2's original test rejects. Nevertheless every permitted world is closed under the relevant joins because {a,b} is always available, and any source terminal union has an enabled singleton retrieval representative. Collapse is valid. The necessity proof's two-outcome world {{a},{b}} is prohibited. The original theorem assumes nonempty restrictions with no mandatory lower bound. A richer contract needs a correspondingly different minimal-world analysis.

## B5. Public iteration events prohibit private collapse

Even one deterministic successful outcome with always-go feedback distinguishes Retry_2 from Collapse when each retrieval publicly emits its call event: their observed words have lengths two and one. The equations about evidence and private resource costs do not erase public events. A capsule must declare whether call counts, prompts, feedback transitions, timestamps, or internal audit records are observable.

## B6. Different nondeterminism contracts are not interchangeable

A deterministic oracle table fixes one outcome per key across the execution. Caching that outcome is qualitatively different from retaining all outcomes in a static nonempty relation and making fresh choices. Conversely a consumptive response iterator changes availability after each call and violates the persistent-world assumption. Distributional independence, probabilities of success, and fairness are not inferred from set-valued reachability.

Even two keys with identical full allowed outcome tables are not interchangeable. Give both keys outcomes a and b, branch to different observed tags on those outcomes, and let a world restrict the first key to a and the second to b. Replacing one key by the other changes the observed tag despite equality in the unrestricted world. The supplied finite program cases equalize their charges so this example isolates sharing, not resource price.

## B7. Componentwise trace domination is stronger than worst scalar domination

A source chooses a trace of cost (2,0) or (0,2), and a target has cost (1,1), with the same observation. For every nonnegative price pair (u,v), u+v<=max(2u,2v), so target worst scalar cost is bounded by source worst scalar cost. Neither source trace dominates (1,1) componentwise. The required single-trace resource match fails. One may choose a weaker price-specific relation, but it is not the relation checked here.

## B8. Provenance and application boundary

Tokens are immutable nominal identifiers with declared source strings. Equal sets prove equality of these identifiers, not logical entailment of an answer, causal influence of every token, accuracy of retrieval, or fidelity to an empirical model. No language model, retriever, production cache, corpus, hardware service, or human study is executed. Public papers motivate program structure and provide comparison; their measured quality results are not inherited by these abstract theorems.
