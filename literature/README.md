# Source calibration and bibliography audit

The matrix contains 17 distinct full papers: 12 TOPLAS articles and five
adjacent-venue articles. Five relevant influential articles overlap the matrix
(three TOPLAS and two adjacent), as explained in influential-selection.csv.
They calibrate foundations and demonstrated methodological uptake, not a
citation-count ranking. No award, nomination, or independent review is claimed.
The retained 12-paper records precede this continuation; the five adjacent
full-text records were completed here. An abstract is not counted as a full read.

The TOPLAS reference counts are 19, 40, 39, 34, 41, 57, 44, 13, 107, 62, 35 and
79; their median is 40.5. The current manuscript has 44 cited scholarly entries.
This is a deliberately relevant finite sample, not a random census of TOPLAS
and not an official reference-count rule. Publication dates, read editions and
reference counts are separate fields. An author's extended manuscript may be
longer than the published article. Generic draft headers are not publication
dates. The final paper uses eight sections rather than copying another paper's
outline. Definitions, central proofs and failure boundaries precede experiments;
figures expose quantifiers and representation sizes rather than decorate claims.

The adjacent papers were selected for distinct roles: Benton for relational
analysis/rewriting, Antonopoulos for trace-refinement inference, Alive2 for
bounded validation, GKAT for algebraic equivalence, and Appel for foundational
proof checking. Their core arguments, boundaries, evaluation scope and figure
roles are recorded. GKAT's read edition has 58 pages, 51 bibliography entries,
and nine main sections; its published edition has 28 pages. Appel's accessible
preprint has ten pages. The original retained citation's 247-256 interval was
corrected to 247-258 using the bibliography of the author's A Trustworthy Proof
Checker; an author preprint's physical length is not a published page interval.

Closest recent work was checked beyond the original bibliography: Cheng et al.
(2026) develop denotational compositional compiler verification, with formal
proof infrastructure much stronger than this Python artifact. Dai et al.'s
LLM4Code 2026 caching paper (2025 preprint) addresses statistical independence,
not this paper's static possibility semantics. Parthasarathy et al. (2024)
validate an IVL translation pipeline. None was rerun here. Their stronger or
different guarantees are acknowledged in the manuscript rather than erased to
support novelty. The general support-cover construction and local shortest-path
witnesses are treated as standard principles, not claimed as first inventions.

The originating Grounding by Trying paper is an empirical adaptive retrieval
method: published author order is Sheryl Hsu, Omar Khattab, Chelsea Finn,
Archit Sharma; the preprint is from October 2024 and the ICLR paper is from
2025. Its full text supports trial/feedback-driven retrieval as motivation but
not trace-refinement, resource-effect or certificate-completeness theorems.
No empirical result or authorship agreement is inherited from that paper.

`bibliography-audit.csv` identifies every scholarly entry and the specific
supporting topic/contrast. It distinguishes full calibration reads from narrow
background/source checks; it does not claim that all 44 papers were fully
reimplemented or that every bibliography entry is an independent baseline.
Source PDFs are not redistributed; primary scholarly identifiers and lawful
access locations are retained. No external source's implementation was modified.
