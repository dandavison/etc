### Questions

-   Should we collect data on numbers of non-affected relatives in
    addition to affected?

### TODO

- Power analysis
- Validation on existing data?


sensitivity: Compute causality score for each known deleterious variant.
specificity: Compute causality score for probands with neither VUS nor known del.

evidence:

- Their variant's causality score compared to those of known deleterious variants



The main scenario is:

#### Scenario 1: A VUS associated with disease incidence in relatives:

We have performed exon sequencing of the relevant disease genes for an
individual and discovered a Variant of Uncertain Significance (VUS).
Initially we lack any further evidence regarding whether or not the
variant is causative. Subsequently, we discover the same VUS in other
individuals, some of which have affected relatives. How many other
individuals, with what sorts of patterns of family disease incidence,
are sufficient to conclude that the variant should be reported as likely
deleterious?

We may also sequence some affected individuals. This is equivalent to a
sequenced individual having an affected relative with relatedness
coefficient equal to 1 (identical twin).

Consider a VUS at locus $l$ which has been observed in several
individuals. A variant classification algorithm should have the
following properties:

1.  The strength of evidence for pathogenicity of $l$ increases with the
    number of families in which there are affected individuals related
    to an individual with the VUS

2.  The evidence for pathogenicity of $l$ is stronger if the affected
    individuals are more closely related to the sequenced individual
    with the VUS.

