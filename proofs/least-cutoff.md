# Least positive cutoff certificate

Fix one admitted declaration and source horizon H. By the adjacent-horizon and
upper-interval theorems, V={K:1<=K<=H and Retry_H refines Retry_K} is a nonempty
upper interval. Identity puts H in V. Let K*=min V.

A bundle names K, a checked valid ordinary cutoff certificate at K, and, if
K>1, a checked invalid ordinary cutoff certificate at K-1. Each component is
bound to the identical input declaration and H. For K=1 the lower component
must be null. No search history is trusted.

**Theorem.** Such a bundle is accepted exactly for K=K*.

**Proof.** The upper component puts K in V. At K=1 this proves minimum over
positive cutoffs. Otherwise the lower component puts K-1 outside V. A smaller
valid J would put K-1 in V by upper-interval closure, contradiction. Conversely
the minimum has a positive certificate by finite certificate completeness and
its predecessor, when present, has a negative certificate. QED.

The producer initializes [low,high]=[1,min(H,D)] with the rank bound D. The
upper endpoint is valid by identity or rank. A positive midpoint replaces high;
a negative midpoint replaces low by midpoint+1. The interval invariant is that
all cutoffs below low are invalid and high is valid. Each step preserves the
invariant and decreases interval length. At equality the endpoint is K*.
There are at most ceil(log2(min(H,D))) midpoint decisions plus at most two
component constructions. Their individual world and evidence-state cost can
be exponential. UNKNOWN propagates rather than taking either branch.

`src/cutoff_search.py` implements search. `src/cutoff_replay.py` imports only
admission and ordinary replay, not search or the certificate producer.
`tests/test_least.py` checks semantic examples, a bounded direct-oracle sweep,
wrong endpoints, wrong horizon, missing components and Boolean/zero admission.
The written theorem is not a proof-assistant certification of Python code.
