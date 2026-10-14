# Windows scientific replay

The 2026-10-14 Windows campaign ran twelve tasks successfully, including 119
tests in each interpreter mode. `records/` retains command, exit, parent-timeout
and stream bindings; `logs/` retains the original stdout/stderr. `outputs/` and
`baseline/` retain ten semantic summaries and 25 raw comparisons. All 25 raw files
agree under CRLF-to-LF normalization; seven also agree byte-for-byte. Summary
comparison excludes only host-dependent measurements. Stored bytes are unchanged.

`historical-source/` contains all 28 source bodies matching the frozen-after
inventory. Their captured identities postdate execution; the original commands
did not record pre-launch source hashes. Those source bodies support this
recorded campaign, while `results/managed-pointwise/tests/` documents the
142-test suite with pointwise-conformance regressions.

The recorded parent-wall sum is 56.6634853000578 seconds. Each child had a
1800-second parent timeout; Windows used no POSIX CPU/address-space caps, and
process-tree CPU/RSS were unavailable. File and source bindings are listed in
`manifest.json` and `historical-source-bindings.json`.
